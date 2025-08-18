"use client"

import { useState } from "react"
import { Button } from "./ui/Button"
import { Input } from "./ui/Input"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/Card"

export function SettingsPanel() {
  const [apiUrl, setApiUrl] = useState("https://api.trading.com/v1")
  const [refreshInterval, setRefreshInterval] = useState("30")
  const [maxRecords, setMaxRecords] = useState("1000")

  const handleSave = () => {
    // Save settings logic here
    console.log("Settings saved:", { apiUrl, refreshInterval, maxRecords })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configuración de API</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">URL de la API</label>
            <Input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="https://api.trading.com/v1"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Intervalo de actualización (segundos)</label>
            <Input
              type="number"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(e.target.value)}
              placeholder="30"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Máximo de registros</label>
            <Input
              type="number"
              value={maxRecords}
              onChange={(e) => setMaxRecords(e.target.value)}
              placeholder="1000"
            />
          </div>
          <Button onClick={handleSave}>Guardar Configuración</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configuración de Alertas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Alertas RSI</span>
            <input type="checkbox" className="rounded" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Alertas MACD</span>
            <input type="checkbox" className="rounded" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Alertas de precio</span>
            <input type="checkbox" className="rounded" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
