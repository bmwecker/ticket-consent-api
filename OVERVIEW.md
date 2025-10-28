# 📋 Обзор системы логирования согласий

## Что было создано

Вы получили полнофункциональную систему юридически защищённого логирования согласий для страницы покупки билетов.

---

## 📁 Структура файлов

```
ticket-service/
│
├── 🐍 BACKEND (Python/Flask)
│   ├── api.py                           # Flask API с endpoints
│   ├── database_tickets.py              # Работа с PostgreSQL
│   └── save_document_snapshot.py        # Скрипт сохранения snapshots
│
├── 🌐 FRONTEND (JavaScript)
│   └── tilda-consent-logger.js          # Код для вставки на страницу Tilda
│
├── 🚀 DEPLOYMENT
│   ├── Procfile                         # Конфигурация для Render
│   ├── runtime.txt                      # Версия Python (3.11.7)
│   ├── requirements.txt                 # Зависимости Python
│   └── .gitignore                       # Что не загружать в Git
│
└── 📚 ДОКУМЕНТАЦИЯ
    ├── README.md                        # Общее описание проекта
    ├── QUICKSTART.md                    # Быстрый старт (15 минут)
    ├── DEPLOY_GUIDE.md                  # Подробная инструкция по деплою
    └── OVERVIEW.md                      # Этот файл
```

---

## 🎯 Что делает система

### 1. Логирование согласий

Когда пользователь нажимает кнопку "СОГЛАСЕН" на странице Tilda:

```
Пользователь нажимает "СОГЛАСЕН"
         ↓
JavaScript вычисляет SHA-256 хеш текста документа
         ↓
Отправляет POST запрос на ваш API
         ↓
API сохраняет в PostgreSQL:
  - Тип документа
  - Версию документа
  - Хеш содержимого
  - Время согласия (UTC)
  - IP адрес
  - Браузер/устройство
  - Уникальный ID сессии
         ↓
Попап закрывается (ваш существующий код работает как раньше)
```

**Важно:** Логирование происходит в фоновом режиме и НЕ блокирует пользователя, даже если сервер недоступен.

### 2. Архивирование документов

Через API (или скрипт) вы сохраняете полные тексты документов в базу данных:

```
Админ отправляет POST /api/document-snapshot
         ↓
API вычисляет SHA-256 хеш текста
         ↓
Деактивирует предыдущие версии
         ↓
Сохраняет новую версию как активную
```

Это позволяет в будущем доказать, **какой именно текст** видел пользователь.

### 3. Проверка согласий

Вы (или следующая страница) можете проверить, дал ли пользователь все три согласия:

```
GET /api/consent/verify/{session_id}
         ↓
API проверяет наличие всех трёх согласий
         ↓
Возвращает статус: все даны или нет
```

---

## 🗄️ Структура базы данных

### Таблица `consent_logs` (логи согласий)

Каждая строка = одно согласие одного пользователя с одним документом.

**Пример записи:**
```
consent_log_id:      550e8400-e29b-41d4-a716-446655440000
session_id:          123e4567-e89b-12d3-a456-426614174000
document_type:       privacy_policy
document_version:    v2025-10-28
document_hash:       a3f2b1c...  (SHA-256)
consent_given:       true
consent_timestamp:   2025-10-28T14:30:00Z
client_ip:           185.45.23.67
user_agent:          Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
ip_country:          IL
```

**Индексы:**
- По `session_id` - быстрый поиск всех согласий пользователя
- По `document_type` - статистика по документам
- По `consent_timestamp` - временные запросы

### Таблица `document_snapshots` (архив документов)

Каждая строка = одна версия одного документа на одном языке.

**Пример записи:**
```
snapshot_id:         660f9511-f39c-52e5-b827-557766551111
document_type:       ticket_terms
version:             v2025-10-28
content_hash:        b4e3c2d...  (SHA-256)
full_text:           "УСЛОВИЯ ПРОДАЖИ БИЛЕТОВ\n\n1. Общие положения..."
language:            ru
is_active:           true
created_at:          2025-10-28T10:00:00Z
```

