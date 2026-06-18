import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface User {
  id: number
  username: string
  nickname: string
  email: string
  twitter_id: string
  avatar_url: string
  role: string
  is_active: boolean
  created_at: string
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  
  async function fetchUser() {
    loading.value = true
    try {
      const response = await fetch('/api/auth/me')
      if (response.ok) {
        user.value = await response.json()
      } else {
        user.value = null
      }
    } catch (error) {
      user.value = null
    } finally {
      loading.value = false
    }
  }
  
  async function logout() {
    try {
      const response = await fetch('/api/auth/logout', { method: 'POST' })
      if (response.ok) {
        user.value = null
        window.location.href = '/login'
      }
    } catch (error) {
      console.error('退出失败:', error)
    }
  }
  
  return {
    user,
    loading,
    isLoggedIn,
    isAdmin,
    fetchUser,
    logout
  }
})
