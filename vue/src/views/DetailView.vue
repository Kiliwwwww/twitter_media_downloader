<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import LoadingState from '../components/LoadingState.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import i18n from '../utils/i18n'
import { formatFileSize } from '../utils/utils'
import { ElMessage } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)
const route = useRoute()
const userId = ref(route.params.userId as string)

const user = ref<any>(null)
const loading = ref(false)
const files = ref<any[]>([])
const avatarUrl = ref('')
const filterType = ref('all')
const viewMode = ref('grid')
const currentPage = ref(1)
const pageSize = ref(24)
const totalPages = ref(1)
const previewFile = ref<any>(null)
const previewIndex = ref(-1)

const stats = ref({
  images: 0,
  videos: 0,
  total: 0
})

const paginatedFiles = ref<any[]>([])

const canGoPrev = computed(() => {
  if (previewIndex.value <= 0) return false
  return true
})

const canGoNext = computed(() => {
  if (previewIndex.value >= paginatedFiles.value.length - 1) return false
  return true
})

const fetchFiles = async (page = 1) => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: pageSize.value.toString(),
      type: filterType.value
    })
    
    const response = await fetch(`/api/user-media/${encodeURIComponent(userId.value)}?${params.toString()}`)
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error)
    }
    
    files.value = data.files || []
    paginatedFiles.value = data.files || []
    totalPages.value = data.total_pages || 1
    currentPage.value = data.page || 1
    
    stats.value = {
      images: data.images || 0,
      videos: data.videos || 0,
      total: (data.images || 0) + (data.videos || 0)
    }
  } catch (error) {
    ElMessage.error(t('detail.fetchFailed'))
    files.value = []
    paginatedFiles.value = []
  } finally {
    loading.value = false
  }
}

const fetchAvatar = async () => {
  try {
    const resp = await fetch(`/api/avatar/${encodeURIComponent(userId.value)}`)
    const data = await resp.json()
    if (data.avatar_url) {
      avatarUrl.value = data.avatar_url
    }
  } catch (e) {
    // 静默失败
  }
}

const applyFilter = () => {
  fetchFiles(1)
}

const goToPage = (page: number) => {
  fetchFiles(page)
}

const openPreview = (file: any) => {
  previewFile.value = file
  previewIndex.value = paginatedFiles.value.findIndex(f => f.name === file.name)
}

const closePreview = () => {
  previewFile.value = null
  previewIndex.value = -1
}

const prevFile = () => {
  if (canGoPrev.value) {
    previewIndex.value--
    previewFile.value = paginatedFiles.value[previewIndex.value]
  }
}

const nextFile = () => {
  if (canGoNext.value) {
    previewIndex.value++
    previewFile.value = paginatedFiles.value[previewIndex.value]
  }
}

const getVideoType = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  const types: Record<string, string> = {
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mov': 'video/quicktime',
    'avi': 'video/x-msvideo',
    'mkv': 'video/x-matroska'
  }
  return types[ext] || 'video/mp4'
}

const goBack = () => {
  window.location.href = '/history'
}

const updating = ref(false)

const updateUser = async () => {
  if (updating.value) return
  
  updating.value = true
  
  try {
    const response = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId.value,
        download_type: 'all',
        export_xlsx: false
      })
    })
    const data = await response.json()
    
    if (response.ok) {
      ElMessage.success(t('detail.updateStarted'))
      // 跳转到历史页面查看下载进度
      setTimeout(() => {
        window.location.href = '/history'
      }, 1500)
    } else {
      ElMessage.error(data.error || t('detail.updateFailed'))
    }
  } catch (error) {
    ElMessage.error(t('detail.updateFailed'))
  } finally {
    updating.value = false
  }
}

const zipping = ref(false)

const createZip = async () => {
  if (zipping.value) return
  
  zipping.value = true
  
  try {
    const response = await fetch(`/api/zip/${encodeURIComponent(userId.value)}`, { method: 'POST' })
    const data = await response.json()
    
    if (response.ok) {
      ElMessage.success(t('detail.zipCreated'))
      if (data.download_url) {
        window.location.href = data.download_url
      }
    } else {
      ElMessage.error(data.error || t('detail.zipFailed'))
    }
  } catch (error) {
    ElMessage.error(t('detail.zipFailed'))
  } finally {
    zipping.value = false
  }
}

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

// 键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  if (!previewFile.value) return
  if (e.key === 'Escape') closePreview()
  if (e.key === 'ArrowLeft') prevFile()
  if (e.key === 'ArrowRight') nextFile()
}

