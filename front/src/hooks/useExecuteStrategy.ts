import { useState, useCallback } from "react";
import {
  tradingStrategiesApi,
  type ExecuteStrategyRequest,
  type ExecuteStrategyResponse,
} from "../services/api";

interface UseExecuteStrategyReturn {
  executeStrategy: (
    strategyId: string,
    investmentAmount: number
  ) => Promise<ExecuteStrategyResponse | null>;
  loading: boolean;
  error: string | null;
  lastResponse: ExecuteStrategyResponse | null;
}

export const useExecuteStrategy = (): UseExecuteStrategyReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] =
    useState<ExecuteStrategyResponse | null>(null);

  const executeStrategy = useCallback(
    async (
      strategyId: string,
      investmentAmount: number
    ): Promise<ExecuteStrategyResponse | null> => {
      try {
        setLoading(true);
        setError(null);

        // Obtener el token del localStorage
        const token = localStorage.getItem("trading-app-token");
        if (!token) {
          throw new Error("No authentication token found");
        }

        const request: ExecuteStrategyRequest = {
          strategy_id: strategyId,
          usdt_amount: investmentAmount,
          token: token,
        };

        const response = await tradingStrategiesApi.executeStrategy(request);
        setLastResponse(response);

        if (!response.success) {
          setError(response.message || "Failed to execute strategy");
          return null;
        }

        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error occurred";
        setError(errorMessage);
        console.error("Error executing strategy:", err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    executeStrategy,
    loading,
    error,
    lastResponse,
  };
};

export default useExecuteStrategy;
