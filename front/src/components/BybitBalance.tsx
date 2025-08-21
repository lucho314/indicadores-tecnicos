"use client"

import { useBybitPositions } from "../hooks/useBybitPositions"
import { formatCurrency } from "../lib/utils"

export function BybitBalance() {
  const { data, loading, error, refetch } = useBybitPositions()

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-card border border-border rounded-lg p-4">
                <div className="h-4 bg-muted rounded w-1/2 mb-2"></div>
                <div className="h-6 bg-muted rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
        <h3 className="text-destructive font-semibold mb-2">Error al cargar datos de Bybit</h3>
        <p className="text-sm text-muted-foreground mb-3">{error}</p>
        <button
          onClick={refetch}
          className="text-sm bg-destructive text-destructive-foreground px-3 py-1 rounded hover:bg-destructive/90"
        >
          Reintentar
        </button>
      </div>
    )
  }

  if (!data) return null

  const activePositions = Object.entries(data.positions).filter(([_, position]) => position !== null)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-foreground">Balance Bybit</h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            Última actualización: {new Date(data.timestamp).toLocaleTimeString()}
          </span>
          <button
            onClick={refetch}
            className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90"
          >
            Actualizar
          </button>
        </div>
      </div>

      {/* Balance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Balance Total</h3>
          <p className="text-2xl font-bold text-foreground">
            {formatCurrency(data.balanceInfo.walletBalance)} {data.balanceInfo.coin}
          </p>
          <p className="text-xs text-muted-foreground">≈ {formatCurrency(data.balanceInfo.usdValue)} USD</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Equity</h3>
          <p className="text-2xl font-bold text-foreground">
            {formatCurrency(data.balanceInfo.equity)} {data.balanceInfo.coin}
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Posiciones Abiertas</h3>
          <p className="text-2xl font-bold text-foreground">{data.totalOpenPositions}</p>
        </div>
      </div>

      {/* Active Positions */}
      {activePositions.length > 0 && (
        <div className="bg-card border border-border rounded-lg">
          <div className="p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground">Posiciones Activas</h3>
          </div>
          <div className="divide-y divide-border">
            {activePositions.map(([symbol, position]) => {
              if (!position) return null

              const pnlColor = position.unrealisedPnl >= 0 ? "text-success" : "text-destructive"
              const sideColor = position.side === "Buy" ? "text-success" : "text-destructive"

              return (
                <div key={symbol} className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-semibold text-foreground">{position.symbol}</h4>
                      <span className={`text-sm font-medium ${sideColor}`}>
                        {position.side} • Leverage {position.leverage}x
                      </span>
                    </div>
                    <div className="text-right">
                      <p className={`font-semibold ${pnlColor}`}>
                        {position.unrealisedPnl >= 0 ? "+" : ""}
                        {formatCurrency(position.unrealisedPnl)} USDT
                      </p>
                      <p className="text-xs text-muted-foreground">PnL No Realizado</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Tamaño</p>
                      <p className="font-medium text-foreground">{position.size}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Precio Promedio</p>
                      <p className="font-medium text-foreground">{formatCurrency(position.avgPrice)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Precio Marca</p>
                      <p className="font-medium text-foreground">{formatCurrency(position.markPrice)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Valor Posición</p>
                      <p className="font-medium text-foreground">{formatCurrency(position.positionValue)} USDT</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {activePositions.length === 0 && (
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <p className="text-muted-foreground">No hay posiciones abiertas</p>
        </div>
      )}
    </div>
  )
}
