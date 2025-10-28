"""
Flask API для логирования согласий с документами при покупке билетов
Минимальная версия - только логирование, без платежей
"""

import os
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

from database_tickets import TicketDatabase

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# CORS - разрешаем запросы только с вашего домена Tilda
# После тестирования замените '*' на ваш домен: 'https://your-site.tilda.ws'
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Инициализация БД
db = TicketDatabase()

# Константы
ALLOWED_DOCUMENT_TYPES = ['ticket_terms', 'refund_policy', 'privacy_policy']
DOCUMENT_VERSION = os.getenv("DOCUMENT_VERSION", "v2025-10-28")


def get_client_ip(request_obj):
    """Получить реальный IP клиента (с учётом прокси)"""
    # Render передаёт реальный IP в X-Forwarded-For
    forwarded_for = request_obj.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Берём первый IP из цепочки (клиентский)
        return forwarded_for.split(',')[0].strip()
    return request_obj.remote_addr


def get_ip_country(ip_address):
    """
    Получить страну по IP (заглушка)
    TODO: Интегрировать с сервисом геолокации (MaxMind, ip-api.com)
    """
    # Пока возвращаем None, можно добавить позже
    return None


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'service': 'ticket-consent-logger',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/consent', methods=['POST', 'OPTIONS'])
def log_consent():
    """
    Логирование согласия пользователя с документом
    
    Ожидаемый JSON:
    {
        "session_id": "uuid",
        "document_type": "ticket_terms|refund_policy|privacy_policy",
        "document_version": "v2025-10-28",
        "document_hash": "sha256_hash",
        "consent_given": true,
        "consent_timestamp": "2025-10-28T12:34:56.789Z",
        "user_agent": "Mozilla/5.0...",
        "referrer": "https://...",
        "page_url": "https://..."
    }
    """
    # OPTIONS для CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        # Валидация обязательных полей
        required_fields = [
            'session_id', 'document_type', 'document_version',
            'document_hash', 'consent_given', 'consent_timestamp'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400
        
        # Валидация типа документа
        if data['document_type'] not in ALLOWED_DOCUMENT_TYPES:
            return jsonify({
                'error': 'Invalid document_type',
                'allowed': ALLOWED_DOCUMENT_TYPES
            }), 400
        
        # Получаем технические данные
        client_ip = get_client_ip(request)
        client_ip_forwarded = request.headers.get('X-Forwarded-For')
        ip_country = get_ip_country(client_ip)
        
        # Сохраняем в БД
        consent_log = {
            'session_id': data['session_id'],
            'document_type': data['document_type'],
            'document_version': data['document_version'],
            'document_hash': data['document_hash'],
            'consent_given': data['consent_given'],
            'consent_timestamp': data['consent_timestamp'],
            'consent_text': data.get('consent_text', f"Я согласен с {data['document_type']}"),
            'client_ip': client_ip,
            'client_ip_forwarded': client_ip_forwarded,
            'user_agent': data.get('user_agent', request.headers.get('User-Agent')),
            'ip_country': ip_country,
            'referrer_url': data.get('referrer'),
            'page_url': data.get('page_url')
        }
        
        consent_log_id = db.create_consent_log(consent_log)
        
        logger.info(f"Consent logged: {consent_log_id} - {data['document_type']} - session: {data['session_id']}")
        
        return jsonify({
            'success': True,
            'consent_log_id': consent_log_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 201
    
    except Exception as e:
        logger.error(f"Error logging consent: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/consent/verify/<session_id>', methods=['GET'])
def verify_consents(session_id):
    """
    Проверить, что все три согласия получены для сессии
    
    Возвращает:
    {
        "session_id": "uuid",
        "all_consents_given": true/false,
        "consents": {
            "ticket_terms": true/false,
            "refund_policy": true/false,
            "privacy_policy": true/false
        }
    }
    """
    try:
        consents = db.get_consents_by_session(session_id)
        
        # Проверяем наличие всех трёх согласий
        consent_status = {
            'ticket_terms': False,
            'refund_policy': False,
            'privacy_policy': False
        }
        
        for consent in consents:
            if consent['consent_given']:
                consent_status[consent['document_type']] = True
        
        all_given = all(consent_status.values())
        
        return jsonify({
            'session_id': session_id,
            'all_consents_given': all_given,
            'consents': consent_status,
            'total_logged': len(consents)
        }), 200
    
    except Exception as e:
        logger.error(f"Error verifying consents: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/document-snapshot', methods=['POST'])
def save_document_snapshot():
    """
    Сохранить snapshot документа (для администраторов)
    
    Ожидаемый JSON:
    {
        "document_type": "ticket_terms|refund_policy|privacy_policy",
        "version": "v2025-10-28",
        "full_text": "полный текст документа",
        "language": "ru|en|he",
        "created_by": "admin_name"
    }
    """
    try:
        # Простая защита: требуем API ключ
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('ADMIN_API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        # Валидация
        required_fields = ['document_type', 'version', 'full_text', 'language']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400
        
        # Вычисляем хеш
        content_hash = hashlib.sha256(data['full_text'].encode('utf-8')).hexdigest()
        
        # Сохраняем
        snapshot_id = db.create_document_snapshot({
            'document_type': data['document_type'],
            'version': data['version'],
            'content_hash': content_hash,
            'full_text': data['full_text'],
            'language': data['language'],
            'created_by': data.get('created_by', 'api')
        })
        
        logger.info(f"Document snapshot saved: {snapshot_id}")
        
        return jsonify({
            'success': True,
            'snapshot_id': snapshot_id,
            'content_hash': content_hash
        }), 201
    
    except Exception as e:
        logger.error(f"Error saving document snapshot: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Для локальной разработки
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

