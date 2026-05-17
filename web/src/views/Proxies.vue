<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type ProxyItem } from '../api'
import Pagination from '../components/Pagination.vue'

const proxies = ref<ProxyItem[]>([])
const loading = ref(true)
const showImport = ref(false)
const importForm = ref({ proxiesText: '' })
const importResult = ref<{ total: number; added: number; duplicates: number } | null>(null)
const submitting = ref(false)
const selectedIds = ref<Set<number>>(new Set())
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const allSelected = computed(() =>
  proxies.value.length > 0 && selectedIds.value.size === proxies.value.length
)

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(proxies.value.map(p => p.id))
  }
}

function toggleSelect(id: number) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

async function loadProxies() {
  loading.value = true
  try {
    const res = await api.getProxies(page.value, pageSize.value)
    proxies.value = res.items
    total.value = res.total
    selectedIds.value = new Set()
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  loadProxies()
}

function parseProxyLine(line: string) {
  const trimmed = line.trim()
  if (!trimmed) return null
  // 格式: protocol://host:port 或 protocol://user:pass@host:port
  let protocol = ''
  let host = ''
  let port = 0
  let username = ''
  let password = ''

  const protoMatch = trimmed.match(/^(https?|socks5):\/\//)
  if (!protoMatch) return null
  protocol = protoMatch[1]
  let rest = trimmed.slice(protoMatch[0].length)

  const atIdx = rest.lastIndexOf('@')
  if (atIdx > -1) {
    const authPart = rest.slice(0, atIdx)
    rest = rest.slice(atIdx + 1)
    const [u, p] = authPart.split(':')
    username = u || ''
    password = p || ''
  }
  const parts = rest.split(':')
  if (parts.length >= 2) {
    host = parts[0]
    port = parseInt(parts[1], 10)
  }
  if (!host || !port || isNaN(port)) return null
  return { protocol, host, port, username: username || undefined, password: password || undefined }
}

async function importProxies() {
  submitting.value = true
  importResult.value = null
  try {
    const lines = importForm.value.proxiesText.split('\n').filter(l => l.trim())
    if (lines.length === 0) return
    const allProxies = await api.getProxies(1, 9999)
    const existing = new Set(allProxies.items.map(p => `${p.host}:${p.port}`))
    let added = 0
    let duplicates = 0
    for (const line of lines) {
      const parsed = parseProxyLine(line)
      if (!parsed) continue
      if (existing.has(`${parsed.host}:${parsed.port}`)) {
        duplicates++
        continue
      }
      try {
        await api.createProxy(parsed as any)
        added++
        existing.add(`${parsed.host}:${parsed.port}`)
      } catch (e: any) {
        if (e?.status === 409) {
          duplicates++
        }
      }
    }
    importResult.value = { total: lines.length, added, duplicates }
    if (added > 0) await loadProxies()
  } finally {
    submitting.value = false
  }
}

function closeImport() {
  showImport.value = false
  importForm.value.proxiesText = ''
  importResult.value = null
}

async function toggleStatus(proxy: ProxyItem) {
  const newStatus = proxy.status === 'active' ? 'disabled' : 'active'
  await api.updateProxy(proxy.id, { status: newStatus })
  await loadProxies()
}

async function deleteProxy(proxy: ProxyItem) {
  if (!confirm(`确认删除代理 ${proxy.host}:${proxy.port}？`)) return
  await api.deleteProxy(proxy.id)
  await loadProxies()
}

async function batchDelete() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确认删除选中的 ${selectedIds.value.size} 个代理？`)) return
  await api.batchDeleteProxies([...selectedIds.value])
  await loadProxies()
}

async function batchEnable() {
  if (selectedIds.value.size === 0) return
  await api.batchUpdateProxies([...selectedIds.value], { status: 'active' })
  await loadProxies()
}

async function batchDisable() {
  if (selectedIds.value.size === 0) return
  await api.batchUpdateProxies([...selectedIds.value], { status: 'disabled' })
  await loadProxies()
}

onMounted(loadProxies)
</script>

<template>
  <div class="proxies-page">
    <div class="page-header">
      <h1>代理池</h1>
      <button class="btn-primary" @click="showImport = true">批量导入</button>
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
            <th>协议</th>
            <th>地址</th>
            <th>端口</th>
            <th>认证</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="proxy in proxies" :key="proxy.id">
            <td class="td-check">
              <input type="checkbox" :checked="selectedIds.has(proxy.id)" @change="toggleSelect(proxy.id)" />
            </td>
            <td><span class="protocol-badge">{{ proxy.protocol.toUpperCase() }}</span></td>
            <td>{{ proxy.host }}</td>
            <td>{{ proxy.port }}</td>
            <td>{{ proxy.username ? '有' : '无' }}</td>
            <td>
              <span class="status-badge" :class="proxy.status">{{ proxy.status }}</span>
            </td>
            <td class="cell-actions">
              <button class="btn-text" @click="toggleStatus(proxy)">
                {{ proxy.status === 'active' ? '禁用' : '启用' }}
              </button>
              <button class="btn-text btn-danger" @click="deleteProxy(proxy)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="proxies.length === 0" class="empty">暂无代理</p>
      <Pagination :page="page" :page-size="pageSize" :total="total" @update:page="changePage" />
    </div>

    <!-- 批量导入弹窗 -->
    <div v-if="showImport" class="modal-overlay" @click.self="closeImport">
      <div class="modal">
        <div class="modal-header">
          <h2>批量导入代理</h2>
          <button class="modal-close" @click="closeImport">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>代理列表（每行一个，必须带协议头）</label>
            <textarea v-model="importForm.proxiesText" class="input textarea" rows="10"
              placeholder="http://host:port&#10;socks5://host:port&#10;http://user:pass@host:port&#10;https://user:pass@host:port"></textarea>
          </div>
          <div v-if="importResult" class="import-result">
            <p>导入完成：共 {{ importResult.total }} 行，成功 {{ importResult.added }} 个，重复跳过 {{ importResult.duplicates }} 个</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeImport">关闭</button>
          <button class="btn-primary" :disabled="submitting || !importForm.proxiesText.trim()" @click="importProxies">
            {{ submitting ? '导入中...' : '开始导入' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/shared.css';

.protocol-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--rounded-xs);
  background: var(--color-canvas-parchment);
  font-size: 12px;
  font-weight: 600;
  font-family: "SF Mono", "Fira Code", monospace;
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

.btn-batch:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-batch:active:not(:disabled) { transform: scale(0.95); }
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
