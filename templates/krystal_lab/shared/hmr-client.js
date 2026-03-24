/**
 * KrystalOS — templates/krystal_lab/shared/hmr-client.js
 * Phase 7.4: HMR WebSocket Client
 *
 * Auto-connects to the KrystalOS Dev Server and applies live-reload
 * changes without a full page refresh.
 *
 * Injected automatically by lab_engine.py into all Lab HTML files.
 *
 * Handles:
 *   RELOAD_STYLES  → Replace <link> or inject <style> into Shadow DOM
 *   RELOAD_WORKER  → Call Krystal.thread.restart(widgetId)
 *   RELOAD_PAGE    → Hard reload fallback
 */

(function () {
  'use strict';

  const HMR_PORT    = window.__KRYSTAL_HMR_PORT__ || 5173;
  const HMR_URL     = `ws://localhost:${HMR_PORT}`;
  const RECONNECT_MS = 2000;

  let _ws = null;

  function _connect() {
    try {
      _ws = new WebSocket(HMR_URL);
    } catch (e) {
      console.warn('[HMR] WebSocket not available in this context.');
      return;
    }

    _ws.onopen = () => {
      console.info(`%c[KrystalOS HMR] 🔥 Live Reload connected on port ${HMR_PORT}`, 'color:#00FFCC;font-weight:bold;');
    };

    _ws.onmessage = ({ data }) => {
      let msg;
      try { msg = JSON.parse(data); } catch { return; }

      switch (msg.type) {
        case 'RELOAD_STYLES':
          _reloadStyles(msg.file, msg.content);
          break;
        case 'RELOAD_WORKER':
          _reloadWorker(msg.widgetId);
          break;
        case 'RELOAD_PAGE':
          console.info('[HMR] Full page reload triggered.');
          location.reload();
          break;
        default:
          console.debug('[HMR] Unknown message type:', msg.type);
      }
    };

    _ws.onclose = () => {
      console.warn('[HMR] Connection lost. Reconnecting...');
      setTimeout(_connect, RECONNECT_MS);
    };

    _ws.onerror = () => {
      _ws.close();
    };
  }

  /**
   * Inject or replace a stylesheet surgically.
   * Works both in the main document and inside the widget's Shadow Root.
   */
  function _reloadStyles(filename, content) {
    console.info(`[HMR] 🎨 Hot-reloading styles: ${filename}`);

    // Try to find the widget's Shadow Root to inject there first
    const widgetHosts = document.querySelectorAll('[data-widget-id]');
    let injected = false;

    widgetHosts.forEach(host => {
      const shadow = host.shadowRoot;
      if (!shadow) return;

      // Look for existing <link> or <style> matching this file
      let existing = shadow.querySelector(`[data-hmr-file="${filename}"]`);
      if (!existing) {
        // Also check for <link> with matching href
        existing = Array.from(shadow.querySelectorAll('link[rel="stylesheet"]'))
          .find(l => l.href.includes(filename));
      }

      if (existing) {
        // Replace with inline style (avoids cache issues)
        const styleEl = document.createElement('style');
        styleEl.dataset.hmrFile = filename;
        styleEl.textContent = content;
        existing.replaceWith(styleEl);
        injected = true;
      } else if (content) {
        // No existing reference — append new style
        const styleEl = document.createElement('style');
        styleEl.dataset.hmrFile = filename;
        styleEl.textContent = content;
        shadow.appendChild(styleEl);
        injected = true;
      }
    });

    if (!injected) {
      // Fallback: inject / replace in the main document
      let existing = document.querySelector(`[data-hmr-file="${filename}"]`);
      if (!existing) {
        existing = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
          .find(l => l.href.includes(filename));
      }

      if (existing && content) {
        const styleEl = document.createElement('style');
        styleEl.dataset.hmrFile = filename;
        styleEl.textContent = content;
        existing.replaceWith(styleEl);
      } else if (content) {
        const styleEl = document.createElement('style');
        styleEl.dataset.hmrFile = filename;
        styleEl.textContent = content;
        document.head.appendChild(styleEl);
      } else {
        // No content fallback → cache-bust the <link>
        const link = document.querySelector(`link[href*="${filename}"]`);
        if (link) link.href = link.href.split('?')[0] + `?hmr=${Date.now()}`;
      }
    }

    console.info(`[HMR] ✓ Styles applied: ${filename}`);
  }

  /**
   * Restart the Web Worker for a specific widget via ThreadBridge.
   */
  function _reloadWorker(widgetId) {
    console.info(`[HMR] 🧵 Restarting worker for: ${widgetId}`);
    if (window.Krystal?.thread) {
      window.Krystal.thread.restart(widgetId);
      console.info(`[HMR] ✓ Worker restarted: ${widgetId}`);
    } else {
      console.warn('[HMR] Krystal.thread not available. Falling back to page reload.');
      location.reload();
    }
  }

  // ── Boot ──────────────────────────────────────────────────────────────────
  _connect();
  console.debug('[HMR] Client script loaded.');
})();
