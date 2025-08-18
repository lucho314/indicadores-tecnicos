"use client"

import { useState, useEffect, useCallback } from "react"
import { indicatorsApi, type IndicatorData, type IndicatorsFilters, type ApiResponse } from "../services/api"

interface UseIndicatorsReturn {
  data: IndicatorData[]
  loading: boolean
  error: string | null
  total: number
  totalPages: number
  currentPage: number
  refetch: () => void
  updateFilters: (filters: IndicatorsFilters) => void
}

export function useIndicators(initialFilters: IndicatorsFilters = {}): UseIndicatorsReturn {
  const [data, setData] = useState<IndicatorData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [filters, setFilters] = useState<IndicatorsFilters>({
    page: 1,
    limit: 10,
    ...initialFilters,
  })

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response: ApiResponse<IndicatorData> = await indicatorsApi.getIndicators(filters)
      setData(response.data)
      setTotal(response.total)
      setTotalPages(response.totalPages)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar los datos")
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const refetch = useCallback(() => {
    fetchData()
  }, [fetchData])

  const updateFilters = useCallback((newFilters: IndicatorsFilters) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: newFilters.page || 1 }))
  }, [])

  return {
    data,
    loading,
    error,
    total,
    totalPages,
    currentPage: filters.page || 1,
    refetch,
    updateFilters,
  }
}
