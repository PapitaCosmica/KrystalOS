/**
 * KrystalOS — shared/krystal-mock.js
 * Sprint v2.0.0-alpha: The Factory
 * 
 * A Mock Simulation Bridge for local widget development.
 * Allows developers to test their widgets in standalone environments
 * (like XAMPP, LiveServer) by simulating KrystalOS core functionalities
 * without needing the Orchestrator gateway running.
 */

window.Krystal = {
    /**
     * Simulates sending an event to the global Event Bus.
     */
    emit: function(event, data = {}) {
        console.info(`[Krystal-Mock] 🛰️ Evento emitido: '${event}'`, data);
    },

    /**
     * Simulates subscribing to an event from the global Event Bus.
     * In the mock environment, you can trigger this callback manually 
     * by typing Krystal._triggerMock('event', { ... }) in your DevTools console.
     */
    on: function(event, callback) {
        if (!this._listeners) this._listeners = {};
        if (!this._listeners[event]) this._listeners[event] = [];
        this._listeners[event].push(callback);
        console.log(`[Krystal-Mock] 👂 Suscrito al evento: '${event}'`);
    },

    /**
     * Developer Helper to test subscriptions via browser console.
     */
    _triggerMock: function(event, payload) {
        if (this._listeners && this._listeners[event]) {
            console.log(`[Krystal-Mock] ⚡ Simulating incoming event: '${event}'`);
            this._listeners[event].forEach(cb => cb(payload));
        } else {
            console.warn(`[Krystal-Mock] No hay nadie suscrito al evento: '${event}'`);
        }
    },

    /**
     * LocalStorage-bound key-value database for standalone development persistence.
     * Simulates the core SQLModel database.
     */
    DB: {
        save: async function(key, value) {
            localStorage.setItem(`krystal_mock_db_${key}`, JSON.stringify(value));
            console.info(`[Krystal-Mock DB] 💾 Guardado '${key}'`, value);
            return true;
        },
        get: async function(key) {
            const val = localStorage.getItem(`krystal_mock_db_${key}`);
            const parsed = val ? JSON.parse(val) : null;
            console.info(`[Krystal-Mock DB] 📂 Leído '${key}':`, parsed);
            return parsed;
        },
        delete: async function(key) {
            localStorage.removeItem(`krystal_mock_db_${key}`);
            console.info(`[Krystal-Mock DB] 🗑️ Borrado '${key}'`);
            return true;
        }
    }
};

console.log("[Krystal-Mock] 🔷 KrystalOS Development Bridge Activado. Listo para LiveServer.");
