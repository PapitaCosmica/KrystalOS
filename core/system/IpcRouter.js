/**
 * KrystalOS — core/system/IpcRouter.js
 * Phase 7.6: Universal JSON IPC Router — Data Mesh Engine
 *
 * Routes data payloads between Widgets and Mods following pipeline rules
 * defined in pipelines.json. Features:
 *   - Hop-limit protection (max 3 hops → loop kill switch)
 *   - iOS-style permission toasts (Allow / Deny) with persistence
 *   - Automatic wake of hibernated target widgets
 *   - IPC_DENIED error propagation back to sender
 *
 * Usage (from inside a Widget's Shadow DOM or Worker):
 *   const result = await Krystal.ipc.route('weather-widget', 'temp', 24.5);
 *   if (result?.error === 'IPC_DENIED') { showPermissionError(); }
 */

(function () {
  'use strict';

  const PIPELINES_API   = '/api/pipelines';
  const PERMISSIONS_API = '/api/permissions';
  const MAX_HOPS        = 3;
  const PERM_KEY = (from, to) => `krystal_perm_${from}_${to}`;

  // ── CSS for Permission Toast ────────────────────────────────────────────────
  function _injectStyles() {
    if (document.getElementById('__kos-ipc-styles')) return;
    const style = document.createElement('style');
    style.id = '__kos-ipc-styles';
    style.textContent = `
      .__kos-ipc-toast {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 999999;
        min-width: 280px;
        max-width: 340px;
        background: rgba(15, 12, 41, 0.92);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(0, 255, 204, 0.25);
        border-radius: 16px;
        padding: 16px 18px;
        font-family: system-ui, -apple-system, sans-serif;
        color: #fff;
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        gap: 10px;
        animation: __kos-ipc-slide 0.3s cubic-bezier(.22,1,.36,1);
      }
      @keyframes __kos-ipc-slide {
        from { opacity:0; transform: translateY(20px) scale(0.95); }
        to   { opacity:1; transform: translateY(0)   scale(1); }
      }
      .__kos-ipc-toast .__title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: var(--kos-accent, #00FFCC);
        text-transform: uppercase;
      }
      .__kos-ipc-toast .__msg {
        font-size: 13px;
        line-height: 1.5;
        color: rgba(255,255,255,0.85);
      }
      .__kos-ipc-toast .__msg strong { color: #fff; }
      .__kos-ipc-toast .__actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
      }
      .__kos-ipc-toast button {
        padding: 6px 16px;
        border-radius: 20px;
        border: 1px solid;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
        background: transparent;
        transition: opacity 0.2s;
      }
      .__kos-ipc-toast button:hover { opacity: 0.7; }
      .__kos-ipc-toast .__btn-allow {
        border-color: var(--kos-accent, #00FFCC);
        color: var(--kos-accent, #00FFCC);
      }
      .__kos-ipc-toast .__btn-deny {
        border-color: rgba(255,100,100,0.6);
        color: rgba(255,130,130,0.9);
      }
    `;
    document.head.appendChild(style);
  }

  // ── Utilities ──────────────────────────────────────────────────────────────
  function _uuid() {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  }

  function _deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  // ── IPC Router ─────────────────────────────────────────────────────────────
  class IpcRouter {
    constructor() {
      this._pipelines   = [];      // Loaded from pipelines.json
      this._permCache   = {};      // { 'from→to': 'allow' | 'deny' }
      this._pendingPerms = new Map(); // Promise resolvers awaiting user choice
      this._errorLog    = [];      // In-memory log for debugging

      _injectStyles();
      this._loadPipelines();
      this._loadLocalPermissions();
    }

    // ── Pipeline Loading ────────────────────────────────────────────────────
    async _loadPipelines() {
      try {
        const res = await fetch(PIPELINES_API);
        if (res.ok) {
          const data = await res.json();
          this._pipelines = data.pipelines || [];
          console.info(`[IpcRouter] 📡 ${this._pipelines.length} pipeline(s) loaded from server.`);
        }
      } catch (_) {
        console.debug('[IpcRouter] Pipeline API not available — running in offline mode.');
      }
    }

    /** Manually register a pipeline in memory (useful in Lab / offline mode). */
    registerPipeline(rule) {
      this._pipelines.push({ id: _uuid(), active: true, ...rule });
    }

    // ── Permission Cache ────────────────────────────────────────────────────
    _loadLocalPermissions() {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('krystal_perm_')) {
          this._permCache[key] = localStorage.getItem(key);
        }
      }
    }

    _getPermission(fromId, toId) {
      return this._permCache[PERM_KEY(fromId, toId)] || null;
    }

    _savePermission(fromId, toId, decision) {
      const key = PERM_KEY(fromId, toId);
      this._permCache[key] = decision;
      localStorage.setItem(key, decision);
      // Async persist to backend
      fetch(PERMISSIONS_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: fromId, to: toId, decision }),
      }).catch(() => {});
    }

    // ── Permission Toast ────────────────────────────────────────────────────
    _requestPermission(fromId, toId) {
      // Already pending for this pair?
      const pendingKey = `${fromId}→${toId}`;
      if (this._pendingPerms.has(pendingKey)) {
        return this._pendingPerms.get(pendingKey);
      }

      const promise = new Promise((resolve) => {
        const toast = document.createElement('div');
        toast.className = '__kos-ipc-toast';
        toast.innerHTML = `
          <span class="__title">🔒 Solicitud de Datos — KrystalOS</span>
          <p class="__msg">
            <strong>${fromId}</strong> quiere enviar datos a <strong>${toId}</strong>.
            ¿Deseas permitirlo?
          </p>
          <div class="__actions">
            <button class="__btn-deny">Denegar</button>
            <button class="__btn-allow">Permitir</button>
          </div>
        `;

        const cleanup = (decision) => {
          toast.remove();
          this._pendingPerms.delete(pendingKey);
          this._savePermission(fromId, toId, decision);
          resolve(decision);
        };

        toast.querySelector('.__btn-allow').addEventListener('click', () => cleanup('allow'));
        toast.querySelector('.__btn-deny').addEventListener('click',  () => cleanup('deny'));

        // Mount on shell or body
        const shell = document.getElementById('krystal-shell') || document.body;
        shell.appendChild(toast);
        console.info(`[IpcRouter] 🔒 Permission request: ${fromId} → ${toId}`);
      });

      this._pendingPerms.set(pendingKey, promise);
      return promise;
    }

    // ── Hop-Limit Protection ───────────────────────────────────────────────
    _checkHops(payload, routeTrace) {
      const hops = (payload._kos_hops || 0) + 1;
      if (hops >= MAX_HOPS) {
        const route = routeTrace.join(' → ');
        const msg = [
          `⚠️ [KrystalOS] Bucle infinito detectado y bloqueado en la ruta [${route}].`,
          `Sugerencia: Revisa los outputs de tu krystal.json para evitar dependencias circulares,`,
          `o implementa una validación de estado previo antes de emitir Krystal.emit().`,
        ].join('\n');
        console.warn(msg);
        this._errorLog.push({ type: 'LOOP_KILLED', route, timestamp: Date.now() });
        document.dispatchEvent(new CustomEvent('krystal:ipc-loop-killed', { detail: { route } }));
        return null; // Signal to destroy packet
      }
      return hops;
    }

    // ── Core Routing ───────────────────────────────────────────────────────
    /**
     * Route a data payload from a source widget's output to all registered targets.
     *
     * @param {string} fromId      - Sender widget ID (e.g. "weather-widget").
     * @param {string} outputKey   - The output field name (e.g. "temp").
     * @param {any}    payload     - The data value to route.
     * @param {object} [_meta]     - Internal hop metadata (don't set manually).
     * @returns {Promise<Array>}   - Array of delivery results per target.
     */
    async route(fromId, outputKey, payload, _meta = {}) {
      const routeTrace = _meta._trace || [fromId];

      // Find matching pipelines
      const rules = this._pipelines.filter(
        p => p.active && p.from === fromId && p.output_key === outputKey
      );

      if (!rules.length) {
        console.debug(`[IpcRouter] No active pipelines for ${fromId}.${outputKey}`);
        return [];
      }

      const results = [];

      for (const rule of rules) {
        const toId = rule.to;

        // ── Hop check ─────────────────────────────────────────────────────
        const packetPayload = typeof payload === 'object' && payload !== null
          ? _deepClone(payload)
          : { value: payload };

        const newTrace = [...routeTrace, toId];
        const hops = this._checkHops(packetPayload, newTrace);
        if (hops === null) {
          results.push({ to: toId, status: 'LOOP_KILLED' });
          continue;
        }
        packetPayload._kos_hops = hops;
        packetPayload._kos_from = fromId;
        packetPayload._kos_key  = outputKey;

        // ── Permission check ───────────────────────────────────────────────
        let perm = this._getPermission(fromId, toId);
        if (!perm) {
          perm = await this._requestPermission(fromId, toId);
        }
        if (perm === 'deny') {
          console.info(`[IpcRouter] 🚫 IPC_DENIED: ${fromId} → ${toId}`);
          results.push({ to: toId, error: 'IPC_DENIED', from: fromId });
          continue;
        }

        // ── Wake hibernated widget ─────────────────────────────────────────
        const targetEl = document.querySelector(`[data-widget-id="${toId}"]`);
        if (targetEl) {
          const isUnmounted = !targetEl.children.length ||
            targetEl.querySelector('.__kos-rehydration-zone');
          if (isUnmounted) {
            console.info(`[IpcRouter] ⏰ Waking hibernated widget: ${toId}`);
            targetEl.dispatchEvent(new CustomEvent('krystal:wake', {
              bubbles: true, detail: { widgetId: toId, reason: 'ipc-delivery' },
            }));
            // Wait briefly for re-hydration
            await new Promise(r => setTimeout(r, 300));
          }
        }

        // ── Deliver ───────────────────────────────────────────────────────
        const event = new CustomEvent('krystal:ipc-receive', {
          bubbles: true,
          detail: {
            widgetId:  toId,
            inputKey:  rule.input_key,
            schema:    rule.schema,
            payload:   packetPayload,
          },
        });

        if (targetEl) {
          targetEl.dispatchEvent(event);
        } else {
          document.dispatchEvent(event);
        }

        console.info(
          `[IpcRouter] ✓ ${fromId}.${outputKey} → ${toId}.${rule.input_key} `
          + `(schema: ${rule.schema}, hops: ${hops})`
        );
        results.push({ to: toId, status: 'DELIVERED', hops });
      }

      return results;
    }

    /** Revoke a previously granted permission. */
    revokePermission(fromId, toId) {
      const key = PERM_KEY(fromId, toId);
      delete this._permCache[key];
      localStorage.removeItem(key);
      console.info(`[IpcRouter] 🔑 Permission revoked: ${fromId} → ${toId}`);
    }

    /** Get the in-memory error/event log. */
    get log() {
      return [...this._errorLog];
    }
  }

  // ── Expose globally ────────────────────────────────────────────────────────
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.ipc = new IpcRouter();

  console.log('[IpcRouter] 📡 Data Mesh IPC Router Online — Krystal.ipc ready.');
})();
