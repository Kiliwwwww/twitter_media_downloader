<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import LoadingState from '../components/LoadingState.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import i18n from '../utils/i18n'
import { getStatusText, formatFileSize, debounce } from '../utils/utils'
import { ElMessage, ElMessageBox } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const user = ref<any>(null)
const history = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(15)
const total = ref(0)
const zippingUsers = ref<string[]>([])

const filters = ref({
  keyword: '',
  status: '',
  date: ''
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const debounceSearch = debounce(() => {
  fetchHistory(1)
})

const resetFilters = () => {
  filters.value = {
    keyword: '',
    status: '',
    date: ''
  }
  fetchHistory(1)
}

const fetchHistory = async (page = 1, showLoading = true) => {
  if (showLoading) {
    loading.value = true
  }
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: pageSize.value.toString()
    })
    if (filters.value.keyword) {
      params.append('keyword', filters.value.keyword)
    }
    if (filters.value.status) {
      params.append('status', filters.value.status)
    }
    if (filters.value.date) {
      params.append('date', filters.value.date)
    }

    const response = await fetch(`/api/history?${params.toString()}`)
    const data = await response.json()
    const newData = data.data || []

    if (JSON.stringify(newData) !== JSON.stringify(history.value)) {
      history.value = newData
    }
    total.value = data.total || 0
    currentPage.value = data.page || 1

    fetchMissingAvatars(newData)
  } catch (error) {
    if (showLoading) {
      ElMessage.error(t('history.fetchFailed'))
    }
    history.value = []
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

  for (const userId of missingUsers) {
    try {
      const resp = await fetch(`/api/avatar/${encodeURIComponent(userId)}`)
      const data = await resp.json()
      if (data.avatar_url) {
        for (const item of history.value) {
          if (item.user_id === userId) {
            item.avatar_url = data.avatar_url
          }
        }
      }
    } catch (e) {
      // 静默失败
    }
  }
}

const downloadFile = (taskId: string) => {
  window.location.href = `/api/download/${encodeURIComponent(taskId)}`
}

