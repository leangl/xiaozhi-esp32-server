<script setup lang="ts">
import { onHide, onLaunch, onShow } from '@dcloudio/uni-app'
import { onMounted, watch } from 'vue'
import { usePageAuth } from '@/hooks/usePageAuth'
import { t } from '@/i18n'
import { useConfigStore } from '@/store'
import { useLangStore } from '@/store/lang'
import 'abortcontroller-polyfill/dist/abortcontroller-polyfill-only'

usePageAuth()

const configStore = useConfigStore()
const langStore = useLangStore()

onLaunch(() => {
  console.log('App Launch')
  // Fetch public configuration
  configStore.fetchPublicConfig().catch((error) => {
    console.error('Failed to fetch public configuration:', error)
  })
})
onShow(() => {
  console.log('App Show')
  // Defer with setTimeout to ensure the tab bar is initialized
  setTimeout(() => {
    updateTabBarText()
  }, 100)
})

// Update tab bar labels dynamically
function updateTabBarText() {
  try {
    // Set the home tab label
    uni.setTabBarItem({
      index: 0,
      text: t('tabBar.home'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set the home tab label:', err)
      },
    })

    // Set the provisioning tab label
    uni.setTabBarItem({
      index: 1,
      text: t('tabBar.deviceConfig'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set the provisioning tab label:', err)
      },
    })

    // Set the settings tab label
    uni.setTabBarItem({
      index: 2,
      text: t('tabBar.settings'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set the settings tab label:', err)
      },
    })
  }
  catch (error) {
    console.log('Failed to update tab bar labels:', error)
  }
}
// Listen for language changes
onMounted(() => {
  // Update tab bar labels automatically when the language changes
  watch(() => langStore.currentLang, () => {
    console.log('Language changed; updating tab bar labels')
    // Update tab bar labels immediately after switching languages
    updateTabBarText()
  })
})

onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss">
swiper,
scroll-view {
  flex: 1;
  height: 100%;
  overflow: hidden;
}

image {
  width: 100%;
  height: 100%;
  vertical-align: middle;
}
</style>
