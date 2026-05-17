import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('admin_token'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(adminKey: string) {
    const res = await api.login(adminKey)
    token.value = res.token
    localStorage.setItem('admin_token', res.token)
  }

  function logout() {
    token.value = null
    localStorage.removeItem('admin_token')
  }

  return { token, isAuthenticated, login, logout }
})
