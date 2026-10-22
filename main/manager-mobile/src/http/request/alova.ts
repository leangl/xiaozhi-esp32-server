import type { uniappRequestAdapter } from '@alova/adapter-uniapp'
import type { IResponse } from './types'
import type { Language } from '@/store/lang'
import AdapterUniapp from '@alova/adapter-uniapp'
import { createAlova } from 'alova'
import { createServerTokenAuthentication } from 'alova/client'
import VueHook from 'alova/vue'
import { getEnvBaseUrl } from '@/utils'
import { toast } from '@/utils/toast'
import { ContentTypeEnum, ResultEnum, ShowMessage } from './enum'

// Language mapping for the Accept-language header
const langMap: Record<Language, string> = {
  zh_CN: 'zh-CN',
  en: 'en-US',
  zh_TW: 'zh-TW',
  de: 'de',
  vi: 'vi',
  pt_BR: 'pt-BR',
}

/**
 * Create a request instance
 */
const { onAuthRequired, onResponseRefreshToken } = createServerTokenAuthentication<
  typeof VueHook,
  typeof uniappRequestAdapter
>({
  refreshTokenOnError: {
    isExpired: (error) => {
      return error.response?.status === ResultEnum.Unauthorized
    },
    handler: async () => {
      try {
        // await authLogin();
      }
      catch (error) {
        // Switch to the login page
        await uni.reLaunch({ url: '/pages/login/index' })
        throw error
      }
    },
  },
})

/**
 * Alova request instance
 */
const alovaInstance = createAlova({
  baseURL: getEnvBaseUrl(),
  ...AdapterUniapp(),
  timeout: 5000,
  statesHook: VueHook,

  beforeRequest: onAuthRequired((method) => {
    // Read the latest baseURL dynamically on H5 to respect the user-configured server URL
    const currentBaseUrl = getEnvBaseUrl()
    if (currentBaseUrl !== method.baseURL) {
      method.baseURL = currentBaseUrl
    }

    // Check for mixed content (an HTTPS page requesting an HTTP API)
    const currentProtocol = typeof window !== 'undefined' && window.location.protocol
    const requestProtocol = method.baseURL?.split(':')[0]
    const currentLang = langMap[uni.getStorageSync('app_language') as Language || 'zh_CN']
    if (currentProtocol === 'https:' && requestProtocol === 'http') {
      // Localized UI fallback: "Cannot configure an HTTP URL; check the API address."
      const errorMessage = '无法配置http协议地址,请检查接口地址'
      throw new Error(errorMessage)
    }

    // Set the default Content-Type
    method.config.headers = {
      'Content-Type': ContentTypeEnum.JSON,
      'Accept': 'application/json, text/plain, */*',
      'Accept-language': currentLang,
      ...method.config.headers,
    }

    const { config } = method
    const ignoreAuth = config.meta?.ignoreAuth
    console.log('ignoreAuth===>', ignoreAuth)

    // Handle authentication
    if (!ignoreAuth) {
      const authInfo = JSON.parse(uni.getStorageSync('token') || '{}')
      if (!authInfo.token) {
        // Navigate to the login page
        uni.reLaunch({ url: '/pages/login/index' })
        // Preserve the localized login error; see TRANSLATION_NOTES.md.
        throw new Error('[请求错误]：未登录')
      }
      // Add the Authorization header
      method.config.headers.Authorization = `Bearer ${authInfo.token}`
    }

    // Handle dynamic domains
    if (config.meta?.domain) {
      method.baseURL = config.meta.domain
      console.log('Current domain', method.baseURL)
    }
  }),

  responded: onResponseRefreshToken((response, method) => {
    const { config } = method
    const { requestType } = config
    const {
      statusCode,
      data: rawData,
      errMsg,
    } = response as UniNamespace.RequestSuccessCallbackResult

    console.log(response)

    // Handle special request types (upload/download)
    if (requestType === 'upload' || requestType === 'download') {
      return response
    }

    // Handle HTTP status errors
    if (statusCode !== 200) {
      // Localized HTTP error fallback; numeric codes and formatting remain unchanged.
      const errorMessage = ShowMessage(statusCode) || `HTTP请求错误[${statusCode}]`
      console.error('errorMessage===>', errorMessage)
      toast.error(errorMessage)
      throw new Error(`${errorMessage}：${errMsg}`)
    }

    // Handle application errors
    const { code, msg, data } = rawData as IResponse
    if (code !== ResultEnum.Success) {
      // Keep the error prefix byte-for-byte: registration, recovery, and voiceprint handlers parse it.
      // Check whether the token has expired
      if (code === ResultEnum.Unauthorized) {
        // Clear the token and redirect to login
        uni.removeStorageSync('token')
        uni.reLaunch({ url: '/pages/login/index' })
        throw new Error(`请求错误[${code}]：${msg}`)
      }

      if (config.meta?.isExposeError) {
        return Promise.reject(msg)
      }

      if (config.meta?.toast !== false) {
        toast.warning(msg)
      }
      throw new Error(`请求错误[${code}]：${msg}`)
    }
    // Handle a successful response and return application data
    return data
  }),
})

export const http = alovaInstance
