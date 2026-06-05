// 公共Vue组件

/**
 * 背景装饰组件
 */
const BgDecoration = {
    template: `
        <div class="bg-decoration">
            <div class="bg-circle bg-circle-1"></div>
            <div class="bg-circle bg-circle-2"></div>
            <div class="bg-circle bg-circle-3"></div>
        </div>
    `
};

/**
 * 导航栏组件
 */
const Navbar = {
    props: {
        activePage: {
            type: String,
            default: ''
        }
    },
    template: `
        <nav class="navbar">
            <div class="navbar-content">
                <a href="/" class="navbar-brand">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                    </svg>
                    {{ t('common.appName') }}
                </a>
                <div class="nav-right">
                    <div class="nav-links">
                        <a href="/" :class="{ active: activePage === 'home' }">{{ t('nav.home') }}</a>
                        <a href="/history" :class="{ active: activePage === 'history' }">{{ t('nav.history') }}</a>
                    </div>
                    <div class="locale-switcher" @mouseenter="showLocaleMenu = true" @mouseleave="showLocaleMenu = false">
                        <button class="locale-btn">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="2" y1="12" x2="22" y2="12"/>
                                <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
                            </svg>
                            {{ currentLocaleName }}
                        </button>
                        <div class="locale-menu" :class="{ show: showLocaleMenu }">
                            <a 
                                v-for="locale in supportedLocales" 
                                :key="locale"
                                class="locale-item" 
                                :class="{ active: locale === currentLocale }"
                                @click.prevent="switchLocale(locale)"
                            >
                                {{ getLocaleName(locale) }}
                            </a>
                        </div>
                    </div>
                    <button class="theme-toggle" @click="toggleTheme" :title="isDark ? t('nav.lightMode') : t('nav.darkMode')">
                        <svg v-if="isDark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="5"/>
                            <line x1="12" y1="1" x2="12" y2="3"/>
                            <line x1="12" y1="21" x2="12" y2="23"/>
                            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                            <line x1="1" y1="12" x2="3" y2="12"/>
                            <line x1="21" y1="12" x2="23" y2="12"/>
                            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                        </svg>
                        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
                        </svg>
                    </button>
                    <div class="nav-user-dropdown" v-if="user" @mouseenter="showDropdown = true" @mouseleave="showDropdown = false">
                        <div class="user-avatar-btn">
                            <div class="nav-avatar">
                                <img v-if="user.avatar_url" :src="user.avatar_url" :alt="user.nickname"
                                     @error="$event.target.style.display='none'; $event.target.nextElementSibling.style.display='flex'" />
                                <span v-else class="nav-avatar-fallback">{{ (user.nickname || user.username || '?').charAt(0).toUpperCase() }}</span>
                            </div>
                        </div>
                        <div class="dropdown-menu" :class="{ show: showDropdown }">
                            <div class="dropdown-header">
                                <div class="dropdown-user-info">
                                    <div class="dropdown-user-name">{{ user.nickname || user.username }}</div>
                                    <div class="dropdown-user-role">{{ user.role === 'admin' ? t('profile.admin') : t('profile.user') }}</div>
                                </div>
                            </div>
                            <div class="dropdown-divider"></div>
                            <a href="/profile" class="dropdown-item">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                                    <circle cx="12" cy="7" r="4"/>
                                </svg>
                                {{ t('nav.profile') }}
                            </a>
                            <a href="/config" class="dropdown-item">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="3"/>
                                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
                                </svg>
                                {{ t('nav.config') }}
                            </a>
                            <a v-if="user.role === 'admin'" href="/admin" class="dropdown-item">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                                    <circle cx="9" cy="7" r="4"/>
                                    <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                                    <path d="M16 3.13a4 4 0 010 7.75"/>
                                </svg>
                                {{ t('nav.admin') }}
                            </a>
                            <a v-if="user.role === 'admin'" href="/logs" class="dropdown-item">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                </svg>
                                {{ t('nav.logs') }}
                            </a>
                            <div class="dropdown-divider"></div>
                            <a href="#" class="dropdown-item danger" @click.prevent="logout">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
                                    <polyline points="16 17 21 12 16 7"/>
                                    <line x1="21" y1="12" x2="9" y2="12"/>
                                </svg>
                                {{ t('nav.logout') }}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    `,
    setup() {
        const isDark = ref(localStorage.getItem('theme') === 'dark');
        const user = ref(null);
        const showDropdown = ref(false);
        const showLocaleMenu = ref(false);
        const supportedLocales = i18n.getSupportedLocales();
        
        const t = (key, params) => i18n.t(key, params);
        
        // 直接依赖i18n.locale响应式ref，语言切换时自动更新
        const currentLocale = Vue.computed(() => i18n.locale ? i18n.locale.value : 'zh-CN');
        const currentLocaleName = Vue.computed(() => i18n.getLocaleName(currentLocale.value));
        
        const toggleTheme = () => {
            isDark.value = !isDark.value;
            document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light');
            localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
        };
        
        const switchLocale = async (locale) => {
            await i18n.switchLocale(locale);
            showLocaleMenu.value = false;
        };
        
        const getLocaleName = (locale) => i18n.getLocaleName(locale);
        
        const fetchUser = async () => {
            try {
                const response = await fetch('/api/auth/me');
                if (response.ok) {
                    user.value = await response.json();
                }
            } catch (error) {
                // 静默失败
            }
        };
        
        const logout = async () => {
            try {
                const response = await fetch('/api/auth/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('退出失败:', error);
            }
        };
        
        Vue.onMounted(() => {
            document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light');
            fetchUser();
        });
        
        return { 
            isDark, user, showDropdown, showLocaleMenu, 
            currentLocale, currentLocaleName, supportedLocales,
            toggleTheme, switchLocale, getLocaleName, logout, t
        };
    }
};

/**
 * 页面标题组件
 */
const PageHeader = {
    props: {
        icon: String,
        title: String,
        subtitle: String
    },
    template: `
        <div class="page-header">
            <div class="page-icon" v-if="icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="icon"></svg>
            </div>
            <div style="flex: 1;">
                <h1 class="page-title">{{ title }}</h1>
                <p class="page-subtitle" v-if="subtitle">{{ subtitle }}</p>
            </div>
            <slot></slot>
        </div>
    `
};

/**
 * 分页组件
 */
const Pagination = {
    props: {
        currentPage: Number,
        totalPages: Number,
        total: Number
    },
    emits: ['page-change'],
    template: `
        <div v-if="totalPages > 1" class="pagination-wrapper">
            <div class="pagination">
                <button 
                    class="page-btn" 
                    :disabled="currentPage <= 1"
                    @click="$emit('page-change', currentPage - 1)"
                >
                    ‹
                </button>
                <button 
                    v-for="page in displayPages" 
                    :key="page"
                    class="page-btn"
                    :class="{ active: page === currentPage }"
                    @click="$emit('page-change', page)"
                >
                    {{ page }}
                </button>
                <button 
                    class="page-btn" 
                    :disabled="currentPage >= totalPages"
                    @click="$emit('page-change', currentPage + 1)"
                >
                    ›
                </button>
            </div>
        </div>
    `,
    setup(props) {
        const displayPages = computed(() => {
            const pages = [];
            const maxDisplay = 5;
            let start = Math.max(1, props.currentPage - Math.floor(maxDisplay / 2));
            let end = Math.min(props.totalPages, start + maxDisplay - 1);
            if (end - start + 1 < maxDisplay) {
                start = Math.max(1, end - maxDisplay + 1);
            }
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            return pages;
        });
        
        return { displayPages };
    }
};

/**
 * 加载状态组件
 */
const LoadingState = {
    template: `
        <div style="text-align: center; padding: 40px;">
            <div class="spinner" style="margin: 0 auto; width: 32px; height: 32px; border-width: 3px; border-color: rgba(74, 108, 247, 0.3); border-top-color: #4A6CF7;"></div>
            <p style="margin-top: 16px; color: #9CA3AF;">{{ t('common.loadingState') }}</p>
        </div>
    `,
    setup() {
        const t = (key, params) => i18n.t(key, params);
        return { t };
    }
};

/**
 * 空状态组件
 */
const EmptyState = {
    props: {
        title: {
            type: String,
            default: ''
        },
        description: {
            type: String,
            default: ''
        }
    },
    template: `
        <div class="empty-state">
            <div class="empty-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M20 12V8H6a2 2 0 01-2-2c0-1.1.9-2 2-2h12v4"/>
                    <path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/>
                    <path d="M18 12a2 2 0 000 4h4v-4h-4z"/>
                </svg>
            </div>
            <h3 class="empty-title">{{ displayTitle }}</h3>
            <p class="empty-desc" v-if="description">{{ description }}</p>
            <slot></slot>
        </div>
    `,
    setup(props) {
        const t = (key, params) => i18n.t(key, params);
        const displayTitle = computed(() => props.title || t('common.emptyState'));
        return { t, displayTitle };
    }
};

// 注册全局组件
function registerGlobalComponents(app) {
    app.component('bg-decoration', BgDecoration);
    app.component('navbar', Navbar);
    app.component('page-header', PageHeader);
    app.component('pagination-component', Pagination);
    app.component('loading-state', LoadingState);
    app.component('empty-state', EmptyState);
}
