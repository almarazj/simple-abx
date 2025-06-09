// Theme management for ABX Test Application
class ThemeManager {
    constructor() {
        this.themeToggle = null;
        this.themeIcon = null;
        this.currentTheme = 'light';
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupTheme());
        } else {
            this.setupTheme();
        }
    }
    
    setupTheme() {
        // Get DOM elements
        this.themeToggle = document.getElementById('theme-toggle');
        this.themeIcon = document.querySelector('.theme-icon');
        
        if (!this.themeToggle || !this.themeIcon) {
            console.warn('Theme toggle elements not found');
            return;
        }
        
        // Load saved theme or use light as default
        this.currentTheme = localStorage.getItem('abx-theme') || 'light';
        this.applyTheme(this.currentTheme);
        
        // Setup event listener
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Listen for system theme changes
        this.setupSystemThemeListener();
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(this.currentTheme);
        this.saveTheme(this.currentTheme);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: this.currentTheme }
        }));
    }
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateThemeIcon(theme);
        this.currentTheme = theme;
    }
    
    updateThemeIcon(theme) {
        if (!this.themeIcon) return;
        
        if (theme === 'dark') {
            this.themeIcon.innerHTML = '<span class="material-icons">light_mode</span>';
            this.themeToggle.title = 'Cambiar a tema claro';
            this.themeToggle.setAttribute('aria-label', 'Activar tema claro');
        } else {
            this.themeIcon.innerHTML = '<span class="material-icons">dark_mode</span>';
            this.themeToggle.title = 'Cambiar a tema oscuro';
            this.themeToggle.setAttribute('aria-label', 'Activar tema oscuro');
        }
    }
    
    saveTheme(theme) {
        localStorage.setItem('abx-theme', theme);
    }
    
    setupSystemThemeListener() {
        // Listen for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        mediaQuery.addEventListener('change', (e) => {
            // Only apply system theme if user hasn't manually set a preference
            if (!localStorage.getItem('abx-theme')) {
                const systemTheme = e.matches ? 'dark' : 'light';
                this.applyTheme(systemTheme);
            }
        });
    }
    
    // Public method to get current theme
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    // Public method to set theme programmatically
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.applyTheme(theme);
            this.saveTheme(theme);
        }
    }
    
    // Public method to reset to system preference
    resetToSystemTheme() {
        localStorage.removeItem('abx-theme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        this.applyTheme(systemTheme);
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// Make it globally available
window.themeManager = themeManager;
