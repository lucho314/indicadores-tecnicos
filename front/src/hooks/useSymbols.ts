"use client"

import { useState, useEffect } from "react"
import { indicatorsApi } from "../services/api"

export function useSymbols() {
  const [symbols, setSymbols] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await indicatorsApi.getSymbols()
        setSymbols(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar símbolos")
      } finally {
        setLoading(false)
      }
    }

    fetchSymbols()
  }, [])

  return { symbols, loading, error }
}
