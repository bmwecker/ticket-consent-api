# 🎫 Микросервис логирования согласий для системы продажи билетов

## 📝 Описание

API-сервис для юридически защищённого логирования согласий пользователей с документами при покупке билетов на саммит.

### Что логируется:

- ✅ Тип документа (Условия продажи, Политика возврата, Политика конфиденциальности)
- ✅ Версия документа и SHA-256 хеш содержимого
- ✅ Точное время согласия (UTC, ISO 8601)
- ✅ IP адрес пользователя (и X-Forwarded-For)
- ✅ User Agent (браузер и устройство)
- ✅ Страна по IP (опционально)
- ✅ Уникальный ID сессии

### Для чего это нужно:

1. **Юридическая защита**: доказательство согласия пользователя с условиями
2. **GDPR compliance**: соответствие требованиям защиты данных
3. **Аудит**: полная история согласий для бухгалтерии и юристов
4. **Неизменяемость**: архив версий документов с хешами

---

## 🏗️ Архитектура

```
Tilda страница (JavaScript)
        ↓ HTTPS POST
Flask API (этот сервис)
        ↓
PostgreSQL (те же БД, что и Telegram бот)
```

### Технологии:

- **Flask** - веб-фреймворк
- **PostgreSQL** - база данных
- **psycopg** - драйвер PostgreSQL
- **Gunicorn** - production сервер
- **Render.com** - хостинг

---

## 📦 Структура проекта

```
ticket-service/
├── api.py                    # Flask API с endpoints
├── database_tickets.py       # Работа с PostgreSQL
├── requirements.txt          # Зависимости Python
├── Procfile                  # Конфигурация для Render
├── runtime.txt               # Версия Python
├── tilda-consent-logger.js   # JavaScript для Tilda
├── DEPLOY_GUIDE.md           # Инструкция по развёртыванию
└── README.md                 # Этот файл
```

---

## 🗄️ Структура базы данных

### Таблица `consent_logs`

Хранит логи согласий пользователей:

| Поле | Тип | Описание |
|------|-----|----------|
| `consent_log_id` | UUID | Уникальный ID записи |
| `session_id` | UUID | ID сессии пользователя |
| `document_type` | TEXT | Тип документа (ticket_terms/refund_policy/privacy_policy) |
| `document_version` | TEXT | Версия документа (v2025-10-28) |
| `document_hash` | TEXT | SHA-256 хеш содержимого |
| `consent_given` | BOOLEAN | Согласие дано (true) |
| `consent_timestamp` | TIMESTAMPTZ | Время согласия (UTC) |
| `client_ip` | TEXT | IP адрес клиента |
| `user_agent` | TEXT | Браузер/устройство |
| `ip_country` | TEXT | Страна по IP |

### Таблица `document_snapshots`

Архив версий документов:

| Поле | Тип | Описание |
|------|-----|----------|
| `snapshot_id` | UUID | Уникальный ID snapshot |
| `document_type` | TEXT | Тип документа |
| `version` | TEXT | Версия |
| `content_hash` | TEXT | SHA-256 хеш |
| `full_text` | TEXT | Полный текст документа |
| `language` | TEXT | Язык (ru/en/he) |
| `is_active` | BOOLEAN | Активная версия |

---

## 🔌 API Endpoints

### `GET /health`

Проверка здоровья сервиса.

