"""Test per il breakdown per strategia in update_portfolio.py."""

from update_portfolio import classify_label, aggregate_by_strategy, strategy_table


# ─── classify_label ────────────────────────────────────────────────────────────

def test_classify_gridmartingala():
    assert classify_label("GridMartDailyFinalFixed") == "GridMartingala"


def test_classify_trfx_extra_base():
    assert classify_label("TRFX_EXTRA") == "TRFX Extra"


def test_classify_trfx_extra_numbered_is_signal():
    assert classify_label("TRFX_EXTRA_001") == "TRFX Signal"
    assert classify_label("TRFX_EXTRA_014") == "TRFX Signal"


def test_classify_explicit_signal_label():
    # Robustezza futura: una label che contiene SIGNAL va in TRFX Signal
    assert classify_label("TRFX_SIGNAL_EURUSD") == "TRFX Signal"


def test_classify_unknown_goes_to_altro():
    assert classify_label("QualcosaDiNuovo") == "Altro"
    assert classify_label("") == "Altro"
    assert classify_label(None) == "Altro"


# ─── aggregate_by_strategy ──────────────────────────────────────────────────────

def _pos(label, pnl):
    return {"label": label, "pnl": pnl}


def test_aggregate_sums_pnl_and_counts():
    positions = [
        _pos("GridMartDailyFinalFixed", -50.0),
        _pos("GridMartDailyFinalFixed", -40.0),
        _pos("TRFX_EXTRA", -12.0),
        _pos("TRFX_EXTRA_001", 10.0),
        _pos("TRFX_EXTRA_002", 14.0),
    ]
    agg = aggregate_by_strategy(positions)
    assert agg["GridMartingala"] == {"pnl": -90.0, "count": 2}
    assert agg["TRFX Extra"] == {"pnl": -12.0, "count": 1}
    assert agg["TRFX Signal"] == {"pnl": 24.0, "count": 2}


def test_aggregate_empty():
    assert aggregate_by_strategy([]) == {}


def test_aggregate_unknown_label_kept_as_altro():
    agg = aggregate_by_strategy([_pos("Mistero", 5.0)])
    assert agg["Altro"] == {"pnl": 5.0, "count": 1}


# ─── strategy_table (markdown) ──────────────────────────────────────────────────

def test_strategy_table_contains_groups_and_percentages():
    positions = [
        _pos("GridMartDailyFinalFixed", -190.69),
        _pos("TRFX_EXTRA", -12.12),
        _pos("TRFX_EXTRA_001", 24.04),
    ]
    table = strategy_table(positions, balance=2482.90, currency="EUR")
    assert "Performance per strategia" in table
    assert "GridMartingala" in table
    assert "TRFX Extra" in table
    assert "TRFX Signal" in table
    # -190.69 / 2482.90 * 100 = -7.68%
    assert "-7.68%" in table
    # P&L in EUR presente
    assert "-190.69" in table


def test_strategy_table_empty_positions():
    table = strategy_table([], balance=2482.90, currency="EUR")
    assert "Performance per strategia" in table
    assert "Nessuna posizione" in table


def test_strategy_table_order_grid_first():
    positions = [
        _pos("TRFX_EXTRA_001", 1.0),
        _pos("TRFX_EXTRA", 1.0),
        _pos("GridMartDailyFinalFixed", 1.0),
    ]
    table = strategy_table(positions, balance=1000.0, currency="EUR")
    i_grid = table.index("GridMartingala")
    i_extra = table.index("TRFX Extra")
    i_signal = table.index("TRFX Signal")
    assert i_grid < i_extra < i_signal
