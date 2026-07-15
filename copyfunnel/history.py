"""Ricostruzione della serie equity/balance dallo storico git di account_snapshot.json.

La VPS committa lo snapshot ogni ora: ogni commit è un punto della curva.
La cache csv evita di rileggere i ~1500 commit a ogni run.
"""
import csv
import json
import os
import subprocess

SNAPSHOT_FILE = "account_snapshot.json"
CSV_FIELDS = ["commit", "timestamp", "balance", "equity"]


def _git(repo_path: str, *args) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path, *args],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout


def load_csv(csv_path: str) -> list:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["balance"] = float(r["balance"])
        r["equity"] = float(r["equity"])
    return rows


def _save_csv(csv_path: str, rows: list) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_history(repo_path: str, csv_path: str) -> list:
    """Aggiorna la cache csv con i commit nuovi e restituisce tutte le righe."""
    rows = load_csv(csv_path)
    known = {r["commit"] for r in rows}

    all_commits = _git(
        repo_path, "log", "--reverse", "--format=%H", "--", SNAPSHOT_FILE
    ).split()

    for commit in all_commits:
        if commit in known:
            continue
        try:
            raw = _git(repo_path, "show", f"{commit}:{SNAPSHOT_FILE}")
            snap = json.loads(raw.lstrip("﻿"))
            rows.append({
                "commit": commit,
                "timestamp": snap["timestamp"],
                "balance": float(snap["balance"]),
                "equity": float(snap["equity"]),
            })
        except (json.JSONDecodeError, KeyError, subprocess.CalledProcessError):
            continue  # snapshot malformato o commit illeggibile: punto saltato

    rows.sort(key=lambda r: r["timestamp"])
    _save_csv(csv_path, rows)
    return rows
