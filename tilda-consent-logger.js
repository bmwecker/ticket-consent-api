/**
 * Модифицированный скрипт для логирования согласий с документами
 * ДЛЯ СТРАНИЦЫ ПОКУПКИ БИЛЕТОВ в Tilda
 * 
 * ИНСТРУКЦИЯ ПО УСТАНОВКЕ:
 * 1. Скопируйте ВЕСЬ этот код
 * 2. В Tilda: Настройки страницы → HTML-код для вставки в HEAD или BODY (до контента)
 * 3. Замените ВАШЕ_API_URL на реальный URL вашего API на Render
 * 4. Замените версии документов на актуальные
 * 
 * ВАЖНО: Этот код НЕ ЛОМАЕТ существующий функционал!
 * Он только ДОБАВЛЯЕТ логирование в фоновом режиме.
 */

<style>
  /* Баннер (ВАШ ОРИГИНАЛЬНЫЙ КОД - НЕ МЕНЯЕМ) */
  .gate-alert {
    position: fixed;
    bottom: -200px;
    left: 50%;
    transform: translateX(-50%);
    background: #ff5555;
    color: #fff;
    padding: 30px 50px;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    font-size: 60px;
    font-weight: 800;
    text-align: center;
    line-height: 1.2;
    z-index: 9999;
    display: block;
    opacity: 0;
    max-width: 90vw;
    transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .gate-alert.is-visible {
    bottom: 50px;
    opacity: 1;
  }

  /* Адаптация для планшетов */
  @media (max-width: 1200px) {
    .gate-alert {
      font-size: 40px;
      padding: 24px 40px;
    }
  }

  /* Адаптация для мобильных */
  @media (max-width: 768px) {
    .gate-alert {
      font-size: 20px;
      padding: 16px 24px;
      border-radius: 12px;
    }
  }
</style>

<div class="gate-alert" id="gate-alert"></div>

<script>
(function () {
  // ========================================
  // КОНФИГУРАЦИЯ - ИЗМЕНИТЕ ЭТИ ЗНАЧЕНИЯ
  // ========================================
  
  // URL вашего API на Render (замените на реальный после деплоя)
  const API_URL = 'https://your-api-name.onrender.com/api/consent';
  
  // Версии документов (обновляйте при изменении текстов)
  const DOCUMENT_VERSIONS = {
    'ticket_terms': 'v2025-10-28',      // Условия продажи билетов
    'refund_policy': 'v2025-10-28',     // Политика возврата
    'privacy_policy': 'v2025-10-28'     // Политика конфиденциальности
  };
  
  // ========================================
  // ОРИГИНАЛЬНЫЙ КОД (НЕ МЕНЯЕМ)
  // ========================================
  
  // Классы кнопок (ваш оригинальный код)
  const CLS_ACCEPT_TERMS      = 'js-accept-terms';       // Условия продажи билетов
  const CLS_ACCEPT_PRIVACY    = 'js-accept-privacy';     // Политика конфиденциальности
  const CLS_ACCEPT_DISCLAIMER = 'js-accept-disclaimer';  // Политика возврата
  const CLS_GO_NEXT           = 'js-go-next';            // Перейти

  let acceptedTerms = false;
  let acceptedPrivacy = false;
  let acceptedDisclaimer = false;

  const alertBox = document.getElementById('gate-alert');

  function showAlert(msg) {
    if (!alertBox) return;
    alertBox.textContent = msg;
    alertBox.classList.add('is-visible');
    clearTimeout(alertBox._timer);
    alertBox._timer = setTimeout(() => {
      alertBox.classList.remove('is-visible');
    }, 4000);
  }

  function closeParentPopup(btn) {
    const popup = btn.closest('.t-popup');
    if (popup) {
      const closeBtn = popup.querySelector('.t-popup__close, .t-popup__close-icon');
      if (closeBtn) closeBtn.click();
      else {
        popup.classList.remove('t-popup_show');
        document.body.classList.remove('t-body_popupshowed');
      }
    }
  }

  // ========================================
  // НОВЫЙ КОД - ЛОГИРОВАНИЕ (ДОБАВЛЯЕМ)
  // ========================================
  
  // Генерация уникального ID сессии (создаётся один раз при загрузке страницы)
  const SESSION_ID = generateUUID();
  
  console.log('🔐 Consent Logger initialized. Session ID:', SESSION_ID);
  
  // Функция генерации UUID v4
  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  // Функция вычисления SHA-256 хеша
  async function sha256(text) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(text);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (error) {
      console.error('Error computing SHA256:', error);
      return 'hash-error-' + Date.now();
    }
  }
  
  // Функция отправки согласия на сервер
  async function logConsent(documentType, documentText) {
    try {
      const hash = await sha256(documentText);
      
      const data = {
        session_id: SESSION_ID,
        document_type: documentType,
        document_version: DOCUMENT_VERSIONS[documentType] || 'v2025-10-28',
        document_hash: hash,
        consent_given: true,
        consent_timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        referrer: document.referrer || 'direct',
        page_url: window.location.href,
        consent_text: `Пользователь согласился с ${documentType}`
      };
      
      console.log('📤 Sending consent log:', documentType);
      
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Consent logged successfully:', result.consent_log_id);
        return true;
      } else {
        console.warn('⚠️ Failed to log consent:', response.status);
        return false;
      }
    } catch (error) {
      console.error('❌ Error logging consent:', error);
      // НЕ блокируем пользователя, если сервер недоступен
      return false;
    }
  }
  
  // Функция получения текста документа из попапа
  function getDocumentText(btn) {
    const popup = btn.closest('.t-popup');
    if (!popup) return '';
    
    // Пытаемся найти текст в попапе (обычно в .t-text, .t-descr или .t-popup__content)
    const textElement = popup.querySelector('.t-text, .t-descr, .t-popup__content');
    return textElement ? textElement.innerText.trim() : '';
  }
  
  // Маппинг классов кнопок на типы документов
  const DOCUMENT_TYPE_MAP = {
    [CLS_ACCEPT_TERMS]: 'ticket_terms',         // Условия продажи билетов
    [CLS_ACCEPT_DISCLAIMER]: 'refund_policy',   // Политика возврата
    [CLS_ACCEPT_PRIVACY]: 'privacy_policy'      // Политика конфиденциальности
  };
  
  // ========================================
  // МОДИФИЦИРОВАННАЯ ФУНКЦИЯ onAccept
  // ========================================
  
  async function onAccept(which, btn) {
    // Получаем текст документа
    const documentText = getDocumentText(btn);
    
    // Определяем тип документа
    const buttonClass = Object.keys(DOCUMENT_TYPE_MAP).find(cls => btn.classList.contains(cls));
    const documentType = DOCUMENT_TYPE_MAP[buttonClass];
    
    // Логируем согласие (в фоновом режиме, не блокируем пользователя)
    if (documentType && documentText) {
      logConsent(documentType, documentText).catch(err => {
        console.error('Background consent logging failed:', err);
      });
    }
    
    // ОРИГИНАЛЬНЫЙ КОД - выполняется сразу, не ждёт логирования
    if (which === 'terms') acceptedTerms = true;
    if (which === 'privacy') acceptedPrivacy = true;
    if (which === 'disclaimer') acceptedDisclaimer = true;
    closeParentPopup(btn);
  }

  // ========================================
  // ОБРАБОТЧИКИ СОБЫТИЙ (ОРИГИНАЛЬНЫЙ КОД)
  // ========================================
  
  document.addEventListener('click', function (e) {
    const termsBtn = e.target.closest('.' + CLS_ACCEPT_TERMS);
    if (termsBtn) { e.preventDefault(); onAccept('terms', termsBtn); return; }

    const privacyBtn = e.target.closest('.' + CLS_ACCEPT_PRIVACY);
    if (privacyBtn) { e.preventDefault(); onAccept('privacy', privacyBtn); return; }

    const disclaimerBtn = e.target.closest('.' + CLS_ACCEPT_DISCLAIMER);
    if (disclaimerBtn) { e.preventDefault(); onAccept('disclaimer', disclaimerBtn); return; }

    const goBtn = e.target.closest('.' + CLS_GO_NEXT);
    if (goBtn && !(acceptedTerms && acceptedPrivacy && acceptedDisclaimer)) {
      e.preventDefault();
      let msgs = [];
      if (!acceptedTerms) msgs.push("Условия продажи билетов");
      if (!acceptedPrivacy) msgs.push("Политика конфиденциальности");
      if (!acceptedDisclaimer) msgs.push("Политика возврата");
      showAlert("Примите: " + msgs.join(", ") + "!");
    }
  });
  
  // ========================================
  // ДОПОЛНИТЕЛЬНО: Сохраняем SESSION_ID в localStorage
  // (полезно, если пользователь перейдёт на следующую страницу)
  // ========================================
  
  try {
    localStorage.setItem('ticket_session_id', SESSION_ID);
    console.log('💾 Session ID saved to localStorage');
  } catch (e) {
    console.warn('Could not save session ID to localStorage:', e);
  }
  
})();
</script>

