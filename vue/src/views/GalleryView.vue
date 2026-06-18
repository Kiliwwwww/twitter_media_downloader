<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import LoadingState from '../components/LoadingState.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import i18n from '../utils/i18n'
import { formatFileSize, debounce } from '../utils/utils'
import { ElMessage } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const users = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const debounceSearch = debounce(() => {
  fetchUsers(1)
})

const resetSearch = () => {
  keyword.value = ''
  fetchUsers(1)
}

const fetchUsers = async (page = 1, showLoading = true) => {
  if (showLoading) {
    loading.value = true
  }
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: pageSize.value.toString()
    })
    if (keyword.value) {
      params.append('keyword', keyword.value)
    }

    const response = await fetch(`/api/gallery/users?${params.toString()}`)
    const data = await response.json()
    const newData = data.data || []

    if (JSON.stringify(newData) !== JSON.stringify(users.value)) {
      users.value = newData
    }
    total.value = data.total || 0
    currentPage.value = data.page || 1

    fetchMissingAvatars(newData)
  } catch (error) {
    if (showLoading) {
      ElMessage.error(t('gallery.fetchFailed'))
    }
    users.value = []
  } finally {
    if (showLoading) {
      loading.value = false
    }
  }
}

const fetchMissingAvatars = async (items: any[]) => {
  const missingUsers = new Set<string>()
  for (const item of items) {
    if (!item.avatar_url && item.user_id) {
      missingUsers.add(item.user_id)
    }
  }

  if (missingUsers.size === 0) return

  const promises = Array.from(missingUsers).map(async (userId) => {
    try {
      const resp = await fetch(`/api/avatar/${encodeURIComponent(userId)}`)
      const data = await resp.json()
      return { userId, avatarUrl: data.avatar_url }
    } catch (e) {
      return { userId, avatarUrl: null }
    }
  })

  const results = await Promise.all(promises)

  for (const result of results) {
    if (result.avatarUrl) {
      const index = users.value.findIndex(u => u.user_id === result.userId)
      if (index !== -1) {
        users.value[index] = { ...users.value[index], avatar_url: result.avatarUrl }
      }
    }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <Navbar active-page="gallery" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('gallery.title')" 
      :subtitle="t('gallery.subtitle')"
      icon="<rect x='3' y='3' width='7' height='7'/><rect x='14' y='3' width='7' height='7'/><rect x='14' y='14' width='7' height='7'/><rect x='3' y='14' width='7' height='7'/>"
    >
    </PageHeader>
    
    <div class="filter-section">
      <div class="filter-item">
        <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
        </svg>
        <input 
          type="text" 
          class="filter-input" 
          v-model="keyword" 
          :placeholder="t('gallery.searchPlaceholder')"
          @input="debounceSearch"
        >
      </div>
      <button class="filter-reset" @click="resetSearch">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="M3 12a9 9 0 019-9 9.75 9.75 0 016.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
          <path d="M21 12a9 9 0 01-9 9 9.75 9.75 0 01-6.74-2.74L3 16"/>
          <path d="M8 16H3v5"/>
        </svg>
        {{ t('common.reset') }}
      </button>
    </div>
    
    <div class="gallery-card">
      <LoadingState v-if="loading" />
      
      <EmptyState 
        v-else-if="users.length === 0" 
        :title="t('gallery.noUsers')" 
        :description="t('gallery.noUsersDesc')"
      >
        <a href="/" class="empty-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
          {{ t('common.goDownload') }}
        </a>
      </EmptyState>
      
      <div v-else class="gallery-grid">
        <a 
          v-for="user in users" 
          :key="user.user_id" 
          :href="'/detail/' + encodeURIComponent(user.user_id)"
          class="gallery-user-card"
        >
          <div class="gallery-card-header">
            <div class="gallery-avatar">
              <img v-if="user.avatar_url" :src="user.avatar_url" :alt="user.user_name" @error="($event.target as HTMLImageElement).style.display='none'; ($event.target as HTMLImageElement).nextElementSibling?.setAttribute('style', 'display:flex')" />
              <span v-else class="avatar-fallback">{{ (user.user_name || user.user_id || '?').charAt(0).toUpperCase() }}</span>
            </div>
            <div class="gallery-user-info">
              <div class="gallery-user-name">{{ user.user_name || t('history.unknownUser') }}</div>
              <div class="gallery-user-id">@{{ user.user_id }}</div>
            </div>
          </div>
          <div class="gallery-stats">
            <div class="gallery-stat-item">
              <div class="gallery-stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
                  <polyline points="13 2 13 9 20 9"/>
                </svg>
              </div>
              <div class="gallery-stat-content">
                <div class="gallery-stat-value">{{ user.total_files || 0 }}</div>
                <div class="gallery-stat-label">{{ t('gallery.totalFiles') }}</div>
              </div>
            </div>
            <div class="gallery-stat-item">
              <div class="gallery-stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </div>
              <div class="gallery-stat-content">
                <div class="gallery-stat-value">{{ formatFileSize(user.total_size || 0) }}</div>
                <div class="gallery-stat-label">{{ t('gallery.totalSize') }}</div>
              </div>
            </div>

          </div>
          <div class="gallery-updated">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            {{ t('gallery.lastUpdate') }}: {{ user.last_completed_at || user.last_created_at || '-' }}
          </div>
        </a>
      </div>
      
      <Pagination 
        v-if="total > pageSize"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total="total"
        @page-change="fetchUsers"
      />
    </div>
  </div>
</template>

<style scoped>
</style>
