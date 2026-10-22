import type { Ref } from 'vue'

interface IUseRequestOptions<T> {
  /** Whether to run immediately */
  immediate?: boolean
  /** Initial data */
  initialData?: T
}

interface IUseRequestReturn<T> {
  loading: Ref<boolean>
  error: Ref<boolean | Error>
  data: Ref<T | undefined>
  run: () => Promise<T | undefined>
}

/**
 * useRequest is a custom hook for asynchronous requests and responses.
 * @param func Asynchronous request function returning a Promise containing response data.
 * @param options Request options: {immediate, initialData}.
 * @param options.immediate Whether to request immediately; defaults to false.
 * @param options.initialData Initial data; defaults to undefined.
 * @returns {loading, error, data, run}: request loading state, error, response data, and a manual trigger.
 */
export default function useRequest<T>(
  func: () => Promise<IResData<T>>,
  options: IUseRequestOptions<T> = { immediate: false },
): IUseRequestReturn<T> {
  const loading = ref(false)
  const error = ref(false)
  const data = ref<T | undefined>(options.initialData) as Ref<T | undefined>
  const run = async () => {
    loading.value = true
    return func()
      .then((res) => {
        data.value = res.data
        error.value = false
        return data.value
      })
      .catch((err) => {
        error.value = err
        throw err
      })
      .finally(() => {
        loading.value = false
      })
  }

  options.immediate && run()
  return { loading, error, data, run }
}
