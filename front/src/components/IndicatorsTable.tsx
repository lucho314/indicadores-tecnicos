"use client"

import { useState, useEffect } from "react"
import { Search, Download, RefreshCw, AlertCircle } from "lucide-react"
import { Button } from "./ui/Button"
import { Input } from "./ui/Input"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/Card"
import { formatCurrency, formatDate } from "../lib/utils"
import { useIndicators } from "../hooks/useIndicators"
import { useSymbols } from "../hooks/useSymbols"

export function IndicatorsTable() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedSymbol, setSelectedSymbol] = useState("all")
  const { symbols } = useSymbols()



  const { data, loading, error, total, totalPages, currentPage, refetch, updateFilters } = useIndicators({
    limit: 10,
  })

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      updateFilters({
        search: searchTerm || undefined,
        symbol: selectedSymbol === "all" ? undefined : selectedSymbol,
        page: 1,
      })
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [searchTerm, selectedSymbol, updateFilters])

  const handlePageChange = (newPage: number) => {
    updateFilters({ page: newPage })
  }

  const exportData = () => {
    const csv = [
      [
        "ID",
        "Timestamp",
        "Symbol",
        "Interval",
        "Price",
        "RSI",
        "SMA",
        "ADX",
        "MACD",
        "MACD Signal",
        "MACD Hist",
        "BB Upper",
        "BB Middle",
        "BB Lower",
      ].join(","),
      ...data.map((item) =>
        [
          item.id,
          item.timestamp,
          item.symbol,
          item.interval_tf,
          item.price,
          item.rsi,
          item.sma,
          item.adx,
          item.macd,
          item.macd_signal,
          item.macd_hist,
          item.bb_upper,
          item.bb_middle,
          item.bb_lower,
        ].join(","),
      ),
    ].join("\n")

    const blob = new Blob([csv], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `indicators-data-${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span>Error: {error}</span>
            <Button variant="outline" size="sm" onClick={refetch}>
              Reintentar
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <CardTitle className="flex items-center gap-2">
            Indicadores Técnicos
            {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
          </CardTitle>
          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar símbolo o intervalo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full sm:w-64"
                disabled={loading}
              />
            </div>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              disabled={loading}
              className="flex h-10 w-full sm:w-32 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50"
            >
              <option value="all">Todos</option>
              {symbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>
            <Button variant="outline" onClick={refetch} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Actualizar
            </Button>
            <Button variant="outline" onClick={exportData} disabled={loading || data.length === 0}>
              <Download className="h-4 w-4 mr-2" />
              Exportar
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-2 font-medium">Símbolo</th>
                <th className="text-left p-2 font-medium">Intervalo</th>
                <th className="text-right p-2 font-medium">Precio</th>
                <th className="text-right p-2 font-medium">RSI</th>
                <th className="text-right p-2 font-medium">SMA</th>
                <th className="text-right p-2 font-medium">ADX</th>
                <th className="text-right p-2 font-medium">MACD</th>
                <th className="text-left p-2 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {loading && data.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-muted-foreground">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
                    Cargando datos...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-muted-foreground">
                    No se encontraron datos
                  </td>
                </tr>
              ) : (
                data.map((item) => (
                  <tr key={item.id} className="border-b border-border/50 hover:bg-accent/50">
                    <td className="p-2 font-medium">{item.symbol}</td>
                    <td className="p-2 text-muted-foreground">{item.interval_tf}</td>
                    <td className="p-2 text-right font-mono">{formatCurrency(item.price)}</td>
                    <td
                      className={`p-2 text-right font-mono ${
                        item.rsi > 70 ? "text-loss" : item.rsi < 30 ? "text-profit" : "text-foreground"
                      }`}
                    >
                      {item.rsi.toFixed(2)}
                    </td>
                    <td className="p-2 text-right font-mono">{formatCurrency(item.sma)}</td>
                    <td className="p-2 text-right font-mono">{item.adx.toFixed(2)}</td>
                    <td className={`p-2 text-right font-mono ${item.macd > 0 ? "text-profit" : "text-loss"}`}>
                      {item.macd.toFixed(2)}
                    </td>
                    <td className="p-2 text-muted-foreground">{formatDate(item.timestamp)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-muted-foreground">
            {loading ? (
              "Cargando..."
            ) : (
              <>
                Mostrando {(currentPage - 1) * 10 + 1} a {Math.min(currentPage * 10, total)} de {total} registros
              </>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1 || loading}
            >
              Anterior
            </Button>
            <span className="flex items-center px-3 text-sm text-muted-foreground">
              Página {currentPage} de {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages || loading}
            >
              Siguiente
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
