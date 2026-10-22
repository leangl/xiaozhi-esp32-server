import { getEnvBaseUrl } from './index'
import { toast } from './toast'

/**
 * Example of using the file upload hook
 * @example
 * const { loading, error, data, progress, run } = useUpload<IUploadResult>(
 *   uploadUrl,
 *   {},
 *   {
 *     maxSize: 5, // Maximum 5 MB
 *     sourceType: ['album'], // Allow selection only from the album
 *         onProgress: (p) => console.log(`Upload progress: ${p}%`),
 *         onSuccess: (res) => console.log('Upload succeeded', res),
 *         onError: (err) => console.error('Upload failed', err),
 *   },
 * )
 */

/**
 * File upload URL configuration
 */
export const uploadFileUrl = {
  /** User avatar upload URL (reads the current effective BaseURL dynamically) */
  get USER_AVATAR() {
    return `${getEnvBaseUrl()}/user/avatar`
  },
}

/**
 * Generic file upload function (accepts a file path directly)
 * @param url Upload URL
 * @param filePath Local file path
 * @param formData Additional form data
 * @param options Upload options
 */
export function useFileUpload<T = string>(url: string, filePath: string, formData: Record<string, any> = {}, options: Omit<UploadOptions, 'sourceType' | 'sizeType' | 'count'> = {}) {
  return useUpload<T>(
    url,
    formData,
    {
      ...options,
      sourceType: ['album'],
      sizeType: ['original'],
    },
    filePath,
  )
}

export interface UploadOptions {
  /** Maximum image count; defaults to 1 */
  count?: number
  /** Selected image sizes: original or compressed */
  sizeType?: Array<'original' | 'compressed'>
  /** Image source: album or camera */
  sourceType?: Array<'album' | 'camera'>
  /** File size limit in MB */
  maxSize?: number //
  /** Upload progress callback */
  onProgress?: (progress: number) => void
  /** Upload success callback */
  onSuccess?: (res: Record<string, any>) => void
  /** Upload failure callback */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** Upload completion callback (on success or failure) */
  onComplete?: () => void
}

/**
 * File upload hook
 * @template T Response data type on successful upload
 * @param url Upload URL
 * @param formData Additional form data
 * @param options Upload options
 * @returns Upload state and controls
 */
export function useUpload<T = string>(url: string, formData: Record<string, any> = {}, options: UploadOptions = {},
  /** Pass a file path directly to skip the picker */
  directFilePath?: string) {
  /** Upload-in-progress state */
  const loading = ref(false)
  /** Upload error state */
  const error = ref(false)
  /** Response data after a successful upload */
  const data = ref<T>()
  /** Upload progress (0-100) */
  const progress = ref(0)

  /** Destructure upload options and set defaults */
  const {
    /** Maximum image count */
    count = 1,
    /** Selected image sizes */
    sizeType = ['original', 'compressed'],
    /** Image source */
    sourceType = ['album', 'camera'],
    /** File size limit (MB) */
    maxSize = 10,
    /** Progress callback */
    onProgress,
    /** Success callback */
    onSuccess,
    /** Failure callback */
    onError,
    /** Completion callback */
    onComplete,
  } = options

  /**
   * Check whether the file exceeds the size limit
   * @param size File size in bytes
   * @returns Whether the size check passes
   */
  const checkFileSize = (size: number) => {
    const sizeInMB = size / 1024 / 1024
    if (sizeInMB > maxSize) {
      toast.warning(`文件大小不能超过${maxSize}MB`)
      return false
    }
    return true
  }
  /**
   * Trigger file selection and upload
   * Choose the picker for the current platform:
   * - WeChat mini-programs use chooseMedia
   * - Other platforms use chooseImage
   */
  const run = () => {
    if (directFilePath) {
      // Use the supplied file path directly
      loading.value = true
      progress.value = 0
      uploadFile<T>({
        url,
        tempFilePath: directFilePath,
        formData,
        data,
        error,
        loading,
        progress,
        onProgress,
        onSuccess,
        onError,
        onComplete,
      })
      return
    }

    // #ifdef MP-WEIXIN
    // Use chooseMedia in WeChat mini-programs
    uni.chooseMedia({
      count,
      mediaType: ['image'], // Images only
      sourceType,
      success: (res) => {
        const file = res.tempFiles[0]
        // Check the file size limit
        if (!checkFileSize(file.size))
          return

        // Start uploading
        loading.value = true
        progress.value = 0
        uploadFile<T>({
          url,
          tempFilePath: file.tempFilePath,
          formData,
          data,
          error,
          loading,
          progress,
          onProgress,
          onSuccess,
          onError,
          onComplete,
        })
      },
      fail: (err) => {
        console.error('Failed to select media:', err)
        error.value = true
        onError?.(err)
      },
    })
    // #endif

    // #ifndef MP-WEIXIN
    // Use chooseImage outside WeChat mini-programs
    uni.chooseImage({
      count,
      sizeType,
      sourceType,
      success: (res) => {
        console.log('Image selection succeeded:', res)

        // Start uploading
        loading.value = true
        progress.value = 0
        uploadFile<T>({
          url,
          tempFilePath: res.tempFilePaths[0],
          formData,
          data,
          error,
          loading,
          progress,
          onProgress,
          onSuccess,
          onError,
          onComplete,
        })
      },
      fail: (err) => {
        console.error('Failed to select an image:', err)
        error.value = true
        onError?.(err)
      },
    })
    // #endif
  }

  return { loading, error, data, progress, run }
}

