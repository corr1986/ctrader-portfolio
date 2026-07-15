"""Statistiche trade-based dal snapshot cTrader.

Le percentuali di ROI sull'equity sarebbero inquinate da depositi/prelievi
(che AccountMonitor non distingue), quindi il recap riporta P&L in valuta
sui trade chiusi nella finestra, più lo stato corrente del conto.
"""
from datetime import datetime


def window_stats(trades: list, start: datetime, end: datetime) -> dict:
    """Statistiche sui trade chiusi nella finestra [start, end)."""
    in_window = [
        t for t in trades
        if start <= datetime.fromisoformat(t["close_time"]) < end
    ]
    wins = [t for t in in_window if t["pnl"] > 0]
    losses = [t for t in in_window if t["pnl"] <= 0]
    pnls = [t["pnl"] for t in in_window]
    n = len(in_window)
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
        "net_pnl": sum(pnls),
        "best": max(pnls) if pnls else None,
        "worst": min(pnls) if pnls else None,
    }


def account_stats(snapshot: dict) -> dict:
    """Stato corrente del conto dal snapshot."""
    return {
        "balance": snapshot["balance"],
        "equity": snapshot["equity"],
        "floating": snapshot["unrealized_pnl"],
        "open_positions": snapshot["open_positions"],
        "total_trades": snapshot["total_trades"],
        "win_rate": snapshot["win_rate"],
        "currency": snapshot.get("currency", "EUR"),
    }


def max_drawdown(equity_series: list) -> float:
    """Max drawdown percentuale dal picco, sulla serie equity."""
    peak = float("-inf")
    dd = 0.0
    for v in equity_series:
        peak = max(peak, v)
        if peak > 0:
            dd = max(dd, (peak - v) / peak * 100)
    return dd
