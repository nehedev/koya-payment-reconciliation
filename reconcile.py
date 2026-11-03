#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime


def parse_amount(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def parse_ts(value):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


latest_by_txn = {}

with open("payments.jsonl", encoding="utf-8") as f:
    for line_no, line in enumerate(f, start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if txn_id is None or str(txn_id).strip() == "":
            continue

        ts = parse_ts(event.get("ts"))
        previous = latest_by_txn.get(txn_id)

        if previous is None or ts is not None and (
            previous[0] is None or ts > previous[0] or (ts == previous[0] and line_no > previous[1])
        ):
            latest_by_txn[txn_id] = (ts, line_no, event)


total = 0.0
count = 0

for _, _, event in latest_by_txn.values():
    if event.get("status") != "success":
        continue

    amount = parse_amount(event.get("amount"))
    if amount is None:
        continue

    total += amount
    count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
