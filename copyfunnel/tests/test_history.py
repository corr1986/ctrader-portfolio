"""Test per history.py — ricostruzione equity curve dallo storico git."""
import json
import subprocess

import pytest

from copyfunnel.history import build_history, load_csv

SNAP = {"timestamp": "2026-07-01T10:00:00", "balance": 1000.0, "equity": 990.0}


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


@pytest.fixture
def fake_repo(tmp_path):
    """Repo git con 3 commit di account_snapshot.json."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    for i in range(3):
        snap = dict(SNAP, timestamp=f"2026-07-0{i+1}T10:00:00",
                    balance=1000.0 + i * 10, equity=990.0 + i * 10)
        (repo / "account_snapshot.json").write_text(json.dumps(snap))
        _git(repo, "add", "account_snapshot.json")
        _git(repo, "commit", "-m", f"snap {i}")
    return repo


def test_build_history_extracts_all_commits(fake_repo, tmp_path):
    csv_path = tmp_path / "equity_history.csv"
    rows = build_history(str(fake_repo), str(csv_path))
    assert len(rows) == 3
    assert rows[0]["balance"] == 1000.0
    assert rows[2]["equity"] == 1010.0
    # ordine cronologico
    assert rows[0]["timestamp"] < rows[2]["timestamp"]


def test_build_history_is_incremental(fake_repo, tmp_path):
    csv_path = tmp_path / "equity_history.csv"
    build_history(str(fake_repo), str(csv_path))

    # nuovo commit dopo la prima build
    snap = dict(SNAP, timestamp="2026-07-04T10:00:00", balance=1030.0, equity=1025.0)
    (fake_repo / "account_snapshot.json").write_text(json.dumps(snap))
    _git(fake_repo, "add", "account_snapshot.json")
    _git(fake_repo, "commit", "-m", "snap 3")

    rows = build_history(str(fake_repo), str(csv_path))
    assert len(rows) == 4
    assert rows[-1]["balance"] == 1030.0
    # il csv riletto corrisponde
    assert len(load_csv(str(csv_path))) == 4


def test_build_history_skips_malformed_snapshots(fake_repo, tmp_path):
    (fake_repo / "account_snapshot.json").write_text("{ rotto")
    _git(fake_repo, "add", "account_snapshot.json")
    _git(fake_repo, "commit", "-m", "broken")
    csv_path = tmp_path / "equity_history.csv"
    rows = build_history(str(fake_repo), str(csv_path))
    assert len(rows) == 3  # il commit rotto viene saltato senza crash
