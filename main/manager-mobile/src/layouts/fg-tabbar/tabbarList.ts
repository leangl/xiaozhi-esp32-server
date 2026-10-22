import type { TabBar } from '@uni-helper/vite-plugin-uni-pages'

type FgTabBarItem = TabBar['list'][0] & {
  icon: string
  iconType: 'uiLib' | 'unocss' | 'iconfont'
}

/**
 * Tab bar strategies; see tabbar.md for details
 * 0: 'NO_TABBAR' `No tab bar`
 * 1: 'NATIVE_TABBAR' `Fully native tab bar`
 * 2: 'CUSTOM_TABBAR_WITH_CACHE' `Cached custom tab bar`
 * 3: 'CUSTOM_TABBAR_WITHOUT_CACHE' `Uncached custom tab bar`
 *
 * Restart after changing this file; otherwise pages.json will be stale and cause errors
 */
export const TABBAR_MAP = {
  NO_TABBAR: 0,
  NATIVE_TABBAR: 1,
  CUSTOM_TABBAR_WITH_CACHE: 2,
  CUSTOM_TABBAR_WITHOUT_CACHE: 3,
}
// TODO: Select the tab bar strategy here
export const selectedTabbarStrategy = TABBAR_MAP.NATIVE_TABBAR

// For selectedTabbarStrategy==NATIVE_TABBAR(1), specify iconPath and selectedIconPath
// For selectedTabbarStrategy==CUSTOM_TABBAR(2,3), specify icon and iconType
// For selectedTabbarStrategy==NO_TABBAR(0), tabbarList is unused
export const tabbarList: FgTabBarItem[] = [
  {
    iconPath: 'static/tabbar/robot.png',
    selectedIconPath: 'static/tabbar/robot_activate.png',
    pagePath: 'pages/index/index',
    text: '首页',
    icon: 'home',
    // Set iconType to uiLib when using icons from the UI framework
    iconType: 'uiLib',
  },
  {
    iconPath: 'static/tabbar/network.png',
    selectedIconPath: 'static/tabbar/network_activate.png',
    pagePath: 'pages/device-config/index',
    text: '配网',
    icon: 'i-carbon-network-3',
    iconType: 'uiLib',
  },
  {
    iconPath: 'static/tabbar/system.png',
    selectedIconPath: 'static/tabbar/system_activate.png',
    pagePath: 'pages/settings/index',
    text: '系统',
    icon: 'i-carbon-settings',
    iconType: 'uiLib',
  },
]

// NATIVE_TABBAR(1) and CUSTOM_TABBAR_WITH_CACHE(2) require tab caching
export const cacheTabbarEnable = selectedTabbarStrategy === TABBAR_MAP.NATIVE_TABBAR
  || selectedTabbarStrategy === TABBAR_MAP.CUSTOM_TABBAR_WITH_CACHE

const _tabbar: TabBar = {
  // Only WeChat mini-programs support custom; App and H5 ignore it
  custom: selectedTabbarStrategy === TABBAR_MAP.CUSTOM_TABBAR_WITH_CACHE,
  color: '#e6e6e6',
  selectedColor: '#667dea',
  backgroundColor: '#fff',
  borderStyle: 'black',
  height: '50px',
  fontSize: '10px',
  iconWidth: '24px',
  spacing: '3px',
  list: tabbarList as unknown as TabBar['list'],
}

// 0 and 1 require bottom tab bar configuration to use caching
export const tabBar = cacheTabbarEnable ? _tabbar : undefined
