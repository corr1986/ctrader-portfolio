"""Immagine recap: equity curve + pannello statistiche, tema scuro."""
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

BG = "#0d1117"
FG = "#e6edf3"
ACCENT = "#3fb950"
ACCENT_NEG = "#f85149"
GRID = "#21262d"


def render_recap(rows: list, week: dict, account: dict,
                 out_path: str, title: str = "XybridFX — Weekly Recap") -> None:
    """Genera il PNG del recap dai punti equity e dalle statistiche."""
    times = [datetime.fromisoformat(r["timestamp"]) for r in rows]
    equity = [r["equity"] for r in rows]
    balance = [r["balance"] for r in rows]
    cur = "€" if account.get("currency", "EUR") == "EUR" else account["currency"]

    fig, (ax, ax_stats) = plt.subplots(
        2, 1, figsize=(10, 7.5), height_ratios=[3, 1],
        facecolor=BG, dpi=150,
    )

    ax.set_facecolor(BG)
    ax.plot(times, equity, color=ACCENT, linewidth=1.8, label="Equity")
    ax.plot(times, balance, color="#58a6ff", linewidth=1.2,
            alpha=0.7, label="Balance")
    ax.fill_between(times, equity, min(equity), color=ACCENT, alpha=0.08)
    ax.grid(color=GRID, linewidth=0.6)
    ax.tick_params(colors=FG, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9)
    ax.set_title(title, color=FG, fontsize=15, fontweight="bold", pad=12)

    ax_stats.set_facecolor(BG)
    ax_stats.axis("off")
    from copyfunnel.compose import weekly_pct

    pnl_color = ACCENT if week["net_pnl"] >= 0 else ACCENT_NEG
    sign = "+" if week["net_pnl"] >= 0 else ""
    pct = weekly_pct(week, account)
    pct_sign = "+" if pct >= 0 else ""
    cells = [
        (f"{sign}{cur}{week['net_pnl']:.2f}", "Week P&L", pnl_color),
        (f"{pct_sign}{pct:.2f}%", "Week %", pnl_color),
        (f"{cur}{account['balance']:,.0f}", "Balance", FG),
        (f"{week['trades']} / {week['win_rate']:.0f}%", "Trades / Win", FG),
    ]
    for i, (value, label, color) in enumerate(cells):
        x = 0.125 + i * 0.25
        ax_stats.text(x, 0.62, value, color=color, fontsize=17,
                      fontweight="bold", ha="center",
                      transform=ax_stats.transAxes)
        ax_stats.text(x, 0.28, label, color="#8b949e", fontsize=9.5,
                      ha="center", transform=ax_stats.transAxes)

    fig.text(0.5, 0.015, "Real account · updated hourly on GitHub · past ≠ future",
             color="#8b949e", fontsize=8.5, ha="center")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)


def render_trades(trades: list, currency: str, out_path: str,
                  title: str = "XybridFX — Closed Trades") -> None:
    """Tabella 'ricevute': i trade chiusi della settimana, P&L colorato."""
    cur = "€" if currency == "EUR" else currency
    n = max(len(trades), 1)
    fig_h = 1.8 + 0.52 * n
    fig, ax = plt.subplots(figsize=(10, fig_h), facecolor=BG, dpi=150)
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_title(title, color=FG, fontsize=15, fontweight="bold", pad=16)

    intestazioni = ["Date", "Pair", "Side", "Lots", "Pips", "P&L"]
    xs = [0.06, 0.26, 0.44, 0.58, 0.72, 0.90]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, n + 1.3)

    for x, h in zip(xs, intestazioni):
        ax.text(x, n + 0.8, h, color="#8b949e", fontsize=11,
                fontweight="bold", ha="center")
    ax.plot([0.02, 0.98], [n + 0.45, n + 0.45], color=GRID, linewidth=1)

    if not trades:
        ax.text(0.5, n / 2, "No trades closed this week",
                color="#8b949e", fontsize=13, ha="center")
    for i, t in enumerate(trades):
        y = n - i - 0.15
        if i % 2 == 0:
            ax.axhspan(y - 0.38, y + 0.42, color="#111823", zorder=0)
        pnl = t["pnl"]
        colore = ACCENT if pnl >= 0 else ACCENT_NEG
        data = datetime.fromisoformat(t["close_time"]).strftime("%d %b")
        valori = [
            (data, FG), (t["symbol"], FG), (t["direction"], FG),
            (f"{float(t['lots']):.2f}", FG),
            (f"{float(t.get('pips', 0)):+.0f}", colore),
            (f"{'+' if pnl >= 0 else ''}{cur}{pnl:.2f}", colore),
        ]
        for x, (v, c) in zip(xs, valori):
            ax.text(x, y, v, color=c, fontsize=12, ha="center",
                    fontweight="bold" if x == xs[-1] else "normal")

    fig.text(0.5, 0.02, "Real account · every trade published · past ≠ future",
             color="#8b949e", fontsize=8.5, ha="center")
    fig.savefig(out_path, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
