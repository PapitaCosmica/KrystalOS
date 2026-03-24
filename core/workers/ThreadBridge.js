/**
 * KrystalOS — core/workers/ThreadBridge.js
 * Phase 7.4: Off-Main-Thread IPC Engine
 *
 * Provides `window.Krystal.thread` API to spawn, communicate with,
 * and gracefully crash-isolate Web Workers for heavy widget logic.
 *
 * IPC Message Protocol:
 *   → CALL:   { type: "CALL",   method, args, requestId }
 *   ← RESULT: { type: "RESULT", data,         requestId }
 *   ← ERROR:  { type: "ERROR",  message,      requestId }
 *   ← EVENT:  { type: "EVENT",  name, payload            }  (worker → UI push)
 *
 * Usage (from widget UI code running in Shadow DOM):
 *   await Krystal.thread.spawn('my-widget', './logic.worker.js');
 *   const result = await Krystal.thread.call('my-widget', 'processData', [payload]);
 *
 * Usage (inside the worker file logic.worker.js):
 *   self.onmessage = ({ data }) => {
 *     if (data.type === 'CALL' && data.method === 'processData') {
 *       const result = heavyCompute(data.args[0]);
 *       self.postMessage({ type: 'RESULT', requestId: data.requestId, data: result });
 *     }
 *   };
 */

