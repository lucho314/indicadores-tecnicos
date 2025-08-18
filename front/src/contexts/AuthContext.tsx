"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import api from "../services/api"

interface User {
  id: string
  username: string
  name: string
}

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const savedUser = localStorage.getItem("trading-app-user")
    if (savedUser) {
      const userData = JSON.parse(savedUser)
      setUser(userData)
    }
    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      const response = await api.post("/login", { username, password })
      console.log("Login response:", response.data)
      const { access_token } = response.data

      const userData = {
        id: "1", // Puedes ajustar esto según la respuesta del backend
        username,
        name: "Trading Admin", // Ajustar según la respuesta del backend
      }

      localStorage.setItem("trading-app-user", JSON.stringify(userData))
      localStorage.setItem("trading-app-token", access_token)
      setUser(userData)
      setIsLoading(false)
      return true
    } catch (error) {
      console.error("Error during login:", error)
      setIsLoading(false)
      return false
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem("trading-app-user")
    localStorage.removeItem("trading-app-token")
  }

  const value = {
    user,
    login,
    logout,
    isLoading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
