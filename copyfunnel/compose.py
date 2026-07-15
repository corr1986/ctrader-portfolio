"""Composizione del testo del post X (inglese, entro 280 caratteri)."""

TCO_URL_LEN = 23  # X riscrive ogni URL come t.co, lunghezza fissa


def effective_length(text: str) -> int:
    """Lunghezza come la conta X: ogni URL vale TCO_URL_LEN."""
    return len(text) - _urls_extra_chars(text)


def _urls_extra_chars(text: str) -> int:
    """Caratteri risparmiati contando le URL come t.co."""
    saved = 0
    for token in text.replace("\n", " ").split(" "):
        if token.startswith("http://") or token.startswith("https://"):
            saved += max(0, len(token) - TCO_URL_LEN)
    return saved


def compose_weekly_post(week: dict, account: dict, dd_30d: float,
                        copy_url: str) -> str:
    """Recap settimanale: numeri veri, anche negativi, più link alla pagina copy."""
    cur = "€" if account.get("currency", "EUR") == "EUR" else account["currency"]
    sign = "+" if week["net_pnl"] >= 0 else ""
    lines = [
        "Weekly recap — real account, 100% automated 🤖",
        "",
        f"📊 Closed P&L: {sign}{cur}{week['net_pnl']:.2f} "
        f"({week['trades']} trades, {week['win_rate']:.0f}% win)",
        f"💼 Equity: {cur}{account['equity']:,.0f} | "
        f"Floating: {'+' if account['floating'] >= 0 else ''}{cur}{account['floating']:.0f}",
        f"📉 Max DD 30d: {dd_30d:.1f}%",
        "",
        f"Copy it on cTrader: {copy_url}",
        "",
        "#forex #copytrading",
    ]
    return "\n".join(lines)
