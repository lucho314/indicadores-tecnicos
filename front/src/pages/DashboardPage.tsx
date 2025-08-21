"use client"

import { useState } from "react"
import { useAuth } from "../contexts/AuthContext"
import { Button } from "../components/ui/Button"
import { Sidebar } from "../components/Sidebar"
import { OverviewCards } from "../components/OverviewCards"
import { IndicatorsTable } from "../components/IndicatorsTable"
import { SettingsPanel } from "../components/SettingsPanel"
import { TradingDashboard } from "../components/charts/TradingDashboard"
import { BybitBalance } from "@/components/BybitBalance"

export function DashboardPage() {
  const { user, logout } = useAuth()
  const [activeSection, setActiveSection] = useState("overview")

  const renderContent = () => {
    switch (activeSection) {
      case "overview":
        return (
          <div className="space-y-6">
            <OverviewCards />
            <BybitBalance />
          </div>
          
        )
      case "indicators":
        return <TradingDashboard />
      case "data":
        return <IndicatorsTable />
      case "settings":
        return <SettingsPanel />
      default:
        return <OverviewCards />
    }
  }

  const getSectionDescription = () => {
    switch (activeSection) {
      case "overview":
        return "Resumen general de indicadores y datos recientes"
      case "indicators":
        return "Gráficos interactivos de indicadores técnicos"
      case "data":
        return "Datos históricos y en tiempo real"
      case "settings":
        return "Configuración del sistema"
      default:
        return "Panel de control principal"
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />

      <div className="flex-1">
        <header className="border-b border-border bg-card sticky top-0 z-10">
          <div className="px-4 py-4 flex justify-between items-center">
            <div className="ml-12 md:ml-0">
              <h1 className="text-2xl font-bold text-foreground">Trading Dashboard</h1>
              <p className="text-sm text-muted-foreground">{getSectionDescription()}</p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground hidden sm:block">Bienvenido, {user?.name}</span>
              <Button variant="outline" onClick={logout}>
                Cerrar Sesión
              </Button>
            </div>
          </div>
        </header>

        <main className="p-4 md:p-6">{renderContent()}</main>
      </div>
    </div>
  )
}
