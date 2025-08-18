"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { formatCurrency, formatDate } from "../../lib/utils"
import type { IndicatorData } from "../../services/api"

interface PriceChartProps {
  data: IndicatorData[]
  symbol?: string
}

export function PriceChart({ data, symbol = "BTC/USD" }: PriceChartProps) {
  const chartData = data
    .filter((item) => item.symbol === symbol)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map((item) => ({
      timestamp: formatDate(item.timestamp),
      price: item.price,
      sma: item.sma,
      bb_upper: item.bb_upper,
      bb_middle: item.bb_middle,
      bb_lower: item.bb_lower,
    }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Precio y Bollinger Bands - {symbol}</span>
          <span className="text-sm text-muted-foreground">
            {chartData.length > 0 && formatCurrency(chartData[chartData.length - 1]?.price || 0)}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="timestamp"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />

              {/* Bollinger Bands */}
              <Line
                type="monotone"
                dataKey="bb_upper"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="BB Superior"
              />
              <Line
                type="monotone"
                dataKey="bb_lower"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="BB Inferior"
              />
              <Line
                type="monotone"
                dataKey="bb_middle"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={1}
                dot={false}
                name="BB Media"
              />

              {/* SMA */}
              <Line type="monotone" dataKey="sma" stroke="hsl(38, 92%, 50%)" strokeWidth={2} dot={false} name="SMA" />

              {/* Price */}
              <Line
                type="monotone"
                dataKey="price"
                stroke="hsl(var(--primary))"
                strokeWidth={3}
                dot={false}
                name="Precio"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
