import React from 'react';
import { useBalanceStore } from '../stores/useBalanceStore';

const GlobalBalance: React.FC = () => {
  const { balance, isLoading, error } = useBalanceStore();

  if (isLoading) {
    return (
      <div className="p-4 bg-gray-100 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Balance Global</h3>
        <p className="text-gray-600">Cargando balance...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 rounded-lg">
        <h3 className="text-lg font-semibold mb-2 text-red-800">Balance Global</h3>
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  if (!balance) {
    return (
      <div className="p-4 bg-gray-100 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Balance Global</h3>
        <p className="text-gray-600">No hay datos de balance disponibles</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
      <h3 className="text-lg font-semibold mb-3 text-green-800">Balance Global ({balance.coin})</h3>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="font-medium text-gray-700">Balance Total:</span>
          <p className="text-green-600 font-semibold">${balance.totalWalletBalance}</p>
        </div>
        <div>
          <span className="font-medium text-gray-700">Disponible:</span>
          <p className="text-blue-600 font-semibold">${balance.totalAvailableBalance}</p>
        </div>
        <div>
          <span className="font-medium text-gray-700">PnL No Realizado:</span>
          <p className={`font-semibold ${
            parseFloat(balance.totalPerpUPL) >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            ${balance.totalPerpUPL}
          </p>
        </div>
        <div>
          <span className="font-medium text-gray-700">Margen Usado:</span>
          <p className="text-orange-600 font-semibold">${balance.totalUsedMargin}</p>
        </div>
      </div>
    </div>
  );
};

export default GlobalBalance;