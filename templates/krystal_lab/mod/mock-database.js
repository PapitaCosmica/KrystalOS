/**
 * KrystalOS — templates/krystal_lab/mod/mock-database.js
 * In-Memory LocalStorage Database to emulate Zero Data-Loss SQL transactions.
 */

window.KrystalModDB = {
    // Basic table emulation
    _storageKey: 'kos_mock_db',

    _load: function() {
        return JSON.parse(localStorage.getItem(this._storageKey)) || {};
    },

    _save: function(data) {
        localStorage.setItem(this._storageKey, JSON.stringify(data));
        // Simple metric for profiler
        window.KrystalProfilerData = window.KrystalProfilerData || { queries: 0 };
        window.KrystalProfilerData.queries++;
    },

    insert: function(table, record) {
        const db = this._load();
        if (!db[table]) db[table] = [];
        record.id = db[table].length + 1;
        db[table].push(record);
        this._save(db);
        return record;
    },

    select: function(table, filter = null) {
        const db = this._load();
        window.KrystalProfilerData = window.KrystalProfilerData || { queries: 0 };
        window.KrystalProfilerData.queries++; // Simulate READ query load
        if (!db[table]) return [];
        return db[table];
    },
    
    // Developer tool to clear sandbox memory
    nuke: function() {
        localStorage.removeItem(this._storageKey);
        console.info("[KrystalModDB] Sandbox Storage Wiped Clean.");
    }
};

/**
 * Latency & Error Injector Hook
 * Developers can attach this layer in their code to stress test UI boundaries.
 */
window.StressTestInjector = {
    async fetchWithStress(url, options = {}) {
        const delay = document.getElementById('lagSlider') ? parseInt(document.getElementById('lagSlider').value) : 0;
        const throwError = document.getElementById('errorToggle') && document.getElementById('errorToggle').checked;
        
        await new Promise(r => setTimeout(r, delay));
        
        if (throwError) {
            console.error(`[StressTest] Forced 500 Internall Error on ${url}`);
            throw new Error("500 Internal Server Error (Forced by Krystal Lab)");
        }
        
        return window.fetch(url, options); // Native call proxy
    }
}