(function () {
  'use strict';

  // ── Utilities ──────────────────────────────────────────────────────────────
  function _uuid() {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
  }

  // ── WorkerProxy wraps a single Worker instance ────────────────────────────
  class WorkerProxy {
    /**
     * @param {string}      widgetId   - Identifier for this worker slot.
     * @param {string}      workerUrl  - URL/path to the worker script.
     * @param {HTMLElement} hostEl     - Widget host element (for Fallback UI).
     */
    constructor(widgetId, workerUrl, hostEl = null) {
      this.widgetId  = widgetId;
      this.workerUrl = workerUrl;
      this.hostEl    = hostEl;
      this._pending  = new Map(); // requestId → { resolve, reject }
      this._worker   = null;
      this._alive    = false;
      this._boot();
    }

    _boot() {
      try {
        this._worker = new Worker(this.workerUrl, { type: 'module' });
        this._alive  = true;

        this._worker.onmessage = ({ data }) => this._handleMessage(data);
        this._worker.onerror   = (err)     => this._handleCrash(err.message || 'Worker Error');
        this._worker.onmessageerror = ()   => this._handleCrash('Message deserialization error');

        console.info(`[ThreadBridge] 🧵 Worker spawned: "${this.widgetId}" → ${this.workerUrl}`);
      } catch (err) {
        this._handleCrash(err.message);
      }
    }

    _handleMessage(data) {
      if (data.type === 'RESULT' || data.type === 'ERROR') {
        const pending = this._pending.get(data.requestId);
        if (!pending) return;
        this._pending.delete(data.requestId);

        if (data.type === 'RESULT') {
          pending.resolve(data.data);
        } else {
          pending.reject(new Error(data.message));
        }
      } else if (data.type === 'EVENT') {
        // Worker-pushed event — dispatch as CustomEvent on the host element
        const target = this.hostEl || document;
        target.dispatchEvent(new CustomEvent(`krystal:worker-event:${data.name}`, {
          bubbles: true,
          detail: { widgetId: this.widgetId, payload: data.payload },
        }));
      }
    }

    _handleCrash(reason) {
      this._alive = false;
      console.error(`[ThreadBridge] 💥 Worker CRASHED: "${this.widgetId}" — ${reason}`);

      // Reject all pending calls
      this._pending.forEach(({ reject }) => reject(new Error(`Worker crashed: ${reason}`)));
      this._pending.clear();

      // Terminate the worker cleanly
      try { this._worker?.terminate(); } catch (_) { }
      this._worker = null;

      // Activate Fallback UI on the host element
      if (this.hostEl) {
        this._showFallbackUI(reason);
      }

      // Notify the OS shell
      document.dispatchEvent(new CustomEvent('krystal:worker-crash', {
        bubbles: true,
        detail: { widgetId: this.widgetId, reason },
      }));
    }

    _showFallbackUI(reason) {
      const el = this.hostEl;
      el.style.cssText += 'position:relative;overflow:hidden;';
      const overlay = document.createElement('div');
      overlay.className = '__kos-worker-crash-overlay';
      overlay.style.cssText = [
        'position:absolute', 'inset:0',
        'background:rgba(15,12,41,0.92)',
        'display:flex', 'flex-direction:column',
        'align-items:center', 'justify-content:center',
        'color:#ff6b6b', 'font-family:system-ui,sans-serif',
        'gap:8px', 'z-index:99999', 'border-radius:inherit',
        'backdrop-filter:blur(4px)',
      ].join(';');
      overlay.innerHTML = `
        <span style="font-size:28px">⚠️</span>
        <strong style="font-size:13px">Widget Worker Crashed</strong>
        <span style="font-size:11px;color:#888;max-width:160px;text-align:center">${reason}</span>
        <button onclick="window.Krystal.thread.restart('${this.widgetId}')"
          style="margin-top:8px;padding:5px 14px;border:1px solid #ff6b6b;border-radius:8px;
                 background:transparent;color:#ff6b6b;cursor:pointer;font-size:11px">
          ↺ Reintentar
        </button>
      `;
      el.appendChild(overlay);
    }

    /**
     * Call a method on the worker and receive a Promise.
     * @param {string} method
     * @param {any[]}  args
     * @param {number} timeoutMs - Default 30s
     * @returns {Promise<any>}
     */
    call(method, args = [], timeoutMs = 30_000) {
      if (!this._alive) {
        return Promise.reject(new Error(`Worker "${this.widgetId}" is not alive.`));
      }
      return new Promise((resolve, reject) => {
        const requestId = _uuid();
        this._pending.set(requestId, { resolve, reject });

        // Timeout guard
        const timer = setTimeout(() => {
          if (this._pending.has(requestId)) {
            this._pending.delete(requestId);
            reject(new Error(`Timeout: Worker "${this.widgetId}" did not respond to "${method}" in ${timeoutMs}ms`));
          }
        }, timeoutMs);

        // Clear timeout on response
        const orig = this._pending.get(requestId);
        this._pending.set(requestId, {
          resolve: (v) => { clearTimeout(timer); resolve(v); },
          reject:  (e) => { clearTimeout(timer); reject(e);  },
        });

        this._worker.postMessage({ type: 'CALL', method, args, requestId });
      });
    }

    terminate() {
      try { this._worker?.terminate(); } catch (_) { }
      this._alive  = false;
      this._worker = null;
    }

    get alive() { return this._alive; }
  }

  // ── ThreadBridge (global manager) ─────────────────────────────────────────
  class ThreadBridge {
    constructor() {
      this._workers = new Map(); // widgetId → WorkerProxy
    }

    /**
     * Spawn a Web Worker for a widget.
     * @param {string}      widgetId
     * @param {string}      workerUrl
     * @param {HTMLElement} hostEl     - Widget container for Fallback UI.
     */
    spawn(widgetId, workerUrl, hostEl = null) {
      if (this._workers.has(widgetId)) {
        console.warn(`[ThreadBridge] Worker "${widgetId}" already exists. Use restart() to replace.`);
        return;
      }
      const proxy = new WorkerProxy(widgetId, workerUrl, hostEl);
      this._workers.set(widgetId, proxy);
    }

    /**
     * Call a method on a widget's worker. Returns a Promise.
     * @param {string} widgetId
     * @param {string} method
     * @param {any[]}  args
     */
    call(widgetId, method, args = []) {
      const proxy = this._workers.get(widgetId);
      if (!proxy) return Promise.reject(new Error(`No worker registered for "${widgetId}".`));
      return proxy.call(method, args);
    }

    /**
     * Terminate and re-spawn a worker (HMR / manual recovery).
     * @param {string} widgetId
     */
    restart(widgetId) {
      const proxy = this._workers.get(widgetId);
      if (!proxy) return;

      const { workerUrl, hostEl } = proxy;

      // Remove old crash overlay if present
      hostEl?.querySelector('.__kos-worker-crash-overlay')?.remove();

      proxy.terminate();
      this._workers.delete(widgetId);

      const fresh = new WorkerProxy(widgetId, workerUrl, hostEl);
      this._workers.set(widgetId, fresh);
      console.info(`[ThreadBridge] ↺ Worker "${widgetId}" restarted.`);
    }

    /**
     * Terminate a worker completely.
     * @param {string} widgetId
     */
    terminate(widgetId) {
      const proxy = this._workers.get(widgetId);
      if (proxy) {
        proxy.terminate();
        this._workers.delete(widgetId);
        console.info(`[ThreadBridge] 🗑 Worker "${widgetId}" terminated.`);
      }
    }

    /**
     * Auto-process a widget manifest: if execution_mode === "worker",
     * spawn the worker automatically.
     * @param {Object}      manifest
     * @param {HTMLElement} hostEl
     */
    processManifest(manifest, hostEl) {
      if (manifest.execution_mode === 'worker' && manifest.worker_file) {
        this.spawn(manifest.name, manifest.worker_file, hostEl);
      }
    }

    terminateAll() {
      this._workers.forEach(p => p.terminate());
      this._workers.clear();
    }
  }

  // ── Expose globally ────────────────────────────────────────────────────────
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.thread = new ThreadBridge();

  window.addEventListener('beforeunload', () => window.Krystal.thread.terminateAll());

  console.log('[ThreadBridge] 🧵 Off-Main-Thread IPC Engine Online — Krystal.thread ready.');
})();
