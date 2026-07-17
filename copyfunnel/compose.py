"""Composizione del testo del post X (inglese, entro 280 caratteri)."""

TCO_URL_LEN = 23  # X riscrive ogni URL come t.co, lunghezza fissa


# range di codepoint che X pesa 1; tutto il resto (emoji compresi) pesa 2
_LIGHT_RANGES = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))


def _char_weight(ch: str) -> int:
    cp = ord(ch)
    return 1 if any(lo <= cp <= hi for lo, hi in _LIGHT_RANGES) else 2


def effective_length(text: str) -> int:
    """Lunghezza come la conta X: URL = TCO_URL_LEN, caratteri pesati."""
    total = 0
    for line in text.split("\n"):
        for token in line.split(" "):
            if token.startswith("http://") or token.startswith("https://"):
                total += TCO_URL_LEN
            else:
                total += sum(_char_weight(c) for c in token)
    # spazi e newline pesano 1 ciascuno
    total += text.count(" ") + text.count("\n")
    return total


def weekly_pct(week: dict, account: dict) -> float:
    """% della settimana sul saldo di inizio settimana (saldo attuale - P&L)."""
    base = account["balance"] - week["net_pnl"]
    return week["net_pnl"] / base * 100 if base else 0.0


def compose_weekly_post(week: dict, account: dict,
                        copy_url: str = None) -> str:
    """Recap settimanale: numeri veri, anche negativi.

    copy_url=None → modalità documentazione (fase rossa): nessun link,
    si costruisce lo storico senza promuovere.
    """
    cur = "€" if account.get("currency", "EUR") == "EUR" else account["currency"]
    sign = "+" if week["net_pnl"] >= 0 else ""
    pct = weekly_pct(week, account)
    pct_sign = "+" if pct >= 0 else ""
    lines = [
        "Weekly recap — real account, 100% automated 🤖",
        "",
        f"📊 Week: {sign}{cur}{week['net_pnl']:.2f} ({pct_sign}{pct:.2f}%) | "
        f"{week['trades']} trades, {week['win_rate']:.0f}% win",
        f"💼 Balance: {cur}{account['balance']:,.0f} | "
        f"Equity: {cur}{account['equity']:,.0f}",
        "",
    ]
    if copy_url:
        lines += [f"Copy it on cTrader: {copy_url}", "", "#forex #copytrading"]
    else:
        lines += ["Documenting every week — reds included. No hype, just the process.",
                  "", "#forex #trading"]
    return "\n".join(lines)
