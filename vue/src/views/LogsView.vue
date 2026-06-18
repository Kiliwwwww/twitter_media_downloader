<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'
import { ElMessage, ElMessageBox } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const logs = ref<any[]>([])
const isConnected = ref(false)
const autoScroll = ref(true)
const filter = ref('all')
const logBody = ref<HTMLElement | null>(null)
let eventSource: EventSource | null = null

// 过滤日志
const filteredLogs = computed(() => {
  if (filter.value === 'all') return logs.value
  if (filter.value === 'error') {
    return logs.value.filter(log => log.level === 'error')
  }
  return logs.value.filter(log => log.category === filter.value)
})

// 连接SSE
const connectSSE = () => {
  if (eventSource) {
    eventSource.close()
  }
  
  eventSource = new EventSource('/api/logs/stream')
  
  eventSource.onopen = () => {
    isConnected.value = true
  }
  
  eventSource.onmessage = (event) => {
    try {
      const log = JSON.parse(event.data)
      logs.value.push(log)
      
      // 限制日志数量
      if (logs.value.length > 2000) {
        logs.value = logs.value.slice(-1500)
      }
      
      // 自动滚动
      if (autoScroll.value) {
        nextTick(() => {
          if (logBody.value) {
            logBody.value.scrollTop = logBody.value.scrollHeight
          }
        })
      }
    } catch (e) {
      console.error('Parse log error:', e)
    }
  }
  
  eventSource.onerror = () => {
    isConnected.value = false
    // 自动重连
    setTimeout(() => {
      if (eventSource?.readyState === EventSource.CLOSED) {
        connectSSE()
      }
    }, 3000)
  }
}

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  })
}

// 切换自动滚动
const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    nextTick(() => {
      if (logBody.value) {
        logBody.value.scrollTop = logBody.value.scrollHeight
      }
    })
  }
}

// 清空日志
const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      t('logs.clearConfirm'),
      t('logs.clearTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    logs.value = []
    await fetch('/api/logs', { method: 'DELETE' })
    ElMessage.success(t('logs.cleared'))
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('logs.clearFailed'))
    }
  }
}

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>

<template>
  <Navbar active-page="logs" />
  
  <div class="main-container" style="max-width: 1200px;">
    <PageHeader 
      :title="t('logs.title')" 
      :subtitle="t('logs.subtitle')"
      icon="<path d='M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/><polyline points='10 9 9 9 8 9'/>"
    >
      <div style="display: flex; gap: 8px;">
        <button class="log-action-btn primary" @click="toggleAutoScroll">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
          </svg>
          {{ autoScroll ? t('logs.pauseScroll') : t('logs.autoScroll') }}
        </button>
        <button class="log-action-btn danger" @click="clearLogs">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
          {{ t('logs.clearLogs') }}
        </button>
      </div>
    </PageHeader>
    
    <div class="log-container">
      <div class="log-toolbar">
        <div class="log-toolbar-left">
          <div class="log-status">
            <div class="log-status-dot" :class="{ connected: isConnected }"></div>
            {{ isConnected ? t('logs.connected') : t('logs.disconnected') }}
          </div>
          <span class="log-count">{{ t('logs.logCount', { count: filteredLogs.length }) }}</span>
        </div>
        <div class="log-toolbar-right">
          <div class="log-filters">
            <button 
              class="log-filter-btn" 
              :class="{ active: filter === 'all' }"
              @click="filter = 'all'"
            >
              {{ t('logs.filterAll') }}
            </button>
            <button 
              class="log-filter-btn" 
              :class="{ active: filter === 'download' }"
              @click="filter = 'download'"
            >
              {{ t('logs.filterDownload') }}
            </button>
            <button 
              class="log-filter-btn" 
              :class="{ active: filter === 'system' }"
              @click="filter = 'system'"
            >
              {{ t('logs.filterSystem') }}
            </button>
            <button 
              class="log-filter-btn" 
              :class="{ active: filter === 'error' }"
              @click="filter = 'error'"
            >
              {{ t('logs.filterError') }}
            </button>
          </div>
        </div>
      </div>
      
      <div class="log-body" ref="logBody">
        <div v-if="filteredLogs.length === 0" class="log-empty">
          <div class="log-empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          <h3>{{ t('logs.waitingForLogs') }}</h3>
          <p>{{ t('logs.waitingForLogsDesc') }}</p>
        </div>
        
        <div 
          v-for="(log, index) in filteredLogs" 
          :key="index"
          class="log-entry"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level" :class="log.level">{{ log.level }}</span>
          <span class="log-category">{{ log.category === 'download' ? t('logs.categoryDownload') : t('logs.categorySystem') }}</span>
          <span class="log-message" :class="log.level">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>