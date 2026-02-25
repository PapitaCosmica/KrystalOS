function demoAction() {
  console.log("Demo widget action triggered");
  alert("¡Widget funcionando perfectamente en la arquitectura KrystalOS!");
}

// Listen for KrystalOS Dynamic Context Actions via IPC
window.addEventListener('message', (event) => {
    // Only process valid krystal intents
    if (event.data && event.data.krystalIntent === 'widgetAction') {
        const action = event.data.action;
        
        switch(action) {
            case 'refreshWidget':
                // Visually flash to show refresh
                document.body.style.opacity = '0.5';
                setTimeout(() => {
                    document.body.style.opacity = '1';
                    if(window.parent && window.parent.krystalOS) {
                        window.parent.krystalOS.showNotification('Demo', 'Estado refrescado con éxito', 'success');
                    }
                }, 300);
                break;
                
            case 'hideAlert':
                if(window.parent && window.parent.krystalOS) {
                    window.parent.krystalOS.showNotification('Demo', 'Acción: Ocultando alertas', 'info');
                }
                break;
                
            default:
                console.warn("Acción no implementada:", action);
        }
    }
});
