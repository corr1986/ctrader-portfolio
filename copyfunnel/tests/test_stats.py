"""Test per stats.py — statistiche trade-based e drawdown."""
from datetime import datetime

from copyfunnel.stats import account_stats, max_drawdown, window_stats

TRADES = [
    {"pnl": 3.21, "close_time": "2026-07-06T10:00:00", "symbol": "EURUSD"},
    {"pnl": -4.65, "close_time": "2026-07-08T12:00:00", "symbol": "AUDNZD"},
    {"pnl": 6.15, "close_time": "2026-07-10T09:00:00", "symbol": "GBPUSD"},
    {"pnl": 0.49, "close_time": "2026-07-13T15:00:00", "symbol": "USDCHF"},
    # fuori finestra (troppo vecchio)
    {"pnl": 99.0, "close_time": "2026-06-01T10:00:00", "symbol": "XAUUSD"},
]


def test_window_stats_counts_only_trades_in_window():
    s = window_stats(TRADES, start=datetime(2026, 7, 6), end=datetime(2026, 7, 14))
    assert s["trades"] == 4
    assert s["wins"] == 3
    assert s["losses"] == 1
    assert s["win_rate"] == 75.0
    assert round(s["net_pnl"], 2) == 5.20
    assert s["best"] == 6.15
    assert s["worst"] == -4.65


def test_window_stats_empty_window():
    s = window_stats(TRADES, start=datetime(2026, 1, 1), end=datetime(2026, 1, 7))
    assert s["trades"] == 0
    assert s["win_rate"] == 0.0
    assert s["net_pnl"] == 0.0
    assert s["best"] is None and s["worst"] is None


def test_account_stats_reads_snapshot_fields():
    snap = {
        "balance": 3267.23, "equity": 3347.21, "unrealized_pnl": 79.98,
        "open_positions": 21, "total_trades": 67, "wins": 49, "losses": 18,
        "win_rate": 73.1, "currency": "EUR",
    }
    a = account_stats(snap)
    assert a["balance"] == 3267.23
    assert a["equity"] == 3347.21
    assert a["floating"] == 79.98
    assert a["open_positions"] == 21
    assert a["win_rate"] == 73.1
    assert a["currency"] == "EUR"


def test_max_drawdown_simple_peak_trough():
    # picco 110 → minimo 88 = -20%
    series = [100.0, 110.0, 95.0, 88.0, 105.0]
    assert round(max_drawdown(series), 1) == 20.0


def test_max_drawdown_monotonic_rise_is_zero():
    assert max_drawdown([100.0, 101.0, 102.0]) == 0.0


def test_max_drawdown_empty_series():
    assert max_drawdown([]) == 0.0
