<script setup lang="ts">
import { computed } from 'vue'
import i18n from '../utils/i18n'

const props = defineProps<{
  title?: string
  description?: string
}>()

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)
const displayTitle = computed(() => props.title || t('common.emptyState'))
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M20 12V8H6a2 2 0 01-2-2c0-1.1.9-2 2-2h12v4"/>
        <path d="M4 6v12c0 1.1.9 2 2 2h14v-4"/>
        <path d="M18 12a2 2 0 000 4h4v-4h-4z"/>
      </svg>
    </div>
    <h3 class="empty-title">{{ displayTitle }}</h3>
    <p class="empty-desc" v-if="description">{{ description }}</p>
    <slot></slot>
  </div>
</template>

<style scoped>
</style>
