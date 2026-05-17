<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const adminKey = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(adminKey.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="10" fill="var(--color-primary)"/>
          <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle"
                fill="white" font-size="18" font-weight="600">KP</text>
        </svg>
      </div>
      <h1>KeyPool</h1>
      <p class="login-subtitle">API Key 池管理面板</p>
      <form @submit.prevent="handleLogin" class="login-form">
        <input
          v-model="adminKey"
          type="password"
          placeholder="输入 Admin Key"
          class="login-input"
          autofocus
        />
        <p v-if="error" class="login-error">{{ error }}</p>
        <button type="submit" class="login-btn" :disabled="loading || !adminKey">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-canvas-parchment);
}

.login-card {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: 48px 40px;
  width: 100%;
  max-width: 380px;
  text-align: center;
}

.login-logo {
  margin-bottom: var(--spacing-lg);
}

.login-card h1 {
  font-size: 28px;
  letter-spacing: -0.28px;
  margin-bottom: var(--spacing-xs);
}

.login-subtitle {
  color: var(--color-ink-muted-48);
  font-size: 14px;
  margin-bottom: var(--spacing-xl);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.login-input {
  width: 100%;
  padding: 12px 20px;
  border-radius: var(--rounded-pill);
  border: 1px solid var(--color-hairline);
  font-size: 17px;
  background: var(--color-canvas);
  transition: border-color 0.2s;
}

.login-input:focus {
  border-color: var(--color-primary);
}

.login-error {
  color: var(--color-danger);
  font-size: 14px;
}

.login-btn {
  width: 100%;
  padding: 12px 22px;
  border-radius: var(--rounded-pill);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: 17px;
  font-weight: 400;
  transition: transform 0.1s;
}

.login-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
