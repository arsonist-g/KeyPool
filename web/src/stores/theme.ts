import { ref } from 'vue'

export type ThemeMode = 'system' | 'light' | 'dark'

const STORAGE_KEY = 'theme_mode'

const mode = ref<ThemeMode>((localStorage.getItem(STORAGE_KEY) as ThemeMode) || 'system')

function getSystemDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyTheme() {
  const isDark = mode.value === 'dark' || (mode.value === 'system' && getSystemDark())
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
}

function setMode(m: ThemeMode) {
  mode.value = m
  localStorage.setItem(STORAGE_KEY, m)
  applyTheme()
}

function cycleMode() {
  const order: ThemeMode[] = ['system', 'light', 'dark']
  const idx = order.indexOf(mode.value)
  setMode(order[(idx + 1) % order.length])
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (mode.value === 'system') applyTheme()
})

applyTheme()

export function useThemeStore() {
  return { mode, setMode, cycleMode }
}
