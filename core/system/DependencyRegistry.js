/**
 * KrystalOS — core/system/DependencyRegistry.js
 * Phase 7.3: Centralized Dependency Registry
 *
 * Reads `shared_tools` and `isolated_tools` from widget krystal.json manifests.
 * - `shared_tools` are injected once globally into `window.KrystalShared`.
 * - `isolated_tools` are sandboxed inside the widget's Shadow DOM only.
 */

(function () {
  'use strict';

  /**
   * Singleton lock registry for globally loaded tools.
   * { "chartjs@3.0": true, "axios": true }
   */
  window.KrystalShared = window.KrystalShared || {};

  /**
   * Map of known CDN endpoints for common shared libraries.
   * Developers can extend this via Krystal.registry.register().
   */
  const KNOWN_CDN = {
    'chartjs':    'https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js',
    'chartjs@3.0':'https://cdn.jsdelivr.net/npm/chart.js@3/dist/chart.min.js',
    'axios':      'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js',
    'lodash':     'https://cdn.jsdelivr.net/npm/lodash@4/lodash.min.js',
    'dayjs':      'https://cdn.jsdelivr.net/npm/dayjs/dayjs.min.js',
    'alpinejs':   'https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js',
    'sortablejs': 'https://cdn.jsdelivr.net/npm/sortablejs@1/Sortable.min.js',
  };

  /**
   * Inject a <script> tag into a target document/shadow root.
   * Returns a Promise that resolves when the script loads.
   */
  function _injectScript(src, targetDocument = document) {
    return new Promise((resolve, reject) => {
      const script = targetDocument.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`[DependencyRegistry] Failed to load: ${src}`));
      (targetDocument.head || targetDocument.body).appendChild(script);
    });
  }

  /**
   * Resolve CDN URL for a tool name/version specifier.
   */
  function _resolveCDN(toolSpec) {
    if (KNOWN_CDN[toolSpec]) return KNOWN_CDN[toolSpec];
    // Fallback: try unpkg with the raw specifier
    return `https://unpkg.com/${toolSpec}`;
  }

  /**
   * Main DependencyRegistry class (Singleton).
   */
  class DependencyRegistry {
    constructor() {
      this._pending = {};
    }

    /**
     * Load a tool globally (shared). Guarantees single injection.
     * @param {string} toolSpec - e.g. "chartjs@3.0"
     * @returns {Promise<void>}
     */
    async loadShared(toolSpec) {
      // Already loaded
      if (window.KrystalShared[toolSpec]) {
        console.debug(`[DependencyRegistry] ♻ Shared hit: ${toolSpec}`);
        return;
      }
      // Loading in progress — await the same promise
      if (this._pending[toolSpec]) {
        return this._pending[toolSpec];
      }

      const src = _resolveCDN(toolSpec);
      console.info(`[DependencyRegistry] 📦 Loading shared tool: ${toolSpec} → ${src}`);

      this._pending[toolSpec] = _injectScript(src, document)
        .then(() => {
          window.KrystalShared[toolSpec] = true;
          delete this._pending[toolSpec];
          console.info(`[DependencyRegistry] ✓ Shared ready: ${toolSpec}`);
        });

      return this._pending[toolSpec];
    }

    /**
     * Load a tool in isolation inside a Widget's ShadowRoot.
     * The script is injected only inside the shadow document — no global pollution.
     * @param {string} toolSpec
     * @param {ShadowRoot} shadowRoot
     */
    async loadIsolated(toolSpec, shadowRoot) {
      if (!shadowRoot) {
        console.warn(`[DependencyRegistry] No ShadowRoot provided for isolated tool: ${toolSpec}`);
        return;
      }
      const src = _resolveCDN(toolSpec);
      console.info(`[DependencyRegistry] 🔒 Loading isolated tool for ${shadowRoot.host?.id || 'widget'}: ${toolSpec}`);
      // shadowRoot.ownerDocument gives us a scoped document context
      await _injectScript(src, shadowRoot.ownerDocument);
    }

    /**
     * Process a widget's manifest payload and load all tools.
     * @param {Object} manifest - parsed krystal.json
     * @param {ShadowRoot|null} shadowRoot - the widget's shadow root
     */
    async processManifest(manifest, shadowRoot = null) {
      const shared   = manifest.shared_tools   || [];
      const isolated = manifest.isolated_tools  || [];

      await Promise.all(shared.map(t => this.loadShared(t)));
      if (shadowRoot) {
        await Promise.all(isolated.map(t => this.loadIsolated(t, shadowRoot)));
      }
    }

    /**
     * Register a custom CDN mapping.
     * @param {string} toolSpec
     * @param {string} url
     */
    register(toolSpec, url) {
      KNOWN_CDN[toolSpec] = url;
      console.info(`[DependencyRegistry] 📝 Registered custom CDN: ${toolSpec} → ${url}`);
    }
  }

  // Expose as global singleton
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.registry = new DependencyRegistry();

  console.log('[DependencyRegistry] 🔷 Centralized Dependency Registry Online.');
})();
