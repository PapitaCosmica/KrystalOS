/**
 * KrystalOS — core/frontend/mod_injector.js
 * Sprint v2.1.0 Part 2: FRONTEND MOD INJECTOR
 * 
 * Lazy-loads required Mods (CSS/JS) tightly bound to Widget lifecycles,
 * preventing Network Spikes via Caching and avoiding Memory Leaks via
 * rigorous Garbage Collection.
 */

class ModInjectorSingleton {
    constructor() {
        // Cache to store injected node references
        // Format: { 'MOD-NAME': { scripts: [], styles: [], count: 0 } }
        this._injectedMods = {};
    }

    /**
     * Called by the Client Orchestrator when a Widget loads.
     * Evaluates its `needs` array and injects the requested Mod scopes.
     * @param {string} widgetId - Unique instance ID.
     * @param {string[]} needs - e.g. ["MOD-USERS", "MOD-AI"]
     */
    async evaluateAndInject(widgetId, needs = []) {
        if (!needs || needs.length === 0) return;

        console.info(`[ModInjector] Evaluando inyección dinámica para [${widgetId}]`);

        for (const modName of needs) {
            if (!this._injectedMods[modName]) {
                this._injectedMods[modName] = { scripts: [], styles: [], count: 0 };
            }

            // Only inject into DOM if it's the first active consumer
            if (this._injectedMods[modName].count === 0) {
                window.KrystalSysUI?.showToast(`Descargando dependencias: ${modName}`, 'info', 2000);
                await this._injectToDOM(modName);
            } else {
                console.debug(`[ModInjector] Cache Hit para '${modName}'. Evitando peticiones redundantes.`);
            }

            // Increment consumer reference count
            this._injectedMods[modName].count++;
        }
    }

    /**
     * Simulates fetching mod data from the KrystalOS backend.
     * Injects the required JS and CSS into the head.
     */
    async _injectToDOM(modName) {
        return new Promise((resolve) => {
            // Emulate backend fetch payload parsing
            const scriptUrl = `/api/mods/${modName}/mod.js`;
            const styleUrl = `/api/mods/${modName}/style.css`;

            // 1. Inject Styles
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = styleUrl;
            link.id = `style-${modName}`;
            document.head.appendChild(link);
            this._injectedMods[modName].styles.push(link);

            // 2. Inject Script
            const script = document.createElement('script');
            script.src = scriptUrl;
            script.type = 'module';
            script.id = `script-${modName}`;
            script.onload = () => {
                console.info(`[ModInjector] Dependencias de '${modName}' activadas y listas.`);
                resolve();
            };
            script.onerror = () => {
                console.warn(`[ModInjector] Fallo cargando dependencias de '${modName}'.`);
                // SysTelemetry Fallback Hook could be triggered here
                resolve(); // resolve anyway to not block execution
            };
            document.head.appendChild(script);
            this._injectedMods[modName].scripts.push(script);
        });
    }

    /**
     * Garbage Collection.
     * Decrements the consumer tracking. If 0 widgets are using the Mod,
     * it physically ejects the DOM nodes to release RAM.
     * @param {string[]} needs - The same array passed on inject.
     */
    cleanup(needs = []) {
        if (!needs || needs.length === 0) return;

        for (const modName of needs) {
            if (this._injectedMods[modName]) {
                this._injectedMods[modName].count--;

                if (this._injectedMods[modName].count <= 0) {
                    console.info(`[ModInjector] Liberando RAM: Borrando dependencias de '${modName}'`);

                    // Remove scripts
                    this._injectedMods[modName].scripts.forEach(s => s.remove());
                    this._injectedMods[modName].scripts = [];

                    // Remove styles
                    this._injectedMods[modName].styles.forEach(l => l.remove());
                    this._injectedMods[modName].styles = [];

                    this._injectedMods[modName].count = 0;
                    
                    window.KrystalSysUI?.showToast(`[GC] Memoria liberada de ${modName}`, 'success', 2000);
                }
            }
        }
    }
}

export const ModInjector = new ModInjectorSingleton();
