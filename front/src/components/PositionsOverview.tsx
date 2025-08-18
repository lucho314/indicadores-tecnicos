import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/badge'
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react'
import { usePositions } from '../hooks/usePositions'
import { Position } from '../services/api'

const PositionCard: React.FC<{ symbol: string; position: Position | null }> = ({ symbol, position }) => {
  if (!position) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">{symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sin posición</p>
        </CardContent>
      </Card>
    )
  }

  const isLong = position.side === 'Buy'
  const pnlColor = position.unrealisedPnl >= 0 ? 'text-green-600' : 'text-red-600'
  const sideColor = isLong ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{symbol}</CardTitle>
          <Badge className={sideColor}>
            {isLong ? (
              <>
                <TrendingUp className="w-3 h-3 mr-1" />
                LONG
              </>
            ) : (
              <>
                <TrendingDown className="w-3 h-3 mr-1" />
                SHORT
              </>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Tamaño:</span>
          <span className="font-medium">{position.size}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Precio Promedio:</span>
          <span className="font-medium">${position.avgPrice.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Precio Actual:</span>
          <span className="font-medium">${position.markPrice.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Apalancamiento:</span>
          <span className="font-medium">{position.leverage}x</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">PnL No Realizado:</span>
          <span className={`font-medium ${pnlColor}`}>
            {position.unrealisedPnl >= 0 ? '+' : ''}${position.unrealisedPnl.toFixed(2)}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

export const PositionsOverview: React.FC = () => {
  const { positions, loading, error, refetch } = usePositions()

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Posiciones Abiertas</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Posiciones Abiertas</h2>
          <button
            onClick={refetch}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reintentar
          </button>
        </div>
        <Card>
          <CardContent className="p-6">
            <p className="text-red-600">Error: {error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!positions) {
    return null
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Posiciones Abiertas</h2>
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {positions.totalOpenPositions} posición{positions.totalOpenPositions !== 1 ? 'es' : ''} activa{positions.totalOpenPositions !== 1 ? 's' : ''}
          </span>
          <button
            onClick={refetch}
            className="ml-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Actualizar
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <PositionCard symbol="BTC/USDT" position={positions.positions.BTCUSDT} />
        <PositionCard symbol="ETH/USDT" position={positions.positions.ETHUSDT} />
        <PositionCard symbol="BNB/USDT" position={positions.positions.BNBUSDT} />
      </div>

      {positions.totalOpenPositions === 0 && (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">No hay posiciones abiertas en este momento</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
