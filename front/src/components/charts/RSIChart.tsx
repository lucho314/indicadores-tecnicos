"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { formatDate } from "../../lib/utils"
import type { IndicatorData } from "../../services/api"

interface RSIChartProps {
  data: IndicatorData[]
  symbol?: string
}

export function RSIChart({ data, symbol = "BTC/USD" }: RSIChartProps) {
  const chartData = data
    .filter((item) => item.symbol === symbol)
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map((item) => ({
      timestamp: formatDate(item.timestamp),
      rsi: item.rsi,
    }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const rsi = payload[0].value
      let status = "Neutral"
      let statusColor = "hsl(var(--foreground))"

      if (rsi > 70) {
        status = "Sobrecomprado"
        statusColor = "hsl(0, 84%, 60%)"
      } else if (rsi < 30) {
        status = "Sobrevendido"
        statusColor = "hsl(142, 76%, 36%)"
      }

      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground">{label}</p>
          <p className="text-sm" style={{ color: payload[0].color }}>
            RSI: {rsi.toFixed(2)}
          </p>
          <p className="text-sm" style={{ color: statusColor }}>
            {status}
          </p>
        </div>
      )
    }
    return null
  }

  const currentRSI = chartData.length > 0 ? chartData[chartData.length - 1]?.rsi : 0
  const rsiStatus = currentRSI > 70 ? "Sobrecomprado" : currentRSI < 30 ? "Sobrevendido" : "Neutral"
  const rsiColor = currentRSI > 70 ? "text-loss" : currentRSI < 30 ? "text-profit" : "text-foreground"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>RSI (Relative Strength Index) - {symbol}</span>
          <div className="text-right">
            <div className="text-sm font-mono">{currentRSI.toFixed(2)}</div>
            <div className={`text-xs ${rsiColor}`}>{rsiStatus}</div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
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
                domain={[0, 100]}
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />

              {/* Reference lines for overbought/oversold */}
              <ReferenceLine y={70} stroke="hsl(0, 84%, 60%)" strokeDasharray="5 5" />
              <ReferenceLine y={30} stroke="hsl(142, 76%, 36%)" strokeDasharray="5 5" />
              <ReferenceLine y={50} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />

              <Line type="monotone" dataKey="rsi" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} name="RSI" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
