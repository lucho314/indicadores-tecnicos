import React, { useCallback } from 'react'
import { StrategyCard } from './StrategyCard'
import { useActiveStrategies } from '../hooks/useActiveStrategies'
import { type TradingStrategy } from '../services/api'

interface StrategiesListProps {
  onStrategyAction?: (strategyId: number, action: 'executed' | 'expired') => void
}

export const StrategiesList: React.FC<StrategiesListProps> = ({ onStrategyAction }) => {
  const { strategies, loading, error, refetch } = useActiveStrategies()

  const handleStrategyExecuted = useCallback((strategyId: number) => {
    onStrategyAction?.(strategyId, 'executed')
    // Refetch strategies to update the list
    refetch()
  }, [onStrategyAction, refetch])

  const handleStrategyExpired = useCallback((strategyId: number) => {
    onStrategyAction?.(strategyId, 'expired')
    // Refetch strategies to update the list
    refetch()
  }, [onStrategyAction, refetch])

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading strategies...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading strategies</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
          <div className="mt-4">
            <button
              onClick={refetch}
              className="bg-red-100 hover:bg-red-200 text-red-800 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (strategies.length === 0) {
    return (
      <div className="space-y-4">
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No active strategies</h3>
          <p className="mt-1 text-sm text-gray-500">
            There are currently no active trading strategies available.
          </p>
          <div className="mt-6">
            <button
              onClick={refetch}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Active Trading Strategies
          </h2>
          <p className="text-sm text-gray-600">
            {strategies.length} {strategies.length === 1 ? 'strategy' : 'strategies'} available
          </p>
        </div>
        <button
          onClick={refetch}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-0.5 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Strategies Grid */}
      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
        {strategies.map((strategy: TradingStrategy) => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            onStrategyExecuted={handleStrategyExecuted}
            onStrategyExpired={handleStrategyExpired}
          />
        ))}
      </div>

      {/* Summary */}
      <div className="mt-8 bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {strategies.filter(s => s.action === 'LONG').length}
            </div>
            <div className="text-gray-600">Long Strategies</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {strategies.filter(s => s.action === 'SHORT').length}
            </div>
            <div className="text-gray-600">Short Strategies</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {strategies.filter(s => new Date(s.expires_at) < new Date(Date.now() + 60 * 60 * 1000)).length}
            </div>
            <div className="text-gray-600">Expiring Soon</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StrategiesList