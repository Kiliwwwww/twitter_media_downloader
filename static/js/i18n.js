/**
 * i18n 国际化模块
 * 支持中文、英文、日文
 */

const I18n = {
    // 响应式语言状态（Vue ref）
    locale: null,
    
    // 语言包缓存
    messages: {},
    
    // 支持的语言
    supportedLocales: ['zh-CN', 'en', 'ja'],
    
    // 语言显示名称
    localeNames: {
        'zh-CN': '中文',
        'en': 'English',
        'ja': '日本語'
    },
    
    /**
     * 初始化i18n
     */
    async init() {
        // 创建响应式locale（Vue已通过CDN加载）
        this.locale = Vue.ref('zh-CN');
        
        // 从localStorage获取语言设置
        const savedLocale = localStorage.getItem('locale');
        if (savedLocale && this.supportedLocales.includes(savedLocale)) {
            this.locale.value = savedLocale;
        } else {
            const browserLang = navigator.language || navigator.userLanguage;
            if (browserLang.startsWith('zh')) {
                this.locale.value = 'zh-CN';
            } else if (browserLang.startsWith('ja')) {
                this.locale.value = 'ja';
            } else {
                this.locale.value = 'en';
            }
        }
        
        // 加载语言包
        await this.loadLocale(this.locale.value);
        
        // 更新HTML lang属性
        document.documentElement.lang = this.locale.value;
        
        return this.locale.value;
    },
    
    /**
     * 加载语言包
     */
    async loadLocale(locale) {
        if (this.messages[locale]) {
            return this.messages[locale];
        }
        try {
            const response = await fetch(`/static/i18n/${locale}.json`);
            if (response.ok) {
                this.messages[locale] = await response.json();
                return this.messages[locale];
            }
        } catch (error) {
            console.error(`Failed to load locale ${locale}:`, error);
        }
        return null;
    },
    
    /**
     * 切换语言
     */
    async switchLocale(locale) {
        if (!this.supportedLocales.includes(locale)) return;
        
        // 先加载语言包，再更新locale，避免渲染时翻译缺失
        if (!this.messages[locale]) {
            await this.loadLocale(locale);
        }
        
        this.locale.value = locale;
        localStorage.setItem('locale', locale);
        document.documentElement.lang = locale;
    },
    
    /**
     * 获取翻译文本（响应式：访问this.locale.value触发Vue依赖追踪）
     */
    t(key, params = {}) {
        // 读取locale.value，让Vue追踪这个依赖
        const current = this.locale ? this.locale.value : 'zh-CN';
        const keys = key.split('.');
        let value = this.messages[current];
        
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                return key;
            }
        }
        
        if (typeof value !== 'string') return key;
        
        return value.replace(/\{(\w+)\}/g, (match, paramKey) => {
            return params[paramKey] !== undefined ? params[paramKey] : match;
        });
    },
    
    getLocale() {
        return this.locale ? this.locale.value : 'zh-CN';
    },
    
    getLocaleName(locale) {
        return this.localeNames[locale] || locale;
    },
    
    getSupportedLocales() {
        return this.supportedLocales;
    }
};

const i18n = I18n;