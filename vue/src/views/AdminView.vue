<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import PageHeader from '../components/PageHeader.vue'
import LoadingState from '../components/LoadingState.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import i18n from '../utils/i18n'
import { ElMessage, ElMessageBox } from 'element-plus'

const t = (key: string, params: Record<string, any> = {}) => i18n.t(key, params)

const activeTab = ref('users')

// 用户管理
const users = ref<any[]>([])
const loadingUsers = ref(false)
const userPage = ref(1)
const userPageSize = ref(20)
const userTotal = ref(0)
const userSearch = ref('')
const showUserModal = ref(false)
const editingUser = ref<any>(null)
const savingUser = ref(false)

const userForm = reactive({
  username: '',
  password: '',
  nickname: '',
  email: '',
  role: 'user'
})

// 重置密码
const showPasswordModal = ref(false)
const resetPasswordUser = ref<any>(null)
const newPassword = ref('')
const resettingPassword = ref(false)

// 邀请码管理
const inviteCodes = ref<any[]>([])
const loadingCodes = ref(false)
const codePage = ref(1)
const codePageSize = ref(20)
const codeTotal = ref(0)

const userTotalPages = computed(() => Math.ceil(userTotal.value / userPageSize.value))
const codeTotalPages = computed(() => Math.ceil(codeTotal.value / codePageSize.value))

// 用户搜索防抖
let searchTimeout: ReturnType<typeof setTimeout> | null = null
const debounceUserSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchUsers(1)
  }, 300)
}

// 获取用户列表
const fetchUsers = async (page = 1) => {
  loadingUsers.value = true
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: userPageSize.value.toString()
    })
    if (userSearch.value) {
      params.append('keyword', userSearch.value)
    }
    
    const response = await fetch(`/api/admin/users?${params.toString()}`)
    if (response.ok) {
      const data = await response.json()
      users.value = data.data || []
      userTotal.value = data.total || 0
      userPage.value = data.page || 1
    } else if (response.status === 403) {
      ElMessage.error(t('admin.permissionDenied'))
      window.location.href = '/'
    }
  } catch (error) {
    ElMessage.error(t('admin.fetchUsersFailed'))
  } finally {
    loadingUsers.value = false
  }
}

// 打开添加用户弹窗
const openAddUserModal = () => {
  editingUser.value = null
  userForm.username = ''
  userForm.password = ''
  userForm.nickname = ''
  userForm.email = ''
  userForm.role = 'user'
  showUserModal.value = true
}

// 打开编辑用户弹窗
const openEditUserModal = (user: any) => {
  editingUser.value = user
  userForm.username = user.username
  userForm.password = ''
  userForm.nickname = user.nickname || ''
  userForm.email = user.email || ''
  userForm.role = user.role
  showUserModal.value = true
}

