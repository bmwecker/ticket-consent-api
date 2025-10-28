"""
Модуль работы с базой данных для системы продажи билетов
Использует ту же PostgreSQL БД, что и Telegram бот
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, List
import logging

# Используем psycopg (как в основном боте)
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

# Подключение к БД (та же, что и у бота)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Render использует postgres://, но psycopg требует postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


class TicketDatabase:
    """Класс для работы с БД билетов и согласий"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.init_database()
    
    def get_connection(self):
        """Получить подключение к БД"""
        return psycopg.connect(self.database_url, row_factory=dict_row)
    
    def init_database(self):
        """Инициализация таблиц для билетов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Таблица consent_logs (логи согласий)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consent_logs (
                    consent_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    purchase_id UUID,
                    session_id UUID NOT NULL,
                    
                    document_type TEXT NOT NULL 
                        CHECK (document_type IN ('ticket_terms', 'refund_policy', 'privacy_policy')),
                    
                    document_version TEXT NOT NULL,
                    document_hash TEXT NOT NULL,
                    
                    consent_given BOOLEAN NOT NULL DEFAULT TRUE,
                    consent_text TEXT,
                    consent_timestamp TIMESTAMPTZ NOT NULL,
                    
                    client_ip TEXT,
                    client_ip_forwarded TEXT,
                    user_agent TEXT,
                    ip_country TEXT,
                    referrer_url TEXT,
                    page_url TEXT,
                    
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            
            # Индексы для consent_logs
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consent_session 
                ON consent_logs(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consent_type 
                ON consent_logs(document_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_consent_timestamp 
                ON consent_logs(consent_timestamp)
            """)
            
            # Таблица document_snapshots (архив версий документов)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_snapshots (
                    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    
                    document_type TEXT NOT NULL 
                        CHECK (document_type IN ('ticket_terms', 'refund_policy', 'privacy_policy')),
                    
                    version TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    
                    full_text TEXT NOT NULL,
                    language TEXT NOT NULL CHECK (language IN ('ru', 'en', 'he')),
                    
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_by TEXT,
                    
                    UNIQUE(document_type, language, version)
                )
            """)
            
            # Индекс для document_snapshots
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_active 
                ON document_snapshots(document_type, language, is_active)
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
    
    def create_consent_log(self, consent_data: Dict) -> str:
        """
        Создать запись о согласии
        
        Args:
            consent_data: словарь с данными согласия
        
        Returns:
            UUID созданной записи (строка)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO consent_logs (
                    session_id, document_type, document_version, document_hash,
                    consent_given, consent_text, consent_timestamp,
                    client_ip, client_ip_forwarded, user_agent,
                    ip_country, referrer_url, page_url
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING consent_log_id
            """, (
                consent_data['session_id'],
                consent_data['document_type'],
                consent_data['document_version'],
                consent_data['document_hash'],
                consent_data['consent_given'],
                consent_data.get('consent_text'),
                consent_data['consent_timestamp'],
                consent_data.get('client_ip'),
                consent_data.get('client_ip_forwarded'),
                consent_data.get('user_agent'),
                consent_data.get('ip_country'),
                consent_data.get('referrer_url'),
                consent_data.get('page_url')
            ))
            
            result = cursor.fetchone()
            consent_log_id = str(result['consent_log_id'])
            
            conn.commit()
            return consent_log_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating consent log: {e}")
            raise
        finally:
            conn.close()
    
    def get_consents_by_session(self, session_id: str) -> List[Dict]:
        """
        Получить все согласия для сессии
        
        Args:
            session_id: UUID сессии
        
        Returns:
            Список словарей с согласиями
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    consent_log_id, session_id, document_type,
                    document_version, consent_given, consent_timestamp
                FROM consent_logs
                WHERE session_id = %s
                ORDER BY consent_timestamp ASC
            """, (session_id,))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        finally:
            conn.close()
    
    def create_document_snapshot(self, snapshot_data: Dict) -> str:
        """
        Создать snapshot документа
        
        Args:
            snapshot_data: словарь с данными документа
        
        Returns:
            UUID созданного snapshot (строка)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Деактивируем предыдущие версии этого документа
            cursor.execute("""
                UPDATE document_snapshots
                SET is_active = FALSE
                WHERE document_type = %s 
                AND language = %s 
                AND is_active = TRUE
            """, (snapshot_data['document_type'], snapshot_data['language']))
            
            # Создаём новую версию
            cursor.execute("""
                INSERT INTO document_snapshots (
                    document_type, version, content_hash,
                    full_text, language, created_by
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                RETURNING snapshot_id
            """, (
                snapshot_data['document_type'],
                snapshot_data['version'],
                snapshot_data['content_hash'],
                snapshot_data['full_text'],
                snapshot_data['language'],
                snapshot_data.get('created_by')
            ))
            
            result = cursor.fetchone()
            snapshot_id = str(result['snapshot_id'])
            
            conn.commit()
            return snapshot_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating document snapshot: {e}")
            raise
        finally:
            conn.close()
    
    def get_active_document(self, document_type: str, language: str) -> Optional[Dict]:
        """
        Получить активную версию документа
        
        Args:
            document_type: тип документа
            language: язык
        
        Returns:
            Словарь с данными документа или None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT *
                FROM document_snapshots
                WHERE document_type = %s 
                AND language = %s 
                AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """, (document_type, language))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        finally:
            conn.close()
    
    def get_consent_stats(self, date_from: Optional[str] = None) -> Dict:
        """
        Получить статистику по согласиям
        
        Args:
            date_from: начальная дата (ISO format)
        
        Returns:
            Словарь со статистикой
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT 
                    COUNT(*) as total_consents,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(*) FILTER (WHERE document_type = 'ticket_terms') as ticket_terms_count,
                    COUNT(*) FILTER (WHERE document_type = 'refund_policy') as refund_policy_count,
                    COUNT(*) FILTER (WHERE document_type = 'privacy_policy') as privacy_policy_count
                FROM consent_logs
            """
            
            params = []
            if date_from:
                query += " WHERE consent_timestamp >= %s"
                params.append(date_from)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            return dict(result) if result else {}
            
        finally:
            conn.close()

