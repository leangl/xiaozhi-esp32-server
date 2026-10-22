import type { Ref } from 'vue'
import { defineStore } from 'pinia'
import { ref } from 'vue'

// Supported language type
export type Language = 'zh_CN' | 'en' | 'zh_TW' | 'de' | 'vi' | 'pt_BR'

export interface LangStore {
  currentLang: Ref<Language>
  changeLang: (lang: Language) => void
}

export const useLangStore = defineStore(
  'lang',
  (): LangStore => {
    // Read the stored language setting, falling back to the default
    const savedLang = uni.getStorageSync('app_language') as Language | null
    const currentLang = ref<Language>(savedLang || 'zh_CN')

    // Switch languages
    const changeLang = (lang: Language) => {
      currentLang.value = lang
      // Save the language setting to local storage
      uni.setStorageSync('app_language', lang)
    }

    return {
      currentLang,
      changeLang,
    }
  },
  {
    persist: {
      key: 'lang',
      serializer: {
        serialize: state => JSON.stringify(state.currentLang),
        deserialize: value => ({ currentLang: JSON.parse(value) }),
      },
    },
  },
)
