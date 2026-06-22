<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import i18n from '../utils/i18n'

const props = defineProps<{
  activePage?: string
}>()

const userStore = useUserStore()
const isDark = ref(localStorage.getItem('theme') === 'dark')
const showDropdown = ref(false)
const showLocaleMenu = ref(false)
const supportedLocales = i18n.getSupportedLocales()

const currentLocale = computed(() => i18n.getLocale())
const currentLocaleName = computed(() => i18n.getLocaleName(currentLocale.value))

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const switchLocale = async (locale: string) => {
  await i18n.switchLocale(locale)
  showLocaleMenu.value = false
}

const getLocaleName = (locale: string) => i18n.getLocaleName(locale)

onMounted(() => {
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  userStore.fetchUser()
})
</script>

<template>
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
          <a href="/gallery" :class="{ active: activePage === 'gallery' }">{{ t('nav.gallery') }}</a>
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
        <button class="theme-toggle" @click="userStore.togglePrivacyMode" :title="userStore.privacyMode ? t('nav.privacyModeOff') : t('nav.privacyModeOn')">
          <svg v-if="userStore.privacyMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
        <div class="nav-user-dropdown" v-if="userStore.user" @mouseenter="showDropdown = true" @mouseleave="showDropdown = false">
          <div class="user-avatar-btn">
            <div class="nav-avatar">
              <img v-if="userStore.user.avatar_url" :src="userStore.user.avatar_url" :alt="userStore.user.nickname"
                   @error="($event.target as HTMLImageElement).style.display='none'; ($event.target as HTMLImageElement).nextElementSibling?.setAttribute('style', 'display:flex')" />
              <span v-else class="nav-avatar-fallback">{{ (userStore.user.nickname || userStore.user.username || '?').charAt(0).toUpperCase() }}</span>
            </div>
          </div>
          <div class="dropdown-menu" :class="{ show: showDropdown }">
            <div class="dropdown-header">
              <div class="dropdown-user-info">
                <div class="dropdown-user-name">{{ userStore.user.nickname || userStore.user.username }}</div>
                <div class="dropdown-user-role">{{ userStore.user.role === 'admin' ? t('profile.admin') : t('profile.user') }}</div>
              </div>
            </div>
            <div class="dropdown-divider"></div>
            <a href="/history" class="dropdown-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ t('nav.history') }}
            </a>
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
            <a v-if="userStore.user.role === 'admin'" href="/admin" class="dropdown-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                <path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
              {{ t('nav.admin') }}
            </a>
            <a v-if="userStore.user.role === 'admin'" href="/logs" class="dropdown-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              {{ t('nav.logs') }}
            </a>
            <div class="dropdown-divider"></div>
            <a href="#" class="dropdown-item danger" @click.prevent="userStore.logout">
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
</template>

<style scoped>
</style>
