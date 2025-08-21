import React from "react"
import { useBybitWebSocket } from "../hooks/useBybitWebSocket"
import { formatCurrency } from "../lib/utils"

interface BybitWebSocketMonitorProps {
  symbol?: string
}

export const BybitWebSocketMonitor: React.FC<BybitWebSocketMonitorProps> = ({ 
  symbol = "BTCUSDT" 
}) => {
  const {
    data,
    isConnected,
    loading,
    error,
    hasPosition,
    currentPrice,
    position,
    balance,
    lastUpdate,
    reconnect
  } = useBybitWebSocket(symbol)

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleTimeString()
  }

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
        <h3 className="text-destructive font-semibold mb-2">Error de conexión WebSocket</h3>
        <p className="text-sm text-muted-foreground mb-3">{error}</p>
        <button
          onClick={reconnect}
          className="text-sm bg-destructive text-destructive-foreground px-3 py-1 rounded hover:bg-destructive/90"
        >
          Reconectar
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-foreground">Monitor WebSocket - {symbol}</h2>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-success' : 'bg-destructive'
            }`}></div>
            <span className="text-xs text-muted-foreground">
              {isConnected ? `Conectado • ${formatTimestamp(lastUpdate)}` : 'Desconectado'}
            </span>
          </div>
          {!isConnected && (
            <button
              onClick={reconnect}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90"
            >
              Reconectar
            </button>
          )}
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Precio Actual</h3>
          <p className="text-2xl font-bold text-foreground">
            {formatCurrency(currentPrice)}
          </p>
          <p className="text-xs text-muted-foreground">
            {symbol}
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Estado de Posición</h3>
          <p className={`text-2xl font-bold ${hasPosition ? 'text-success' : 'text-muted-foreground'}`}>
            {hasPosition ? 'Activa' : 'Sin Posición'}
          </p>
          <p className="text-xs text-muted-foreground">
            {hasPosition ? `${position?.side} • ${position?.size}` : 'No hay posiciones abiertas'}
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Balance Disponible</h3>
          <p className="text-2xl font-bold text-foreground">
            {formatCurrency(balance?.walletBalance || 0)} USDT
          </p>
          <p className="text-xs text-muted-foreground">
            Disponible: {formatCurrency(balance?.availableToWithdraw || 0)}
          </p>
        </div>
      </div>

      {/* Position Details */}
      {hasPosition && position && (
        <div className="bg-card border border-border rounded-lg">
          <div className="p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground">Detalles de la Posición</h3>
          </div>
          <div className="p-4">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="font-semibold text-foreground">{position.symbol}</h4>
                <span className={`text-sm font-medium ${
                  position.side === "Buy" ? "text-success" : "text-destructive"
                }`}>
                  {position.side} • Leverage {position.leverage || '1'}x
                </span>
              </div>
              <div className="text-right">
                <p className={`font-semibold ${
                  (position.unrealisedPnl || 0) >= 0 ? "text-success" : "text-destructive"
                }`}>
                  {(position.unrealisedPnl || 0) >= 0 ? "+" : ""}
                  {formatCurrency(position.unrealisedPnl || 0)} USDT
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
                <p className="font-medium text-foreground">{formatCurrency(position.avgPrice || 0)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Precio Marca</p>
                <p className="font-medium text-foreground">{formatCurrency(position.markPrice || 0)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Valor Posición</p>
                <p className="font-medium text-foreground">{formatCurrency(position.positionValue || 0)} USDT</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Balance Details */}
      {balance && (
        <div className="bg-card border border-border rounded-lg">
          <div className="p-4 border-b border-border">
            <h3 className="text-lg font-semibold text-foreground">Información de Balance</h3>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Balance Total</p>
                <p className="font-medium text-foreground">{formatCurrency(balance.walletBalance || 0)} {balance.coin}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Disponible para Retiro</p>
                <p className="font-medium text-foreground">{formatCurrency(balance.availableToWithdraw || 0)} {balance.coin}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Equity</p>
                <p className="font-medium text-foreground">{formatCurrency(balance.equity || 0)} {balance.coin}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Valor USD</p>
                <p className="font-medium text-foreground">{formatCurrency(balance.usdValue || 0)} USD</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Position State */}
      {!hasPosition && data && (
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <p className="text-muted-foreground">No hay posiciones abiertas para {symbol}</p>
        </div>
      )}

      {/* Debug Panel */}
      {data && (
        <details className="bg-card border border-border rounded-lg">
          <summary className="p-4 cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground border-b border-border">
            Ver datos raw (debugging)
          </summary>
          <div className="p-4">
            <pre className="text-xs overflow-auto bg-muted rounded p-3">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </div>
  )
}