const deleteHistory = async (taskId: string) => {
  try {
    await ElMessageBox.confirm(
      t('history.deleteConfirm'),
      t('history.deleteTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    const response = await fetch(`/api/history/${encodeURIComponent(taskId)}`, { method: 'DELETE' })
    if (response.ok) {
      ElMessage.success(t('history.deleted'))
      fetchHistory(currentPage.value)
    } else {
      ElMessage.error(t('history.deleteFailed'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('history.deleteFailed'))
    }
  }
}

const createZip = async (userId: string) => {
  if (zippingUsers.value.includes(userId)) return

  zippingUsers.value.push(userId)

  try {
    const response = await fetch(`/api/zip/${encodeURIComponent(userId)}`, { method: 'POST' })
    const data = await response.json()

    if (response.ok) {
      ElMessage.success(t('history.zipCreated'))
      if (data.download_url) {
        window.location.href = data.download_url
      }
      fetchHistory(currentPage.value)
    } else {
      ElMessage.error(data.error || t('history.zipFailed'))
    }
  } catch (error) {
    ElMessage.error(t('history.zipFailed'))
  } finally {
    zippingUsers.value = zippingUsers.value.filter(u => u !== userId)
  }
}

const clearCache = async () => {
  try {
    await ElMessageBox.confirm(
      t('history.clearCacheConfirm'),
      t('history.clearCacheTitle'),
      {
        confirmButtonText: t('history.clearCacheButton'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    loading.value = true
    const response = await fetch('/api/cache', { method: 'DELETE' })
    const data = await response.json()

    if (response.ok) {
      ElMessage.success(data.message)
      fetchHistory(currentPage.value)
    } else {
      ElMessage.error(data.error || t('history.clearFailed'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('history.clearFailed'))
    }
  } finally {
    loading.value = false
  }
}

let refreshInterval: ReturnType<typeof setInterval> | null = null

const fetchUser = async () => {
  try {
    const response = await fetch('/api/auth/me')
    if (response.ok) {
      user.value = await response.json()
    }
  } catch (error) {
    // 静默失败
  }
}

onMounted(() => {
  fetchUser()
  fetchHistory()
  refreshInterval = setInterval(() => {
    fetchHistory(currentPage.value, false)
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})
</script>

<template>
  <Navbar active-page="history" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('history.title')" 
      :subtitle="t('history.subtitle')"
      icon="<circle cx='12' cy='12' r='10'/><polyline points='12 6 12 12 16 14'/>"
    >
      <button v-if="user && user.role === 'admin'" class="btn btn-secondary" @click="clearCache">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          <path d="M9 10h6M9 14h6"/>
        </svg>
        {{ t('history.clearCache') }}
      </button>
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
          v-model="filters.keyword" 
          :placeholder="t('history.searchPlaceholder')"
          @input="debounceSearch"
        >
      </div>
      <div class="filter-item">
        <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>
        <select class="filter-select" v-model="filters.status" @change="fetchHistory(1)">
          <option value="">{{ t('history.allStatus') }}</option>
          <option value="downloading">{{ t('history.downloading') }}</option>
          <option value="completed">{{ t('history.completed') }}</option>
          <option value="failed">{{ t('history.failed') }}</option>
          <option value="pending">{{ t('history.pending') }}</option>
        </select>
      </div>
      <div class="filter-item">
        <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <input 
          type="date" 
          class="filter-input" 
          v-model="filters.date" 
          @change="fetchHistory(1)"
        >
      </div>
      <button class="filter-reset" @click="resetFilters">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <path d="M3 12a9 9 0 019-9 9.75 9.75 0 016.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
          <path d="M21 12a9 9 0 01-9 9 9.75 9.75 0 01-6.74-2.74L3 16"/>
          <path d="M8 16H3v5"/>
        </svg>
        {{ t('common.reset') }}
      </button>
    </div>
    
    <div class="history-card">
      <LoadingState v-if="loading" />
      
      <EmptyState 
        v-else-if="history.length === 0" 
        :title="t('history.noRecords')" 
        :description="t('history.noRecordsDesc')"
      >
        <a href="/" class="empty-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
          {{ t('common.goDownload') }}
        </a>
      </EmptyState>
      
      <div v-else class="history-list">
        <div v-for="item in history" :key="item.task_id" class="history-item">
          <div class="history-info">
            <a :href="'/detail/' + encodeURIComponent(item.user_id)" class="history-avatar-link">
              <div class="history-avatar">
                <img v-if="item.avatar_url" :src="item.avatar_url" :alt="item.user_name" @error="($event.target as HTMLImageElement).style.display='none'; ($event.target as HTMLImageElement).nextElementSibling?.setAttribute('style', 'display:flex')" />
                <span v-else class="avatar-fallback">{{ (item.user_name || item.user_id || '?').charAt(0).toUpperCase() }}</span>
              </div>
            </a>
            <div class="history-details">
              <div class="history-user">
                <a :href="'/detail/' + encodeURIComponent(item.user_id)" class="user-name-link">
                  {{ item.user_name || t('history.unknownUser') }}
                </a>
                <a :href="'/detail/' + encodeURIComponent(item.user_id)" class="history-user-id">@{{ item.user_id }}</a>
                <span 
                  class="status-tag" 
                  :class="'status-' + item.status"
                >
                  {{ getStatusText(item.status) }}
                  <span v-if="item.status === 'failed' && item.error_message" class="error-tooltip">
                    {{ item.error_message }}
                  </span>
                </span>
              </div>
              <div class="history-meta">
                <span class="history-meta-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
                    <polyline points="13 2 13 9 20 9"/>
                  </svg>
                  {{ item.downloaded_files || 0 }}/{{ item.total_files || 0 }} {{ t('history.files') }}
                </span>
                <span v-if="item.file_size" class="history-meta-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  {{ formatFileSize(item.file_size) }}
                </span>
                <span class="history-meta-item">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                  {{ item.created_at || '-' }}
                </span>
              </div>
            </div>
          </div>
          <div class="history-actions">
            <button 
              v-if="item.status === 'completed' && item.zip_path"
              class="action-btn action-download"
              @click="downloadFile(item.task_id)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              {{ t('history.download') }}
            </button>
            <button 
              v-if="item.status === 'completed' && !item.zip_path"
              class="action-btn action-zip"
              @click="createZip(item.user_id)"
              :disabled="zippingUsers.includes(item.user_id)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              {{ zippingUsers.includes(item.user_id) ? t('history.zipping') : t('history.createZip') }}
            </button>
            <button 
              class="action-btn action-delete"
              @click="deleteHistory(item.task_id)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
              {{ t('common.delete') }}
            </button>
          </div>
        </div>
      </div>
      
      <Pagination 
        v-if="total > pageSize"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total="total"
        @page-change="fetchHistory"
      />
    </div>
  </div>
</template>

<style scoped>
</style>