// 保存用户
const saveUser = async () => {
  if (!editingUser.value && (!userForm.username || !userForm.password)) {
    ElMessage.warning(t('admin.fillUsernamePassword'))
    return
  }
  
  savingUser.value = true
  try {
    let response
    if (editingUser.value) {
      // 编辑用户
      response = await fetch(`/api/admin/users/${editingUser.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nickname: userForm.nickname,
          email: userForm.email,
          role: userForm.role
        })
      })
    } else {
      // 创建用户
      response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: userForm.username,
          password: userForm.password,
          nickname: userForm.nickname,
          email: userForm.email,
          role: userForm.role
        })
      })
    }
    
    if (response.ok) {
      ElMessage.success(editingUser.value ? t('admin.userUpdated') : t('admin.userCreated'))
      showUserModal.value = false
      fetchUsers(userPage.value)
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('admin.operationFailed'))
    }
  } catch (error) {
    ElMessage.error(t('admin.operationFailed'))
  } finally {
    savingUser.value = false
  }
}

// 切换用户状态
const toggleUser = async (user: any) => {
  try {
    const response = await fetch(`/api/admin/users/${user.id}/toggle`, { method: 'POST' })
    if (response.ok) {
      const data = await response.json()
      ElMessage.success(data.message)
      fetchUsers(userPage.value)
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('admin.operationFailed'))
    }
  } catch (error) {
    ElMessage.error(t('admin.operationFailed'))
  }
}

// 删除用户
const deleteUser = async (user: any) => {
  try {
    await ElMessageBox.confirm(
      t('admin.deleteUserConfirm', { name: user.nickname || user.username }),
      t('admin.confirmDeleteTitle'),
      {
        confirmButtonText: t('admin.confirmDeleteButton'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    const response = await fetch(`/api/admin/users/${user.id}`, { method: 'DELETE' })
    if (response.ok) {
      ElMessage.success(t('admin.userDeleted'))
      fetchUsers(userPage.value)
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('admin.deleteFailed'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('admin.deleteFailed'))
    }
  }
}

// 打开重置密码弹窗
const openResetPasswordModal = (user: any) => {
  resetPasswordUser.value = user
  newPassword.value = ''
  showPasswordModal.value = true
}

// 重置密码
const resetPassword = async () => {
  if (!newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning(t('admin.passwordLengthError'))
    return
  }
  
  resettingPassword.value = true
  try {
    const response = await fetch(`/api/admin/users/${resetPasswordUser.value.id}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: newPassword.value })
    })
    
    if (response.ok) {
      ElMessage.success(t('admin.passwordReset'))
      showPasswordModal.value = false
    } else {
      const data = await response.json()
      ElMessage.error(data.error || t('admin.resetFailed'))
    }
  } catch (error) {
    ElMessage.error(t('admin.resetFailed'))
  } finally {
    resettingPassword.value = false
  }
}

// 获取邀请码列表
const fetchInviteCodes = async (page = 1) => {
  loadingCodes.value = true
  try {
    const response = await fetch(`/api/admin/invite-codes?page=${page}&per_page=${codePageSize.value}`)
    if (response.ok) {
      const data = await response.json()
      inviteCodes.value = data.data || []
      codeTotal.value = data.total || 0
      codePage.value = data.page || 1
    }
  } catch (error) {
    ElMessage.error(t('admin.fetchInviteCodesFailed'))
  } finally {
    loadingCodes.value = false
  }
}

// 生成邀请码
const generateInviteCodes = async (count: number) => {
  try {
    const response = await fetch(`/api/admin/invite-codes?count=${count}`, { method: 'POST' })
    if (response.ok) {
      const data = await response.json()
      ElMessage.success(data.message)
      fetchInviteCodes(codePage.value)
    }
  } catch (error) {
    ElMessage.error(t('admin.generateInviteCodeFailed'))
  }
}

// 复制邀请码
const copyCode = async (code: string) => {
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success(t('admin.copiedToClipboard'))
  } catch (error) {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = code
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(t('admin.copiedToClipboard'))
  }
}

