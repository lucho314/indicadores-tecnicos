"use client"

import { Activity, DollarSign } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/Card"
import { useStats } from "../hooks/useStats"
import { formatCurrency } from "../lib/utils"

export function OverviewCards() {
  const { stats, loading, error } = useStats()

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted animate-pulse rounded mb-1" />
              <div className="h-3 w-24 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="text-sm text-destructive">Error al cargar estadísticas</div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const statsData = [
    {
      title: "BTC/USD",
      value: formatCurrency(stats.avgBtcPrice),
      change: `${stats.btcPriceChange > 0 ? "+" : ""}${stats.btcPriceChange.toFixed(2)}%`,
      rsi: stats.avgBtcRsi.toFixed(2),
      icon: DollarSign,
      trend: stats.btcPriceChange > 0 ? "up" : "down",
    },
    {
      title: "ETH/USD",
      value: formatCurrency(stats.avgEthPrice),
      change: `${stats.ethPriceChange > 0 ? "+" : ""}${stats.ethPriceChange.toFixed(2)}%`,
      rsi: stats.avgEthRsi.toFixed(2),
      icon: DollarSign,
      trend: stats.ethPriceChange > 0 ? "up" : "down",
    },
    {
      title: "BNB/USD",
      value: formatCurrency(stats.avgBnbPrice),
      change: `${stats.bnbPriceChange > 0 ? "+" : ""}${stats.bnbPriceChange.toFixed(2)}%`,
      rsi: stats.avgBnbRsi.toFixed(2),
      icon: DollarSign,
      trend: stats.bnbPriceChange > 0 ? "up" : "down",
    },
    {
      title: "Señales Activas",
      value: stats.llmSignals.toString(),
      change: `Total símbolos: ${stats.totalSymbols}`,
      icon: Activity,
      trend: "up",
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {statsData.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              {stat.rsi && (
                <div className="text-sm text-muted-foreground mt-1">RSI: {stat.rsi}</div>
              )}
              <p className={`text-xs ${stat.trend === "up" ? "text-profit" : "text-loss"}`}>{stat.change}</p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
