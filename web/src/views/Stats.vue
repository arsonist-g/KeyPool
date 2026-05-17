<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api, type PlatformStats, type QuotaOverviewItem } from '../api'

const stats = ref<PlatformStats[]>([])
const quotaOverview = ref<QuotaOverviewItem[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [s, q] = await Promise.all([api.getStats(), api.getQuotaOverview()])
    stats.value = s
    quotaOverview.value = q
  } finally {
    loading.value = false
  }
})

function errorRate(p: PlatformStats): string {
  if (p.total_requests === 0) return '0%'
  return ((p.failed_requests / p.total_requests) * 100).toFixed(1) + '%'
}

function errorRateNum(p: PlatformStats): number {
  if (p.total_requests === 0) return 0
  return (p.failed_requests / p.total_requests) * 100
}

const totalRequests = computed(() => stats.value.reduce((s, p) => s + p.total_requests, 0))
const totalFailed = computed(() => stats.value.reduce((s, p) => s + p.failed_requests, 0))
const overallErrorRate = computed(() => {
  if (totalRequests.value === 0) return '0%'
  return ((totalFailed.value / totalRequests.value) * 100).toFixed(1) + '%'
})

const maxRequests = computed(() => Math.max(...stats.value.map(p => p.total_requests), 1))

function requestBarWidth(p: PlatformStats): string {
  return (p.total_requests / maxRequests.value * 100) + '%'
}

function quotaColorClass(remaining: number): string {
  if (remaining < 0.2) return 'quota-fill-danger'
  if (remaining < 0.5) return 'quota-fill-warning'
  return 'quota-fill-good'
}
</script>

<template>
  <div class="stats-page">
    <h1>用量统计</h1>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="overview-bar">
        <div class="overview-item">
          <span class="overview-label">总请求</span>
          <span class="overview-value">{{ totalRequests }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">总失败</span>
          <span class="overview-value">{{ totalFailed }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">总错误率</span>
          <span class="overview-value">{{ overallErrorRate }}</span>
        </div>
      </div>

      <div v-if="stats.length > 0" class="charts-section">
        <div class="chart-card">
          <h3>请求分布</h3>
          <div class="bar-chart">
            <div v-for="p in stats" :key="p.platform + '-req'" class="bar-row">
              <span class="bar-label">{{ p.platform }}</span>
              <div class="bar-track">
                <div class="bar-fill bar-fill-primary" :style="{ width: requestBarWidth(p) }"></div>
              </div>
              <span class="bar-value">{{ p.total_requests }}</span>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <h3>错误率</h3>
          <div class="bar-chart">
            <div v-for="p in stats" :key="p.platform + '-err'" class="bar-row">
              <span class="bar-label">{{ p.platform }}</span>
              <div class="bar-track">
                <div class="bar-fill bar-fill-danger" :style="{ width: errorRateNum(p) + '%' }"></div>
              </div>
              <span class="bar-value">{{ errorRate(p) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="quotaOverview.length > 0" class="charts-section charts-section-full">
        <div class="chart-card">
          <h3>各平台余额概览</h3>
          <div class="quota-platforms">
            <div v-for="item in quotaOverview" :key="item.platform" class="quota-platform-block">
              <div class="quota-platform-header">
                <span class="quota-platform-name">{{ item.platform }}</span>
                <span v-if="item.avg_remaining !== null" class="quota-platform-avg">
                  平均 {{ (item.avg_remaining * 100).toFixed(0) }}%
                </span>
                <span v-else class="quota-platform-avg quota-no-data">暂无数据</span>
              </div>
              <div v-if="item.keys.length > 0" class="quota-keys-bar">
                <div v-for="k in item.keys" :key="k.id" class="quota-key-segment"
                  :style="{ width: (100 / item.keys.length) + '%' }">
                  <div class="quota-key-fill" :class="quotaColorClass(k.remaining)"
                    :style="{ height: (k.remaining * 100) + '%' }"></div>
                </div>
              </div>
              <div v-else class="quota-empty">暂无已查询的 Key</div>
            </div>
          </div>
        </div>
      </div>

      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>平台</th>
              <th>总 Key</th>
              <th>活跃 Key</th>
              <th>总请求</th>
              <th>失败请求</th>
              <th>错误率</th>
              <th>活跃 Session</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in stats" :key="p.platform">
              <td class="cell-platform">{{ p.platform }}</td>
              <td>{{ p.total_keys }}</td>
              <td>{{ p.active_keys }}</td>
              <td>{{ p.total_requests }}</td>
              <td>{{ p.failed_requests }}</td>
              <td>{{ errorRate(p) }}</td>
              <td>{{ p.active_sessions }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="stats.length === 0" class="empty">暂无统计数据</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
@import '../styles/shared.css';

.stats-page h1 {
  margin-bottom: var(--spacing-xl);
}

.overview-bar {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.overview-item {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: var(--spacing-lg) var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex: 1;
}

.overview-label {
  font-size: 12px;
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.overview-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.28px;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.chart-card {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: var(--spacing-lg);
}

.chart-card h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-muted-80);
  margin-bottom: var(--spacing-md);
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.bar-row {
  display: grid;
  grid-template-columns: 72px 1fr 56px;
  align-items: center;
  gap: var(--spacing-sm);
}

.bar-label {
  font-size: 13px;
  font-weight: 600;
  text-transform: capitalize;
  color: var(--color-ink-muted-80);
}

.bar-track {
  height: 24px;
  background: var(--color-canvas-parchment);
  border-radius: var(--rounded-xs);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: var(--rounded-xs);
  transition: width 0.4s ease;
  min-width: 2px;
}

.bar-fill-primary {
  background: var(--color-primary);
}

.bar-fill-danger {
  background: var(--color-danger);
}

.bar-value {
  font-size: 13px;
  text-align: right;
  color: var(--color-ink-muted-80);
  font-variant-numeric: tabular-nums;
}

.charts-section-full {
  grid-template-columns: 1fr;
}

.quota-platforms {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.quota-platform-block {
  background: var(--color-canvas-parchment);
  border-radius: var(--rounded-sm);
  padding: var(--spacing-md);
}

.quota-platform-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.quota-platform-name {
  font-size: 14px;
  font-weight: 600;
  text-transform: capitalize;
}

.quota-platform-avg {
  font-size: 12px;
  color: var(--color-ink-muted-80);
  font-variant-numeric: tabular-nums;
}

.quota-no-data {
  color: var(--color-ink-muted-48);
  font-style: italic;
}

.quota-keys-bar {
  display: flex;
  gap: 2px;
  height: 48px;
  align-items: flex-end;
}

.quota-key-segment {
  height: 100%;
  display: flex;
  align-items: flex-end;
}

.quota-key-fill {
  width: 100%;
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height 0.3s ease;
}

.quota-fill-good { background: var(--color-success); }
.quota-fill-warning { background: #f5a623; }
.quota-fill-danger { background: var(--color-danger); }

.quota-empty {
  font-size: 12px;
  color: var(--color-ink-muted-48);
  text-align: center;
  padding: var(--spacing-sm) 0;
}
</style>
