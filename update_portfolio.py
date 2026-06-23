"""
update_portfolio.py — Legge snapshot cTrader e aggiorna Portfolio Forex su Obsidian/GitHub.
Gira sulla VPS via Windows Scheduled Task ogni 30-60 minuti.
"""

import json
import os
import shutil
import subprocess
from datetime import datetime

# ─── CONFIGURAZIONE ────────────────────────────────────────────────────────────
SNAPSHOT_PATH  = r"C:\AccountMonitor\snapshot.json"
REPO_PATH      = r"C:\AccountMonitor\ctrader-portfolio"   # cartella git clonata
MD_FILENAME    = "Portfolio Forex.md"
JSON_FILENAME  = "account_snapshot.json"
GITHUB_REPO    = "https://github.com/corr1986/ctrader-portfolio.git"
# ───────────────────────────────────────────────────────────────────────────────


def load_snapshot() -> dict:
    with open(SNAPSHOT_PATH, encoding="utf-8-sig") as f:
        return json.load(f)


def fmt_pnl(value: float, currency: str) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f} {currency}"


def fmt_price(value) -> str:
    if value is None:
        return "—"
    return f"{float(value):.5f}"


# ─── Breakdown per strategia (raggruppamento per label) ─────────────────────────
STRATEGY_ORDER = ["GridMartingala", "TRFX Extra", "TRFX Signal"]


def classify_label(label) -> str:
    """Mappa la label di una posizione al gruppo strategia."""
    lb = label or ""
    if lb == "GridMartDailyFinalFixed":
        return "GridMartingala"
    if lb == "TRFX_EXTRA":
        return "TRFX Extra"
    if lb.startswith("TRFX_EXTRA_") or "SIGNAL" in lb.upper():
        return "TRFX Signal"
    return "Altro"


def aggregate_by_strategy(positions: list) -> dict:
    """Somma P&L e conta le posizioni aperte per gruppo strategia."""
    agg: dict = {}
    for p in positions:
        g = classify_label(p.get("label"))
        bucket = agg.setdefault(g, {"pnl": 0.0, "count": 0})
        bucket["pnl"] += p["pnl"]
        bucket["count"] += 1
    return agg


def strategy_table(positions: list, balance: float, currency: str) -> str:
    """Tabella markdown: P&L non realizzato e % sul balance per ogni strategia."""
    if not positions:
        return "## Performance per strategia\n*Nessuna posizione aperta.*\n"

    agg = aggregate_by_strategy(positions)
    lines = [
        "## Performance per strategia",
        "*P&L non realizzato delle posizioni aperte, % sul balance del conto.*",
        "| Strategia | Pos | P&L | % su balance |",
        "|---|---|---|---|",
    ]
    # ordine fisso noto, poi eventuali gruppi imprevisti (Altro) in coda
    groups = [g for g in STRATEGY_ORDER if g in agg]
    groups += [g for g in agg if g not in STRATEGY_ORDER]

    tot_pnl, tot_cnt = 0.0, 0
    for g in groups:
        pnl, cnt = agg[g]["pnl"], agg[g]["count"]
        tot_pnl += pnl
        tot_cnt += cnt
        pct = (pnl / balance * 100) if balance else 0.0
        lines.append(f"| {g} | {cnt} | {fmt_pnl(pnl, currency)} | {pct:+.2f}% |")

    tot_pct = (tot_pnl / balance * 100) if balance else 0.0
    lines.append(
        f"| **Totale** | **{tot_cnt}** | **{fmt_pnl(tot_pnl, currency)}** "
        f"| **{tot_pct:+.2f}%** |"
    )
    return "\n".join(lines) + "\n"


