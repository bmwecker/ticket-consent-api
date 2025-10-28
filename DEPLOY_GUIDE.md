# 🚀 Инструкция по развёртыванию микросервиса логирования согласий

## Что это такое?

Это API-сервис, который принимает и сохраняет согласия пользователей с юридическими документами при покупке билетов. Сервис логирует:
- ✅ Какой документ принят
- ✅ Когда принят (точное время UTC)
- ✅ Версию и хеш документа
- ✅ IP адрес, браузер, геолокацию
- ✅ Уникальный ID сессии

## 📋 Предварительные требования

1. ✅ Аккаунт на [Render.com](https://render.com) (бесплатно)
2. ✅ Аккаунт на [GitHub](https://github.com) (бесплатно)
3. ✅ Существующая PostgreSQL БД на Render (та же, что использует ваш Telegram бот)

---

## Шаг 1: Подготовка кода

### 1.1. Создайте отдельный Git репозиторий

В корне проекта `summit-registration-bot/` выполните:

```bash
# Переходим в папку ticket-service
cd ticket-service

# Инициализируем Git
git init

# Добавляем файлы
git add .

# Коммитим
git commit -m "Initial commit: Consent logging API"
```

### 1.2. Создайте репозиторий на GitHub

1. Зайдите на [GitHub](https://github.com)
2. Нажмите "New repository"
3. Название: `ticket-consent-api` (или любое другое)
4. Выберите **Private** (для безопасности)
5. НЕ добавляйте README, .gitignore, license
6. Создайте репозиторий

### 1.3. Загрузите код на GitHub

```bash
# Привяжите локальный репозиторий к GitHub (замените YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ticket-consent-api.git

# Загрузите код
git branch -M main
git push -u origin main
```

---

## Шаг 2: Развёртывание на Render

### 2.1. Создание Web Service

1. Зайдите на [Render Dashboard](https://dashboard.render.com/)
2. Нажмите **"New +"** → **"Web Service"**
3. Подключите ваш GitHub репозиторий `ticket-consent-api`
4. Настройте сервис:

   | Параметр | Значение |
   |----------|----------|
   | **Name** | `ticket-consent-api` (или любое имя) |
   | **Environment** | `Python 3` |
   | **Region** | Выберите ближайший (Europe West для ЕС/Израиль) |
   | **Branch** | `main` |
   | **Root Directory** | оставьте пустым (если весь код в корне) |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn api:app --bind 0.0.0.0:$PORT` |
   | **Plan** | **Free** (бесплатный) |

5. Нажмите **"Advanced"** для добавления переменных окружения

### 2.2. Настройка переменных окружения

Добавьте следующие переменные (кнопка "Add Environment Variable"):

#### **Обязательные:**

| Key | Value | Где взять? |
|-----|-------|-----------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Render Dashboard → PostgreSQL → Connection String (Internal) |
| `DOCUMENT_VERSION` | `v2025-10-28` | Текущая версия документов (обновляйте при изменениях) |
| `ADMIN_API_KEY` | Случайная строка | Сгенерируйте: `openssl rand -hex 32` или используйте [генератор](https://generate-random.org/api-key-generator) |

#### **Опциональные:**

| Key | Value | Примечание |
|-----|-------|------------|
| `ALLOWED_ORIGINS` | `*` | Для тестирования. Потом замените на домен Tilda: `https://yoursite.tilda.ws` |

### 2.3. Получение DATABASE_URL

1. В Render Dashboard найдите ваш **PostgreSQL сервис** (тот, что использует бот)
2. Перейдите на вкладку **"Info"**
3. Скопируйте **"Internal Database URL"** (не External!)
4. Вставьте в `DATABASE_URL` в настройках Web Service

**ВАЖНО:** Используйте Internal URL, он бесплатный и быстрее!

### 2.4. Запуск сервиса

1. Нажмите **"Create Web Service"**
2. Render начнёт развёртывание (займёт 3-5 минут)
3. Следите за логами на вкладке **"Logs"**
4. Дождитесь сообщения: `Database tables initialized successfully`

### 2.5. Получение URL API

После успешного деплоя:
1. На вкладке **"Settings"** найдите **"Your service is live at:"**
2. Скопируйте URL (например: `https://ticket-consent-api.onrender.com`)
3. Сохраните его - понадобится для JavaScript

---

## Шаг 3: Проверка работы API

### 3.1. Проверка здоровья

Откройте в браузере:
```
https://your-service-name.onrender.com/health
```

Должны увидеть:
```json
{
  "status": "healthy",
  "service": "ticket-consent-logger",
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

### 3.2. Тестовый запрос (через curl или Postman)

```bash
curl -X POST https://your-service-name.onrender.com/api/consent \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "document_type": "privacy_policy",
    "document_version": "v2025-10-28",
    "document_hash": "abc123",
    "consent_given": true,
    "consent_timestamp": "2025-10-28T12:00:00Z",
    "user_agent": "Test Browser",
    "referrer": "test",
    "page_url": "https://test.com"
  }'
```

Ожидаемый ответ:
```json
{
  "success": true,
  "consent_log_id": "uuid-here",
  "timestamp": "2025-10-28T12:34:56.789Z"
}
```

---

## Шаг 4: Интеграция с Tilda

### 4.1. Откройте файл `tilda-consent-logger.js`

В строке **21** замените:
```javascript
const API_URL = 'https://your-api-name.onrender.com/api/consent';
```

На ваш реальный URL:
```javascript
const API_URL = 'https://ticket-consent-api.onrender.com/api/consent';
```

### 4.2. Обновите версии документов (если нужно)

В строках **24-28** проверьте версии:
```javascript
const DOCUMENT_VERSIONS = {
  'ticket_terms': 'v2025-10-28',      // Условия продажи билетов
  'refund_policy': 'v2025-10-28',     // Политика возврата
  'privacy_policy': 'v2025-10-28'     // Политика конфиденциальности
};
```

### 4.3. Добавьте код на страницу Tilda

1. Откройте вашу страницу в редакторе Tilda
2. Нажмите **"Настройки страницы"** (иконка шестерёнки)
3. Перейдите на вкладку **"Дополнительно"**
4. Найдите **"HTML-код для вставки в HEAD"** или **"HTML-код для вставки перед </body>"**
5. **УДАЛИТЕ ваш старый код** (весь блок с `<style>` и `<script>`)
6. **ВСТАВЬТЕ новый код** из файла `tilda-consent-logger.js` (весь целиком)
7. Нажмите **"Сохранить и опубликовать"**

### 4.4. Проверьте классы кнопок на странице

Убедитесь, что ваши кнопки имеют правильные классы:

| Документ | Класс кнопки "СОГЛАСЕН" |
|----------|-------------------------|
| Условия продажи билетов | `js-accept-terms` |
| Политика возврата | `js-accept-disclaimer` |
| Политика конфиденциальности | `js-accept-privacy` |
| Кнопка "Перейти далее" | `js-go-next` |

**Как проверить:**
1. Откройте блок с кнопкой в редакторе Tilda
2. Нажмите "Настройки" → "Дополнительно" → "CSS ID и класс"
3. В поле "CSS class" должен быть указан нужный класс

---

## Шаг 5: Тестирование на Tilda

### 5.1. Откройте опубликованную страницу

1. Откройте страницу в браузере
2. Нажмите **F12** (открыть Developer Tools)
3. Перейдите на вкладку **"Console"**

### 5.2. Проверьте инициализацию

Вы должны увидеть:
```
🔐 Consent Logger initialized. Session ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
💾 Session ID saved to localStorage
```

### 5.3. Нажмите кнопки "СОГЛАСЕН"

Для каждой кнопки в консоли должно появиться:
```
📤 Sending consent log: privacy_policy
✅ Consent logged successfully: uuid-here
```

Если видите ошибки:
```
❌ Error logging consent: ...
```

Проверьте:
- ✅ Правильный ли URL API в строке 21
- ✅ Запущен ли сервис на Render (зелёный статус)
- ✅ Есть ли ошибки в логах Render

### 5.4. Проверьте в базе данных

**Вариант А: Через Render Dashboard**

1. Render Dashboard → PostgreSQL → "Connect" → "PSQL Command"
2. Скопируйте команду и выполните в терминале:
   ```bash
   psql postgresql://user:pass@host/db
   ```
3. Выполните запрос:
   ```sql
   SELECT session_id, document_type, consent_timestamp 
   FROM consent_logs 
   ORDER BY consent_timestamp DESC 
   LIMIT 10;
   ```

**Вариант Б: Через API**

Откройте в браузере:
```
https://your-service-name.onrender.com/api/consent/verify/SESSION_ID
```
(замените SESSION_ID на тот, что видели в консоли)

Должны увидеть:
```json
{
  "session_id": "uuid",
  "all_consents_given": true,
  "consents": {
    "ticket_terms": true,
    "refund_policy": true,
    "privacy_policy": true
  }
}
```

---

## 🔒 Безопасность (для продакшн)

### 1. Ограничьте CORS

После тестирования в `ALLOWED_ORIGINS` укажите только ваш домен:
```
ALLOWED_ORIGINS=https://yoursite.tilda.ws
```

### 2. Включите HTTPS only

В коде Tilda замените:
```javascript
const API_URL = 'https://...';  // обязательно HTTPS!
```

### 3. Защитите API ключ админа

`ADMIN_API_KEY` должен быть длинным и случайным (минимум 32 символа).

### 4. Мониторинг логов

Регулярно проверяйте логи на Render:
```
Dashboard → ticket-consent-api → Logs
```

---

## 📊 Просмотр статистики

### Получить статистику согласий

```bash
curl https://your-service-name.onrender.com/api/consent/stats
```

---

## ❗ Решение проблем

### Проблема: "Failed to log consent: 500"

**Причина:** Ошибка в БД или API
**Решение:**
1. Проверьте логи на Render
2. Убедитесь, что DATABASE_URL правильный
3. Проверьте, что таблицы созданы

### Проблема: "CORS policy blocked"

**Причина:** Браузер блокирует запросы с другого домена
**Решение:**
1. Проверьте `ALLOWED_ORIGINS` в настройках Render
2. Убедитесь, что домен Tilda указан правильно
3. Для тестирования временно установите `ALLOWED_ORIGINS=*`

### Проблема: API не отвечает (Render в спящем режиме)

**Причина:** На бесплатном плане Render засыпает после 15 минут неактивности
**Решение:**
- Первый запрос после сна займёт 30-60 секунд (это нормально)
- Для продакшн можно перейти на платный план ($7/мес)

### Проблема: "Module psycopg not found"

**Причина:** Не установлены зависимости
**Решение:**
1. Проверьте, что `requirements.txt` есть в репозитории
2. В Render Settings проверьте Build Command: `pip install -r requirements.txt`

---

## 🎯 Что дальше?

После успешного развёртывания системы логирования:

1. ✅ **Сохраните snapshots документов** (см. следующий раздел)
2. ✅ **Добавьте форму сбора данных покупателя**
3. ✅ **Интегрируйте платёжную систему**
4. ✅ **Создайте генератор билетов**

---

## 📝 Сохранение snapshots документов

Snapshots - это архивные копии ваших юридических документов. Их нужно сохранить СРАЗУ после публикации.

### Почему это важно?

Если в будущем возникнет спор, вы сможете доказать, **какой именно текст** видел пользователь в момент согласия.

### Как сохранить snapshot:

```bash
# 1. Скопируйте полный текст документа из Tilda (например, "Условия продажи билетов")
# 2. Сохраните в файл ticket_terms_ru.txt

# 3. Отправьте через API:
curl -X POST https://your-service-name.onrender.com/api/document-snapshot \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ваш_ADMIN_API_KEY" \
  -d '{
    "document_type": "ticket_terms",
    "version": "v2025-10-28",
    "full_text": "ПОЛНЫЙ ТЕКСТ ДОКУМЕНТА ЗДЕСЬ...",
    "language": "ru",
    "created_by": "admin"
  }'
```

**Сделайте это для всех трёх документов:**
- `ticket_terms` (Условия продажи билетов)
- `refund_policy` (Политика возврата)
- `privacy_policy` (Политика конфиденциальности)

**ВАЖНО:** Обновляйте snapshots при КАЖДОМ изменении текста документов!

---

## 📞 Поддержка

Если что-то не работает:
1. Проверьте логи на Render
2. Откройте Developer Console в браузере (F12)
3. Убедитесь, что все переменные окружения заданы правильно

---

**Готово! 🎉 Теперь у вас работает юридически защищённая система логирования согласий.**

