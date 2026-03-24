/**
 * KrystalOS — core/ui/InteractiveGuardian.js
 * Phase 7.5: Non-Invasive Lite-Mode Resource Guardian
 *
 * Instead of silently force-hibernating widgets (HibernationEngine behavior),
 * InteractiveGuardian injects a user-controlled Smart Prompt overlay,
 * giving the developer or end-user the choice to:
 *
 *   [Suspender] → Deep Unmount: serialize state → innerHTML='' → kill Worker
 *   [Ignorar]   → Throttle Mode: slow animations + reduce polling rate 30%
 *
 * On click of the now-empty zone → Re-hydration from localStorage.
 *
 * Usage:
 *   window.Krystal.guardian.register(hostEl, manifest, innerWin);
 */

(function () {
  'use strict';

  const STATE_KEY = (id) => `krystal_state_${id}`;

  // ── CSS Injection ──────────────────────────────────────────────────────────
  function _injectStyles() {
    if (document.getElementById('__kos-guardian-styles')) return;
    const style = document.createElement('style');
    style.id = '__kos-guardian-styles';
    style.textContent = `
      /* Smart Prompt Overlay */
      .__kos-guardian-prompt {
        position: absolute;
        inset: 0;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: rgba(10, 8, 30, 0.82);
        backdrop-filter: blur(6px);
        border-radius: inherit;
        font-family: system-ui, -apple-system, sans-serif;
        animation: __kos-guardian-fadein 0.3s ease;
      }
      @keyframes __kos-guardian-fadein {
        from { opacity: 0; transform: scale(0.96); }
        to   { opacity: 1; transform: scale(1); }
      }
      .__kos-guardian-prompt .__msg {
        color: rgba(255,255,255,0.85);
        font-size: 12px;
        text-align: center;
        max-width: 200px;
        line-height: 1.5;
      }
      .__kos-guardian-prompt .__icon {
        font-size: 26px;
      }
      .__kos-guardian-prompt .__actions {
        display: flex;
        gap: 8px;
        margin-top: 4px;
      }
      .__kos-guardian-prompt button {
        padding: 5px 14px;
        border-radius: 20px;
        border: 1px solid;
        cursor: pointer;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.04em;
        transition: opacity 0.2s;
        background: transparent;
      }
      .__kos-guardian-prompt button:hover { opacity: 0.75; }
      .__kos-guardian-prompt .__btn-suspend {
        border-color: var(--kos-accent, #00FFCC);
        color: var(--kos-accent, #00FFCC);
      }
      .__kos-guardian-prompt .__btn-ignore {
        border-color: rgba(255,255,255,0.3);
        color: rgba(255,255,255,0.5);
      }

      /* Throttled widget: slower animations, slightly dimmed */
      .kos-throttled {
        opacity: 0.82 !important;
        animation-duration: 3s !important;
        transition-duration: 0.8s !important;
        filter: brightness(0.9);
      }

      /* Empty (deep-unmounted) zone */
      .__kos-rehydration-zone {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 80px;
        cursor: pointer;
        border: 2px dashed rgba(255,255,255,0.15);
        border-radius: inherit;
        color: rgba(255,255,255,0.3);
        font-size: 11px;
        font-family: system-ui, sans-serif;
        gap: 6px;
        transition: border-color 0.2s, color 0.2s;
      }
      .__kos-rehydration-zone:hover {
        border-color: var(--kos-accent, #00FFCC);
        color: var(--kos-accent, #00FFCC);
      }
    `;
    document.head.appendChild(style);
  }

  // ── Duration parser (shared with HibernationEngine convention) ────────────
  function _parseDuration(str) {
    if (!str) return 5 * 60 * 1000;
    const m = String(str).trim().match(/^(\d+)(s|m|h)$/i);
    if (!m) return 5 * 60 * 1000;
    const mult = { s: 1000, m: 60_000, h: 3_600_000 };
    return parseInt(m[1], 10) * (mult[m[2].toLowerCase()] || 60_000);
  }

  // ── WidgetGuardianController ───────────────────────────────────────────────
  class WidgetGuardianController {
    /**
     * @param {HTMLElement} hostEl    - Widget outer container.
     * @param {Object}      manifest  - Parsed krystal.json.
     * @param {Window}      innerWin  - Optional iframe window for event bus.
     */
    constructor(hostEl, manifest, innerWin = null) {
      this.host       = hostEl;
      this.manifest   = manifest;
      this.widgetId   = manifest.name || hostEl.id || `widget-${Date.now()}`;
      this.timeout    = _parseDuration(manifest.timeout_idle);
      this.innerWin   = innerWin;
      this._timer     = null;
      this._prompted  = false;
      this._unmounted = false;
      this._throttled = false;

      this._onActivity = this._onActivity.bind(this);
      this._attach();
      this._resetTimer();
    }

    _attach() {
      ['pointermove', 'pointerdown', 'keydown', 'focus'].forEach(evt => {
        this.host.addEventListener(evt, this._onActivity, { passive: true, capture: true });
      });
    }

    _resetTimer() {
      clearTimeout(this._timer);
      if (!this._unmounted) {
        this._timer = setTimeout(() => this._showSmartPrompt(), this.timeout);
      }
    }

    _onActivity() {
      if (this._prompted) return; // Don't dismiss the prompt on accidental wiggle
      if (this._throttled) this._resetThrottle();
      this._resetTimer();
    }

    // ── Smart Prompt ─────────────────────────────────────────────────────────
    _showSmartPrompt() {
      if (this._prompted || this._unmounted) return;
      this._prompted = true;
      console.info(`[InteractiveGuardian] 💤 Widget "${this.widgetId}" → Smart Prompt shown`);

      this.host.style.position = this.host.style.position || 'relative';

      const overlay = document.createElement('div');
      overlay.className = '__kos-guardian-prompt';
      overlay.dataset.guardianOverlay = this.widgetId;

      overlay.innerHTML = `
        <span class="__icon">⏳</span>
        <p class="__msg">Este widget lleva tiempo inactivo y consume recursos.</p>
        <div class="__actions">
          <button class="__btn-suspend">Suspender</button>
          <button class="__btn-ignore">Ignorar</button>
        </div>
      `;

      // ── Event isolation: prevent bubbling to widget UI beneath ────────────
      overlay.addEventListener('click',       e => e.stopPropagation());
      overlay.addEventListener('pointerdown', e => e.stopPropagation());

      overlay.querySelector('.__btn-suspend').addEventListener('click', (e) => {
        e.stopPropagation();
        this._deepUnmount(overlay);
      });

      overlay.querySelector('.__btn-ignore').addEventListener('click', (e) => {
        e.stopPropagation();
        this._applyThrottle(overlay);
      });

      this.host.appendChild(overlay);
    }

    _dismissPrompt(overlay) {
      overlay?.remove();
      this._prompted = false;
    }

    // ── Deep Unmount (Suspend) ────────────────────────────────────────────────
    _deepUnmount(overlay) {
      console.info(`[InteractiveGuardian] ❄️  Widget "${this.widgetId}" → Deep Unmount`);

      // 1. Serialize state
      const stateData = {
        widgetId:  this.widgetId,
        manifest:  this.manifest,
        timestamp: Date.now(),
        html:      this.host.innerHTML,
      };
      try {
        localStorage.setItem(STATE_KEY(this.widgetId), JSON.stringify(stateData));
      } catch (_) { /* storage full — proceed anyway */ }

      // 2. Emit lifecycle event
      this._emit('Krystal.lifecycle.hibernate');
      this.host.dispatchEvent(new CustomEvent('krystal:hibernate', {
        bubbles: true, detail: { widgetId: this.widgetId, reason: 'guardian-suspend' },
      }));

      // 3. Kill Worker
      try {
        window.Krystal?.thread?.terminate(this.widgetId);
      } catch (_) { }

      // 4. Wipe DOM
      this._unmounted = true;
      this.host.innerHTML = '';
      clearTimeout(this._timer);

      // 5. Inject re-hydration zone
      const zone = document.createElement('div');
      zone.className = '__kos-rehydration-zone';
      zone.innerHTML = `<span>▶</span> ${this.manifest.ui?.icon || '🧩'} Clic para reanudar`;
      zone.addEventListener('click', () => this._rehydrate(zone));
      this.host.appendChild(zone);
    }

    // ── Re-hydration ─────────────────────────────────────────────────────────
    _rehydrate(zone) {
      const raw = localStorage.getItem(STATE_KEY(this.widgetId));
      if (!raw) {
        zone.textContent = '⚠ Estado no disponible. Recarga el widget manualmente.';
        return;
      }

      const stateData = JSON.parse(raw);
      console.info(`[InteractiveGuardian] ☀️  Widget "${this.widgetId}" → Re-hydration`);

      // Restore HTML
      this.host.innerHTML = stateData.html || '';
      this._unmounted = false;
      this._prompted  = false;

      // Re-attach activity listeners
      this._attach();
      this._resetTimer();

      // Emit wake
      this._emit('Krystal.lifecycle.wake');
      this.host.dispatchEvent(new CustomEvent('krystal:wake', {
        bubbles: true, detail: { widgetId: this.widgetId },
      }));

      localStorage.removeItem(STATE_KEY(this.widgetId));
    }

    // ── Throttle Mode (Ignore) ────────────────────────────────────────────────
    _applyThrottle(overlay) {
      console.info(`[InteractiveGuardian] 🐢 Widget "${this.widgetId}" → Throttle Mode (30%)`);
      this._dismissPrompt(overlay);
      this._throttled = true;
      this.host.classList.add('kos-throttled');

      // Signal the ThreadBridge if a Worker is running (reduce call frequency)
      try {
        const bridge = window.Krystal?.thread;
        if (bridge) {
          // Store throttle factor — Workers can read this via Krystal.throttle.get(id)
          if (!window.Krystal.throttle) window.Krystal.throttle = {};
          window.Krystal.throttle[this.widgetId] = 0.3;
        }
      } catch (_) { }

      this._emit('Krystal.lifecycle.throttle');
      // Continue idle timer at normal interval — user activity resets it
      this._resetTimer();
    }

    _resetThrottle() {
      if (!this._throttled) return;
      this._throttled = false;
      this.host.classList.remove('kos-throttled');
      if (window.Krystal?.throttle) delete window.Krystal.throttle[this.widgetId];
      console.info(`[InteractiveGuardian] ✅ Widget "${this.widgetId}" → Full speed restored`);
    }

    // ── IPC Utility ───────────────────────────────────────────────────────────
    _emit(eventName) {
      try {
        if (this.innerWin?.Krystal?.emit) {
          this.innerWin.Krystal.emit(eventName, { widgetId: this.widgetId });
        }
      } catch (_) { }
    }

    destroy() {
      clearTimeout(this._timer);
      ['pointermove', 'pointerdown', 'keydown', 'focus'].forEach(evt => {
        this.host.removeEventListener(evt, this._onActivity, { capture: true });
      });
      this.host.querySelector('.__kos-guardian-prompt')?.remove();
      this.host.classList.remove('kos-throttled');
    }
  }

  // ── InteractiveGuardian (Global Registry) ─────────────────────────────────
  class InteractiveGuardian {
    constructor() {
      this._controllers = new Map();
      _injectStyles();
    }

    /**
     * Register a widget for non-invasive lifecycle monitoring.
     * @param {HTMLElement} hostEl    - Widget container element.
     * @param {Object}      manifest  - Parsed krystal.json.
     * @param {Window}      innerWin  - Optional inner frame window.
     */
    register(hostEl, manifest, innerWin = null) {
      const id = manifest.name || hostEl.id;
      if (this._controllers.has(id)) return;
      const ctrl = new WidgetGuardianController(hostEl, manifest, innerWin);
      this._controllers.set(id, ctrl);
      console.info(`[InteractiveGuardian] 🛡 Monitoring "${id}" — idle: ${manifest.timeout_idle || '5m'}`);
    }

    unregister(widgetId) {
      const ctrl = this._controllers.get(widgetId);
      if (ctrl) { ctrl.destroy(); this._controllers.delete(widgetId); }
    }

    destroyAll() {
      this._controllers.forEach(c => c.destroy());
      this._controllers.clear();
    }
  }

  // ── Expose globally ────────────────────────────────────────────────────────
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.guardian = new InteractiveGuardian();

  window.addEventListener('beforeunload', () => window.Krystal.guardian.destroyAll());

  console.log('[InteractiveGuardian] 🛡 Non-Invasive Lite Guardian Online.');
})();