**Ответ:**
```json
{
  "status": "healthy",
  "service": "ticket-consent-logger",
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

---

### `POST /api/consent`

Логирование согласия с документом.

**Запрос:**
```json
{
  "session_id": "uuid",
  "document_type": "privacy_policy",
  "document_version": "v2025-10-28",
  "document_hash": "sha256_hash",
  "consent_given": true,
  "consent_timestamp": "2025-10-28T12:00:00Z",
  "user_agent": "Mozilla/5.0...",
  "referrer": "https://...",
  "page_url": "https://..."
}
```

**Ответ (201 Created):**
```json
{
  "success": true,
  "consent_log_id": "uuid",
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

---

### `GET /api/consent/verify/<session_id>`

Проверка, что все три согласия даны.

**Ответ:**
```json
{
  "session_id": "uuid",
  "all_consents_given": true,
  "consents": {
    "ticket_terms": true,
    "refund_policy": true,
    "privacy_policy": true
  },
  "total_logged": 3
}
```

---

### `POST /api/document-snapshot`

Сохранение snapshot документа (требует API ключ).

**Заголовки:**
```
X-API-Key: your-admin-api-key
```

**Запрос:**
```json
{
  "document_type": "ticket_terms",
  "version": "v2025-10-28",
  "full_text": "Полный текст документа...",
  "language": "ru",
  "created_by": "admin"
}
```

**Ответ (201 Created):**
```json
{
  "success": true,
  "snapshot_id": "uuid",
  "content_hash": "sha256_hash"
}
```

---

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий**
   ```bash
   cd ticket-service
   ```

2. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   .\venv\Scripts\activate   # Windows
   ```

3. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте переменные окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env и укажите DATABASE_URL
   ```

5. **Запустите сервер**
   ```bash
   python api.py
   ```

   API будет доступен на `http://localhost:5000`

6. **Проверьте**
   ```bash
   curl http://localhost:5000/health
   ```

---

## 📤 Деплой на Render

Подробная инструкция в файле **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)**.

Краткая версия:
1. Загрузите код на GitHub
2. Создайте Web Service на Render
3. Подключите PostgreSQL БД
4. Добавьте переменные окружения
5. Деплой!

---

## 🔒 Безопасность

### Что реализовано:

- ✅ CORS защита (ограничение доменов)
- ✅ HTTPS обязательно
- ✅ API ключ для админ-функций
- ✅ Валидация всех входных данных
- ✅ Логирование всех операций
- ✅ Хеширование содержимого документов (SHA-256)

### Что нужно настроить:

1. **CORS**: Укажите домен Tilda в `ALLOWED_ORIGINS`
2. **API ключ**: Сгенерируйте сложный `ADMIN_API_KEY`
3. **PostgreSQL**: Используйте Internal URL на Render
4. **Мониторинг**: Регулярно проверяйте логи

---

## 📊 Мониторинг

### Логи на Render

```
Dashboard → ticket-consent-api → Logs
```

### Статистика в БД

```sql
-- Всего согласий
SELECT COUNT(*) FROM consent_logs;

-- По типам документов
SELECT document_type, COUNT(*) 
FROM consent_logs 
GROUP BY document_type;

-- Последние 10 согласий
SELECT session_id, document_type, consent_timestamp 
FROM consent_logs 
ORDER BY consent_timestamp DESC 
LIMIT 10;
```

---

## 🧪 Тестирование

### Тест health check

```bash
curl https://your-api.onrender.com/health
```

### Тест логирования согласия

```bash
curl -X POST https://your-api.onrender.com/api/consent \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "document_type": "privacy_policy",
    "document_version": "v2025-10-28",
    "document_hash": "abc123",
    "consent_given": true,
    "consent_timestamp": "2025-10-28T12:00:00Z"
  }'
```

### Тест проверки согласий

```bash
curl https://your-api.onrender.com/api/consent/verify/test-123
```

---

## 🛠️ Обновление версий документов

**При изменении текста любого документа:**

1. Измените версию в `.env`:
   ```
   DOCUMENT_VERSION=v2025-11-15
   ```

2. Обновите JavaScript на Tilda (в `DOCUMENT_VERSIONS`)

3. Сохраните новый snapshot через API:
   ```bash
   curl -X POST https://your-api.onrender.com/api/document-snapshot \
     -H "Content-Type: application/json" \
     -H "X-API-Key: ваш_ключ" \
     -d '{...}'
   ```

---

## 📞 Поддержка

### Проблемы и вопросы:

- Проверьте [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
- Посмотрите логи на Render
- Откройте Developer Console в браузере (F12)

---

## 📄 Лицензия

Часть проекта **Aleph Bet Foresight Summit Registration System**.

---

**Создано для юридически защищённой системы продажи билетов 🎫**