onMounted(() => {
  fetchUser()
  fetchFiles()
  fetchAvatar()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Navbar active-page="history" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('detail.title')" 
      :subtitle="t('detail.subtitle')"
      icon="<path d='M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2'/><circle cx='12' cy='7' r='4'/>"
    >
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-success" @click="updateUser" :disabled="updating">
          <span v-if="updating" class="btn-spinner"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M21 2v6h-6M3 12a9 9 0 0115.364-6.364L21 8M3 22v-6h6M21 12a9 9 0 01-15.364 6.364L3 16"/>
          </svg>
          {{ updating ? t('detail.updating') : t('detail.update') }}
        </button>
        <button class="btn btn-primary" @click="createZip" :disabled="zipping">
          <span v-if="zipping" class="btn-spinner"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          {{ zipping ? t('detail.zipping') : t('detail.downloadZip') }}
        </button>
        <button class="btn btn-secondary" @click="goBack">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          {{ t('common.back') }}
        </button>
      </div>
    </PageHeader>
    
    <!-- 用户信息卡片 -->
    <div class="user-info-card">
      <div class="user-avatar-large">
        <img v-if="avatarUrl" :src="avatarUrl" :alt="userId" 
             @error="($event.target as HTMLImageElement).style.display='none'; ($event.target as HTMLImageElement).nextElementSibling?.setAttribute('style', 'display:flex')" />
        <span v-else class="avatar-fallback-large">{{ userId.charAt(0).toUpperCase() }}</span>
      </div>
      <div class="user-details">
        <div class="user-name-row">
          <h2 class="user-name-display">@{{ userId }}</h2>
          <a :href="'https://x.com/' + userId" target="_blank" class="twitter-link" :title="t('detail.viewOnTwitter')">
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="currentColor"/>
            </svg>
          </a>
        </div>
        <div class="user-stats">
          <div class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            <span class="stat-value">{{ stats.images }}</span>
            <span class="stat-label">{{ t('detail.images') }}</span>
          </div>
          <div class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="23 7 16 12 23 17 23 7"/>
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
            <span class="stat-value">{{ stats.videos }}</span>
            <span class="stat-label">{{ t('detail.videos') }}</span>
          </div>
          <div class="stat-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
              <polyline points="13 2 13 9 20 9"/>
            </svg>
            <span class="stat-value">{{ stats.total }}</span>
            <span class="stat-label">{{ t('detail.totalFiles') }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 筛选和视图切换 -->
    <div class="filter-section">
      <div class="filter-item">
        <svg class="filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>
        <select class="filter-select" v-model="filterType" @change="applyFilter">
          <option value="all">{{ t('detail.allTypes') }}</option>
          <option value="image">{{ t('detail.imagesOnly') }}</option>
          <option value="video">{{ t('detail.videosOnly') }}</option>
        </select>
      </div>
      <div class="view-toggle">
        <button 
          class="view-btn" 
          :class="{ active: viewMode === 'grid' }"
          @click="viewMode = 'grid'"
          :title="t('detail.gridView')"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
        </button>
        <button 
          class="view-btn" 
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
          :title="t('detail.listView')"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 媒体内容 -->
    <div class="media-card">
      <LoadingState v-if="loading" />
      
      <EmptyState 
        v-else-if="files.length === 0" 
        :title="t('detail.noMedia')" 
        :description="t('detail.noMediaDesc')"
      >
        <a href="/" class="empty-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
          {{ t('common.goDownload') }}
        </a>
      </EmptyState>
      
      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="media-grid">
        <div 
          v-for="file in paginatedFiles" 
          :key="file.name" 
          class="media-grid-item"
          @click="openPreview(file)"
        >
          <div class="media-thumbnail">
            <img v-if="file.type === 'image'" :src="file.path" :alt="file.name" loading="lazy" />
            <div v-else class="video-thumbnail">
              <img :src="file.thumb || file.path" :alt="file.name" loading="lazy" />
              <div class="video-play-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              </div>
            </div>
          </div>
          <div class="media-info-overlay">
            <span class="media-name">{{ file.name }}</span>
            <span class="media-size">{{ formatFileSize(file.size) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 列表视图 -->
      <div v-else class="media-list">
        <div 
          v-for="file in paginatedFiles" 
          :key="file.name" 
          class="media-list-item"
          @click="openPreview(file)"
        >
          <div class="media-list-thumb">
            <img v-if="file.type === 'image'" :src="file.path" :alt="file.name" loading="lazy" />
            <div v-else class="video-thumb-small">
              <img :src="file.thumb || file.path" :alt="file.name" loading="lazy" />
              <svg viewBox="0 0 24 24" fill="currentColor" class="play-icon-small">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </div>
          </div>
          <div class="media-list-info">
            <span class="media-list-name">{{ file.name }}</span>
            <span class="media-list-meta">
              <span class="media-type-tag" :class="'type-' + file.type">
                {{ file.type === 'image' ? t('detail.image') : t('detail.video') }}
              </span>
              {{ formatFileSize(file.size) }}
            </span>
          </div>
          <div class="media-list-actions">
            <a :href="file.path" download class="action-btn action-download" @click.stop>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
      
      <Pagination 
        v-if="totalPages > 1"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total="totalPages * pageSize"
        @page-change="goToPage"
      />
    </div>
  </div>
  
  <!-- 预览模态框 -->
  <div v-if="previewFile" class="preview-modal" @click.self="closePreview">
    <div class="preview-content">
      <button class="preview-close" @click="closePreview">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
      <div class="preview-nav">
        <button class="nav-btn prev-btn" @click="prevFile" :disabled="!canGoPrev">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <button class="nav-btn next-btn" @click="nextFile" :disabled="!canGoNext">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
      <div class="preview-main">
        <img v-if="previewFile.type === 'image'" :src="previewFile.path" :alt="previewFile.name" />
        <video v-else controls autoplay>
          <source :src="previewFile.path" :type="getVideoType(previewFile.name)">
        </video>
      </div>
      <div class="preview-info">
        <span class="preview-name">{{ previewFile.name }}</span>
        <span class="preview-size">{{ formatFileSize(previewFile.size) }}</span>
        <a :href="previewFile.path" download class="btn btn-primary preview-download">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
          {{ t('detail.download') }}
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>