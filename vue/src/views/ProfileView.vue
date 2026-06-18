<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

onMounted(() => {
  // TODO: 实现个人资料页逻辑
})
</script>

<template>
  <Navbar active-page="profile" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('profile.title')" 
      :subtitle="t('profile.subtitle')"
      icon="<path d='M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2'/><circle cx='12' cy='7' r='4'/>"
    />
    
    <div class="card">
      <p>个人资料页</p>
      <p>此页面需要进一步实现</p>
    </div>
  </div>
</template>

<style scoped>
</style>
