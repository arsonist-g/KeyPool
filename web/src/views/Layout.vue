<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()

const navItems = [
  { path: '/', label: '概览', icon: 'dashboard' },
  { path: '/keys', label: 'Key 管理', icon: 'key' },
  { path: '/proxies', label: '代理池', icon: 'proxy' },
  { path: '/tokens', label: 'Token 分发', icon: 'token' },
  { path: '/stats', label: '用量统计', icon: 'stats' },
  { path: '/guide', label: '接入指南', icon: 'guide' },
]

const themeLabels = { system: '跟随系统', light: '浅色', dark: '深色' }

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
          <rect width="40" height="40" rx="10" fill="var(--color-primary)"/>
          <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle"
                fill="white" font-size="18" font-weight="600">KP</text>
        </svg>
        <span class="sidebar-title">KeyPool</span>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          {{ item.label }}
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <button class="theme-btn" @click="theme.cycleMode()">
          <span class="theme-icon">{{ theme.mode.value === 'dark' ? '&#9790;' : theme.mode.value === 'light' ? '&#9788;' : '&#9684;' }}</span>
          <span>{{ themeLabels[theme.mode.value] }}</span>
        </button>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  background: var(--color-canvas);
  border-right: 1px solid var(--color-divider-soft);
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg) 0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.sidebar-title {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
  letter-spacing: 0.231px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 var(--spacing-sm);
}

.nav-item {
  display: block;
  padding: 10px 16px;
  border-radius: var(--rounded-sm);
  color: var(--color-ink-muted-80);
  font-size: 14px;
  font-weight: 400;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--color-canvas-parchment);
}

.nav-item.active {
  background: var(--color-canvas-parchment);
  color: var(--color-primary);
  font-weight: 600;
}

.sidebar-footer {
  padding: 0 var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.theme-btn {
  width: 100%;
  padding: 8px 15px;
  border-radius: var(--rounded-sm);
  background: transparent;
  color: var(--color-ink-muted-48);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  transition: color 0.15s;
}

.theme-btn:hover {
  color: var(--color-primary);
}

.theme-icon {
  font-size: 16px;
}

.logout-btn {
  width: 100%;
  padding: 8px 15px;
  border-radius: var(--rounded-sm);
  background: transparent;
  color: var(--color-ink-muted-48);
  font-size: 14px;
  transition: color 0.15s;
}

.logout-btn:hover {
  color: var(--color-danger);
}

.main-content {
  flex: 1;
  margin-left: 220px;
  padding: var(--spacing-xl);
  min-height: 100vh;
}
</style>
