/**
 * KrystalOS — templates/krystal_lab/widget/krystal-bridge.js
 * Sandbox Simulator for Krystal Event Bus.
 * Captures emit/on and prints them to the visual console UI.
 */

window.Krystal = {
    _listeners: {},
    
    emit: function(eventName, payload) {
        const consoleEl = document.getElementById('labConsole');
        if (consoleEl) {
            const entry = document.createElement('div');
            entry.className = 'log-emit';
            entry.innerHTML = `<strong>[EMIT]</strong> ${eventName} <br><span style="color:#888">${JSON.stringify(payload)}</span>`;
            consoleEl.prepend(entry);
        }
        
        console.log(`[Krystal Lab] Emitted: ${eventName}`, payload);
        
        if (this._listeners[eventName]) {
            this._listeners[eventName].forEach(cb => cb(payload));
        }
    },
    
    on: function(eventName, callback) {
        const consoleEl = document.getElementById('labConsole');
        if (consoleEl) {
            const entry = document.createElement('div');
            entry.className = 'log-on';
            entry.innerHTML = `<strong>[ON]</strong> Listening to: ${eventName}`;
            consoleEl.prepend(entry);
        }
        
        if (!this._listeners[eventName]) {
            this._listeners[eventName] = [];
        }
        this._listeners[eventName].push(callback);
        console.log(`[Krystal Lab] Subscribed to: ${eventName}`);
    }
};

// Also inject into the iframe if it exists so the widget can use window.parent.Krystal
window.addEventListener('load', () => {
    const frame = document.getElementById('widgetFrame');
    if (frame && frame.contentWindow) {
        frame.contentWindow.Krystal = window.Krystal;
    }
});
