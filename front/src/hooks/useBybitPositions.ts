"use client"

import { useState, useEffect } from "react"
import { getBybitPositions, type BybitPositionsResponse } from "../services/api"

export const useBybitPositions = (refreshInterval = 30000) => {
  const [data, setData] = useState<BybitPositionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPositions = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await getBybitPositions()
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al obtener posiciones")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPositions()

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchPositions, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  return {
    data,
    loading,
    error,
    refetch: fetchPositions,
  }
}
