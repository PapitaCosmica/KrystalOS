/**
 * KrystalOS — templates/krystal_lab/shared/profiler.js
 * Injected Performance Monitor. Validates architecture metrics on the fly.
 */

(function() {
    // 1. Inject Profiler UI Element
    const pBox = document.createElement('div');
    pBox.id = "kos-profiler";
    pBox.style.cssText = `
        position: fixed; bottom: 10px; right: 10px; background: rgba(0,0,0,0.85); 
        color: #0f0; font-family: monospace; font-size: 11px; padding: 10px; 
        border-radius: 8px; z-index: 999999; border: 1px solid #333; pointer-events: none; width: 220px;
    `;
    document.body.appendChild(pBox);

    let lastQueryCount = 0;
    let querySpikeTracker = 0;

    function renderMetrics() {
        const data = window.KrystalProfilerData || { queries: 0, latestCSS: '' };
        
        let warnings = [];

        // Metric 1: Widget DOM Size (Heuristics)
        const domNodes = document.getElementsByTagName('*').length;
        if (domNodes > 1500) {
            warnings.push(`<span style="color:#ef4444">DOM OVERLOAD: ${domNodes} nodes</span>`);
        } else {
            warnings.push(`DOM: ${domNodes} nodes ✅`);
        }

        // Metric 2: Memory Leaks tracking Krystal Event Bus
        if (window.Krystal && window.Krystal._listeners) {
            let totalListeners = 0;
            for (let e in window.Krystal._listeners) {
                totalListeners += window.Krystal._listeners[e].length;
            }
            if (totalListeners > 50) {
                 warnings.push(`<span style="color:#ef4444">MEMORY LEAK: ${totalListeners} listeners!</span>`);
            } else {
                 warnings.push(`Listeners: ${totalListeners} ✅`);
            }
        }

        // Metric 3: N+1 Mod Queries
        if (data.queries > lastQueryCount) {
            querySpikeTracker += (data.queries - lastQueryCount);
            lastQueryCount = data.queries;
        } else {
            // Decay tracker slowly to detect 100 queries in 1 second
            querySpikeTracker = Math.max(0, querySpikeTracker - 1); 
        }
        
        if (querySpikeTracker > 50) {
            warnings.push(`<span style="color:#ef4444">DB N+1 QUERY LOOP DETECTED</span>`);
        } else {
            warnings.push(`DB Queries: ${data.queries} ✅`);
        }

        // Metric 4: Theme CSS Global wildcard
        window.analyzeTheme = function() {
            if (!data.latestCSS) return;
            const hasGlobal = /\*\s*\{/.test(data.latestCSS);
            if (hasGlobal) {
                console.error("[Krystal Profiler] Global wildcard selector `* {` detected. This breaks Krystal isolation.");
                warnings.push(`<span style="color:#ef4444">CSS BLOCK: Bad '*' selector</span>`);
            }
        };
        // Auto-run if AST analysis exists
        if (data.latestCSS && /\*\s*\{/.test(data.latestCSS)) {
             warnings.push(`<span style="color:#ef4444">CSS BLOCK: Bad '*' selector</span>`);
        }

        pBox.innerHTML = `<strong>KRYSTAL PERF MONITOR</strong><br><hr style="border:0;border-top:1px dashed #333;margin:4px 0;">` + warnings.join('<br>');
    }

    setInterval(renderMetrics, 500);
})();
