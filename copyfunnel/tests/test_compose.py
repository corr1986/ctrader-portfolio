"""Test per compose.py — testo del post X entro 280 caratteri."""
from copyfunnel.compose import TCO_URL_LEN, compose_weekly_post, effective_length

COPY_URL = "https://ct.spotware.com/copy/strategy/115617"

WEEK = {"trades": 12, "wins": 9, "losses": 3, "win_rate": 75.0,
        "net_pnl": 23.40, "best": 6.15, "worst": -4.65}
ACCOUNT = {"balance": 3267.23, "equity": 3347.21, "floating": 79.98,
           "open_positions": 21, "total_trades": 67, "win_rate": 73.1,
           "currency": "EUR"}


def test_post_contains_key_numbers_and_url():
    text = compose_weekly_post(WEEK, ACCOUNT, dd_30d=8.2, copy_url=COPY_URL)
    assert COPY_URL in text
    assert "23.40" in text
    assert "12" in text          # numero trade
    assert "75" in text          # win rate settimana
    assert "8.2" in text         # drawdown

def test_post_within_280_chars_with_tco_url():
    text = compose_weekly_post(WEEK, ACCOUNT, dd_30d=8.2, copy_url=COPY_URL)
    assert effective_length(text) <= 280


def test_negative_week_is_stated_plainly():
    week = dict(WEEK, net_pnl=-31.75, wins=4, losses=8, win_rate=33.3)
    text = compose_weekly_post(week, ACCOUNT, dd_30d=12.5, copy_url=COPY_URL)
    assert "-31.75" in text
    assert effective_length(text) <= 280


def test_effective_length_counts_urls_as_23():
    # una URL lunga conta come 23 (t.co), il resto carattere per carattere
    text = "abc " + COPY_URL
    assert effective_length(text) == 4 + TCO_URL_LEN


def test_post_senza_link_in_modalita_documentazione():
    # copy_url=None → fase rossa: si documenta senza promuovere
    text = compose_weekly_post(WEEK, ACCOUNT, dd_30d=8.2, copy_url=None)
    assert "ct.spotware.com" not in text
    assert "Documenting" in text
    assert effective_length(text) <= 280


def test_effective_length_counts_emoji_as_2():
    # X pesa 2 i caratteri fuori dai range "leggeri" (emoji inclusi)
    assert effective_length("ab📊") == 4
    assert effective_length("✅") == 2
    # ma lettere accentate e trattini lunghi restano 1
    assert effective_length("è—") == 2
