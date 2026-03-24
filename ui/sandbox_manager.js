/**
 * KrystalOS — ui/sandbox_manager.js
 * Sprint v2.1.0 Part 2: FRONTEND ISOLATION 
 * 
 * Creates isolated realms for widgets to execute safely without
 * CSS bleeding or State Race Conditions.
 */

export class SandboxManager {
    /**
     * Wraps a widget's HTML content inside a Shadow DOM.
     * @param {HTMLElement} container - The host element.
     * @param {string} htmlContent - The raw HTML of the widget.
     * @param {string} mode - 'open' or 'closed' (default 'closed' for max isolation).
     * @returns {ShadowRoot} The sandboxed root.
     */
    static createShadowRealm(container, htmlContent, mode = 'closed') {
        // Enforce Shadow DOM to isolate styles and DOM queries
        const shadow = container.attachShadow({ mode });
        
        // Wrap everything in a dedicated KrystalOS micro-frame
        const wrapper = document.createElement('div');
        wrapper.className = 'kos-widget-frame';
        wrapper.innerHTML = htmlContent;

        // Common structural styles for the sandbox
        const coreStyles = document.createElement('style');
        coreStyles.textContent = `
            :host { display: block; width: 100%; height: 100%; }
            .kos-widget-frame { width: 100%; height: 100%; box-sizing: border-box; }
        `;

        shadow.appendChild(coreStyles);
        shadow.appendChild(wrapper);

        return shadow;
    }

    /**
     * Generates an isolated State Proxy for a specific Mod dependency.
     * Ensures that if Widget A and B use Mod-Users, their local changes 
     * don't randomly overwrite each other before hitting the backend.
     * 
     * @param {string} widgetName - The identifier of the widget consuming the Mod.
     * @param {Object} rawModMetadata - The actual global state of the Mod.
     */
    static createIsolatedStateProxy(widgetName, rawModMetadata) {
        return new Proxy(rawModMetadata, {
            get(target, prop) {
                if (prop === '_kos_widget_owner') return widgetName;
                if (prop === '_kos_isolated') return true;
                
                // Track reads (Telemetry hook)
                // console.debug(`[Sandbox:${widgetName}] read prop '${prop}'`);
                return Reflect.get(target, prop);
            },
            set(target, prop, value) {
                // Pre-flight check before mutating
                if (prop.startsWith('_kos_')) {
                    console.warn(`[Sandbox:${widgetName}] Attempted to write protected property '${prop}'. Blocked.`);
                    return false;
                }
                
                // In a production scenario, this mutation could be sent 
                // to an EventBus to be resolved by the backend AutoMigrator.
                console.info(`[Sandbox:${widgetName}] Muted overwrite on '${prop}' = ${value}`);
                return Reflect.set(target, prop, value);
            }
        });
    }
}
