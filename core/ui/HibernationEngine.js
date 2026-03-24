/**
 * KrystalOS — core/ui/HibernationEngine.js
 * Phase 7.3: Widget Lifecycle Manager — Hibernate & Wake
 *
 * Monitors user interaction over each Widget zone. When idle for
 * `timeout_idle` (from krystal.json), emits `Krystal.lifecycle.hibernate`.
 * Resumes with `Krystal.lifecycle.wake` on pointer re-entry.
 */

(function () {
  'use strict';

  /**
   * Parses a duration string like "5m", "30s", "1h" to milliseconds.
   */
  function _parseDuration(str) {
    if (!str) return 5 * 60 * 1000; // default 5 minutes
    const match = String(str).trim().match(/^(\d+)(s|m|h)$/i);
    if (!match) return 5 * 60 * 1000;
    const val  = parseInt(match[1], 10);
    const unit = match[2].toLowerCase();
    const mult = { s: 1000, m: 60_000, h: 3_600_000 };
    return val * (mult[unit] || 60_000);
  }

  /**
   * Applies the visual hibernation effect to a host element.
   * Uses a lightweight CSS class instead of inline styles
   * to remain composable with the theme layer.
   */
  function _applyHibernateStyle(hostEl) {
    hostEl.style.transition = 'filter 0.6s ease, opacity 0.6s ease';
    hostEl.style.filter     = 'grayscale(0.8) blur(1.5px)';
    hostEl.style.opacity    = '0.55';

    // Inject a "Pausado" badge if it doesn't already exist
    if (!hostEl.querySelector('.__krystal-paused-badge')) {
      const badge = document.createElement('div');
      badge.className = '__krystal-paused-badge';
      badge.style.cssText = [
        'position:absolute', 'top:50%', 'left:50%',
        'transform:translate(-50%,-50%)',
        'background:rgba(0,0,0,0.55)',
        'color:#fff', 'font-size:11px',
        'padding:4px 10px', 'border-radius:20px',
        'pointer-events:none', 'z-index:9999',
        'font-family:system-ui,sans-serif',
        'letter-spacing:0.05em',
      ].join(';');
      badge.textContent = '⏸ Pausado';
      hostEl.style.position = hostEl.style.position || 'relative';
      hostEl.appendChild(badge);
    }
  }

  function _removeHibernateStyle(hostEl) {
    hostEl.style.filter  = '';
    hostEl.style.opacity = '';
    const badge = hostEl.querySelector('.__krystal-paused-badge');
    if (badge) badge.remove();
  }

  /**
   * HibernationEngine — tracks one Widget zone at a time.
   */
  class WidgetHibernationController {
    /**
     * @param {HTMLElement} hostEl   - The widget's outer DOM element.
     * @param {string}      widgetId - Identifier (from krystal.json name).
     * @param {number}      timeoutMs - Idle threshold in milliseconds.
     * @param {Window|null} innerWin  - Optional inner frame window to emit lifecycle events.
     */
    constructor(hostEl, widgetId, timeoutMs, innerWin = null) {
      this.host       = hostEl;
      this.widgetId   = widgetId;
      this.timeout    = timeoutMs;
      this.innerWin   = innerWin;
      this._timer     = null;
      this._sleeping  = false;

      this._onActivity = this._onActivity.bind(this);
      this._onEnter    = this._onEnter.bind(this);

      this._attach();
      this._resetTimer();
    }

    _attach() {
      // Activity events
      ['pointermove', 'pointerdown', 'keydown', 'focus', 'scroll'].forEach(evt => {
        this.host.addEventListener(evt, this._onActivity, { passive: true, capture: true });
      });
      // Wake-up on hover
      this.host.addEventListener('mouseenter', this._onEnter);
    }

    _resetTimer() {
      clearTimeout(this._timer);
      this._timer = setTimeout(() => this._hibernate(), this.timeout);
    }

    _onActivity() {
      if (this._sleeping) {
        this._wake();
      } else {
        this._resetTimer();
      }
    }

    _onEnter() {
      if (this._sleeping) this._wake();
    }

    _hibernate() {
      if (this._sleeping) return;
      this._sleeping = true;
      console.info(`[HibernationEngine] ❄️  Widget "${this.widgetId}" → HIBERNATE`);

      _applyHibernateStyle(this.host);

      // Emit lifecycle event into inner frame
      this._emit('Krystal.lifecycle.hibernate');

      // Also dispatch a DOM CustomEvent for inline listeners
      this.host.dispatchEvent(new CustomEvent('krystal:hibernate', { bubbles: true, detail: { widgetId: this.widgetId } }));
    }

    _wake() {
      if (!this._sleeping) return;
      this._sleeping = false;
      console.info(`[HibernationEngine] ☀️  Widget "${this.widgetId}" → WAKE`);

      _removeHibernateStyle(this.host);
      this._resetTimer();

      this._emit('Krystal.lifecycle.wake');
      this.host.dispatchEvent(new CustomEvent('krystal:wake', { bubbles: true, detail: { widgetId: this.widgetId } }));
    }

    /** Emit a named event into an inner frame's Krystal event bus (if present). */
    _emit(eventName) {
      try {
        if (this.innerWin && this.innerWin.Krystal && typeof this.innerWin.Krystal.emit === 'function') {
          this.innerWin.Krystal.emit(eventName, { widgetId: this.widgetId });
        }
      } catch (_) { /* cross-origin frame — safe to skip */ }
    }

    /** Cleanup all listeners and timers. */
    destroy() {
      clearTimeout(this._timer);
      ['pointermove', 'pointerdown', 'keydown', 'focus', 'scroll'].forEach(evt => {
        this.host.removeEventListener(evt, this._onActivity, { capture: true });
      });
      this.host.removeEventListener('mouseenter', this._onEnter);
      _removeHibernateStyle(this.host);
    }
  }

  /**
   * Global HibernationEngine — registry for all active controllers.
   */
  class HibernationEngine {
    constructor() {
      this._controllers = new Map(); // widgetId → WidgetHibernationController
    }

    /**
     * Register a Widget DOM zone for lifecycle monitoring.
     *
     * @param {HTMLElement} hostEl         - Widget outer container.
     * @param {Object}      manifest       - Parsed krystal.json object.
     * @param {Window|null} innerFrameWin  - Optional <iframe>.contentWindow inside the widget.
     */
    register(hostEl, manifest, innerFrameWin = null) {
      const id      = manifest.name || hostEl.id || `widget-${Date.now()}`;
      const timeout = _parseDuration(manifest.timeout_idle);

      if (this._controllers.has(id)) {
        console.warn(`[HibernationEngine] Widget "${id}" already registered. Skipping.`);
        return;
      }

      const controller = new WidgetHibernationController(hostEl, id, timeout, innerFrameWin);
      this._controllers.set(id, controller);
      console.info(`[HibernationEngine] 🔷 監視開始 Widget "${id}" — idle timeout: ${manifest.timeout_idle || '5m'}`);
    }

    /**
     * Unregister and cleanup a widget's lifecycle controller.
     * @param {string} widgetId
     */
    unregister(widgetId) {
      const ctrl = this._controllers.get(widgetId);
      if (ctrl) {
        ctrl.destroy();
        this._controllers.delete(widgetId);
        console.info(`[HibernationEngine] 🗑 Unregistered "${widgetId}"`);
      }
    }

    /** Force-hibernate a specific widget immediately. */
    forceHibernate(widgetId) {
      this._controllers.get(widgetId)?._hibernate();
    }

    /** Force-wake a specific widget immediately. */
    forceWake(widgetId) {
      this._controllers.get(widgetId)?._wake();
    }

    /** Destroy all controllers on page unload. */
    destroyAll() {
      this._controllers.forEach(ctrl => ctrl.destroy());
      this._controllers.clear();
    }
  }

  // Expose as global singleton
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.hibernation = new HibernationEngine();

  // Auto-cleanup on page unload
  window.addEventListener('beforeunload', () => window.Krystal.hibernation.destroyAll());

  console.log('[HibernationEngine] ❄️  Lifecycle Manager Online — Monitor Mode Active.');
})();
