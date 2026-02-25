/**
 * krystal-core.js
 * Core engine for GridStack initialization, Autodiscovery loading, and A11y.
 */

// --- Alpine.js Store for Accessibility ---
document.addEventListener('alpine:init', () => {
    Alpine.data('accessibilityStore', () => ({
        isDarkMode: localStorage.getItem('krystal_theme_dark') === 'true',
        prefersReducedMotion: localStorage.getItem('krystal_a11y_motion') === 'true',
        currentTheme: localStorage.getItem('krystal_theme_name') || 'pastel-blue',
        
        initStore() {
            // Respect OS settings if not overridden
            if (localStorage.getItem('krystal_a11y_motion') === null) {
                const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
                this.prefersReducedMotion = motionQuery.matches;
            }
            if (localStorage.getItem('krystal_theme_dark') === null) {
                const themeQuery = window.matchMedia('(prefers-color-scheme: dark)');
                this.isDarkMode = themeQuery.matches;
            }
            this.applyTheme(this.currentTheme);
        },

        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode;
            localStorage.setItem('krystal_theme_dark', this.isDarkMode);
            if(window.krystalOS) window.krystalOS.syncAllIframes();
        },
        toggleReducedMotion() {
            this.prefersReducedMotion = !this.prefersReducedMotion;
            localStorage.setItem('krystal_a11y_motion', this.prefersReducedMotion);
        },
        setTheme(themeName) {
            this.currentTheme = themeName;
            localStorage.setItem('krystal_theme_name', themeName);
            this.applyTheme(themeName);
        },
        applyTheme(themeName) {
            // Set data attribute on html for CSS specific overrides
            document.documentElement.setAttribute('data-theme', themeName);
            // Update the stylesheet dynamically
            const themeLink = document.getElementById('theme-stylesheet');
            if (themeLink) {
                themeLink.href = `/public/css/themes/${themeName}.css`;
            }
            if(window.krystalOS) window.krystalOS.syncAllIframes();
        }
    }));

    Alpine.data('authStore', () => ({
        authState: 'loading', // 'loading', 'setup', 'login', 'authenticated'
        username: '',
        password: '',
        setupName: '',
        setupEmail: '',
        setupPassword: '',
        setupRole: 'admin',
        
        async checkStatus() {
            try {
                console.log("[Auth] Checking setup status...");
                // Fetch from the real backend endpoint
                const res = await fetch('/api/auth/setup-status');
                const data = await res.json();
                
                const hasUsers = data.has_users;
                const hasToken = localStorage.getItem('krystal_token') !== null;

                if (!hasUsers) {
                    this.authState = 'setup';
                } else if (!hasToken) {
                    this.authState = 'login';
                } else {
                    this.authState = 'authenticated';
                    window.dispatchEvent(new CustomEvent('krystal-authenticated'));
                }
            } catch (error) {
                console.error("Auth check failed:", error);
                // Si la red falla o estamos en el puerto equivocado (8080), mostrar aviso
                if (window.location.port !== "8000") {
                    this.authState = 'loading';
                    document.querySelector('.auth-loader p').innerText = "⚠️ Error: Por favor entra desde http://localhost:8000";
                } else {
                    this.authState = 'setup'; // Fallback to setup by default
                }
            }
        },

        async doSetup() {
            if (!this.setupName || !this.setupEmail || !this.setupPassword) {
                window.krystalOS?.showNotification("Error", "Todos los campos obligatorios.", "error");
                return;
            }
            
            try {
                const res = await fetch('/api/auth/register-admin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.setupName,
                        email: this.setupEmail,
                        password: this.setupPassword
                    })
                });
                
                if (!res.ok) throw new Error("Fallo en el registro");
                const data = await res.json();
                
                localStorage.setItem('krystal_token', data.token);
                // Also cache the boolean so we don't have to wait for network visually
                localStorage.setItem('krystal_has_users', 'true'); 
                
                this.authState = 'authenticated';
                window.krystalOS?.showNotification("Setup Completo", `Bienvenido administrador ${this.setupName}`, "success");
                window.dispatchEvent(new CustomEvent('krystal-authenticated'));
            } catch (e) {
                window.krystalOS?.showNotification("Error", "El sistema ya está inicializado o hubo un error.", "error");
            }
        },

        async doLogin() {
            if (!this.username || !this.password) {
                window.krystalOS?.showNotification("Error", "Ingresa usuario y contraseña.", "warning");
                return;
            }
            
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: this.username,
                        password: this.password
                    })
                });
                
                if (!res.ok) throw new Error("Credenciales inválidas");
                const data = await res.json();
                
                localStorage.setItem('krystal_token', data.token);
                
                this.authState = 'authenticated';
                window.krystalOS?.showNotification("Sesión Iniciada", `Bienvenido de vuelta, ${this.username}`, "info");
                window.dispatchEvent(new CustomEvent('krystal-authenticated'));
            } catch (e) {
                window.krystalOS?.showNotification("Error", "Credenciales incorrectas.", "error");
            }
        }
    }));
});

