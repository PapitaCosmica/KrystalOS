/**
 * KrystalOS — core/theming/UiCompositor.js
 * Phase 7: The Modular UI Compositor
 * 
 * Orchestrates rendering multiple theme layers (Layouts, Skins, Colors)
 * via dynamic CSS Cascade injection depending on priority_level.
 */

export class KrystalUiCompositor {
    constructor() {
        // Active themes sorted by priority_level
        this.activeLayers = [];
        
        // Allowed Enum Types for safe CSS Injection Layering
        this.LAYER_TYPES = [
            'CORE_LAYOUT',
            'WIDGET_SKIN',
            'COLOR_PALETTE',
            'ANIMATION_PACK',
            'SYSTEM_ASSETS',
            'FULL_OVERHAUL'
        ];
    }

    /**
     * Registers and activates a new theme layer.
     * @param {Object} compositeManifest - The parsed `composite.json`.
     * @param {string} cssContent - The raw CSS styles of the layer.
     */
    activateLayer(compositeManifest, cssContent) {
        if (!this.LAYER_TYPES.includes(compositeManifest.theme_type)) {
            console.warn(`[UiCompositor] Invalid theme_type: ${compositeManifest.theme_type}`);
            return;
        }

        const layer = {
            id: compositeManifest.name.replace(/\s+/g, '-').toLowerCase(),
            type: compositeManifest.theme_type,
            priority: compositeManifest.priority_level || 10,
            definesStructure: compositeManifest.defines_structure || false,
            css: this._prefixSelectors(cssContent, compositeManifest.theme_type)
        };

        // Remove previous layer of exactly same type if priority is same/lower?
        // For now, we just stack them, but we sort by priority so the highest wins CSS cascada.
        this.activeLayers = this.activeLayers.filter(l => l.id !== layer.id);
        this.activeLayers.push(layer);
        
        // Sort Ascending (Higher priority index comes last in DOM so it overrides)
        this.activeLayers.sort((a, b) => a.priority - b.priority);

        this._renderCascade();

        // If it's a structural layout change, we trigger a reflow
        if (layer.definesStructure) {
            window.dispatchEvent(new CustomEvent('kos:layout:reflow', { detail: { layerId: layer.id } }));
        }
    }

    /**
     * Dumps the ordered layers into the document head using distinct <style> tags.
     */
    _renderCascade() {
        // Clear all composited layers
        document.querySelectorAll('style[id^="krystal-layer-"]').forEach(el => el.remove());

        // Append in priority order
        for (const layer of this.activeLayers) {
            const style = document.createElement('style');
            style.id = `krystal-layer-${layer.type}-${layer.id}`;
            style.textContent = `/* Priority: ${layer.priority} | Type: ${layer.type} */\n${layer.css}`;
            document.head.appendChild(style);
        }
        
        console.info(`[UiCompositor] Cascade Re-rendered. Active Layers: ${this.activeLayers.length}`);
    }

    /**
     * Automatically sandbox standard CSS.
     * Tokens/Colors are kept at :root, but Skins and Layouts are prefixed to `#krystal-root`
     * to prevent bleeding outside of KrystalOS to the host page.
     */
    _prefixSelectors(css, themeType) {
        if (themeType === 'COLOR_PALETTE' || themeType === 'SYSTEM_ASSETS') {
            // Colors and variables usually live in :root {}
            return css;
        }
        
        // Basic Regex logic to prefix non-token layers. Extremely simple approach 
        // to enforcing #krystal-root isolation globally!
        // In production, an AST CSS parser is better.
        return css.replace(/(^|})([^{]+){/g, (match, prefix, selectors) => {
            const safeSelectors = selectors
                .split(',')
                .map(s => {
                    const trimmed = s.trim();
                    if (trimmed.startsWith('@') || trimmed.startsWith(':root')) return trimmed;
                    if (trimmed === '') return '';
                    return `#krystal-root ${trimmed}`;
                })
                .join(', ');
            return `${prefix} ${safeSelectors} {`;
        });
    }
}

// Global Singleton
window.KrystalThemes = new KrystalUiCompositor();
