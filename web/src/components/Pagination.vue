<script setup lang="ts">
defineProps<{
  page: number
  pageSize: number
  total: number
}>()

const emit = defineEmits<{
  (e: 'update:page', page: number): void
}>()

function totalPages(total: number, pageSize: number) {
  return Math.max(1, Math.ceil(total / pageSize))
}
</script>

<template>
  <div v-if="total > pageSize" class="pagination">
    <button class="page-btn" :disabled="page <= 1" @click="emit('update:page', page - 1)">上一页</button>
    <span class="page-info">{{ page }} / {{ totalPages(total, pageSize) }}</span>
    <button class="page-btn" :disabled="page >= totalPages(total, pageSize)" @click="emit('update:page', page + 1)">下一页</button>
    <span class="page-total">共 {{ total }} 条</span>
  </div>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
}

.page-btn {
  padding: 6px 14px;
  border-radius: var(--rounded-pill);
  background: var(--color-canvas-parchment);
  color: var(--color-ink-muted-80);
  font-size: 13px;
  transition: background 0.15s;
}

.page-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: var(--color-ink-muted-80);
  font-variant-numeric: tabular-nums;
}

.page-total {
  font-size: 13px;
  color: var(--color-ink-muted-48);
}
</style>