/**
 * File upload options interface
 * @template T Response data type on successful upload
 */
interface UploadFileOptions<T> {
  /** Upload URL */
  url: string
  /** Temporary file path */
  tempFilePath: string
  /** Additional form data */
  formData: Record<string, any>
  /** Response data after a successful upload */
  data: Ref<T | undefined>
  /** Upload error state */
  error: Ref<boolean>
  /** Upload-in-progress state */
  loading: Ref<boolean>
  /** Upload progress (0-100) */
  progress: Ref<number>
  /** Upload progress callback */
  onProgress?: (progress: number) => void
  /** Upload success callback */
  onSuccess?: (res: Record<string, any>) => void
  /** Upload failure callback */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** Upload completion callback */
  onComplete?: () => void
}

/**
 * Perform the file upload
 * @template T Response data type on successful upload
 * @param options Upload options
 */
function uploadFile<T>({
  url,
  tempFilePath,
  formData,
  data,
  error,
  loading,
  progress,
  onProgress,
  onSuccess,
  onError,
  onComplete,
}: UploadFileOptions<T>) {
  try {
    // Create the upload task
    const uploadTask = uni.uploadFile({
      url,
      filePath: tempFilePath,
      name: 'file', // Form key for the file
      formData,
      header: {
        // On H5, let the browser set Content-Type and handle multipart encoding
        // #ifndef H5
        'Content-Type': 'multipart/form-data',
        // #endif
      },
      // Ensure the file name is valid
      success: (uploadFileRes) => {
        console.log('File upload succeeded:', uploadFileRes)
        try {
          // Parse response data
          const { data: _data } = JSON.parse(uploadFileRes.data)
          // Upload succeeded
          data.value = _data as T
          onSuccess?.(_data)
        }
        catch (err) {
          // Response parsing error
          console.error('Failed to parse the upload response:', err)
          error.value = true
          onError?.(new Error('Failed to parse the upload response'))
        }
      },
      fail: (err) => {
        // Upload request failed
        console.error('File upload failed:', err)
        error.value = true
        onError?.(err)
      },
      complete: () => {
        // Run on both success and failure
        loading.value = false
        onComplete?.()
      },
    })

    // Listen for upload progress
    uploadTask.onProgressUpdate((res) => {
      progress.value = res.progress
      onProgress?.(res.progress)
    })
  }
  catch (err) {
    // Failed to create the upload task
    console.error('Failed to create the upload task:', err)
    error.value = true
    loading.value = false
    onError?.(new Error('Failed to create the upload task'))
  }
}