// --- KrystalOS Core Logic ---
class KrystalEngine {
    constructor() {
        this.grid = null;
        this.widgets = [];
        this.contextMenu = null;
        this.isEditing = false;
        this.activeWidgetContent = null;
        this.activeWidgetName = null;
        this.widgetConfigs = {};
    }

    async init() {
        if (this.grid) return; // Prevent double initialization

        try {
            const res = await fetch('/api/widgets/configs');
            this.widgetConfigs = await res.json();
            console.log("[Krystal] Loaded Widget Configs:", this.widgetConfigs);
        } catch(e) {
            console.error("[Krystal] Failed to load widget configs", e);
        }

        // Initialize GridStack securely as Static by default
        this.grid = GridStack.init({
            column: 12,
            cellHeight: 120,
            margin: 16,
            staticGrid: true, // Prevents dragging and resizing globally by default
            float: true, // Allow widgets to be dragged anywhere
            draggable: { handle: '.krystal-drag-handle' },
            resizable: { handles: 'e, se, s, sw, w' }
        });

        // Setup Context Menu Listener
        this.setupContextMenu();

        // Load Widgets from Backend
        this.loadWidgets();
        
        // Setup "Finish Edit" button
        document.getElementById('btn-finish-edit').addEventListener('click', () => {
            this.toggleEditMode(false);
        });

        // Listen for iframe loads to inject themes
        document.getElementById('krystal-bento-grid').addEventListener('load', (e) => {
            if (e.target.tagName === 'IFRAME') {
                const isDark = document.body.classList.contains('dark-mode');
                const themeUrl = document.getElementById('theme-stylesheet')?.href;
                this.applyThemeToIframe(e.target, isDark, themeUrl);
            }
        }, true);
    }

