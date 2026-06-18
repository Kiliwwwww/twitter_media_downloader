import './assets/css/common.css'
import './assets/css/login.css'
import './assets/css/home.css'
import './assets/css/gallery.css'
import './assets/css/history.css'
import './assets/css/admin.css'
import './assets/css/config.css'
import './assets/css/detail.css'
import './assets/css/logs.css'
import './assets/css/profile.css'
import './assets/css/dark-mode.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import i18n from './utils/i18n'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 初始化i18n
i18n.init().then(() => {
  app.mount('#app')
})
