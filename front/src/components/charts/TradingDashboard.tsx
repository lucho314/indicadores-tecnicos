"use client"

import { useState } from "react"
import { PriceChart } from "./PriceChart"
import { RSIChart } from "./RSIChart"
import { MACDChart } from "./MACDChart"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { useIndicators } from "../../hooks/useIndicators"
import { useSymbols } from "../../hooks/useSymbols"

export function TradingDashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTC/USD")
  const { data, loading, error } = useIndicators({ limit: 50 })
  const { symbols } = useSymbols()

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <div className="h-6 w-48 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-destructive">Error al cargar los datos de gráficos: {error}</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Symbol Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Dashboard de Trading</span>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="flex h-10 w-40 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              {symbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Price Chart with Bollinger Bands */}
      <PriceChart data={data} symbol={selectedSymbol} />

      {/* Technical Indicators */}
      <div className="grid gap-6 lg:grid-cols-2">
        <RSIChart data={data} symbol={selectedSymbol} />
        <MACDChart data={data} symbol={selectedSymbol} />
      </div>

      {/* Additional Info */}
      <Card>
        <CardHeader>
          <CardTitle>Información de Indicadores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 text-sm">
            <div>
              <h4 className="font-medium text-foreground mb-2">RSI</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• &gt; 70: Sobrecomprado</li>
                <li>• &lt; 30: Sobrevendido</li>
                <li>• 30-70: Neutral</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-foreground mb-2">MACD</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• MACD &gt; Señal: Alcista</li>
                <li>• MACD &lt; Señal: Bajista</li>
                <li>• Histograma: Momentum</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-foreground mb-2">Bollinger Bands</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• Banda Superior: Resistencia</li>
                <li>• Banda Inferior: Soporte</li>
                <li>• Banda Media: SMA(20)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-foreground mb-2">ADX</h4>
              <ul className="space-y-1 text-muted-foreground">
                <li>• &gt; 25: Tendencia fuerte</li>
                <li>• &lt; 20: Tendencia débil</li>
                <li>• Mide fuerza de tendencia</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
