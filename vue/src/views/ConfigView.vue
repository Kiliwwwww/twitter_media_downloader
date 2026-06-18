<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'
import { ElMessage } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const configList = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)

const fetchConfigs = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/configs')
    const data = await response.json()
    configList.value = data
  } catch (error) {
    ElMessage.error(t('config.fetchFailed'))
  } finally {
    loading.value = false
  }
}

const saveConfigs = async () => {
  saving.value = true
  try {
    const data: Record<string, any> = {}
    configList.value.forEach(cfg => {
      data[cfg.key] = cfg.value
    })
    
    const response = await fetch('/api/configs', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    
    if (response.ok) {
      ElMessage.success(t('config.configSaved'))
      fetchConfigs()
    } else {
      ElMessage.error(t('config.saveFailed'))
    }
  } catch (error: any) {
    ElMessage.error(t('config.saveFailed') + ': ' + error.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => fetchConfigs())
</script>

<template>
  <Navbar active-page="config" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('config.title')" 
      :subtitle="t('config.subtitle')"
      icon="<circle cx='12' cy='12' r='3'/><path d='M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83'/>"
    />
    
    <!-- 配置卡片 -->
    <div class="config-card" v-loading="loading">
      <div v-for="(cfg, index) in configList" :key="cfg.key" class="config-item">
        <div class="label-row">
          <label>
            <svg class="label-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83"/>
            </svg>
            {{ cfg.description || cfg.key }}
          </label>
          <div v-if="cfg.key === 'auth_token' || cfg.key === 'ct0'" class="tip-wrapper">
            <span class="tip-tag">
              <el-icon><Warning /></el-icon>
              {{ t('config.howToGet') }}
            </span>
            <div class="tip-content">
              <div class="tip-content-title">{{ t('config.howToGetTitle') }}</div>
              <ul class="tip-content-list">
                <li v-for="step in t('config.howToGetSteps')" :key="step">{{ step }}</li>
              </ul>
            </div>
          </div>
        </div>
        <input
          class="config-input"
          v-model="configList[index].value"
          :placeholder="cfg.key === 'auth_token' ? t('config.authTokenPlaceholder') : (cfg.key === 'ct0' ? t('config.ct0Placeholder') : t('config.inputPlaceholder') + (cfg.description || cfg.key))"
          @keyup.enter="saveConfigs"
        >
        <div v-if="cfg.updated_at" class="config-hint">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
          {{ t('config.lastUpdated') }}{{ cfg.updated_at }}
        </div>
      </div>
      
      <button 
        class="save-btn"
        :disabled="saving"
        @click="saveConfigs"
      >
        <span v-if="saving" class="btn-spinner"></span>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
          <polyline points="17 21 17 13 7 13 7 21"/>
          <polyline points="7 3 7 8 15 8"/>
        </svg>
        {{ saving ? t('config.saving') : t('config.saveConfig') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
</style>