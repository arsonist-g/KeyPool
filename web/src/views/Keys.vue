<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type KeyItem, type PlatformInfo } from '../api'
import Pagination from '../components/Pagination.vue'

const keys = ref<KeyItem[]>([])
const platforms = ref<PlatformInfo[]>([])
const loading = ref(true)
const showImport = ref(false)
const importForm = ref({ platform: '', keysText: '' })
const importResult = ref<{ total: number; added: number; duplicates: number } | null>(null)
const submitting = ref(false)
const selectedIds = ref<Set<number>>(new Set())
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterPlatform = ref('')
const filterStatus = ref('')
const refreshingIds = ref<Set<number>>(new Set())

const quotaSupportedPlatforms = computed(() =>
  new Set(platforms.value.filter(p => p.quota_supported).map(p => p.name))
)

async function refreshQuota(key: KeyItem) {
  refreshingIds.value = new Set([...refreshingIds.value, key.id])
  try {
    const res = await api.getKeyQuota(key.id)
    if (res.supported && res.remaining !== null) {
      key.quota_remaining = res.remaining
      key.quota_updated_at = new Date().toISOString()
    }
  } finally {
    const s = new Set(refreshingIds.value)
    s.delete(key.id)
    refreshingIds.value = s
  }
}

async function refreshAllQuotas() {
  for (const key of keys.value) {
    refreshQuota(key)
  }
}

const allSelected = computed(() =>
  keys.value.length > 0 && selectedIds.value.size === keys.value.length
)

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(keys.value.map(k => k.id))
  }
}

function toggleSelect(id: number) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

async function loadKeys() {
  loading.value = true
  try {
    const res = await api.getKeys(page.value, pageSize.value, filterPlatform.value || undefined, filterStatus.value || undefined)
    keys.value = res.items
    total.value = res.total
    selectedIds.value = new Set()
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  loadKeys()
}

function applyFilter() {
  page.value = 1
  loadKeys()
}

async function loadPlatforms() {
  try {
    platforms.value = await api.getPlatforms()
    if (platforms.value.length > 0 && !importForm.value.platform) {
      importForm.value.platform = platforms.value.filter(p => p.enabled)[0]?.name || ''
    }
  } catch { /* ignore */ }
}

async function importKeys() {
  submitting.value = true
  importResult.value = null
  try {
    const lines = importForm.value.keysText.split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length === 0) return
    const allKeys = await api.getKeys(1, 9999, importForm.value.platform)
    const existingKeys = new Set(allKeys.items.map(k => k.api_key))
    const newKeys = lines.filter(k => !existingKeys.has(k))
    const duplicates = lines.length - newKeys.length
    let added = 0
    for (const key of newKeys) {
      try {
        await api.createKey({ platform: importForm.value.platform, api_key: key, weight: 1.0 })
        added++
      } catch { /* skip failed */ }
    }
    importResult.value = { total: lines.length, added, duplicates }
    if (added > 0) await loadKeys()
  } finally {
    submitting.value = false
  }
}

function closeImport() {
  showImport.value = false
  importForm.value.keysText = ''
  importResult.value = null
}

async function toggleStatus(key: KeyItem) {
  const newStatus = key.status === 'active' ? 'disabled' : 'active'
  await api.updateKey(key.id, { status: newStatus })
  await loadKeys()
}

async function deleteKey(key: KeyItem) {
  if (!confirm(`确认删除 ${key.platform} 的 Key？`)) return
  await api.deleteKey(key.id)
  await loadKeys()
}

function maskKey(k: string) {
  if (k.length <= 8) return '****'
  return k.slice(0, 4) + '****' + k.slice(-4)
}

