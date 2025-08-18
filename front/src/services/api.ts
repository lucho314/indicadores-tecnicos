import axios from "axios"

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("CZECAC")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("trading-app-user")
      window.location.href = "/login"
    }
    return Promise.reject(error)
  },
)

export interface IndicatorData {
  id: number
  timestamp: string
  symbol: string
  interval_tf: string
  price: number
  rsi: number
  sma: number
  adx: number
  macd: number
  macd_signal: number
  macd_hist: number
  bb_upper: number
  bb_middle: number
  bb_lower: number
  signal?: boolean
  raw_data?: string
  created_at: string
}

export interface ApiResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
  totalPages: number
}

export interface IndicatorsFilters {
  symbol?: string
  interval?: string
  search?: string
  page?: number
  limit?: number
  startDate?: string
  endDate?: string
}

export interface Position {
  symbol: string
  side: string
  size: number
  avgPrice: number
  markPrice: number
  unrealisedPnl: number
  leverage: string
  positionStatus: string
  createdTime: string
  updatedTime: string
}

export interface PositionsResponse {
  success: boolean
  totalOpenPositions: number
  positions: {
    BTCUSDT: Position | null
    ETHUSDT: Position | null
    BNBUSDT: Position | null
  }
  timestamp: string
  error?: string
}

// Mock data fallback
const mockIndicators: IndicatorData[] = [
  {
    id: 1,
    timestamp: "2025-08-16 15:14:58.096545",
    symbol: "BTC/USD",
    interval_tf: "4h",
    price: 60000.0,
    rsi: 43.58,
    sma: 117818.93,
    adx: 23.73,
    macd: -532.21,
    macd_signal: -267.31,
    macd_hist: -264.9,
    bb_upper: 123557.96,
    bb_middle: 119400.1,
    bb_lower: 115242.24,
    created_at: "2025-08-16 15:15:00.546506",
  },
  {
    id: 2,
    timestamp: "2025-08-16 11:14:58.096545",
    symbol: "ETH/USD",
    interval_tf: "4h",
    price: 2800.0,
    rsi: 65.23,
    sma: 2750.45,
    adx: 31.45,
    macd: 45.67,
    macd_signal: 38.21,
    macd_hist: 7.46,
    bb_upper: 2890.34,
    bb_middle: 2800.12,
    bb_lower: 2709.9,
    created_at: "2025-08-16 11:15:00.546506",
  },
  {
    id: 3,
    timestamp: "2025-08-16 07:14:58.096545",
    symbol: "BTC/USD",
    interval_tf: "1h",
    price: 59800.0,
    rsi: 38.92,
    sma: 59950.23,
    adx: 28.67,
    macd: -123.45,
    macd_signal: -98.76,
    macd_hist: -24.69,
    bb_upper: 60200.45,
    bb_middle: 59900.12,
    bb_lower: 59599.78,
    created_at: "2025-08-16 07:15:00.546506",
  },
  {
    id: 4,
    timestamp: "2025-08-16 03:14:58.096545",
    symbol: "ETH/USD",
    interval_tf: "1h",
    price: 2750.0,
    rsi: 72.15,
    sma: 2780.34,
    adx: 42.18,
    macd: 89.23,
    macd_signal: 67.45,
    macd_hist: 21.78,
    bb_upper: 2820.67,
    bb_middle: 2760.23,
    bb_lower: 2699.79,
    created_at: "2025-08-16 03:15:00.546506",
  },
  {
    id: 5,
    timestamp: "2025-08-15 23:14:58.096545",
    symbol: "ADA/USD",
    interval_tf: "4h",
    price: 0.45,
    rsi: 28.67,
    sma: 0.47,
    adx: 19.34,
    macd: -0.012,
    macd_signal: -0.008,
    macd_hist: -0.004,
    bb_upper: 0.49,
    bb_middle: 0.46,
    bb_lower: 0.43,
    created_at: "2025-08-15 23:15:00.546506",
  },
]

export const indicatorsApi = {
  async getIndicators(filters: IndicatorsFilters = {}): Promise<ApiResponse<IndicatorData>> {
    try {
      const params = new URLSearchParams()
      if (filters.symbol) params.append("symbol", filters.symbol)
      if (filters.interval) params.append("interval", filters.interval)
      if (filters.search) params.append("search", filters.search)
      if (filters.page) params.append("page", filters.page.toString())
      if (filters.limit) params.append("limit", filters.limit.toString())
      if (filters.startDate) params.append("start_date", filters.startDate)
      if (filters.endDate) params.append("end_date", filters.endDate)

      const response = await api.get(`/indicators?${params.toString()}`)
      return response.data
    } catch (error) {
      console.warn("API call failed, using mock data:", error)

      // Fallback to mock data with filtering
      let filteredData = [...mockIndicators]

      if (filters.symbol && filters.symbol !== "all") {
        filteredData = filteredData.filter((item) => item.symbol === filters.symbol)
      }

      if (filters.search) {
        filteredData = filteredData.filter(
          (item) =>
            item.symbol.toLowerCase().includes(filters.search!.toLowerCase()) ||
            item.interval_tf.toLowerCase().includes(filters.search!.toLowerCase()),
        )
      }

      const page = filters.page || 1
      const limit = filters.limit || 10
      const startIndex = (page - 1) * limit
      const paginatedData = filteredData.slice(startIndex, startIndex + limit)

      return {
        data: paginatedData,
        total: filteredData.length,
        page,
        limit,
        totalPages: Math.ceil(filteredData.length / limit),
      }
    }
  },

  async getSymbols(): Promise<string[]> {
    try {
      const response = await api.get("/symbols")
      return response.data
    } catch (error) {
      console.warn("API call failed, using mock symbols:", error)
      return [...new Set(mockIndicators.map((item) => item.symbol))]
    }
  },

  async getStats() {
    try {
      const response = await api.get("/stats")
      return response.data
    } catch (error) {
      console.warn("API call failed, using mock stats:", error)
      return {
        totalSymbols: 5,
        avgBtcPrice: 59900,
        avgRsi: 49.24,
        activeSignals: 8,
        priceChange: -1.2,
        rsiChange: 3.1,
      }
    }
  },

  async getPositions() {
    try {
      const response = await api.get("/positions")
      return response.data
    } catch (error) {
      console.warn("API call failed, using mock positions:", error)
      return {
        success: false,
        totalOpenPositions: 0,
        positions: {
          BTCUSDT: null,
          ETHUSDT: null,
          BNBUSDT: null
        },
        timestamp: new Date().toISOString(),
        error: "API not available"
      }
    }
  },
}

export default api
