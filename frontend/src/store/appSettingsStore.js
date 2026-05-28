import { reactive, computed } from 'vue'
import { getSettings, updateSettings } from '@/api/settingsApi'

const DEFAULT_TITLE = 'PFM Marketing'
const DEFAULT_COLOR = '#0099ff'

/**
 * Darkens a hex color by reducing its HSL lightness.
 * Used to derive the gradient end color from a single brand color.
 */
function darkenHex(hex, amount = 20) {
  const clean = hex.replace('#', '')
  if (clean.length !== 6) return hex
  const r = parseInt(clean.substring(0, 2), 16) / 255
  const g = parseInt(clean.substring(2, 4), 16) / 255
  const b = parseInt(clean.substring(4, 6), 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s, l = (max + min) / 2

  if (max === min) {
    h = s = 0
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
      case g: h = ((b - r) / d + 2) / 6; break
      case b: h = ((r - g) / d + 4) / 6; break
    }
  }

  l = Math.max(0, l - amount / 100)

  function hue2rgb(p, q, t) {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1 / 6) return p + (q - p) * 6 * t
    if (t < 1 / 2) return q
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
    return p
  }

  let rOut, gOut, bOut
  if (s === 0) {
    rOut = gOut = bOut = l
  } else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s
    const p = 2 * l - q
    rOut = hue2rgb(p, q, h + 1 / 3)
    gOut = hue2rgb(p, q, h)
    bOut = hue2rgb(p, q, h - 1 / 3)
  }

  const toHex = (x) => Math.round(x * 255).toString(16).padStart(2, '0')
  return `#${toHex(rOut)}${toHex(gOut)}${toHex(bOut)}`
}

function applyBrandVars(primaryColor) {
  const endColor = darkenHex(primaryColor, 20)
  const root = document.documentElement
  root.style.setProperty('--brand-primary', primaryColor)
  root.style.setProperty('--brand-gradient', `linear-gradient(135deg, ${primaryColor} 0%, ${endColor} 100%)`)
  root.style.setProperty('--brand-gradient-end', endColor)
}

const state = reactive({
  appTitle: DEFAULT_TITLE,
  primaryColor: DEFAULT_COLOR,
  loading: false,
  initialized: false,
})

export function useAppSettingsStore() {
  const brandGradient = computed(() => {
    const end = darkenHex(state.primaryColor, 20)
    return `linear-gradient(135deg, ${state.primaryColor} 0%, ${end} 100%)`
  })

  async function init() {
    if (state.loading) return
    state.loading = true
    try {
      const data = await getSettings()
      state.appTitle = data.title || DEFAULT_TITLE
      state.primaryColor = data.primary_color || DEFAULT_COLOR
      applyBrandVars(state.primaryColor)
      document.title = state.appTitle
      state.initialized = true
    } catch (e) {
      // Fall back to defaults — apply them so CSS vars are always set
      applyBrandVars(DEFAULT_COLOR)
    } finally {
      state.loading = false
    }
  }

  async function save(title, color) {
    const data = await updateSettings({ title, primary_color: color })
    state.appTitle = data.title
    state.primaryColor = data.primary_color
    applyBrandVars(data.primary_color)
    document.title = data.title
  }

  return {
    get appTitle() { return state.appTitle },
    get primaryColor() { return state.primaryColor },
    get loading() { return state.loading },
    get initialized() { return state.initialized },
    brandGradient,
    init,
    save,
  }
}
