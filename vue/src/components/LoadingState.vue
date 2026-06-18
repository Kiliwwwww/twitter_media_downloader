<script setup lang="ts">
import i18n from '../utils/i18n'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)
</script>

<template>
  <div style="text-align: center; padding: 40px;">
    <div class="spinner" style="margin: 0 auto; width: 32px; height: 32px; border-width: 3px; border-color: rgba(74, 108, 247, 0.3); border-top-color: #4A6CF7;"></div>
    <p style="margin-top: 16px; color: #9CA3AF;">{{ t('common.loadingState') }}</p>
  </div>
</template>

<style scoped>
</style>
