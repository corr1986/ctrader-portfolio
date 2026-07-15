"""Smoke test per render.py e test dry-run per post_x.py."""
import os

from copyfunnel.post_x import post
from copyfunnel.render import render_recap

ROWS = [
    {"timestamp": f"2026-07-{d:02d}T10:00:00", "balance": 3200.0 + d,
     "equity": 3180.0 + d * 3, "commit": str(d)}
    for d in range(1, 15)
]
WEEK = {"trades": 12, "wins": 9, "losses": 3, "win_rate": 75.0,
        "net_pnl": 23.40, "best": 6.15, "worst": -4.65}
ACCOUNT = {"balance": 3267.23, "equity": 3347.21, "floating": 79.98,
           "open_positions": 21, "total_trades": 67, "win_rate": 73.1,
           "currency": "EUR"}


def test_render_creates_png(tmp_path):
    out = tmp_path / "recap.png"
    render_recap(ROWS, WEEK, ACCOUNT, dd_30d=8.2, out_path=str(out))
    assert out.exists()
    assert os.path.getsize(out) > 1000


def test_post_dry_run_writes_preview_and_does_not_need_keys(tmp_path):
    preview = tmp_path / "preview.txt"
    result = post("hello world", image_path=None, dry_run=True,
                  preview_path=str(preview))
    assert result["posted"] is False
    assert result["dry_run"] is True
    assert preview.exists()
    assert "hello world" in preview.read_text(encoding="utf-8")


def test_post_without_credentials_refuses_to_post(tmp_path, monkeypatch):
    for var in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"):
        monkeypatch.delenv(var, raising=False)
    result = post("hello", image_path=None, dry_run=False,
                  preview_path=str(tmp_path / "p.txt"))
    assert result["posted"] is False
    assert "credenziali" in result["error"].lower()
