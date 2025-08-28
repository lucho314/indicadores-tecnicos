import { useState, useCallback } from 'react'
import { tradingStrategiesApi, type ExpireStrategyResponse } from '../services/api'

interface UseExpireStrategyReturn {
  expireStrategy: (strategyId: string) => Promise<ExpireStrategyResponse | null>
  loading: boolean
  error: string | null
  lastResponse: ExpireStrategyResponse | null
}

export const useExpireStrategy = (): UseExpireStrategyReturn => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResponse, setLastResponse] = useState<ExpireStrategyResponse | null>(null)

  const expireStrategy = useCallback(async (
    strategyId: string
  ): Promise<ExpireStrategyResponse | null> => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await tradingStrategiesApi.expireStrategy(strategyId)
      setLastResponse(response)
      
      if (!response.success) {
        setError(response.message || 'Failed to expire strategy')
        return null
      }
      
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      console.error('Error expiring strategy:', err)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    expireStrategy,
    loading,
    error,
    lastResponse
  }
}

export default useExpireStrategy