"""
Вспомогательный скрипт для сохранения snapshots документов
Используйте этот скрипт ПОСЛЕ развёртывания API на Render
"""

import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
API_URL = os.getenv("API_URL", "http://localhost:5000")  # Замените на ваш URL
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

if not ADMIN_API_KEY:
    print("❌ Ошибка: ADMIN_API_KEY не задан в .env файле")
    exit(1)


def save_snapshot(document_type, version, full_text, language="ru", created_by="admin"):
    """
    Сохранить snapshot документа
    
    Args:
        document_type: ticket_terms | refund_policy | privacy_policy
        version: версия документа (например, v2025-10-28)
        full_text: полный текст документа
        language: ru | en | he
        created_by: кто создал snapshot
    """
    
    # Вычисляем хеш
    content_hash = hashlib.sha256(full_text.encode('utf-8')).hexdigest()
    
    print(f"\n📄 Сохранение snapshot документа:")
    print(f"   Тип: {document_type}")
    print(f"   Версия: {version}")
    print(f"   Язык: {language}")
    print(f"   Длина текста: {len(full_text)} символов")
    print(f"   SHA-256 хеш: {content_hash}")
    
    data = {
        "document_type": document_type,
        "version": version,
        "full_text": full_text,
        "language": language,
        "created_by": created_by
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": ADMIN_API_KEY
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/document-snapshot",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Snapshot сохранён успешно!")
            print(f"   ID: {result['snapshot_id']}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False


def load_document_from_file(file_path):
    """Загрузить текст документа из файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Файл не найден: {file_path}")
        return None


def main():
    """
    Пример использования:
    
    1. Сохраните тексты документов в файлы:
       - ticket_terms_ru.txt
       - refund_policy_ru.txt
       - privacy_policy_ru.txt
    
    2. Запустите этот скрипт:
       python save_document_snapshot.py
    """
    
    print("=" * 60)
    print("📦 Сохранение snapshots документов")
    print("=" * 60)
    
    # Проверяем подключение
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ API доступен: {API_URL}")
        else:
            print(f"⚠️ API вернул код: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        print(f"   Проверьте URL: {API_URL}")
        return
    
    # Текущая версия документов
    version = "v2025-10-28"  # Измените на актуальную версию!
    
    # Сохраняем snapshots
    documents = [
        {
            "type": "ticket_terms",
            "file": "ticket_terms_ru.txt",
            "name": "Условия продажи билетов"
        },
        {
            "type": "refund_policy",
            "file": "refund_policy_ru.txt",
            "name": "Политика возврата"
        },
        {
            "type": "privacy_policy",
            "file": "privacy_policy_ru.txt",
            "name": "Политика конфиденциальности"
        }
    ]
    
    success_count = 0
    
    for doc in documents:
        print(f"\n{'='*60}")
        print(f"Обработка: {doc['name']}")
        print(f"{'='*60}")
        
        # Загружаем текст из файла
        text = load_document_from_file(doc['file'])
        
        if text:
            if save_snapshot(doc['type'], version, text, language="ru"):
                success_count += 1
        else:
            print(f"⏭️ Пропускаем {doc['name']}")
    
    print(f"\n{'='*60}")
    print(f"✅ Сохранено snapshots: {success_count} из {len(documents)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

