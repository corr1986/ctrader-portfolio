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
from copyfunnel.stats import account_stats, max_drawdown, window_stats

COPY_URL = "https://ct.spotware.com/copy/strategy/115617"
MAX_SNAPSHOT_AGE_HOURS = 24


def main() -> int:
    parser = argparse.ArgumentParser(description="Recap settimanale XybridFX")
    parser.add_argument("--post", action="store_true",
                        help="pubblica su X (default: dry-run)")
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
    dd_30d = max_drawdown([r["equity"] for r in rows_30d])

    image_path = os.path.join(out_dir, "recap.png")
    render_recap(rows_30d, week, account, dd_30d, image_path)
    text = compose_weekly_post(week, account, dd_30d, COPY_URL)

    print(f"\n─── Testo del post ({effective_length(text)}/280) ───")
    print(text)
    print(f"─── Immagine: {image_path} ───\n")

    result = post(text, image_path=image_path, dry_run=not args.post,
                  preview_path=os.path.join(out_dir, "preview.txt"),
                  env_path=os.path.join(repo, "copyfunnel", ".env"))
    if result.get("error"):
        print(f"✗ {result['error']}")
        return 1
    print("✓ Pubblicato su X" if result["posted"]
          else "✓ Dry-run completato (nessuna pubblicazione)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
