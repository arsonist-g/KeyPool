<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type TokenItem, type PlatformInfo } from '../api'
import Pagination from '../components/Pagination.vue'

const tokens = ref<TokenItem[]>([])
const platforms = ref<PlatformInfo[]>([])
const loading = ref(true)
const showAdd = ref(false)
const form = ref({ name: '', selectedPlatforms: [] as string[] })
const submitting = ref(false)
const formError = ref('')
const copiedId = ref<number | null>(null)
const selectedIds = ref<Set<number>>(new Set())
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const allSelected = computed(() =>
  tokens.value.length > 0 && selectedIds.value.size === tokens.value.length
)

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(tokens.value.map(t => t.id))
  }
}

function toggleSelect(id: number) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

async function loadTokens() {
  loading.value = true
  try {
    const res = await api.getTokens(page.value, pageSize.value)
    tokens.value = res.items
    total.value = res.total
    selectedIds.value = new Set()
  } finally {
    loading.value = false
  }
}

function changePage(p: number) {
  page.value = p
  loadTokens()
}

async function addToken() {
  submitting.value = true
  formError.value = ''
  try {
    await api.createToken({ name: form.value.name, allowed_platforms: form.value.selectedPlatforms })
    form.value = { name: '', selectedPlatforms: [] }
    showAdd.value = false
    await loadTokens()
  } catch (e: any) {
    if (e?.status === 409) {
      formError.value = 'Token 名称已存在，请使用其他名称'
    } else {
      formError.value = '创建失败，请重试'
    }
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(token: TokenItem) {
  const newStatus = token.status === 'active' ? 'disabled' : 'active'
  await api.updateToken(token.id, { status: newStatus })
  await loadTokens()
}

async function deleteToken(token: TokenItem) {
  if (!confirm(`确认删除 Token "${token.name}"？`)) return
  await api.deleteToken(token.id)
  await loadTokens()
}

function copyToken(token: TokenItem) {
  navigator.clipboard.writeText(token.token_value)
  copiedId.value = token.id
  setTimeout(() => { copiedId.value = null }, 2000)
}

async function batchDelete() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确认删除选中的 ${selectedIds.value.size} 个 Token？`)) return
  await api.batchDeleteTokens([...selectedIds.value])
  await loadTokens()
}

async function batchEnable() {
  if (selectedIds.value.size === 0) return
  await api.batchUpdateTokens([...selectedIds.value], { status: 'active' })
  await loadTokens()
}

async function batchDisable() {
  if (selectedIds.value.size === 0) return
  await api.batchUpdateTokens([...selectedIds.value], { status: 'disabled' })
  await loadTokens()
}

async function loadPlatforms() {
  try {
    platforms.value = await api.getPlatforms()
  } catch { /* ignore */ }
}

function togglePlatform(name: string) {
  const idx = form.value.selectedPlatforms.indexOf(name)
  if (idx > -1) {
    form.value.selectedPlatforms.splice(idx, 1)
  } else {
    form.value.selectedPlatforms.push(name)
  }
}

function closeAdd() {
  showAdd.value = false
  form.value = { name: '', selectedPlatforms: [] }
  formError.value = ''
}

onMounted(() => {
  loadTokens()
  loadPlatforms()
})
</script>

<template>
  <div class="tokens-page">
    <div class="page-header">
      <h1>Token 分发</h1>
      <button class="btn-primary btn-fixed" @click="showAdd = true">创建 Token</button>
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
            <th>名称</th>
            <th>Token</th>
            <th>允许平台</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="token in tokens" :key="token.id">
            <td class="td-check">
              <input type="checkbox" :checked="selectedIds.has(token.id)" @change="toggleSelect(token.id)" />
            </td>
            <td class="cell-name">{{ token.name }}</td>
            <td class="cell-key">
              <span>{{ token.token_value.slice(0, 8) }}...</span>
              <button class="btn-copy" @click="copyToken(token)">
                {{ copiedId === token.id ? '已复制' : '复制' }}
              </button>
            </td>
            <td>
              <span v-for="p in token.allowed_platforms" :key="p" class="platform-tag">{{ p }}</span>
            </td>
            <td>
              <span class="status-badge" :class="token.status">{{ token.status }}</span>
            </td>
            <td class="cell-date">{{ new Date(token.created_at).toLocaleDateString() }}</td>
            <td class="cell-actions">
              <button class="btn-text" @click="toggleStatus(token)">
                {{ token.status === 'active' ? '禁用' : '启用' }}
              </button>
              <button class="btn-text btn-danger" @click="deleteToken(token)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="tokens.length === 0" class="empty">暂无 Token</p>
      <Pagination :page="page" :page-size="pageSize" :total="total" @update:page="changePage" />
    </div>

    <!-- 创建 Token 弹窗 -->
    <div v-if="showAdd" class="modal-overlay" @click.self="closeAdd">
      <div class="modal">
        <div class="modal-header">
          <h2>创建 Token</h2>
          <button class="modal-close" @click="closeAdd">&times;</button>
        </div>
        <form @submit.prevent="addToken">
          <div class="modal-body">
            <div v-if="formError" class="form-error">{{ formError }}</div>
            <div class="form-group">
              <label>名称</label>
              <input v-model="form.name" placeholder="如: 张三的token" class="input" required />
            </div>
            <div class="form-group">
              <label>允许平台</label>
              <div class="platform-select">
                <label v-for="p in platforms.filter(x => x.enabled)" :key="p.name" class="platform-option">
                  <input type="checkbox" :checked="form.selectedPlatforms.includes(p.name)" @change="togglePlatform(p.name)" />
                  <span>{{ p.name }}</span>
                </label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="closeAdd">取消</button>
            <button type="submit" class="btn-primary" :disabled="submitting || !form.name || form.selectedPlatforms.length === 0">
              {{ submitting ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '../styles/shared.css';

.cell-name {
  font-weight: 600;
}

.cell-date {
  color: var(--color-ink-muted-48);
  font-size: 13px;
}

.btn-copy {
  background: none;
  color: var(--color-primary);
  font-size: 12px;
  padding: 2px 6px;
  margin-left: 8px;
  border-radius: var(--rounded-xs);
}

.btn-copy:hover {
  background: var(--color-canvas-parchment);
}

.platform-tag {
  display: inline-block;
  padding: 2px 8px;
  margin-right: 4px;
  border-radius: var(--rounded-xs);
  background: var(--color-canvas-parchment);
  font-size: 12px;
  text-transform: capitalize;
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

.btn-batch-enable {
  background: var(--color-success);
  color: white;
}

.btn-batch-disable {
  background: var(--color-ink-muted-48);
  color: white;
}

.btn-batch-delete {
  background: var(--color-danger);
  color: white;
}

.th-check, .td-check {
  width: 40px;
  text-align: center;
}

input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.btn-fixed {
  min-width: 100px;
  text-align: center;
}

.platform-select {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.platform-option {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
  color: var(--color-ink);
  line-height: 1;
}

.platform-option input[type="checkbox"] {
  width: 14px;
  height: 14px;
  margin: 0;
}

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
  width: 440px;
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

.btn-secondary {
  padding: 8px 18px;
  border-radius: var(--rounded-pill);
  background: var(--color-canvas-parchment);
  color: var(--color-ink-muted-80);
  font-size: 14px;
}

.form-error {
  background: color-mix(in srgb, var(--color-danger) 10%, transparent);
  color: var(--color-danger);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--rounded-sm);
  font-size: 13px;
  margin-bottom: var(--spacing-md);
}
</style>