**Уникальность:** На каждом языке может быть только одна активная версия документа.

---

## 🔌 API Endpoints

### 1. `GET /health`
**Назначение:** Проверка работоспособности  
**Использование:** Мониторинг, тесты  
**Ответ:** `{"status": "healthy"}`

### 2. `POST /api/consent`
**Назначение:** Логирование согласия  
**Использование:** Вызывается из JavaScript на Tilda  
**Аутентификация:** Не требуется (публичный endpoint)

### 3. `GET /api/consent/verify/{session_id}`
**Назначение:** Проверка всех согласий  
**Использование:** Перед переходом на следующую страницу  
**Аутентификация:** Не требуется

### 4. `POST /api/document-snapshot`
**Назначение:** Сохранение snapshot документа  
**Использование:** Админ (через скрипт или curl)  
**Аутентификация:** Требуется `X-API-Key` заголовок

---

## 🔒 Безопасность

### Что защищено:

✅ **CORS** - только разрешённые домены могут отправлять запросы  
✅ **HTTPS** - все данные шифруются в передаче  
✅ **API ключ** - админ-функции защищены  
✅ **Валидация** - все входные данные проверяются  
✅ **SQL Injection** - защита через параметризованные запросы (psycopg)  
✅ **Хеширование** - неизменяемость документов проверяется через SHA-256

### Что НЕ защищено (пока):

⚠️ **Rate Limiting** - нет ограничения запросов (можно добавить Flask-Limiter)  
⚠️ **IP Whitelisting** - нет белого списка IP (не критично для публичного API)  
⚠️ **DDoS защита** - базовая защита Render (для серьёзного трафика нужен Cloudflare)

### Рекомендации для продакшн:

1. **Ограничьте CORS:**
   ```
   ALLOWED_ORIGINS=https://yoursite.tilda.ws
   ```

2. **Используйте сложный API ключ:**
   ```bash
   # Сгенерируйте 64-символьный ключ
   openssl rand -hex 32
   ```

3. **Мониторьте логи:**
   - Проверяйте подозрительную активность
   - Настройте алерты на ошибки

4. **Регулярные бэкапы:**
   - Render делает автоматические бэкапы PostgreSQL
   - Проверьте настройки на вкладке "Backups"

---

## 📊 Как пользоваться данными

### SQL запросы для статистики

**Всего согласий:**
```sql
SELECT COUNT(*) FROM consent_logs;
```

**По типам документов:**
```sql
SELECT document_type, COUNT(*) 
FROM consent_logs 
GROUP BY document_type;
```

**Уникальных пользователей:**
```sql
SELECT COUNT(DISTINCT session_id) FROM consent_logs;
```

**Последние 10 согласий:**
```sql
SELECT 
  session_id, 
  document_type, 
  consent_timestamp,
  client_ip,
  ip_country
FROM consent_logs 
ORDER BY consent_timestamp DESC 
LIMIT 10;
```

**Согласия за сегодня:**
```sql
SELECT COUNT(*) 
FROM consent_logs 
WHERE DATE(consent_timestamp) = CURRENT_DATE;
```

**Полные сессии (все 3 согласия):**
```sql
SELECT session_id, COUNT(*) as consents_count
FROM consent_logs
GROUP BY session_id
HAVING COUNT(*) = 3;
```

### Экспорт в CSV (для бухгалтерии)

```sql
COPY (
  SELECT 
    consent_log_id,
    session_id,
    document_type,
    document_version,
    consent_timestamp,
    client_ip
  FROM consent_logs
  WHERE consent_timestamp >= '2025-10-01'
) TO '/tmp/consents_october.csv' WITH CSV HEADER;
```

---

## 🧪 Тестирование

### Локальное тестирование

1. Запустите API локально:
   ```bash
   python api.py
   ```

2. В браузере откройте страницу Tilda

3. В JavaScript коде временно измените URL:
   ```javascript
   const API_URL = 'http://localhost:5000/api/consent';
   ```

