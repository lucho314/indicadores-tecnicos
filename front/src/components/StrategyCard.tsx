import React, { useState, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/Card";
import { Button } from "./ui/Button";
import { Badge } from "./ui/badge";
import { type TradingStrategy } from "../services/api";
import { useBalanceStore } from "../stores/useBalanceStore";
import { useExecuteStrategy } from "../hooks/useExecuteStrategy";
import { useExpireStrategy } from "../hooks/useExpireStrategy";

interface StrategyCardProps {
  strategy: TradingStrategy;
  onStrategyExecuted?: (strategyId: number) => void;
  onStrategyExpired?: (strategyId: number) => void;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onStrategyExecuted,
  onStrategyExpired,
}) => {
  const { balance } = useBalanceStore();
  const {
    executeStrategy,
    loading: executeLoading,
    error: executeError,
  } = useExecuteStrategy();
  const {
    expireStrategy,
    loading: expireLoading,
    error: expireError,
  } = useExpireStrategy();

  const [investmentPercentage, setInvestmentPercentage] = useState(10); // Default 10%
  const [showConfirmation, setShowConfirmation] = useState<
    "execute" | "decline" | null
  >(null);

  const totalBalance = parseFloat(balance?.totalWalletBalance || "0");
  const maxInvestment = totalBalance * 0.8; // Max 80% of total balance
  const investmentAmount = (maxInvestment * investmentPercentage) / 100;

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "LOW":
        return "bg-green-100 text-green-800";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800";
      case "HIGH":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getActionColor = (action: string) => {
    return action === "LONG"
      ? "bg-green-100 text-green-800"
      : "bg-red-100 text-red-800";
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleExecute = useCallback(async () => {
    if (investmentAmount <= 0) {
      alert("Investment amount must be greater than 0");
      return;
    }

    const result = await executeStrategy(
      strategy.id.toString(),
      investmentAmount
    );
    if (result?.success) {
      onStrategyExecuted?.(strategy.id);
      setShowConfirmation(null);
    }
  }, [strategy.id, investmentAmount, executeStrategy, onStrategyExecuted]);

  const handleDecline = useCallback(async () => {
    const result = await expireStrategy(strategy.id.toString());
    if (result?.success) {
      onStrategyExpired?.(strategy.id);
      setShowConfirmation(null);
    }
  }, [strategy.id, expireStrategy, onStrategyExpired]);

  const isExpiringSoon =
    new Date(strategy.expires_at) < new Date(Date.now() + 60 * 60 * 1000); // 1 hour

  return (
    <Card className="border-l-4 border-l-blue-500 shadow-sm bg-card">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-xl font-semibold text-card-foreground">
              {strategy.symbol}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Trading Strategy
            </p>
          </div>
          <div className="flex gap-2">
            <Badge className={getActionColor(strategy.action)}>
              {strategy.action}
            </Badge>
            <Badge className={getRiskColor(strategy.risk_level)}>
              {strategy.risk_level} risk
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Strategy Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-muted-foreground">
              Entry Price:
            </span>
            <p className="text-profit font-semibold">
              {formatCurrency(strategy.entry_price)}
            </p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">
              Confidence:
            </span>
            <p className="text-blue-400 font-semibold">
              {(strategy.confidence * 100).toFixed(1)}%
            </p>
          </div>
          {strategy.stop_loss && (
            <div>
              <span className="font-medium text-muted-foreground">
                Stop Loss:
              </span>
              <p className="text-loss font-semibold">
                {formatCurrency(strategy.stop_loss)}
              </p>
            </div>
          )}
          {strategy.take_profit && (
            <div>
              <span className="font-medium text-muted-foreground">
                Take Profit:
              </span>
              <p className="text-profit font-semibold">
                {formatCurrency(strategy.take_profit)}
              </p>
            </div>
          )}
          <div>
            <span className="font-medium text-muted-foreground">
              Risk/Reward:
            </span>
            <p className="text-orange-400 font-semibold">
              {strategy.risk_reward_ratio.toFixed(2)}
            </p>
          </div>
          <div>
            <span className="font-medium text-muted-foreground">Expires:</span>
            <p
              className={`font-semibold ${
                isExpiringSoon ? "text-loss" : "text-muted-foreground"
              }`}
            >
              {formatDate(strategy.expires_at)}
            </p>
          </div>
        </div>

        {strategy.justification && (
          <div className="p-4 bg-muted/50 rounded-lg border border-border">
            <p className="text-sm font-medium text-card-foreground mb-1">
              Justification:
            </p>
            <p className="text-sm text-muted-foreground">
              {strategy.justification}
            </p>
            {strategy.key_factors && (
              <>
                <p className="text-sm font-medium text-card-foreground mt-3 mb-1">
                  Key Factors:
                </p>
                <p className="text-sm text-muted-foreground">
                  {strategy.key_factors}
                </p>
              </>
            )}
          </div>
        )}

        {/* Investment Control */}
        <div className="space-y-3 p-4 bg-muted/30 rounded-lg border border-border">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-card-foreground">
              Investment Amount
            </span>
            <span className="text-sm text-profit">
              Balance Total: {formatCurrency(totalBalance)} USDT
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-muted-foreground">
                {investmentPercentage}%
              </span>
              <span className="font-semibold text-profit">
                {formatCurrency(investmentAmount)} USDT
              </span>
            </div>

            <div className="relative mb-6">
              <label htmlFor="investment-range-input" className="sr-only">
                Investment range
              </label>
              <input
                id="investment-range-input"
                type="range"
                value={investmentPercentage}
                min="1"
                max="80"
                onChange={(e) =>
                  setInvestmentPercentage(Number(e.target.value))
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
              <span className="text-sm text-gray-500 dark:text-gray-400 absolute start-0 -bottom-6">
                Min (1%)
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400 absolute start-1/3 -translate-x-1/2 rtl:translate-x-1/2 -bottom-6">
                27%
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400 absolute start-2/3 -translate-x-1/2 rtl:translate-x-1/2 -bottom-6">
                53%
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400 absolute end-0 -bottom-6">
                Max (80%)
              </span>
            </div>
          </div>
        </div>

        {/* Error Messages */}
        {(executeError || expireError) && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <p className="text-sm text-destructive">
              {executeError || expireError}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        {!showConfirmation ? (
          <div className="flex gap-3">
            <Button
              onClick={() => setShowConfirmation("execute")}
              disabled={
                executeLoading ||
                expireLoading ||
                investmentAmount <= 0 ||
                totalBalance <= 0
              }
              className="flex-1 bg-profit hover:bg-profit/90 text-white"
            >
              Execute Strategy
            </Button>
            <Button
              onClick={() => setShowConfirmation("decline")}
              disabled={executeLoading || expireLoading}
              variant="outline"
              className="flex-1 border-destructive/30 text-destructive hover:bg-destructive/10"
            >
              Decline
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
              <p className="text-sm text-yellow-600 dark:text-yellow-400">
                {showConfirmation === "execute"
                  ? `Are you sure you want to execute this strategy with ${formatCurrency(
                      investmentAmount
                    )} USDT?`
                  : "Are you sure you want to decline this strategy?"}
              </p>
            </div>

            <div className="flex gap-3">
              <Button
                onClick={
                  showConfirmation === "execute" ? handleExecute : handleDecline
                }
                disabled={executeLoading || expireLoading}
                className={`flex-1 ${
                  showConfirmation === "execute"
                    ? "bg-profit hover:bg-profit/90"
                    : "bg-destructive hover:bg-destructive/90"
                } text-white`}
              >
                {executeLoading || expireLoading ? "Processing..." : "Confirm"}
              </Button>
              <Button
                onClick={() => setShowConfirmation(null)}
                disabled={executeLoading || expireLoading}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default StrategyCard;
