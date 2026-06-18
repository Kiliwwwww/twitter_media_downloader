<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  currentPage: number
  totalPages: number
  total: number
}>()

const emit = defineEmits<{
  (e: 'page-change', page: number): void
}>()

const displayPages = computed(() => {
  const pages: number[] = []
  const maxDisplay = 5
  let start = Math.max(1, props.currentPage - Math.floor(maxDisplay / 2))
  let end = Math.min(props.totalPages, start + maxDisplay - 1)
  if (end - start + 1 < maxDisplay) {
    start = Math.max(1, end - maxDisplay + 1)
  }
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})
</script>

<template>
  <div v-if="totalPages > 1" class="pagination-wrapper">
    <div class="pagination">
      <button 
        class="page-btn" 
        :disabled="currentPage <= 1"
        @click="emit('page-change', currentPage - 1)"
      >
        ‹
      </button>
      <button 
        v-for="page in displayPages" 
        :key="page"
        class="page-btn"
        :class="{ active: page === currentPage }"
        @click="emit('page-change', page)"
      >
        {{ page }}
      </button>
      <button 
        class="page-btn" 
        :disabled="currentPage >= totalPages"
        @click="emit('page-change', currentPage + 1)"
      >
        ›
      </button>
    </div>
  </div>
</template>

<style scoped>
</style>