4. Нажимайте кнопки и смотрите логи в терминале

### Production тестирование

1. Откройте страницу Tilda
2. Нажмите F12 → Console
3. Нажмите кнопку "СОГЛАСЕН"
4. Проверьте сообщения:
   ```
   📤 Sending consent log: privacy_policy
   ✅ Consent logged successfully: uuid
   ```

5. Проверьте через API:
   ```bash
   curl https://your-api.onrender.com/api/consent/verify/SESSION_ID
   ```

---

## 🔧 Maintenance (обслуживание)

### При изменении текста документа:

1. **Обновите версию** в `.env`:
   ```
   DOCUMENT_VERSION=v2025-11-15
   ```

2. **Обновите JavaScript** на Tilda (в `DOCUMENT_VERSIONS`)

3. **Сохраните новый snapshot:**
   ```bash
   python save_document_snapshot.py
   ```

4. **Перезапустите сервис** на Render (если нужно)

### Мониторинг

**Каждую неделю:**
- Проверяйте логи на Render (ищите ошибки)
- Проверяйте количество согласий в БД
- Убедитесь, что все snapshots сохранены

**Каждый месяц:**
- Делайте backup БД (вручную или настройте автоматический)
- Проверяйте место на диске (PostgreSQL Free = 1GB)

### Обновление зависимостей

**Python пакеты:**
```bash
pip list --outdated
pip install --upgrade flask flask-cors psycopg
pip freeze > requirements.txt
git commit -am "Update dependencies"
git push
```

Render автоматически передеплоит сервис.

---

## 💡 Советы и лучшие практики

### ✅ DO (делайте так):

- ✅ Сохраняйте snapshot СРАЗУ после публикации новой версии документа
- ✅ Проверяйте логи регулярно
- ✅ Используйте HTTPS везде
- ✅ Делайте бэкапы БД
- ✅ Тестируйте после каждого изменения
- ✅ Документируйте изменения версий

### ❌ DON'T (не делайте так):

- ❌ НЕ удаляйте старые snapshots из БД (нужны для аудита)
- ❌ НЕ храните API ключи в Git (используйте .env)
- ❌ НЕ используйте `ALLOWED_ORIGINS=*` в продакшн
- ❌ НЕ изменяйте старые записи в `consent_logs` (только INSERT)
- ❌ НЕ отключайте HTTPS

---

## 📞 Что делать, если...

### ...API не отвечает?

1. Проверьте статус на Render Dashboard
2. Посмотрите логи (вкладка "Logs")
3. Убедитесь, что DATABASE_URL правильный
4. Перезапустите сервис (Manual Deploy)

### ...JavaScript не отправляет данные?

1. Откройте F12 → Console
2. Ищите ошибки (красный текст)
3. Проверьте, что URL API правильный
4. Проверьте CORS настройки

### ...БД переполнена?

1. Проверьте размер: `SELECT pg_size_pretty(pg_database_size('database_name'));`
2. Удалите старые тестовые данные (если есть)
3. Обновите план PostgreSQL на Render (платно)

### ...Нужно удалить все тестовые данные?

```sql
-- ОСТОРОЖНО! Это удалит ВСЕ данные!
DELETE FROM consent_logs WHERE session_id LIKE 'test%';
```

---

## 🎓 Дальнейшее развитие

После успешного внедрения логирования согласий, следующие шаги:

1. **Форма сбора данных покупателя**
   - Имя, email, телефон
   - Выбор способа доставки билета

2. **Интеграция платёжной системы**
   - Stripe / PayPal / Fondy
   - Webhook'и для обработки платежей

3. **Генерация билетов**
   - PDF с QR-кодом
   - Персонализация

4. **Отправка билетов**
   - Email (SendGrid / Mailgun)
   - WhatsApp (Twilio)

5. **Админ-панель**
   - Просмотр покупок
   - Экспорт данных
   - Статистика

---

**Вопросы? Проблемы? Смотрите [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) или [README.md](README.md)**

**Создано с ❤️ для юридически защищённой системы продажи билетов 🎫**

