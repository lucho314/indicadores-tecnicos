import { useState, useEffect } from 'react'
import { indicatorsApi, PositionsResponse } from '../services/api'

export function usePositions() {
  const [positions, setPositions] = useState<PositionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPositions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await indicatorsApi.getPositions()
      setPositions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error obteniendo posiciones')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPositions()
  }, [])

  return {
    positions,
    loading,
    error,
    refetch: fetchPositions
  }
}
