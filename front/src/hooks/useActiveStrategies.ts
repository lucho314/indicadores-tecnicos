import { useState, useEffect, useCallback } from 'react'
import { tradingStrategiesApi, type TradingStrategy, type ActiveStrategiesResponse } from '../services/api'

interface UseActiveStrategiesReturn {
  strategies: TradingStrategy[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  getStrategyBySymbol: (symbol: string) => TradingStrategy | undefined
}

export const useActiveStrategies = (): UseActiveStrategiesReturn => {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStrategies = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response: ActiveStrategiesResponse = await tradingStrategiesApi.getActiveStrategies()
      
      if (response.success) {
        // Filtrar para asegurar que solo hay una estrategia por par
        const uniqueStrategies = response.strategies.reduce((acc, strategy) => {
          const existingIndex = acc.findIndex(s => s.symbol === strategy.symbol)
          if (existingIndex === -1) {
            acc.push(strategy)
          } else {
            // Mantener la estrategia más reciente
            if (new Date(strategy.created_at) > new Date(acc[existingIndex].created_at)) {
              acc[existingIndex] = strategy
            }
          }
          return acc
        }, [] as TradingStrategy[])
        
        setStrategies(uniqueStrategies)
      } else {
        setError('Failed to fetch strategies')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      console.error('Error fetching active strategies:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const getStrategyBySymbol = useCallback((symbol: string): TradingStrategy | undefined => {
    return strategies.find(strategy => strategy.symbol === symbol)
  }, [strategies])

  useEffect(() => {
    fetchStrategies()
  }, [])

  return {
    strategies,
    loading,
    error,
    refetch: fetchStrategies,
    getStrategyBySymbol
  }
}

export default useActiveStrategies