    setupContextMenu() {
        this.contextMenu = document.getElementById('krystal-context-menu');
        
        document.addEventListener('contextmenu', (e) => {
            // Check if clicked inside a widget or the main canvas
            const widgetContent = e.target.closest('.grid-stack-item-content');
            const mainCanvas = e.target.closest('.krystal-main');
            
            if (widgetContent || mainCanvas) {
                e.preventDefault();
                this.activeWidgetContent = widgetContent; // Store it if they want to edit specific widget
                
                // Try to determine the widget name if clicking on the wrapper
                let widgetName = null;
                if (widgetContent) {
                    const iframe = widgetContent.querySelector('iframe');
                    if (iframe) widgetName = iframe.getAttribute('data-widget-name');
                }
                
                this.showContextMenu(e.pageX, e.pageY, widgetContent, widgetName);
            }
        });

        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
        
        // Context Menu Action: Edit Widgets
        document.getElementById('ctx-edit-widgets').addEventListener('click', (e) => {
            e.stopPropagation(); // prevent immediate closing
            this.toggleEditMode(true);
            this.hideContextMenu();
        });
        
        // Context Menu Action: Show Themes
        document.getElementById('ctx-themes').addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('krystal-themes-submenu').classList.toggle('hidden');
        });
        
        // Context Menu Action: Show Accessibility
        document.getElementById('ctx-a11y').addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('krystal-a11y-submenu').classList.toggle('hidden');
        });
    }

    toggleEditMode(enable) {
        this.isEditing = enable;
        this.grid.setStatic(!enable); // GridStack toggle: static true means cannot move/resize
        
        const finishBtn = document.getElementById('btn-finish-edit');
        const handles = document.querySelectorAll('.krystal-drag-handle');
        
        if (enable) {
            finishBtn.classList.remove('hidden');
            handles.forEach(h => h.style.display = 'flex');
            document.body.classList.add('is-editing');
            this.showNotification("Modo Edición Activado", "Puedes mover y redimensionar los widgets libremente.", "info");
        } else {
            finishBtn.classList.add('hidden');
            handles.forEach(h => h.style.display = 'none');
            document.body.classList.remove('is-editing');
            this.showNotification("Modo Edición Finalizado", "Los widgets han sido fijados.", "success");
        }
    }

    showNotification(title, message, type = 'info', actionableLog = false) {
        const container = document.getElementById('krystal-toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `krystal-toast toast-${type}`;
        
        // Define Icon based on type
        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'warning') icon = '⚠️';
        if (type === 'error') icon = '❌';

        let actionHtml = '';
        if (actionableLog) {
            actionHtml = `<button class="toast-action-btn" onclick="console.log('Opening System Log...')">Ver Logs del Sistema</button>`;
        }

        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <strong>${title}</strong>
                <p>${message}</p>
                ${actionHtml}
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('toast-exit');
                setTimeout(() => toast.remove(), 300); // Wait for exit animation
            }
        }, 5000);
    }

    showContextMenu(x, y, widgetElement, widgetName = null) {
        this.activeWidgetName = widgetName;
        
        // Clean up previous dynamic items
        const menuUl = this.contextMenu.querySelector('ul');
        menuUl.querySelectorAll('.dynamic-widget-action').forEach(el => el.remove());
        
        // Inject dynamic items if the widget has a context_menu config
        if (widgetName && this.widgetConfigs[widgetName]) {
            const config = this.widgetConfigs[widgetName];
            if (config.context_menu && Array.isArray(config.context_menu)) {
                // Prepend actions in reverse order so they appear at top
                [...config.context_menu].reverse().forEach(actionObj => {
                    const li = document.createElement('li');
                    li.role = "menuitem";
                    li.tabIndex = "0";
                    li.className = "dynamic-widget-action";
                    // Very subtle visual distinction for widget actions vs OS actions
                    li.style.borderLeft = "3px solid var(--focus-ring-color)";
                    
                    const icon = actionObj.icon ? `<span style="margin-right: 6px;">${actionObj.icon}</span>` : '';
                    li.innerHTML = `${icon}${actionObj.label}`;
                    
                    li.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.executeWidgetAction(widgetName, actionObj.action);
                        this.hideContextMenu();
                    });
                    
                    menuUl.insertBefore(li, menuUl.firstChild);
                });
                
                // Add a divider if we added items
                if (config.context_menu.length > 0) {
                    const divider = document.createElement('div');
                    divider.className = "dynamic-widget-action";
                    divider.style.height = "1px";
                    divider.style.background = "var(--base-glass-border)";
                    divider.style.margin = "4px 0";
                    menuUl.insertBefore(divider, menuUl.children[config.context_menu.length]);
                }
            }
        }
        
        this.contextMenu.style.left = `${x}px`;
        this.contextMenu.style.top = `${y}px`;
        this.contextMenu.classList.remove('hidden');
        this.contextMenu.focus(); // A11y: move focus to menu
    }
    
    executeWidgetAction(widgetName, actionName) {
        console.log(`[Krystal] Executing action '${actionName}' on widget '${widgetName}'`);
        
        // Find the iframe belonging to this widget
        const iframe = document.querySelector(`iframe[data-widget-name="${widgetName}"]`);
        if (iframe && iframe.contentWindow) {
            // Send IPC message to the widget
            iframe.contentWindow.postMessage({
                krystalIntent: 'widgetAction',
                action: actionName
            }, '*');
        } else {
            this.showNotification("Error", `Widget '${widgetName}' no se encuentra activo.`, "error");
        }
    }

    hideContextMenu() {
        this.contextMenu.classList.add('hidden');
    }

    syncAllIframes() {
        setTimeout(() => {
            const isDark = document.body.classList.contains('dark-mode');
            const themeUrl = document.getElementById('theme-stylesheet')?.href;
            document.querySelectorAll('iframe').forEach(iframe => {
                this.applyThemeToIframe(iframe, isDark, themeUrl);
            });
        }, 50); // slight delay to allow Alpine to flush DOM classes
    }

    applyThemeToIframe(iframe, isDark, themeUrl) {
        try {
            const doc = iframe.contentDocument || iframe.contentWindow?.document;
            if (!doc) return;
            
            if (isDark) doc.body.classList.add('dark-mode');
            else doc.body.classList.remove('dark-mode');
            
            if (themeUrl) {
                let themeLink = doc.getElementById('theme-stylesheet');
                if (!themeLink) {
                    themeLink = doc.createElement('link');
                    themeLink.id = 'theme-stylesheet';
                    themeLink.rel = 'stylesheet';
                    doc.head.appendChild(themeLink);
                }
                themeLink.href = themeUrl;
            }
        } catch(e) {
            console.warn("Cross-origin iframe theme sync blocked or iframe not ready.");
        }
    }

    async loadWidgets() {
        // Mocking the Backend Call for now. 
        // In reality, this will call /api/widgets/all to get layout + HTML
        console.log("[Krystal] Requesting widget layout...");
        
        const demoWidgetLayout = {
            id: 'demo-widget-1',
            x: 0,
            y: 0,
            w: 4,
            h: 3,
            content: `
                <div class="krystal-drag-handle" aria-label="Mover widget" style="display: none; align-items:center; justify-content:center; background: rgba(0,0,0,0.5); border-radius: 5px; margin: 4px; cursor: move; height: 24px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M7 19h10V4H7v15zm-5-2h4V6H2v11zM19 6v11h4V6h-4z"/></svg>
                </div>
                <iframe src="/api/widgets/demo/status" data-widget-name="demo" style="width:100%;height:100%;border:none; pointer-events: auto;"></iframe>
            `
        };

        const usersWidgetLayout = {
            id: 'users-widget-1',
            x: 4,
            y: 0,
            w: 6,
            h: 4,
            content: `
                <div class="krystal-drag-handle" aria-label="Mover widget" style="display: none; align-items:center; justify-content:center; background: rgba(0,0,0,0.5); border-radius: 5px; margin: 4px; cursor: move; height: 24px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M7 19h10V4H7v15zm-5-2h4V6H2v11zM19 6v11h4V6h-4z"/></svg>
                </div>
                <iframe src="/api/widgets/users/ui" data-widget-name="users" style="width:100%;height:100%;border:none; pointer-events: auto;"></iframe>
            `
        };

        this.grid.addWidget(demoWidgetLayout);
        this.grid.addWidget(usersWidgetLayout);
    }
}

// Boot up
document.addEventListener('DOMContentLoaded', () => {
    window.krystalOS = new KrystalEngine();
    
    // Wait for the auth store to signal authentication is complete before booting the UI
    window.addEventListener('krystal-authenticated', () => {
        // Alpine.js needs a tick to remove 'display: none' from the dashboard wrapper.
        // If GridStack initializes while hidden, it calculates 0x0 sizes and elements collapse (disappear).
        setTimeout(() => {
            window.krystalOS.init();
        }, 100);
    });
});