def positions_table(positions: list, currency: str) -> str:
    if not positions:
        return "## Posizioni aperte\n*Nessuna posizione aperta.*\n"

    lines = [
        "## Posizioni aperte",
        "| Symbol | Dir | Lotti | Entry | Corrente | P&L | Pips | SL | TP | Label |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for p in positions:
        sl = fmt_price(p.get("sl"))
        tp = fmt_price(p.get("tp"))
        label = p.get("label") or "—"
        lines.append(
            f"| {p['symbol']} | {p['direction']} | {float(p['lots']):.2f} "
            f"| {fmt_price(p['entry_price'])} | {fmt_price(p['current_price'])} "
            f"| {fmt_pnl(p['pnl'], currency)} | {float(p['pips']):.1f} "
            f"| {sl} | {tp} | {label} |"
        )
    return "\n".join(lines) + "\n"


def history_table(history: list, currency: str, limit: int = 15) -> str:
    if not history:
        return "## Ultimi trade chiusi\n*Nessun trade chiuso.*\n"

    lines = [
        "## Ultimi trade chiusi",
        "| Chiusura | Symbol | Dir | Lotti | Entry | Close | P&L | Pips |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t in history[:limit]:
        close_dt = datetime.fromisoformat(t["close_time"]).strftime("%d/%m %H:%M")
        lines.append(
            f"| {close_dt} | {t['symbol']} | {t['direction']} | {float(t['lots']):.2f} "
            f"| {fmt_price(t['entry_price'])} | {fmt_price(t['close_price'])} "
            f"| {fmt_pnl(t['pnl'], currency)} | {float(t['pips']):.1f} |"
        )
    return "\n".join(lines) + "\n"


def generate_markdown(data: dict) -> str:
    ts = datetime.fromisoformat(data["timestamp"]).strftime("%d/%m/%Y %H:%M")
    cur = data["currency"]
    total = data["wins"] + data["losses"]
    wl = f"{data['wins']}W / {data['losses']}L"

    summary = f"""## Riepilogo
| Voce | Valore |
|---|---|
| Balance | {data['balance']:.2f} {cur} |
| Equity | {data['equity']:.2f} {cur} |
| P&L non realizzato | {fmt_pnl(data['unrealized_pnl'], cur)} |
| P&L realizzato totale | {fmt_pnl(data['realized_pnl'], cur)} |
| Posizioni aperte | {data['open_positions']} |
| Trade chiusi totali | {total} ({wl}) |
| Win Rate | {data['win_rate']:.1f}% |"""

    strat_section = strategy_table(data.get("positions", []), data["balance"], cur)
    pos_section   = positions_table(data.get("positions", []), cur)
    hist_section  = history_table(data.get("history", []), cur)

    return f"""# Portfolio Forex — cTrader
*Aggiornato: {ts} UTC*

[📊 Vedi snapshot JSON su GitHub](https://github.com/corr1986/ctrader-portfolio/blob/main/{JSON_FILENAME})

---

{summary}

---

{strat_section}
---

{pos_section}
---

{hist_section}
---

[[Portfolio V1]] | [[Portfolio V3]] | [[Portfolio Insider]]
"""


def git_push(repo_path: str, message: str) -> bool:
    try:
        subprocess.run(["git", "-C", repo_path, "add", MD_FILENAME, JSON_FILENAME],
                       check=True, capture_output=True)
        result = subprocess.run(["git", "-C", repo_path, "commit", "-m", message],
                                capture_output=True, text=True)
        if result.returncode != 0 and "nothing to commit" in result.stdout:
            print("Nessuna modifica da committare.")
            return True
        # pull --rebase prima del push: assorbe eventuali aggiornamenti di codice
        # committati dal locale, evita che la VPS si blocchi su push non fast-forward
        subprocess.run(["git", "-C", repo_path, "pull", "--rebase", "origin", "main"],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", repo_path, "push"], check=True, capture_output=True)
        print(f"✓ Push GitHub: {message}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Git error: {e.stderr}")
        return False


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Aggiornamento portfolio forex...")

    if not os.path.exists(SNAPSHOT_PATH):
        print(f"✗ Snapshot non trovato: {SNAPSHOT_PATH}")
        print("  Verifica che AccountMonitor.cs stia girando in cTrader.")
        return

    data = load_snapshot()

    md_path   = os.path.join(REPO_PATH, MD_FILENAME)
    json_path = os.path.join(REPO_PATH, JSON_FILENAME)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown(data))

    shutil.copy(SNAPSHOT_PATH, json_path)

    ts_commit = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    git_push(REPO_PATH, f"Portfolio update {ts_commit} UTC")

    print(f"✓ Fatto. Balance: {data['balance']:.2f} {data['currency']} | "
          f"Equity: {data['equity']:.2f} | Posizioni: {data['open_positions']}")


if __name__ == "__main__":
    main()
