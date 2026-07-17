"""Orchestratore del recap settimanale.

Uso:
    python -m copyfunnel.weekly_recap            # dry-run: genera immagine + testo, non pubblica
    python -m copyfunnel.weekly_recap --post     # pubblica su X (richiede copyfunnel/.env)

Sola lettura sui dati di trading: legge account_snapshot.json e lo storico git.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# la console Windows è cp1252: il testo del post contiene emoji
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from copyfunnel.compose import compose_weekly_post, effective_length
from copyfunnel.history import build_history
from copyfunnel.post_x import post
from copyfunnel.render import render_recap, render_trades
from copyfunnel.stats import account_stats, window_stats

COPY_URL = "https://ct.spotware.com/copy/strategy/115617"
MAX_SNAPSHOT_AGE_HOURS = 24

# Community X a rotazione settimanale (mai lo stesso post in più community:
# X penalizza i duplicati). Iscrizioni fatte il 17/07/2026.
COMMUNITIES = [
    ("FOREX TRADING (43k)", "https://x.com/i/communities/1593968992296787970"),
    ("Future Traders (9k)", "https://x.com/i/communities/1884247281366618267"),
    ("X Forex Trading (8k)", "https://x.com/i/communities/1735157404684128669"),
    ("Investing Forex/Crypto (7k)", "https://x.com/i/communities/1744219889718407196"),
]


def community_della_settimana(giorno) -> tuple:
    """(nome, url) della community dove postare il recap questa settimana."""
    settimana = giorno.isocalendar()[1]
    return COMMUNITIES[settimana % len(COMMUNITIES)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Recap settimanale XybridFX")
    parser.add_argument("--post", action="store_true",
                        help="pubblica su X via API (default: dry-run)")
    parser.add_argument("--no-link", action="store_true",
                        help="modalità documentazione: recap senza link copy (fase rossa)")
    parser.add_argument("--telegram", action="store_true",
                        help="invia immagine + testo su Telegram per pubblicazione manuale")
    parser.add_argument("--days", type=int, default=7,
                        help="finestra del recap in giorni (default 7)")
    parser.add_argument("--out-dir", default=None,
                        help="cartella output (default: copyfunnel/out)")
    args = parser.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = args.out_dir or os.path.join(repo, "copyfunnel", "out")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(repo, "account_snapshot.json"),
              encoding="utf-8-sig") as f:
        snapshot = json.load(f)

    snap_time = datetime.fromisoformat(snapshot["timestamp"])
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    age_hours = (now_utc - snap_time).total_seconds() / 3600
    if age_hours > MAX_SNAPSHOT_AGE_HOURS:
        print(f"✗ Snapshot vecchio di {age_hours:.0f}h (>{MAX_SNAPSHOT_AGE_HOURS}h): "
              "niente post con dati stantii. Controlla la VPS.")
        return 1

    print("Ricostruzione equity curve dallo storico git...")
    rows = build_history(repo, os.path.join(out_dir, "equity_history.csv"))
    print(f"  {len(rows)} punti equity")

    now = snap_time
    week = window_stats(snapshot.get("history", []),
                        start=now - timedelta(days=args.days), end=now)
    account = account_stats(snapshot)

    # trade chiusi nella finestra: tabella "ricevute" + cashtag delle coppie
    trades_week = sorted(
        [t for t in snapshot.get("history", [])
         if now - timedelta(days=args.days)
         <= datetime.fromisoformat(t["close_time"]) <= now],
        key=lambda t: t["close_time"])
    symbols = [t["symbol"] for t in trades_week]

    # il grafico copre la stessa finestra del recap (default: la settimana)
    rows_week = [r for r in rows
                 if datetime.fromisoformat(r["timestamp"]) >= now - timedelta(days=args.days)]

    image_path = os.path.join(out_dir, "recap.png")
    render_recap(rows_week, week, account, image_path)
    trades_path = os.path.join(out_dir, "trades.png")
    render_trades(trades_week, account["currency"], trades_path)
    text = compose_weekly_post(week, account,
                               None if args.no_link else COPY_URL,
                               symbols=symbols)

    print(f"\n─── Testo del post ({effective_length(text)}/280) ───")
    print(text)
    print(f"─── Immagini: {image_path} + {trades_path} ───\n")

    if args.telegram:
        esito = invia_telegram(repo, [image_path, trades_path], text)
        print(esito)
        return 0

    result = post(text, image_path=image_path, dry_run=not args.post,
                  preview_path=os.path.join(out_dir, "preview.txt"),
                  env_path=os.path.join(repo, "copyfunnel", ".env"))
    if result.get("error"):
        print(f"✗ {result['error']}")
        return 1
    print("✓ Pubblicato su X" if result["posted"]
          else "✓ Dry-run completato (nessuna pubblicazione)")
    return 0


def invia_telegram(repo: str, image_paths: list, text: str) -> str:
    """Manda le immagini + testo del recap su Telegram (pubblicazione manuale su X)."""
    import time

    import requests

    from copyfunnel.post_x import _load_env_file

    _load_env_file(os.path.join(repo, "copyfunnel", ".env"))
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return ("✗ TELEGRAM_TOKEN/TELEGRAM_CHAT_ID mancanti in copyfunnel/.env")

    from datetime import date
    nome_com, url_com = community_della_settimana(date.today())
    caption = ("RECAP SETTIMANALE per X — pubblica manualmente:\n"
               "1. salva le immagini  2. copia il testo qui sotto\n"
               "3. nuovo post su x.com con entrambe le immagini + testo\n"
               f"4. COMMUNITY della settimana: {nome_com}\n"
               f"   {url_com}\n"
               "   (nel composer scegli la community dal menu in alto, "
               "al posto di 'Chiunque')\n\n"
               "— TESTO da copiare —\n" + text)
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    media = [{"type": "photo", "media": f"attach://img{i}",
              **({"caption": caption} if i == 0 else {})}
             for i in range(len(image_paths))]
    for tentativo in range(3):
        try:
            files = {f"img{i}": open(p, "rb") for i, p in enumerate(image_paths)}
            try:
                r = requests.post(url, data={"chat_id": chat,
                                             "media": json.dumps(media)},
                                  files=files, timeout=120)
            finally:
                for f in files.values():
                    f.close()
            r.raise_for_status()
            return "✓ Recap inviato su Telegram (2 immagini)"
        except Exception as e:
            ultimo = e
            time.sleep(3)
    return f"✗ Invio Telegram fallito dopo 3 tentativi: {type(ultimo).__name__}"


if __name__ == "__main__":
    sys.exit(main())
