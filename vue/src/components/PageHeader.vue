<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  subtitle?: string
}>()
</script>

<template>
  <div class="page-header">
    <div class="page-icon" v-if="icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="icon"></svg>
    </div>
    <div style="flex: 1;">
      <h1 class="page-title">{{ title }}</h1>
      <p class="page-subtitle" v-if="subtitle">{{ subtitle }}</p>
    </div>
    <slot></slot>
  </div>
</template>

<style scoped>
</style>
