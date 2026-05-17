<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api, type PlatformStats } from '../api'

const stats = ref<PlatformStats[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    stats.value = await api.getStats()
  } finally {
    loading.value = false
  }
})

const totalKeys = computed(() => stats.value.reduce((s, p) => s + p.total_keys, 0))
const activeKeys = computed(() => stats.value.reduce((s, p) => s + p.active_keys, 0))
const totalRequests = computed(() => stats.value.reduce((s, p) => s + p.total_requests, 0))
const activeSessions = computed(() => stats.value.reduce((s, p) => s + p.active_sessions, 0))
</script>

<template>
  <div class="dashboard">
    <h1>概览</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="summary-grid">
        <div class="summary-card">
          <span class="summary-value">{{ totalKeys }}</span>
          <span class="summary-label">总 Key 数</span>
        </div>
        <div class="summary-card">
          <span class="summary-value">{{ activeKeys }}</span>
          <span class="summary-label">活跃 Key</span>
        </div>
        <div class="summary-card">
          <span class="summary-value">{{ totalRequests }}</span>
          <span class="summary-label">总请求数</span>
        </div>
        <div class="summary-card">
          <span class="summary-value">{{ activeSessions }}</span>
          <span class="summary-label">活跃 Session</span>
        </div>
      </div>

      <h2 class="section-title">各平台状态</h2>
      <div class="platform-grid">
        <div v-for="p in stats" :key="p.platform" class="platform-card">
          <div class="platform-name">{{ p.platform }}</div>
          <div class="platform-stats">
            <div class="stat-row">
              <span>Key</span>
              <span>{{ p.active_keys }} / {{ p.total_keys }}</span>
            </div>
            <div class="stat-row">
              <span>请求</span>
              <span>{{ p.total_requests }}</span>
            </div>
            <div class="stat-row">
              <span>失败</span>
              <span>{{ p.failed_requests }}</span>
            </div>
            <div class="stat-row">
              <span>Session</span>
              <span>{{ p.active_sessions }}</span>
            </div>
          </div>
        </div>
      </div>

      <p v-if="stats.length === 0" class="empty">暂无平台数据</p>
    </template>
  </div>
</template>

<style scoped>
.dashboard h1 {
  margin-bottom: var(--spacing-xl);
}

.loading {
  color: var(--color-ink-muted-48);
  padding: var(--spacing-xxl) 0;
  text-align: center;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xxl);
}

.summary-card {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.summary-value {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.374px;
}

.summary-label {
  font-size: 14px;
  color: var(--color-ink-muted-48);
}

.section-title {
  margin-bottom: var(--spacing-md);
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--spacing-md);
}

.platform-card {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: var(--spacing-lg);
}

.platform-name {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  text-transform: capitalize;
}

.platform-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--color-ink-muted-80);
}

.empty {
  color: var(--color-ink-muted-48);
  text-align: center;
  padding: var(--spacing-xxl) 0;
}
</style>
