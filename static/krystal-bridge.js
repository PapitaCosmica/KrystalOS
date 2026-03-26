/**
 * KrystalOS — static/krystal-bridge.js
 * Phase 3: The Nervous System
 * 
 * Provides a universal `window.Krystal` object for widgets to communicate
 * seamlessly via WebSockets, completely language-agnostic.
 */

class KrystalBridge {
    constructor(widgetName) {
        this.widgetName = widgetName;
        this.socket = null;
        this.listeners = {}; // eventName -> array of callbacks
        this.reconnectAttempts = 0;
        // Default system theme subscriptions
        this.on('THEME_CHANGED', (themeDict) => this._applyThemeVariables(themeDict));
    }

    _applyThemeVariables(themeDict) {
        // Apply CSS variables to the host document so they pierce through Shadow DOM
        const root = document.documentElement;
        for (const [key, value] of Object.entries(themeDict)) {
            root.style.setProperty(`--${key}`, value);
        }
        console.log(`[KrystalOS] 🎨 Theme applied via EventBus.`);
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        this.socket = new WebSocket(`${protocol}//${host}/ws/events/${this.widgetName}`);

        this.socket.onopen = () => {
            console.log(`[KrystalOS] 🔷 Widget '${this.widgetName}' connected to the Core Event Bus.`);
            this.reconnectAttempts = 0;
        };

        this.socket.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this._dispatch(msg.event, msg.data, msg.sender);
            } catch (err) {
                console.error("[KrystalOS] Failed to parse incoming event:", err);
            }
        };

        this.socket.onclose = () => {
            console.warn(`[KrystalOS] Connection lost for '${this.widgetName}'. Reconnecting in 3s...`);
            setTimeout(() => this.connect(), 3000);
        };
    }

    /**
     * Subscribe to a KrystalOS event.
     * @param {string} eventName - The event to listen for.
     * @param {function} callback - Function receiving (data, sender).
     */
    on(eventName, callback) {
        if (!this.listeners[eventName]) {
            this.listeners[eventName] = [];
        }
        this.listeners[eventName].push(callback);
    }

    /**
     * Broadcast an event to all subscribed widgets.
     * @param {string} eventName - The event to trigger.
     * @param {object} data - Payload data to send.
     */
    emit(eventName, data = {}) {
        if (this.socket && this.socket.readyState === window.WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                sender: this.widgetName,
                event: eventName,
                data: data
            }));
        } else {
            console.error(`[KrystalOS] Cannot emit '${eventName}'. WebSocket is offline.`);
        }
    }

    // Internal dispatcher
    _dispatch(eventName, data, sender) {
        const callbacks = this.listeners[eventName] || [];
        // Support wildcard fallback listeners
        const wildcard = this.listeners['*'] || [];
        
        [...callbacks, ...wildcard].forEach(cb => {
            try {
                cb(data, sender);
            } catch (err) {
                console.error(`[KrystalOS] Error in listener for '${eventName}':`, err);
            }
        });
    }
}

// Attach globally so widgets injected via Shadow DOM can access it.
window.KrystalInitBridge = (widgetName) => {
    return new KrystalBridge(widgetName);
};

/**
 * Krystal — Public API Namespace (v2.2.6.5)
 * Exposes helpers to widget developers for safe path resolution and bridge init.
 */
window.Krystal = {
    /**
     * Resolve a relative widget asset path to a safe absolute URL served by KrystalOS.
     * Use this to instantiate Web Workers or load assets without 404 errors.
     *
     * @param {string} widgetName - The widget's folder name (e.g. 'criptostreamer')
     * @param {string} relativePath - The path relative to the widget root (e.g. 'logic/worker.js')
     * @returns {string} Full URL safe to use in `new Worker(...)`, `fetch(...)`, etc.
     *
     * @example
     *   const worker = new Worker(Krystal.resolvePath('criptostreamer', 'logic/worker.js'));
     */
    resolvePath(widgetName, relativePath) {
        return `/widgets/${widgetName}/${relativePath}`;
    },

    /**
     * Convenience wrapper: create a KrystalBridge for a given widget and auto-connect.
     * @param {string} widgetName
     * @returns {KrystalBridge}
     */
    initBridge(widgetName) {
        const bridge = new KrystalBridge(widgetName);
        bridge.connect();
        return bridge;
    },
};
