/**
 * KrystalOS — core/ui/GridManager.js
 * Phase 7.4: Drag & Drop Grid Compositor with Persistent Layout
 *
 * Uses SortableJS (loaded via DependencyRegistry) to enable fluid
 * widget reordering across named Drop Zones. Saves layout to
 * grid.krystal.json with a 500ms debounce. Reconstructs on boot.
 *
 * Usage:
 *   await window.Krystal.grid.init();
 *
 * Markup convention:
 *   <div data-krystal-zone="krystal-desktop">
 *     <div data-widget-id="chat">...</div>
 *     <div data-widget-id="weather">...</div>
 *   </div>
 */

(function () {
  'use strict';

  const GRID_SAVE_PATH  = '/api/grid/save';       // Backend endpoint to persist
  const GRID_LOAD_PATH  = '/api/grid/load';       // Backend endpoint to load
  const DEBOUNCE_MS     = 500;
  const GHOST_CLASS     = 'kos-drag-ghost';
  const CHOSEN_CLASS    = 'kos-drag-chosen';
  const DROP_CLASS      = 'kos-drop-target';

  // ── Inject required CSS tokens into document head (once) ──────────────────
  function _injectStyles() {
    if (document.getElementById('__kos-grid-styles')) return;
    const style = document.createElement('style');
    style.id = '__kos-grid-styles';
    style.textContent = `
      /* Ghost: the original element while dragging */
      .${GHOST_CLASS} {
        opacity: 0.45 !important;
        border: 2px dashed var(--kos-accent, #00FFCC) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 18px var(--kos-accent, #00FFCC) !important;
        transition: opacity 0.15s ease !important;
      }
      /* Chosen: the element being held */
      .${CHOSEN_CLASS} {
        cursor: grabbing !important;
        transform: scale(1.03) rotate(0.8deg) !important;
        box-shadow: 0 16px 48px rgba(0,0,0,0.4) !important;
        z-index: 9999 !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
      }
      /* Drop target zone highlight */
      .${DROP_CLASS} {
        background: rgba(0, 255, 204, 0.06) !important;
        outline: 2px dashed var(--kos-accent, #00FFCC) !important;
        outline-offset: -4px !important;
        border-radius: inherit !important;
        transition: background 0.2s ease, outline 0.2s ease !important;
      }
    `;
    document.head.appendChild(style);
  }

  // ── Debounce helper ────────────────────────────────────────────────────────
  function _debounce(fn, ms) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  }

  // ── Serialize current zone state ───────────────────────────────────────────
  function _serializeLayout() {
    const layout = {};
    document.querySelectorAll('[data-krystal-zone]').forEach(zone => {
      const zoneId = zone.dataset.krystalZone;
      layout[zoneId] = Array.from(zone.querySelectorAll('[data-widget-id]'))
        .map(el => el.dataset.widgetId);
    });
    return layout;
  }

  // ── Save layout (debounced) ────────────────────────────────────────────────
  const _saveLayout = _debounce(async function () {
    const layout = _serializeLayout();
    try {
      // Try API endpoint first (KrystalOS backend)
      const res = await fetch(GRID_SAVE_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(layout),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      console.info('[GridManager] 💾 Layout saved to grid.krystal.json');
    } catch (_) {
      // Fallback: persist to localStorage for offline/Lab use
      localStorage.setItem('krystal_grid_layout', JSON.stringify(layout));
      console.info('[GridManager] 💾 Layout saved to localStorage (offline fallback)');
    }
    // Dispatch event for other systems to react
    document.dispatchEvent(new CustomEvent('krystal:grid-saved', { detail: layout }));
  }, DEBOUNCE_MS);

  // ── Load saved layout ──────────────────────────────────────────────────────
  async function _loadLayout() {
    try {
      const res = await fetch(GRID_LOAD_PATH);
      if (res.ok) return await res.json();
    } catch (_) { /* offline */ }
    // Fallback localStorage
    const raw = localStorage.getItem('krystal_grid_layout');
    return raw ? JSON.parse(raw) : null;
  }

  // ── Reconstruct DOM from saved layout ─────────────────────────────────────
  async function _reconstructLayout() {
    const layout = await _loadLayout();
    if (!layout) return;

    for (const [zoneId, widgetIds] of Object.entries(layout)) {
      const zone = document.querySelector(`[data-krystal-zone="${zoneId}"]`);
      if (!zone) continue;

      widgetIds.forEach(widgetId => {
        const el = zone.querySelector(`[data-widget-id="${widgetId}"]`);
        if (el) zone.appendChild(el); // AppendChild reorders to end — iterating preserves order
      });
    }
    console.info('[GridManager] 📐 Layout reconstructed from saved state.');
  }

  // ── Main GridManager class ─────────────────────────────────────────────────
  class GridManager {
    constructor() {
      this._sortables = new Map(); // zoneId → Sortable instance
    }

    /**
     * Initialize Drag & Drop across all [data-krystal-zone] elements.
     * Must be called after SortableJS is loaded.
     */
    async init() {
      _injectStyles();

      // Load SortableJS via DependencyRegistry
      if (!window.Sortable) {
        await window.Krystal.registry.loadShared('sortablejs');
      }

      // Reconstruct previous layout first
      await _reconstructLayout();

      // Activate each zone
      document.querySelectorAll('[data-krystal-zone]').forEach(zone => {
        this._activateZone(zone);
      });

      console.info(`[GridManager] 🔷 Drag & Drop active on ${this._sortables.size} zone(s).`);
    }

    /**
     * Activate a specific zone element as a Drop Zone.
     * @param {HTMLElement} zone
     */
    _activateZone(zone) {
      const zoneId = zone.dataset.krystalZone;
      if (this._sortables.has(zoneId)) return; // Already active

      const sortable = new window.Sortable(zone, {
        group:        'krystal-widgets',    // Allow cross-zone dragging
        animation:    180,
        ghostClass:   GHOST_CLASS,
        chosenClass:  CHOSEN_CLASS,
        dragClass:    GHOST_CLASS,

        // Highlight the drop target on enter
        onMove: (evt) => {
          document.querySelectorAll(`.${DROP_CLASS}`).forEach(el => el.classList.remove(DROP_CLASS));
          evt.to.classList.add(DROP_CLASS);
          return true; // Allow move
        },

        // Save layout after every drop
        onEnd: (evt) => {
          document.querySelectorAll(`.${DROP_CLASS}`).forEach(el => el.classList.remove(DROP_CLASS));
          console.debug(`[GridManager] ↔ Widget "${evt.item.dataset.widgetId}" moved to zone "${evt.to.dataset.krystalZone}"`);
          _saveLayout();
        },
      });

      this._sortables.set(zoneId, sortable);
    }

    /**
     * Dynamically register a new zone (e.g., when a new panel is added).
     * @param {HTMLElement} zoneEl
     */
    registerZone(zoneEl) {
      this._activateZone(zoneEl);
    }

    /**
     * Programmatically move a widget to a target zone.
     * @param {string} widgetId
     * @param {string} targetZoneId
     */
    moveWidget(widgetId, targetZoneId) {
      const widget = document.querySelector(`[data-widget-id="${widgetId}"]`);
      const target = document.querySelector(`[data-krystal-zone="${targetZoneId}"]`);
      if (widget && target) {
        target.appendChild(widget);
        _saveLayout();
      }
    }

    /** Force-save the current layout immediately (bypasses debounce). */
    saveNow() {
      const layout = _serializeLayout();
      localStorage.setItem('krystal_grid_layout', JSON.stringify(layout));
      document.dispatchEvent(new CustomEvent('krystal:grid-saved', { detail: layout }));
    }

    /** Destroy all SortableJS instances. */
    destroy() {
      this._sortables.forEach(s => s.destroy());
      this._sortables.clear();
    }
  }

  // ── Expose as global singleton ─────────────────────────────────────────────
  if (!window.Krystal) window.Krystal = {};
  window.Krystal.grid = new GridManager();

  console.log('[GridManager] 🔷 Fluid Grid Engine loaded — call Krystal.grid.init() to activate.');
})();
