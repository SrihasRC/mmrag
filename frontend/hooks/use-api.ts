import { useState, useCallback, useEffect } from 'react'
import { ApiError } from '@/lib/api'

export interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export interface UseApiActions<T> {
  execute: (...args: any[]) => Promise<T>
  reset: () => void
  setData: (data: T | null) => void
}

export type UseApiReturn<T> = UseApiState<T> & UseApiActions<T>

/**
 * Hook for managing API call state (loading, error, data)
 * @param apiFunction - The API function to call
 * @param immediate - Whether to call the function immediately on mount
 */
export function useApi<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  immediate: boolean = false
): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (...args: any[]): Promise<T> => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await apiFunction(...args)
      setData(result)
      return result
    } catch (err) {
      const errorMessage = err instanceof ApiError 
        ? err.message 
        : err instanceof Error 
        ? err.message 
        : 'An unexpected error occurred'
      
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFunction])

  const reset = useCallback(() => {
    setData(null)
    setLoading(false)
    setError(null)
  }, [])

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, [immediate, execute])

  return {
    data,
    loading,
    error,
    execute,
    reset,
    setData,
  }
}

/**
 * Hook for managing multiple API calls with individual state
 */
export function useMultipleApi<T extends Record<string, any>>(
  apiFunctions: { [K in keyof T]: (...args: any[]) => Promise<T[K]> }
): { [K in keyof T]: UseApiReturn<T[K]> } {
  const results = {} as { [K in keyof T]: UseApiReturn<T[K]> }

  for (const key in apiFunctions) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    results[key] = useApi(apiFunctions[key])
  }

  return results
}

/**
 * Hook for managing optimistic updates
 */
export function useOptimisticApi<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  optimisticUpdate?: (currentData: T | null, ...args: any[]) => T | null
): UseApiReturn<T> & { executeOptimistic: (...args: any[]) => Promise<T> } {
  const api = useApi(apiFunction)

  const executeOptimistic = useCallback(async (...args: any[]): Promise<T> => {
    // Apply optimistic update immediately
    if (optimisticUpdate) {
      const optimisticData = optimisticUpdate(api.data, ...args)
      api.setData(optimisticData)
    }

    try {
      // Execute the actual API call
      const result = await api.execute(...args)
      return result
    } catch (error) {
      // Revert optimistic update on error
      // Note: This is a simple revert - in practice you might want to store the previous state
      api.reset()
      throw error
    }
  }, [api, optimisticUpdate])

  return {
    ...api,
    executeOptimistic,
  }
}

/**
 * Hook for managing paginated API calls
 */
export interface UsePaginatedApiOptions {
  pageSize?: number
  immediate?: boolean
}

export interface PaginatedData<T> {
  items: T[]
  totalCount: number
  currentPage: number
  totalPages: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}

export function usePaginatedApi<T>(
  apiFunction: (page: number, pageSize: number, ...args: any[]) => Promise<PaginatedData<T>>,
  options: UsePaginatedApiOptions = {}
) {
  const { pageSize = 10, immediate = false } = options
  const [currentPage, setCurrentPage] = useState(1)
  
  const api = useApi(
    useCallback(
      (...args: any[]) => apiFunction(currentPage, pageSize, ...args),
      [apiFunction, currentPage, pageSize]
    ),
    immediate
  )

  const goToPage = useCallback((page: number) => {
    setCurrentPage(page)
  }, [])

  const nextPage = useCallback(() => {
    if (api.data?.hasNextPage) {
      setCurrentPage(prev => prev + 1)
    }
  }, [api.data?.hasNextPage])

  const previousPage = useCallback(() => {
    if (api.data?.hasPreviousPage) {
      setCurrentPage(prev => prev - 1)
    }
  }, [api.data?.hasPreviousPage])

  const refresh = useCallback((...args: any[]) => {
    return api.execute(...args)
  }, [api])

  return {
    ...api,
    currentPage,
    pageSize,
    goToPage,
    nextPage,
    previousPage,
    refresh,
  }
}
