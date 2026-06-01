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
                    TW
                </a>
                <div class="nav-right">
                    <div class="nav-links">
                        <a href="/" :class="{ active: activePage === 'home' }">首页</a>
                        <a href="/config" :class="{ active: activePage === 'config' }">配置</a>
                        <a href="/history" :class="{ active: activePage === 'history' }">历史</a>
                    </div>
                    <button class="theme-toggle" @click="toggleTheme" title="切换主题">
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
                </div>
            </div>
        </nav>
    `,
    setup() {
        const isDark = ref(localStorage.getItem('theme') === 'dark');
        
        const toggleTheme = () => {
            isDark.value = !isDark.value;
            document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light');
            localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
        };
        
        // 初始化主题
        onMounted(() => {
            document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light');
        });
        
        return { isDark, toggleTheme };
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
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path :d="icon"/>
                </svg>
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
            <p style="margin-top: 16px; color: #9CA3AF;">加载中...</p>
        </div>
    `
};

/**
 * 空状态组件
 */
const EmptyState = {
    props: {
        title: {
            type: String,
            default: '暂无数据'
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
            <h3 class="empty-title">{{ title }}</h3>
            <p class="empty-desc" v-if="description">{{ description }}</p>
            <slot></slot>
        </div>
    `
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
