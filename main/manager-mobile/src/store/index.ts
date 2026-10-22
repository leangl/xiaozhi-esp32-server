import { createPinia } from 'pinia'
import { createPersistedState } from 'pinia-plugin-persistedstate' // Persistent state

const store = createPinia()
store.use(
  createPersistedState({
    storage: {
      getItem: uni.getStorageSync,
      setItem: uni.setStorageSync,
    },
  }),
)

export default store

export * from './config'
export * from './plugin'
export * from './provider'
export * from './speedPitch'
// Re-export modules
export * from './user'
