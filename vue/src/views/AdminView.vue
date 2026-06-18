<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

onMounted(() => {
  // TODO: 实现管理后台逻辑
})
</script>

<template>
  <Navbar active-page="admin" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('admin.title')" 
      :subtitle="t('admin.subtitle')"
      icon="<path d='M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 00-3-3.87'/><path d='M16 3.13a4 4 0 010 7.75'/>"
    />
    
    <div class="card">
      <p>管理后台页</p>
      <p>此页面需要进一步实现</p>
    </div>
  </div>
</template>

<style scoped>
</style>