// 删除邀请码
const deleteInviteCode = async (codeId: number) => {
  try {
    await ElMessageBox.confirm(
      t('admin.deleteInviteCodeConfirm'),
      t('admin.confirmDeleteTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    const response = await fetch(`/api/admin/invite-codes/${codeId}`, { method: 'DELETE' })
    if (response.ok) {
      ElMessage.success(t('admin.inviteCodeDeleted'))
      fetchInviteCodes(codePage.value)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('admin.deleteFailed'))
    }
  }
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString()
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <Navbar active-page="admin" />
  
  <div class="main-container" style="max-width: 1000px;">
    <PageHeader 
      :title="t('admin.title')" 
      :subtitle="t('admin.subtitle')"
      icon="<path d='M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 00-3-3.87'/><path d='M16 3.13a4 4 0 010 7.75'/>"
    />
    
    <!-- 标签切换 -->
    <div class="admin-tabs">
      <button 
        class="admin-tab" 
        :class="{ active: activeTab === 'users' }"
        @click="activeTab = 'users'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87"/>
          <path d="M16 3.13a4 4 0 010 7.75"/>
        </svg>
        {{ t('admin.userManagement') }}
      </button>
      <button 
        class="admin-tab" 
        :class="{ active: activeTab === 'invite' }"
        @click="activeTab = 'invite'; fetchInviteCodes()"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="4" width="20" height="16" rx="2"/>
          <path d="M2 8h20"/>
          <path d="M6 12h4"/>
          <path d="M14 12h4"/>
        </svg>
        {{ t('admin.inviteCodeManagement') }}
      </button>
    </div>
    
    <!-- 用户管理 -->
    <div v-if="activeTab === 'users'" class="table-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <div class="search-input-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
            <input 
              type="text" 
              class="search-input" 
              v-model="userSearch" 
              :placeholder="t('admin.searchPlaceholder')"
              @input="debounceUserSearch"
            >
          </div>
        </div>
        <div class="toolbar-right">
          <button class="add-btn" @click="openAddUserModal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {{ t('admin.addUser') }}
          </button>
        </div>
      </div>
      
      <LoadingState v-if="loadingUsers" />
      
      <EmptyState 
        v-else-if="users.length === 0" 
        :title="t('admin.noUsers')"
        :description="t('admin.noUsersDesc')"
      />
      
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>{{ t('admin.userColumn') }}</th>
            <th>{{ t('admin.roleColumn') }}</th>
            <th>{{ t('admin.statusColumn') }}</th>
            <th>{{ t('admin.twitterIdColumn') }}</th>
            <th>{{ t('admin.createdAtColumn') }}</th>
            <th>{{ t('admin.actionsColumn') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <div class="user-cell">
                <div class="user-avatar">
                  <img v-if="user.avatar_url" :src="user.avatar_url" :alt="user.nickname"
                       @error="$event.target.style.display='none'; $event.target.nextElementSibling.style.display='flex'" />
                  <span v-else class="avatar-fallback">{{ (user.nickname || user.username || '?').charAt(0).toUpperCase() }}</span>
                </div>
                <div class="user-info">
                  <div class="user-name">{{ user.nickname || user.username }}</div>
                  <div class="user-username">@{{ user.username }}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="role-badge" :class="user.role">{{ user.role === 'admin' ? t('admin.adminRole') : t('admin.normalUser') }}</span>
            </td>
            <td>
              <span class="status-badge" :class="user.is_active ? 'active' : 'inactive'">
                <span class="status-dot"></span>
                {{ user.is_active ? t('admin.active') : t('admin.inactive') }}
              </span>
            </td>
            <td>{{ user.twitter_id || '-' }}</td>
            <td>{{ formatTime(user.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button class="action-btn" :title="t('admin.editTooltip')" @click="openEditUserModal(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button class="action-btn" :title="t('admin.resetPasswordTooltip')" @click="openResetPasswordModal(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0110 0v4"/>
                  </svg>
                </button>
                <button class="action-btn" :title="user.is_active ? t('admin.disableTooltip') : t('admin.enableTooltip')" @click="toggleUser(user)">
                  <svg v-if="user.is_active" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                </button>
                <button class="action-btn danger" :title="t('admin.deleteTooltip')" @click="deleteUser(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <Pagination 
        v-if="userTotal > userPageSize"
        :current-page="userPage"
        :total-pages="userTotalPages"
        :total="userTotal"
        @page-change="fetchUsers"
      />
    </div>
    
    <!-- 邀请码管理 -->
    <div v-if="activeTab === 'invite'" class="table-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <h3 style="font-size: 16px; font-weight: 600; color: #1F2937;">{{ t('admin.inviteCodeList') }}</h3>
        </div>
        <div class="toolbar-right">
          <button class="add-btn" @click="generateInviteCodes(1)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {{ t('admin.generateInviteCode') }}
          </button>
          <button class="add-btn" style="background: linear-gradient(135deg, #10B981, #059669);" @click="generateInviteCodes(5)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            {{ t('admin.batchGenerate') }}
          </button>
        </div>
      </div>
      
      <LoadingState v-if="loadingCodes" />
      
      <EmptyState 
        v-else-if="inviteCodes.length === 0" 
        :title="t('admin.noInviteCodes')"
        :description="t('admin.noInviteCodesDesc')"
      />
      
      <div v-else>
        <div v-for="code in inviteCodes" :key="code.id" class="invite-code-item">
          <div class="invite-code-info">
            <div class="invite-code">{{ code.code }}</div>
            <div class="invite-code-meta">
              <span>{{ t('admin.creator', { name: code.creator_name }) }}</span>
              <span>{{ code.is_used ? t('admin.used') : t('admin.unused') }}</span>
              <span v-if="code.used_by_name">{{ t('admin.usedBy', { name: code.used_by_name }) }}</span>
              <span>{{ formatTime(code.created_at) }}</span>
            </div>
          </div>
          <div class="invite-code-actions">
            <button class="copy-btn" @click="copyCode(code.code)" :title="t('admin.copyTooltip')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              {{ t('admin.copy') }}
            </button>
            <button class="action-btn danger" :title="t('admin.deleteTooltip')" @click="deleteInviteCode(code.id)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </button>
          </div>
        </div>
        
        <Pagination 
          v-if="codeTotal > codePageSize"
          :current-page="codePage"
          :total-pages="codeTotalPages"
          :total="codeTotal"
          @page-change="fetchInviteCodes"
        />
      </div>
    </div>
  </div>
  
  <!-- 添加/编辑用户弹窗 -->
  <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">{{ editingUser ? t('admin.editUser') : t('admin.addUserTitle') }}</h3>
        <button class="modal-close" @click="showUserModal = false">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <div class="modal-form">
          <div class="form-group">
            <label class="form-label">{{ t('admin.usernameLabel') }}</label>
            <input 
              type="text" 
              class="form-input" 
              v-model="userForm.username"
              :placeholder="t('admin.usernamePlaceholder')"
              :disabled="!!editingUser"
            >
          </div>
          
          <div v-if="!editingUser" class="form-group">
            <label class="form-label">{{ t('admin.passwordLabel') }}</label>
            <input 
              type="password" 
              class="form-input" 
              v-model="userForm.password"
              :placeholder="t('admin.passwordPlaceholder')"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ t('admin.nicknameLabel') }}</label>
            <input 
              type="text" 
              class="form-input" 
              v-model="userForm.nickname"
              :placeholder="t('admin.optionalPlaceholder')"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ t('admin.emailLabel') }}</label>
            <input 
              type="email" 
              class="form-input" 
              v-model="userForm.email"
              :placeholder="t('admin.optionalPlaceholder')"
            >
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ t('admin.roleLabel') }}</label>
            <select class="form-select" v-model="userForm.role">
              <option value="user">{{ t('admin.normalUser') }}</option>
              <option value="admin">{{ t('admin.adminRole') }}</option>
            </select>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="modal-btn cancel" @click="showUserModal = false">{{ t('common.cancel') }}</button>
        <button class="modal-btn primary" @click="saveUser" :disabled="savingUser">
          {{ savingUser ? t('admin.saving') : t('admin.save') }}
        </button>
      </div>
    </div>
  </div>
  
  <!-- 重置密码弹窗 -->
  <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">{{ t('admin.resetPasswordTitle') }}</h3>
        <button class="modal-close" @click="showPasswordModal = false">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <p style="color: #6B7280; margin-bottom: 16px;">
          {{ t('admin.resetPasswordDesc', { name: resetPasswordUser?.nickname || resetPasswordUser?.username }) }}
        </p>
        <div class="modal-form">
          <div class="form-group">
            <label class="form-label">{{ t('admin.newPasswordLabel') }}</label>
            <input 
              type="password" 
              class="form-input" 
              v-model="newPassword"
              :placeholder="t('admin.newPasswordPlaceholder')"
            >
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="modal-btn cancel" @click="showPasswordModal = false">{{ t('common.cancel') }}</button>
        <button class="modal-btn primary" @click="resetPassword" :disabled="resettingPassword">
          {{ resettingPassword ? t('admin.resetting') : t('admin.resetPasswordButton') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>