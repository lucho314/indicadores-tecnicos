"use client"

import { useState, useEffect, useRef, useCallback } from "react"
const API_BASE_URL = import.meta.env.VITE_API_URL  || "http://localhost:8000"
export interface WebSocketPositionData {
  symbol: string
  timestamp: string
  position: any
  balance: any
  current_price: number
  has_position: boolean
  error?: string
}

export const useBybitWebSocket = (symbol: string = "BTCUSDT") => {
  const [data, setData] = useState<WebSocketPositionData | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const getToken = useCallback(() => {
    return localStorage.getItem("trading-app-token")
  }, [])

  const connect = useCallback(() => {
    const token = getToken()
    
    if (!token) {
      setError("Token de autenticación no encontrado")
      setLoading(false)
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // Ya está conectado
    }

    try {
      const wsUrl = `ws://${API_BASE_URL}/ws/positions/${symbol}?token=${encodeURIComponent(token)}`
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        console.log(`🔌 WebSocket conectado para ${symbol}`)
        setIsConnected(true)
        setError(null)
        setLoading(false)
        reconnectAttempts.current = 0
      }

      wsRef.current.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data)
          setData(parsedData)
          
          if (parsedData.error) {
            setError(parsedData.error)
          } else {
            setError(null)
          }
        } catch (parseError) {
          console.error("Error parsing WebSocket data:", parseError)
          setError("Error al procesar datos del servidor")
        }
      }

      wsRef.current.onclose = (event) => {
        console.log(`🔌 WebSocket desconectado para ${symbol}`, event.code, event.reason)
        setIsConnected(false)
        setLoading(false)

        // Manejar códigos de error específicos
        if (event.code === 4001) {
          setError("Token de autenticación requerido")
        } else if (event.code === 4002 || event.code === 4003) {
          setError("Token inválido o expirado")
        } else if (event.code === 4000) {
          setError("Error en autenticación")
        } else if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          // Intentar reconectar si no fue un cierre normal
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          console.log(`🔄 Reintentando conexión en ${delay}ms (intento ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        }
      }

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error)
        setError("Error de conexión WebSocket")
        setLoading(false)
      }

    } catch (connectionError) {
      console.error("Error creating WebSocket connection:", connectionError)
      setError("No se pudo establecer la conexión WebSocket")
      setLoading(false)
    }
  }, [symbol, getToken])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "Desconexión manual")
      wsRef.current = null
    }

    setIsConnected(false)
    setData(null)
    setError(null)
    setLoading(false)
  }, [])

  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttempts.current = 0
    setLoading(true)
    setTimeout(connect, 1000)
  }, [connect, disconnect])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // Limpiar timeouts al desmontar
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    data,
    isConnected,
    loading,
    error,
    connect,
    disconnect,
    reconnect,
    // Propiedades de conveniencia
    hasPosition: data?.has_position || false,
    currentPrice: data?.current_price || 0,
    position: data?.position || null,
    balance: data?.balance || null,
    lastUpdate: data?.timestamp || null,
  }
}
