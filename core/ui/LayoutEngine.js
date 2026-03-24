/**
 * KrystalOS — core/ui/LayoutEngine.js
 * Phase 7: The Modular UI Compositor
 * 
 * Intercepts CORE_LAYOUT events to reflow semantical Grid Areas
 * (Taskbar, Desktop, Notifications) natively on the browser.
 */

export class LayoutEngine {
    constructor(rootContainerId = 'krystal-root') {
        this.rootContainer = document.getElementById(rootContainerId);
        if (this.rootContainer) {
            this._setupListeners();
        } else {
            console.warn("[LayoutEngine] Cannot find root #krystal-root container.");
        }
    }

    _setupListeners() {
        // Listen to UiCompositor when a structural layout fires
        window.addEventListener('kos:layout:reflow', (e) => {
            console.info(`[LayoutEngine] Received Hot-Swap Trigger from layer: ${e.detail.layerId}. Reflowing grid areas...`);
            this.forceReflow();
        });
    }

    /**
     * Forces the browser to recalculate the grid by toggling a generic utility class.
     * Since the UiCompositor already injected the new `grid-template-areas` CSS into the head via `<style>`,
     * we just need to smoothly animate or trigger a repaint.
     */
    forceReflow() {
        if (!this.rootContainer) return;
        
        // Simple trick to trigger smooth CSS transitions on grid layout swaps
        this.rootContainer.style.opacity = '0.99';
        
        requestAnimationFrame(() => {
            // Reapply CSS 
            this.rootContainer.style.opacity = '1';
            
            // Dispatch to widgets that might need a canvas resize update
            window.dispatchEvent(new Event('resize'));
            
            console.debug("[LayoutEngine] Layout Reflow Applied. Grid Areas Repositioned.");
        });
    }
}