async function batchDelete() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确认删除选中的 ${selectedIds.value.size} 个 Key？`)) return
  await api.batchDeleteKeys([...selectedIds.value])
  await loadKeys()
}

async function batchEnable() {
  if (selectedIds.value.size === 0) return
  await api.batchUpdateKeys([...selectedIds.value], { status: 'active' })
  await loadKeys()
}

async function batchDisable() {
  if (selectedIds.value.size === 0) return
  await api.batchUpdateKeys([...selectedIds.value], { status: 'disabled' })
  await loadKeys()
}

onMounted(() => {
  loadKeys()
  loadPlatforms()
})
</script>

<template>
  <div class="keys-page">
    <div class="page-header">
      <h1>Key 管理</h1>
      <button class="btn-primary" @click="showImport = true">批量导入</button>
    </div>

    <div class="filter-bar">
      <select v-model="filterPlatform" class="input filter-select" @change="applyFilter">
        <option value="">全部平台</option>
        <option v-for="p in platforms" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>
      <select v-model="filterStatus" class="input filter-select" @change="applyFilter">
        <option value="">全部状态</option>
        <option value="active">活跃</option>
        <option value="disabled">已禁用</option>
        <option value="exhausted">已耗尽</option>
      </select>
      <button class="btn-text" @click="refreshAllQuotas">刷新全部余额</button>
    </div>

    <div class="batch-bar">
      <span class="batch-info">{{ selectedIds.size > 0 ? `已选 ${selectedIds.size} 项` : '批量操作' }}</span>
      <button class="btn-batch btn-batch-enable" :disabled="selectedIds.size === 0" @click="batchEnable">批量启用</button>
      <button class="btn-batch btn-batch-disable" :disabled="selectedIds.size === 0" @click="batchDisable">批量禁用</button>
      <button class="btn-batch btn-batch-delete" :disabled="selectedIds.size === 0" @click="batchDelete">批量删除</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th class="th-check">
              <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
            </th>
            <th>平台</th>
            <th>API Key</th>
            <th>余额</th>
            <th>权重</th>
            <th>状态</th>
            <th>请求数</th>
            <th>失败数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="key in keys" :key="key.id">
            <td class="td-check">
              <input type="checkbox" :checked="selectedIds.has(key.id)" @change="toggleSelect(key.id)" />
            </td>
            <td class="cell-platform">{{ key.platform }}</td>
            <td class="cell-key">{{ maskKey(key.api_key) }}</td>
            <td class="cell-quota">
              <template v-if="quotaSupportedPlatforms.has(key.platform)">
                <span v-if="key.quota_remaining !== null" class="quota-value" :class="{ 'quota-low': key.quota_remaining < 0.2 }">
                  {{ (key.quota_remaining * 100).toFixed(0) }}%
                </span>
                <span v-else class="quota-na">未查询</span>
                <button class="btn-text btn-sm btn-refresh" :disabled="refreshingIds.has(key.id)" @click="refreshQuota(key)">
                  {{ refreshingIds.has(key.id) ? '...' : '↻' }}
                </button>
              </template>
              <span v-else class="quota-unsupported">不支持</span>
            </td>
            <td>{{ key.weight }}</td>
            <td>
              <span class="status-badge" :class="key.status">{{ key.status }}</span>
            </td>
            <td>{{ key.total_requests }}</td>
            <td>{{ key.failed_requests }}</td>
            <td class="cell-actions">
              <button class="btn-text" @click="toggleStatus(key)">
                {{ key.status === 'active' ? '禁用' : '启用' }}
              </button>
              <button class="btn-text btn-danger" @click="deleteKey(key)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="keys.length === 0" class="empty">暂无 Key</p>
      <Pagination :page="page" :page-size="pageSize" :total="total" @update:page="changePage" />
    </div>
    <div v-if="showImport" class="modal-overlay" @click.self="closeImport">
      <div class="modal">
        <div class="modal-header">
          <h2>批量导入 Key</h2>
          <button class="modal-close" @click="closeImport">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择平台</label>
            <select v-model="importForm.platform" class="input" required>
              <option value="" disabled>选择平台</option>
              <option v-for="p in platforms.filter(x => x.enabled)" :key="p.name" :value="p.name">
                {{ p.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>API Keys（每行一个）</label>
            <textarea v-model="importForm.keysText" class="input textarea" rows="10"
              placeholder="sk-abc123...&#10;sk-def456...&#10;sk-ghi789..."></textarea>
          </div>
          <div v-if="importResult" class="import-result">
            <p>导入完成：共 {{ importResult.total }} 个，成功 {{ importResult.added }} 个，重复跳过 {{ importResult.duplicates }} 个</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeImport">关闭</button>
          <button class="btn-primary" :disabled="submitting || !importForm.platform || !importForm.keysText.trim()" @click="importKeys">
            {{ submitting ? '导入中...' : '开始导入' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/shared.css';

.filter-bar {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.filter-select {
  min-width: 140px;
  padding: 8px 12px;
}

.cell-quota {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.quota-na {
  color: var(--color-ink-muted-48);
  font-size: 12px;
}

.quota-unsupported {
  color: var(--color-ink-muted-48);
  font-size: 12px;
  font-style: italic;
}

.quota-value {
  color: var(--color-success);
  font-weight: 600;
}

.quota-value.quota-low {
  color: var(--color-danger);
}

.btn-sm {
  font-size: 12px;
  padding: 2px 6px;
}

.btn-refresh {
  margin-left: 4px;
  opacity: 0.5;
  transition: opacity 0.15s;
}

.btn-refresh:hover:not(:disabled) {
  opacity: 1;
}

.btn-refresh:disabled {
  cursor: wait;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: var(--spacing-sm) var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.batch-info {
  font-size: 14px;
  color: var(--color-ink-muted-80);
  margin-right: auto;
}

.btn-batch {
  padding: 6px 14px;
  border-radius: var(--rounded-pill);
  font-size: 13px;
  font-weight: 400;
  transition: transform 0.1s, opacity 0.15s;
}

.btn-batch:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-batch:active:not(:disabled) {
  transform: scale(0.95);
}

.btn-batch-enable { background: var(--color-success); color: white; }
.btn-batch-disable { background: var(--color-ink-muted-48); color: white; }
.btn-batch-delete { background: var(--color-danger); color: white; }

.th-check, .td-check { width: 40px; text-align: center; }
input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-divider-soft);
}

.modal-header h2 { font-size: 17px; font-weight: 600; }

.modal-close {
  background: none;
  font-size: 24px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  line-height: 1;
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-divider-soft);
}

.form-group { margin-bottom: var(--spacing-md); }
.form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: var(--spacing-xs); color: var(--color-ink-muted-80); }

.textarea {
  width: 100%;
  resize: vertical;
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 13px;
  line-height: 1.5;
}

.btn-secondary {
  padding: 8px 18px;
  border-radius: var(--rounded-pill);
  background: var(--color-canvas-parchment);
  color: var(--color-ink-muted-80);
  font-size: 14px;
}

.import-result {
  background: var(--color-canvas-parchment);
  border-radius: var(--rounded-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: 13px;
  color: var(--color-ink-muted-80);
}
</style>
