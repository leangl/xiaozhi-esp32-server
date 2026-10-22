import type { UserInfo } from '@/api/auth'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getUserInfo as _getUserInfo,
} from '@/api/auth'

// Initialize state
const userInfoState: UserInfo & { avatar?: string, token?: string } = {
  id: 0,
  username: '',
  realName: '',
  email: '',
  mobile: '',
  status: 0,
  superAdmin: 0,
  avatar: '/static/images/default-avatar.png',
  token: '',
}

export const useUserStore = defineStore(
  'userInfo',
  () => {
    // Define user information
    const userInfo = ref<UserInfo & { avatar?: string, token?: string }>({ ...userInfoState })
    // Set user information
    const setUserInfo = (val: UserInfo & { avatar?: string, token?: string }) => {
      console.log('Setting user information', val)
      // Use the default avatar when none is provided
      if (!val.avatar) {
        val.avatar = userInfoState.avatar
      }
      else {
        val.avatar = 'https://oss.laf.run/ukw0y1-site/avatar.jpg?feige'
      }
      userInfo.value = val
    }
    const setUserAvatar = (avatar: string) => {
      userInfo.value.avatar = avatar
      console.log('Setting user avatar', avatar)
      console.log('userInfo', userInfo.value)
    }
    // Delete user information
    const removeUserInfo = () => {
      userInfo.value = { ...userInfoState }
      uni.removeStorageSync('userInfo')
      uni.removeStorageSync('token')
    }
    /**
     * Get user information
     */
    const getUserInfo = async () => {
      const userData = await _getUserInfo()
      setUserInfo(userData)
      return userData
    }
    /**
     * Sign out and delete user information
     */
    const logout = async () => {
      removeUserInfo()
    }

    return {
      userInfo,
      getUserInfo,
      setUserInfo,
      setUserAvatar,
      logout,
      removeUserInfo,
    }
  },
  {
    persist: {
      key: 'userInfo',
      serializer: {
        serialize: state => JSON.stringify(state.userInfo),
        deserialize: value => ({ userInfo: JSON.parse(value) }),
      },
    },
  },
)
