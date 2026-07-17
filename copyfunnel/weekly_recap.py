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
from copyfunnel.render import render_recap
from copyfunnel.stats import account_stats, window_stats

COPY_URL = "https://ct.spotware.com/copy/strategy/115617"
MAX_SNAPSHOT_AGE_HOURS = 24


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

    rows_30d = [r for r in rows
                if datetime.fromisoformat(r["timestamp"]) >= now - timedelta(days=30)]

    image_path = os.path.join(out_dir, "recap.png")
    render_recap(rows_30d, week, account, image_path)
    text = compose_weekly_post(week, account,
                               None if args.no_link else COPY_URL)

    print(f"\n─── Testo del post ({effective_length(text)}/280) ───")
    print(text)
    print(f"─── Immagine: {image_path} ───\n")

    if args.telegram:
        esito = invia_telegram(repo, image_path, text)
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


def invia_telegram(repo: str, image_path: str, text: str) -> str:
    """Manda immagine + testo del recap su Telegram (pubblicazione manuale su X)."""
    import time

    import requests

    from copyfunnel.post_x import _load_env_file

    _load_env_file(os.path.join(repo, "copyfunnel", ".env"))
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return ("✗ TELEGRAM_TOKEN/TELEGRAM_CHAT_ID mancanti in copyfunnel/.env")

    caption = ("RECAP SETTIMANALE per X — pubblica manualmente:\n"
               "1. salva l'immagine  2. copia il testo qui sotto  "
               "3. nuovo post su x.com con immagine + testo\n\n"
               "— TESTO da copiare —\n" + text)
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    for tentativo in range(3):
        try:
            with open(image_path, "rb") as f:
                r = requests.post(url, data={"chat_id": chat, "caption": caption},
                                  files={"photo": f}, timeout=90)
            r.raise_for_status()
            return "✓ Recap inviato su Telegram"
        except Exception as e:
            ultimo = e
            time.sleep(3)
    return f"✗ Invio Telegram fallito dopo 3 tentativi: {type(ultimo).__name__}"


if __name__ == "__main__":
    sys.exit(main())
