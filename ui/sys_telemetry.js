/**
 * KrystalOS — ui/sys_telemetry.js
 * Sprint v2.1.0 Part 2: SYS-UI
 * 
 * Unobtrusive System Toasts and Error Boundaries specifically 
 * engineered for Backend Migration hookbacks.
 */

export class SysTelemetry {
    constructor() {
        this.container = this._ensureContainer();
    }

    /**
     * Creates the toast container overlay for KrystalOS.
     */
    _ensureContainer() {
        let container = document.getElementById('kos-sys-telemetry-root');
        if (!container) {
            container = document.createElement('div');
            container.id = 'kos-sys-telemetry-root';
            // Smooth Glassmorphism corner for system toasts
            container.style.cssText = `
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Shows a non-intrusive Glassmorphism toast when backend emits an event.
     * i.e., "\[KrystalOS-Migrator] Optimizando esquema para ModX..."
     */
    showToast(message, type = 'info', durationMs = 4000) {
        const toast = document.createElement('div');
        
        let bgColor = 'rgba(30, 41, 59, 0.85)'; // Default slate
        let icon = '⚡';
        
        if (type === 'success') {
            bgColor = 'rgba(16, 185, 129, 0.85)'; // Emerald
            icon = '✅';
        } else if (type === 'warning') {
            bgColor = 'rgba(245, 158, 11, 0.85)'; // Amber
            icon = '⚠️';
        } else if (type === 'error') {
            bgColor = 'rgba(239, 68, 68, 0.85)'; // Red
            icon = '💥';
            durationMs = 8000; // Errors stay longer
        }

        toast.style.cssText = `
            background: ${bgColor};
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            padding: 14px 20px;
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 10px;
            transform: translateX(120%);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28);
        `;

        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        this.container.appendChild(toast);

        // Animate In
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });

        // Auto remove
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400); // Wait for transition
        }, durationMs);
    }

    /**
     * Error Boundary: HIJACKS a widget container when a fatal backend Rollback happens,
     * replacing it with a safe Fallback UI to prevent the entire dashboard from freezing.
     */
    renderFallbackBoundary(containerElement, widgetName, errorMessage) {
        // Clear whatever corrupted rendering the widget had
        containerElement.innerHTML = '';
        
        const fallback = document.createElement('div');
        fallback.style.cssText = `
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: rgba(255,0,0,0.05);
            border: 1px dashed rgba(239, 68, 68, 0.5);
            border-radius: 16px;
            padding: 20px;
            color: #fca5a5;
            text-align: center;
            font-family: 'Inter', sans-serif;
            box-sizing: border-box;
        `;

        fallback.innerHTML = `
            <div style="font-size: 32px; margin-bottom: 12px;">⚠️</div>
            <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #ef4444;">Widget Crashed</h3>
            <p style="margin: 0; font-size: 12px; opacity: 0.8;">[${widgetName}]</p>
            <p style="margin: 12px 0 0 0; font-size: 11px; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; max-width: 100%; overflow: hidden; text-overflow: ellipsis;">
                ${errorMessage}
            </p>
        `;

        containerElement.appendChild(fallback);
        this.showToast(`El widget '${widgetName}' fue detenido por seguridad.`, 'error');
    }
}

// Global Singleton
window.KrystalSysUI = new SysTelemetry();
