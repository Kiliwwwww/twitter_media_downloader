import { ref, computed } from 'vue'
import zhCN from '../assets/i18n/zh-CN.json'
import en from '../assets/i18n/en.json'
import ja from '../assets/i18n/ja.json'

class I18n {
  locale = ref('zh-CN')
  messages: Record<string, any> = {
    'zh-CN': zhCN,
    'en': en,
    'ja': ja
  }
  supportedLocales = ['zh-CN', 'en', 'ja']
  localeNames: Record<string, string> = {
    'zh-CN': '中文',
    'en': 'English',
    'ja': '日本語'
  }

  async init() {
    // 从localStorage获取语言设置
    const savedLocale = localStorage.getItem('locale')
    if (savedLocale && this.supportedLocales.includes(savedLocale)) {
      this.locale.value = savedLocale
    } else {
      const browserLang = navigator.language || (navigator as any).userLanguage
      if (browserLang.startsWith('zh')) {
        this.locale.value = 'zh-CN'
      } else if (browserLang.startsWith('ja')) {
        this.locale.value = 'ja'
      } else {
        this.locale.value = 'en'
      }
    }

    // 更新HTML lang属性
    document.documentElement.lang = this.locale.value

    return this.locale.value
  }

  async loadLocale(locale: string) {
    // 语言包已经在初始化时加载，这里直接返回
    return this.messages[locale] || null
  }

  async switchLocale(locale: string) {
    if (!this.supportedLocales.includes(locale)) return

    // 先加载语言包，再更新locale，避免渲染时翻译缺失
    if (!this.messages[locale]) {
      await this.loadLocale(locale)
    }

    this.locale.value = locale
    localStorage.setItem('locale', locale)
    document.documentElement.lang = locale
  }

  t(key: string, params: Record<string, any> = {}): string {
    // 读取locale.value，让Vue追踪这个依赖
    const current = this.locale.value
    const keys = key.split('.')
    let value = this.messages[current]

    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k]
      } else {
        return key
      }
    }

    if (typeof value !== 'string') return key

    return value.replace(/\{(\w+)\}/g, (match: string, paramKey: string) => {
      return params[paramKey] !== undefined ? params[paramKey] : match
    })
  }

  getLocale() {
    return this.locale.value
  }

  getLocaleName(locale: string) {
    return this.localeNames[locale] || locale
  }

  getSupportedLocales() {
    return this.supportedLocales
  }
}

const i18n = new I18n()

export default i18n
