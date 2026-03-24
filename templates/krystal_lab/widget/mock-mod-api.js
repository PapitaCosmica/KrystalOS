/**
 * KrystalOS — templates/krystal_lab/widget/mock-mod-api.js
 * Simulates Mod endpoints via fetch interception or direct window.MockAPI objects.
 * Allows devs to hardcode JSON responses.
 */

window.MockModAPI = {
    // Example: GET /api/mods/MOD-USERS/list
    "MOD-USERS": {
        "list": () => {
            return Promise.resolve([
                { id: 1, name: "PapitaCosmica", role: "admin" },
                { id: 2, name: "KrystalBot", role: "system" }
            ]);
        }
    }
};

// We intercept global fetch to simulate calls to Krystal Gateway
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    
    // Intercept Mod API requests
    if (typeof resource === 'string' && resource.startsWith('/api/mods/')) {
        const parts = resource.split('/'); // ['', 'api', 'mods', 'MOD-USERS', 'list']
        if (parts.length >= 5) {
            const modName = parts[3];
            const modAction = parts[4];
            
            if (window.MockModAPI[modName] && window.MockModAPI[modName][modAction]) {
                const consoleEl = document.getElementById('labConsole');
                if (consoleEl) {
                    const entry = document.createElement('div');
                    entry.style.color = '#fde047'; // Yellow
                    entry.innerHTML = `<strong>[FETCH MOCK]</strong> ${modName}/${modAction}`;
                    consoleEl.prepend(entry);
                }
                
                const data = await window.MockModAPI[modName][modAction]();
                return new Response(JSON.stringify(data), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        }
        
        // If not found in mock, return 404
        return new Response(JSON.stringify({ error: "Mod endpoint not mocked in Lab" }), { status: 404 });
    }
    
    // Pass through normally
    return originalFetch.apply(this, arguments);
};
