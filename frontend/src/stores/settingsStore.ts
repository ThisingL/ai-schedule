import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '../api'

export const useSettingsStore = defineStore('settings', () => {
  const categories = ref<string[]>([])
  const loaded = ref(false)

  async function fetchSettings() {
    try {
      const { data } = await settingsApi.getAll()
      if (data.categories) {
        try {
          const cats = JSON.parse(data.categories)
          if (Array.isArray(cats)) categories.value = cats
        } catch {}
      }
      loaded.value = true
    } catch {}
  }

  return { categories, loaded, fetchSettings }
})
