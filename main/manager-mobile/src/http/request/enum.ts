export enum ResultEnum {
  Success = 0, // Success
  Error = 400, // Error
  Unauthorized = 401, // Unauthorized
  Forbidden = 403, // Forbidden (formerly forbidden)
  NotFound = 404, // Not found (formerly notFound)
  MethodNotAllowed = 405, // Method not allowed (formerly methodNotAllowed)
  RequestTimeout = 408, // Request timeout (formerly requestTimeout)
  InternalServerError = 500, // Internal server error (formerly internalServerError)
  NotImplemented = 501, // Not implemented (formerly notImplemented)
  BadGateway = 502, // Bad gateway (formerly badGateway)
  ServiceUnavailable = 503, // Service unavailable (formerly serviceUnavailable)
  GatewayTimeout = 504, // Gateway timeout (formerly gatewayTimeout)
  HttpVersionNotSupported = 505, // HTTP version not supported (formerly httpVersionNotSupported)
  MixedContent = 600, // Mixed content (an HTTPS page requesting an HTTP API)
}
export enum ContentTypeEnum {
  JSON = 'application/json;charset=UTF-8',
  FORM_URLENCODED = 'application/x-www-form-urlencoded;charset=UTF-8',
  FORM_DATA = 'multipart/form-data;charset=UTF-8',
}
/**
 * Generate an error message for a status code
 * @param {number|string} status Status code
 * @returns {string} Error message
 */
export function ShowMessage(status: number | string): string {
  // These strings are displayed to users, not developer logs. Preserve the localized
  // fallbacks; TRANSLATION_NOTES.md provides the complete English status-message map.
  let message: string
  switch (status) {
    case 400:
      message = '请求错误(400)'
      break
    case 401:
      message = '未授权，请重新登录(401)'
      break
    case 403:
      message = '拒绝访问(403)'
      break
    case 404:
      message = '请求出错(404)'
      break
    case 408:
      message = '请求超时(408)'
      break
    case 500:
      message = '服务器错误(500)'
      break
    case 501:
      message = '服务未实现(501)'
      break
    case 502:
      message = '网络错误(502)'
      break
    case 503:
      message = '服务不可用(503)'
      break
    case 504:
      message = '网络超时(504)'
      break
    case 505:
      message = 'HTTP版本不受支持(505)'
      break
    case 600:
      message = '混合内容错误(600)'
      break
    default:
      message = `连接出错(${status})!`
  }
  return `${message}，请检查网络或联系管理员！`
}
