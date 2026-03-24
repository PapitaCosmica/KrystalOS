/**
 * KrystalOS — core/ui/ErrorBoundary.js
 * Phase 7.6: Visual Crash Recovery — Isolated Widget Error Containers
 *
 * Catches fatal JavaScript errors within individual widget contexts and
 * replaces their DOM container with a friendly, isolated crash card —
 * preserving the full OS shell and all other widgets.
 *
 * The full stack trace is stored in sessionStorage for retrieval
 * via the "Ver Log Completo" button.
 *
 * Usage (from the Krystal Gateway when mounting a widget):
 *   Krystal.errorBoundary.watch(hostEl, 'weather-widget');
 *
 * Manual capture (for try/catch scenarios):
 *   try { riskyOperation(); }
 *   catch (e) { Krystal.errorBoundary.capture(hostEl, 'weather-widget', e); }
 */

(function () {
  'use strict';

  const LOG_KEY = (id) => `krystal_log_${id}`;

  // ── CSS ─────────────────────────────────────────────────────────────────────
  function _injectStyles() {
    if (document.getElementById('__kos-eb-styles')) return;
    const style = document.createElement('style');
    style.id = '__kos-eb-styles';
    style.textContent = `
      .__kos-crash-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 20px;
        height: 100%;
        min-height: 100px;
        background: rgba(30, 10, 10, 0.9);
        border: 1px solid rgba(255, 80, 80, 0.35);
        border-radius: inherit;
        font-family: system-ui, -apple-system, sans-serif;
        text-align: center;
        animation: __kos-eb-in 0.25s ease;
      }
      @keyframes __kos-eb-in {
        from { opacity: 0; transform: scale(0.97); }
        to   { opacity: 1; transform: scale(1); }
      }
      .__kos-crash-card .__icon  { font-size: 28px; }
      .__kos-crash-card .__name  {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: rgba(255, 120, 120, 0.9);
      }
      .__kos-crash-card .__msg   {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.45);
        max-width: 220px;
        line-height: 1.5;
        word-break: break-word;
      }
      .__kos-crash-card .__log-btn {
        margin-top: 4px;
        padding: 5px 14px;
        border: 1px solid rgba(255, 80, 80, 0.5);
        border-radius: 20px;
        background: transparent;
        color: rgba(255, 120, 120, 0.8);
        font-size: 11px;
        cursor: pointer;
        transition: opacity 0.2s;
      }
      .__kos-crash-card .__log-btn:hover { opacity: 0.7; }

      /* Full log modal */
      .__kos-log-modal-backdrop {
        position: fixed;
        inset: 0;
        z-index: 9999999;
        background: rgba(0, 0, 0, 0.75);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: __kos-eb-in 0.2s ease;
      }
      .__kos-log-modal {
        background: #0d0a1e;
        border: 1px solid rgba(255,80,80,0.3);
        border-radius: 16px;
        padding: 24px;
        width: 90%;
        max-width: 640px;
        max-height: 80vh;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        color: rgba(255,255,255,0.8);
        font-size: 12px;
        line-height: 1.7;
      }
      .__kos-log-modal .__modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        font-family: system-ui, sans-serif;
      }
      .__kos-log-modal .__modal-title {
        font-size: 14px;
        font-weight: 700;
        color: rgba(255,120,120,0.9);
      }
      .__kos-log-modal .__close {
        background: none;
        border: none;
        color: rgba(255,255,255,0.5);
        font-size: 20px;
        cursor: pointer;
        line-height: 1;
      }
      .__kos-log-modal pre {
        white-space: pre-wrap;
        word-break: break-word;
        color: rgba(255,220,100,0.85);
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 12px;
        margin: 0;
      }
    `;
    document.head.appendChild(style);
  }

  // ── Log Modal ───────────────────────────────────────────────────────────────
  function _showLogModal(widgetId) {
    const raw = sessionStorage.getItem(LOG_KEY(widgetId));
    if (!raw) {
      alert(`No log data found for "${widgetId}".`);
      return;
    }
    const logData = JSON.parse(raw);

    const backdrop = document.createElement('div');
    backdrop.className = '__kos-log-modal-backdrop';
    backdrop.innerHTML = `
      <div class="__kos-log-modal">
        <div class="__modal-header">
          <span class="__modal-title">⚠️ Crash Log — ${widgetId}</span>
          <button class="__close" title="Cerrar">✕</button>
        </div>
        <p style="font-family:system-ui;font-size:12px;color:rgba(255,255,255,0.4);margin:0 0 12px">
          ${new Date(logData.timestamp).toLocaleString()} · ${logData.errorType}
        </p>
        <pre>${_escHtml(logData.message)}\n\n${_escHtml(logData.stack || '')}</pre>
      </div>
    `;

    backdrop.querySelector('.__close').addEventListener('click', () => backdrop.remove());
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.remove(); });

    document.body.appendChild(backdrop);
  }

  function _escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ── ErrorBoundary Singleton ─────────────────────────────────────────────────
  class ErrorBoundary {
    constructor() {
      this._watched = new Set(); // widgetIds we're monitoring
      _injectStyles();
    }

    /**
     * Watch a widget host element for unhandled errors.
     * Intercepts errors that bubble up to the widget's host or its Shadow Root.
     *
     * @param {HTMLElement} hostEl   - Widget outer container.
     * @param {string}      widgetId - Widget identifier.
     */
    watch(hostEl, widgetId) {
      if (this._watched.has(widgetId)) return;
      this._watched.add(widgetId);

      // Listen for errors dispatched on the host (Shadow DOM bubbles can be intercepted here)
      hostEl.addEventListener('error', (evt) => {
        evt.stopPropagation();
        const err = evt.error || new Error(evt.message || 'Unknown error');
        this.capture(hostEl, widgetId, err);
      }, true);

      // Also attach to any <iframe> inside the host
      hostEl.querySelectorAll('iframe').forEach(frame => {
        try {
          frame.contentWindow.addEventListener('error', (evt) => {
            const err = evt.error || new Error(evt.message);
            this.capture(hostEl, widgetId, err);
          });
          frame.contentWindow.addEventListener('unhandledrejection', (evt) => {
            this.capture(hostEl, widgetId, evt.reason || new Error('Unhandled Promise rejection'));
          });
        } catch (_) { /* cross-origin */ }
      });

      console.debug(`[ErrorBoundary] 🛡 Watching: ${widgetId}`);
    }

    /**
     * Manually capture and display a widget crash.
     *
     * @param {HTMLElement} hostEl   - Widget container to replace.
     * @param {string}      widgetId - Widget identifier.
     * @param {Error|any}   error    - The caught error object.
     */
    capture(hostEl, widgetId, error) {
      const err = error instanceof Error ? error : new Error(String(error));

      console.error(`[ErrorBoundary] 💥 Widget "${widgetId}" crashed:`, err);

      // ── Save full log to sessionStorage ────────────────────────────────────
      const logData = {
        widgetId,
        timestamp: Date.now(),
        errorType: err.name || 'Error',
        message:   err.message || String(err),
        stack:     err.stack   || '(no stack trace)',
      };
      try {
        sessionStorage.setItem(LOG_KEY(widgetId), JSON.stringify(logData));
      } catch (_) { }

      // ── Replace host content with crash card ───────────────────────────────
      const shortMsg = logData.message.slice(0, 120) + (logData.message.length > 120 ? '…' : '');

      hostEl.innerHTML = '';
      hostEl.style.overflow = 'hidden';

      const card = document.createElement('div');
      card.className = '__kos-crash-card';
      card.dataset.crashedWidget = widgetId;
      card.innerHTML = `
        <span class="__icon">⚠️</span>
        <span class="__name">${widgetId}</span>
        <p class="__msg">${_escHtml(shortMsg)}</p>
        <button class="__log-btn">Ver Log Completo</button>
      `;

      card.querySelector('.__log-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        _showLogModal(widgetId);
      });

      hostEl.appendChild(card);

      // ── Notify the OS ──────────────────────────────────────────────────────
      document.dispatchEvent(new CustomEvent('krystal:widget-crashed', {
        bubbles: true,
        detail: { widgetId, error: logData },
      }));
    }

    /**
     * Clear crash state and re-enable a widget zone.
     * @param {HTMLElement} hostEl
     * @param {string}      widgetId
     */
    clear(hostEl, widgetId) {
      const card = hostEl.querySelector(`[data-crashed-widget="${widgetId}"]`);
      if (card) card.remove();
      sessionStorage.removeItem(LOG_KEY(widgetId));
      this._watched.delete(widgetId);
      console.info(`[ErrorBoundary] ✓ Crash state cleared for "${widgetId}"`);
    }
  }

  // ── Expose globally ─────────────────────────────────────────────────────────
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.errorBoundary = new ErrorBoundary();

  console.log('[ErrorBoundary] 🛡 Visual Crash Recovery Online — Krystal.errorBoundary ready.');
})();
