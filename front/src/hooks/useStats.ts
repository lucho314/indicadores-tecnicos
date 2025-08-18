"use client"

import { useState, useEffect } from "react"
import { indicatorsApi } from "../services/api"

interface Stats {
  totalSymbols: number
  avgBtcPrice: number
  avgEthPrice: number
  avgBnbPrice: number
  avgBtcRsi: number
  avgEthRsi: number
  avgBnbRsi: number
  avgRsi: number
  activeSignals: number
  btcPriceChange: number
  btcRsiChange: number
  ethPriceChange: number
  ethRsiChange: number
  bnbPriceChange: number
  bnbRsiChange: number
  priceChange: number
  rsiChange: number,
  llmSignals: number
}

export function useStats() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await indicatorsApi.getStats()
        setStats(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar estadísticas")
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  return { stats, loading, error }
}
