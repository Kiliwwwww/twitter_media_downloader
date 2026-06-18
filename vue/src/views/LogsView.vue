<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

onMounted(() => {
  // TODO: 实现实时日志逻辑
})
</script>

<template>
  <Navbar active-page="logs" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('logs.title')" 
      :subtitle="t('logs.subtitle')"
      icon="<path d='M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z'/><polyline points='14 2 14 8 20 8'/><line x1='16' y1='13' x2='8' y2='13'/><line x1='16' y1='17' x2='8' y2='17'/>"
    />
    
    <div class="card">
      <p>实时日志页</p>
      <p>此页面需要进一步实现</p>
    </div>
  </div>
</template>

<style scoped>
</style>
