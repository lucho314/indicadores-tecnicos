import { useEffect, useRef, useState } from "react";

type TickerData = { symbol: string; lastPrice: string };

const WS_URL = "wss://stream.bybit.com/v5/public/spot";
const READY = { CONNECTING: 0, OPEN: 1, CLOSING: 2, CLOSED: 3 } as const;

export function useBybitTicker(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, string>>({});
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<number | null>(null);

  // Evitá re-ejecutar el efecto por referencias distintas del array
  const symbolsKey = JSON.stringify([...symbols].sort());

  const safeSend = (obj: any) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== READY.OPEN) return false;
    ws.send(JSON.stringify(obj));
    return true;
  };

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      safeSend({
        op: "subscribe",
        args: symbols.map((s) => `tickers.${s}`),
      });

      // ping cada 20s SOLO si está OPEN
      if (pingRef.current) clearInterval(pingRef.current);
      pingRef.current = window.setInterval(() => {
        safeSend({ op: "ping" });
      }, 20000);
    };

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg?.topic?.startsWith("tickers.")) {
        const d: TickerData = msg.data;
        if (d?.symbol && d?.lastPrice) {
          setPrices((p) => ({ ...p, [d.symbol]: d.lastPrice }));
        }
      }
    };

    ws.onclose = () => {
      if (pingRef.current) {
        clearInterval(pingRef.current);
        pingRef.current = null;
      }
    };

    ws.onerror = () => {
      // Dejá que onclose limpie; podrías loguear si querés
    };

    return () => {
      if (pingRef.current) {
        clearInterval(pingRef.current);
        pingRef.current = null;
      }
      try { ws.close(); } catch {}
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbolsKey]);

  return prices;
}
