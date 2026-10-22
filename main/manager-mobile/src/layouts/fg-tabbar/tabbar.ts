/**
 * Tab bar state; storageSync restores the correct tab after a browser refresh
 * Use simple reactive state rather than global Pinia state
 */
export const tabbarStore = reactive({
  curIdx: uni.getStorageSync('app-tabbar-index') || 0,
  setCurIdx(idx: number) {
    this.curIdx = idx
    uni.setStorageSync('app-tabbar-index', idx)
  },
})
