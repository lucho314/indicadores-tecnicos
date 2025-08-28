import { create } from "zustand";

interface BalanceData {
  totalWalletBalance: string;
  totalAvailableBalance: string;
  totalPerpUPL: string;
  totalUsedMargin: string;
  totalOrderIM: string;
  totalPositionIM: string;
  totalPositionMM: string;
  coin: string;
}

interface BalanceState {
  balance: BalanceData | null;
  isLoading: boolean;
  error: string | null;
  setBalance: (balance: BalanceData | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearBalance: () => void;
}

export const useBalanceStore = create<BalanceState>((set, get) => ({
  balance: null,
  isLoading: false,
  error: null,
  setBalance: (balance) => {
    const currentBalance = get().balance;
    // Solo actualizar si los datos son diferentes
    if (
      !currentBalance ||
      JSON.stringify(currentBalance) !== JSON.stringify(balance)
    ) {
      set({ balance, error: null });
    }
  },
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
  clearBalance: () => set({ balance: null, error: null, isLoading: false }),
}));
