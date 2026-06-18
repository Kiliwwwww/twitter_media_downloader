<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)
const route = useRoute()
const userId = ref(route.params.userId as string)

onMounted(() => {
  // TODO: 实现详情页逻辑
})
</script>

<template>
  <Navbar active-page="detail" />
  
  <div class="main-container">
    <PageHeader 
      :title="t('detail.title')" 
      :subtitle="t('detail.subtitle')"
      icon="<path d='M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z'/><polyline points='13 2 13 9 20 9'/>"
    />
    
    <div class="card">
      <p>用户详情页: {{ userId }}</p>
      <p>此页面需要进一步实现</p>
    </div>
  </div>
</template>

<style scoped>
</style>
