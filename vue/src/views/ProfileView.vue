<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import i18n from '../utils/i18n'
import { ElMessage } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const profile = reactive({
  id: null as number | null,
  username: '',
  nickname: '',
  email: '',
  twitter_id: '',
  avatar_url: '',
  role: 'user'
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const savingProfile = ref(false)
const savingTwitter = ref(false)
const savingPassword = ref(false)
const fetchingAvatar = ref(false)

const fetchProfile = async () => {
  try {
    const response = await fetch('/api/profile')
    if (response.ok) {
      const data = await response.json()
      Object.assign(profile, data)
    } else if (response.status === 401) {
      window.location.href = '/login'
    }
  } catch (error) {
    console.error('Fetch profile failed:', error)
  }
}

const saveProfile = async () => {
  savingProfile.value = true
  try {
    const response = await fetch('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nickname: profile.nickname,
        email: profile.email
      })
    })
    
    if (response.ok) {
      ElMessage.success(t('profile.profileSaved'))
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('profile.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('profile.saveFailed'))
  } finally {
    savingProfile.value = false
  }
}

const saveTwitterId = async () => {
  savingTwitter.value = true
  try {
    const response = await fetch('/api/profile/twitter-id', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        twitter_id: profile.twitter_id
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.avatar_url) {
        profile.avatar_url = data.avatar_url
      }
      ElMessage.success(t('profile.twitterIdSaved'))
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('profile.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('profile.saveFailed'))
  } finally {
    savingTwitter.value = false
  }
}

const fetchAvatar = async () => {
  if (!profile.twitter_id) return
  
  fetchingAvatar.value = true
  try {
    const response = await fetch(`/api/avatar/${encodeURIComponent(profile.twitter_id)}`)
    if (response.ok) {
      const data = await response.json()
      if (data.avatar_url) {
        profile.avatar_url = data.avatar_url
        // 同时更新到后端
        await fetch('/api/profile/twitter-id', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ twitter_id: profile.twitter_id })
        })
        ElMessage.success(t('profile.avatarUpdated'))
      } else {
        ElMessage.warning(t('profile.avatarNotFound'))
      }
    }
  } catch (error) {
    ElMessage.error(t('profile.fetchAvatarFailed'))
  } finally {
    fetchingAvatar.value = false
  }
}

const changePassword = async () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    ElMessage.warning(t('profile.fillAllPasswordFields'))
    return
  }
  
  if (passwordForm.newPassword.length < 6) {
    ElMessage.warning(t('profile.passwordLengthError'))
    return
  }
  
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning(t('profile.passwordMismatch'))
    return
  }
  
  savingPassword.value = true
  try {
    const response = await fetch('/api/profile/password', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        old_password: passwordForm.oldPassword,
        new_password: passwordForm.newPassword,
        confirm_password: passwordForm.confirmPassword
      })
    })
    
    if (response.ok) {
      ElMessage.success(t('profile.passwordChanged'))
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('profile.passwordChangeFailed'))
    }
  } catch (error) {
    ElMessage.error(t('profile.passwordChangeFailed'))
  } finally {
    savingPassword.value = false
  }
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <Navbar active-page="profile" />
  
  <div class="main-container" style="max-width: 700px;">
    <PageHeader 
      :title="t('profile.title')" 
      :subtitle="t('profile.subtitle')"
      icon="<path d='M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2'/><circle cx='12' cy='7' r='4'/>"
    />
    
    <!-- 头像和基本信息 -->
    <div class="profile-card">
      <div class="avatar-section">
        <div class="avatar-wrapper">
          <img v-if="profile.avatar_url" :src="profile.avatar_url" :alt="profile.nickname"
               @error="$event.target.style.display='none'; $event.target.nextElementSibling.style.display='flex'" />
          <span v-else class="avatar-fallback">{{ (profile.nickname || profile.username || '?').charAt(0).toUpperCase() }}</span>
        </div>
        <div class="avatar-info">
          <h3>{{ profile.nickname || profile.username }}</h3>
          <p>@{{ profile.username }}</p>
          <span class="role-tag" :class="profile.role">{{ profile.role === 'admin' ? t('profile.admin') : t('profile.user') }}</span>
        </div>
      </div>
      
      <h3 class="profile-card-title">
        <el-icon><User /></el-icon>
        {{ t('profile.basicInfo') }}
      </h3>
      
      <div class="profile-form">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {{ t('profile.nickname') }}
            </label>
            <input 
              type="text" 
              class="form-input" 
              v-model="profile.nickname"
              :placeholder="t('profile.nicknamePlaceholder')"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              {{ t('profile.email') }}
            </label>
            <input 
              type="email" 
              class="form-input" 
              v-model="profile.email"
              :placeholder="t('profile.emailPlaceholder')"
            >
          </div>
        </div>
        
        <button 
          class="save-btn"
          :disabled="savingProfile"
          @click="saveProfile"
        >
          <span v-if="savingProfile" class="spinner"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          {{ savingProfile ? t('profile.savingProfile') : t('profile.saveProfile') }}
        </button>
      </div>
    </div>
    
    <!-- 推特ID配置 -->
    <div class="profile-card">
      <h3 class="profile-card-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
        </svg>
        {{ t('profile.twitterConfig') }}
      </h3>
      
      <div class="profile-form">
        <div class="form-group">
          <label class="form-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            {{ t('profile.twitterUsername') }}
          </label>
          <div class="twitter-input-row">
            <input 
              type="text" 
              class="form-input" 
              v-model="profile.twitter_id"
              :placeholder="t('profile.twitterPlaceholder')"
            >
            <button 
              class="fetch-avatar-btn"
              :disabled="fetchingAvatar || !profile.twitter_id"
              @click="fetchAvatar"
            >
              <svg v-if="fetchingAvatar" class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
              </svg>
              {{ fetchingAvatar ? t('profile.fetchingAvatar') : t('profile.fetchAvatar') }}
            </button>
          </div>
          <div class="form-hint">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
            </svg>
            {{ t('profile.avatarHint') }}
          </div>
        </div>
        
        <button 
          class="save-btn"
          :disabled="savingTwitter"
          @click="saveTwitterId"
        >
          <span v-if="savingTwitter" class="spinner"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          {{ savingTwitter ? t('profile.savingTwitter') : t('profile.saveTwitterId') }}
        </button>
      </div>
    </div>
    
    <!-- 修改密码 -->
    <div class="profile-card">
      <h3 class="profile-card-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
        {{ t('profile.changePassword') }}
      </h3>
      
      <div class="profile-form">
        <div class="form-group">
          <label class="form-label">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
            {{ t('profile.currentPassword') }}
          </label>
          <input 
            type="password" 
            class="form-input" 
            v-model="passwordForm.oldPassword"
            :placeholder="t('profile.currentPasswordPlaceholder')"
          >
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
              {{ t('profile.newPassword') }}
            </label>
            <input 
              type="password" 
              class="form-input" 
              v-model="passwordForm.newPassword"
              :placeholder="t('profile.newPasswordPlaceholder')"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
              {{ t('profile.confirmPassword') }}
            </label>
            <input 
              type="password" 
              class="form-input" 
              v-model="passwordForm.confirmPassword"
              :placeholder="t('profile.confirmPasswordPlaceholder')"
            >
          </div>
        </div>
        
        <button 
          class="save-btn"
          :disabled="savingPassword"
          @click="changePassword"
        >
          <span v-if="savingPassword" class="spinner"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          {{ savingPassword ? t('profile.savingPassword') : t('profile.savePassword') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>