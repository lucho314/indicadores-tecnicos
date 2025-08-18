"use client"

import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { formatDate } from "../../lib/utils"
import type { IndicatorData } from "../../services/api"

interface MACDChartProps {
  data: IndicatorData[]
  symbol?: string
}

export function MACDChart({ data, symbol = "BTC/USD" }: MACDChartProps) {
  const chartData = data
    .filter((item) => item.symbol === symbol)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map((item) => ({
      timestamp: formatDate(item.timestamp),
      macd: item.macd,
      macd_signal: item.macd_signal,
      macd_hist: item.macd_hist,
    }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(4)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const currentMACD = chartData.length > 0 ? chartData[chartData.length - 1] : null
  const macdTrend = currentMACD && currentMACD.macd > currentMACD.macd_signal ? "Alcista" : "Bajista"
  const macdColor = currentMACD && currentMACD.macd > currentMACD.macd_signal ? "text-profit" : "text-loss"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>MACD - {symbol}</span>
          <div className="text-right">
            <div className="text-sm font-mono">{currentMACD?.macd.toFixed(4) || "0.0000"}</div>
            <div className={`text-xs ${macdColor}`}>{macdTrend}</div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="timestamp"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />

              {/* Zero line */}
              <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />

              {/* MACD Histogram */}
              <Bar dataKey="macd_hist" fill="hsl(var(--muted))" name="MACD Histograma" opacity={0.6} />

              {/* MACD Line */}
              <Line
                type="monotone"
                dataKey="macd"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="MACD"
              />

              {/* Signal Line */}
              <Line
                type="monotone"
                dataKey="macd_signal"
                stroke="hsl(0, 84%, 60%)"
                strokeWidth={2}
                dot={false}
                name="Señal"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
