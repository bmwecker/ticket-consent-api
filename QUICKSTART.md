# ⚡ Быстрый старт - 5 шагов до запуска

Эта краткая инструкция поможет вам развернуть систему логирования за 15 минут.

---

## ✅ Шаг 1: Загрузите код на GitHub (3 минуты)

```bash
# Перейдите в папку ticket-service
cd ticket-service

# Инициализируйте Git
git init
git add .
git commit -m "Initial commit"

# Создайте репозиторий на GitHub и загрузите код
git remote add origin https://github.com/YOUR_USERNAME/ticket-consent-api.git
git branch -M main
git push -u origin main
```

---

## ✅ Шаг 2: Разверните на Render (5 минут)

1. Зайдите на [Render Dashboard](https://dashboard.render.com/)
2. Нажмите **"New +"** → **"Web Service"**
3. Подключите репозиторий `ticket-consent-api`
4. Настройте:
   - **Name:** `ticket-consent-api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn api:app`
   - **Plan:** `Free`

5. Добавьте переменные окружения (кнопка "Advanced"):

   ```
   DATABASE_URL = postgresql://... (скопируйте из вашей PostgreSQL БД на Render)
   DOCUMENT_VERSION = v2025-10-28
   ADMIN_API_KEY = (сгенерируйте случайную строку)
   ALLOWED_ORIGINS = *
   ```

6. Нажмите **"Create Web Service"**
7. Дождитесь развёртывания (3-5 минут)

---

## ✅ Шаг 3: Проверьте работу API (1 минута)

Откройте в браузере:
```
https://your-service-name.onrender.com/health
```

Должны увидеть:
```json
{
  "status": "healthy",
  "service": "ticket-consent-logger"
}
```

✅ **API работает!**

---

## ✅ Шаг 4: Добавьте код на Tilda (3 минуты)

1. Откройте файл `tilda-consent-logger.js`
2. В строке 21 замените URL на ваш:
   ```javascript
   const API_URL = 'https://your-service-name.onrender.com/api/consent';
   ```
3. Скопируйте **весь код** из файла
4. В Tilda: **Настройки страницы** → **Дополнительно** → **HTML-код для вставки**
5. **Удалите старый код** (если есть)
6. **Вставьте новый код**
7. Сохраните и опубликуйте

---

## ✅ Шаг 5: Протестируйте (3 минуты)

1. Откройте страницу на Tilda
2. Нажмите **F12** (Developer Tools)
3. Перейдите на вкладку **Console**
4. Нажмите кнопки "СОГЛАСЕН" на странице
5. Проверьте, что в консоли появляются сообщения:
   ```
   🔐 Consent Logger initialized. Session ID: ...
   📤 Sending consent log: privacy_policy
   ✅ Consent logged successfully: ...
   ```

✅ **Всё работает!**

---

## 🎯 Что дальше?

### Сохраните snapshots документов

Это важно для юридической защиты!

1. Создайте файлы с текстами документов:
   - `ticket_terms_ru.txt` - Условия продажи билетов
   - `refund_policy_ru.txt` - Политика возврата
   - `privacy_policy_ru.txt` - Политика конфиденциальности

2. Откройте файл `.env` и добавьте:
   ```
   API_URL=https://your-service-name.onrender.com
   ADMIN_API_KEY=ваш_ключ_из_render
   ```

3. Запустите скрипт:
   ```bash
   pip install requests
   python save_document_snapshot.py
   ```

### Ограничьте CORS (для безопасности)

После тестирования в настройках Render измените:
```
ALLOWED_ORIGINS=https://yoursite.tilda.ws
```

### Проверьте данные в БД

```bash
# Подключитесь к PostgreSQL на Render
psql postgresql://...

# Посмотрите последние согласия
SELECT session_id, document_type, consent_timestamp 
FROM consent_logs 
ORDER BY consent_timestamp DESC 
LIMIT 10;
```

---

## 📚 Полезные ссылки

- 📖 [Подробная инструкция по деплою](DEPLOY_GUIDE.md)
- 📘 [Полная документация API](README.md)
- 🔧 [Решение проблем](DEPLOY_GUIDE.md#-решение-проблем)

---

## ❓ Частые вопросы

### API не отвечает

**Причина:** Render засыпает после 15 минут неактивности (бесплатный план)  
**Решение:** Первый запрос займёт 30-60 секунд - это нормально

### "CORS policy blocked"

**Причина:** Неправильный домен в ALLOWED_ORIGINS  
**Решение:** Временно установите `ALLOWED_ORIGINS=*` для тестирования

### "Failed to log consent"

**Причина:** Ошибка в DATABASE_URL  
**Решение:** Проверьте логи на Render и убедитесь, что DATABASE_URL правильный

---

**Готово! 🎉 Ваша система логирования согласий работает!**

**Время развёртывания:** ~15 минут  
**Стоимость:** $0 (бесплатный план Render)  
**Юридическая защита:** ✅ Максимальная

