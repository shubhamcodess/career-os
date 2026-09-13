#!/usr/bin/env python3
"""
Career OS — Connector Budget Ledger

Tracks how many calls Career OS makes to rate-limited connectors and refuses to
go past a self-imposed cap.

This exists because Indeed authenticates as the *user's own account*. Exhausting
its quota does not just fail a job search — it degrades a service they rely on
personally, outside this tool. A job feed refresh that fans out across 25
companies can burn a daily allowance in one command, so the budget is enforced
rather than merely documented.

The cap is a self-imposed budget, not a limit discovered from the provider.
Neither Indeed nor ZipRecruiter publishes a per-account MCP quota, so
config/user.json carries an `assumed_daily_limit` and a `cap_fraction`; the
effective cap is their product. If you learn the real number, change
`assumed_daily_limit` and the cap follows.

Usage:
  python3 scripts/mcp-budget.py status
  python3 scripts/mcp-budget.py check indeed     # exit 0 = go, 1 = budget spent
  python3 scripts/mcp-budget.py record indeed    # after a successful call
  python3 scripts/mcp-budget.py record indeed --count 5
  python3 scripts/mcp-budget.py reset indeed
"""

import argparse
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_CONFIG_PATH = os.path.join(ROOT, "config", "user.json")
LEDGER_PATH = os.path.join(ROOT, "data", "logs", "connector-usage.json")

# Used only when config/user.json says nothing about a connector.
DEFAULTS = {
    "indeed": {"assumed_daily_limit": 100, "cap_fraction": 0.6},
    "ziprecruiter": {"assumed_daily_limit": 100, "cap_fraction": 0.6},
    "dice": {"assumed_daily_limit": 0, "cap_fraction": 0.6},  # 0 = unmetered
}


def load_settings(connector: str) -> dict:
    cfg = {}
    try:
        with open(USER_CONFIG_PATH) as f:
            cfg = json.load(f).get("integrations", {}).get(connector, {}) or {}
    except Exception:
        pass
    base = dict(DEFAULTS.get(connector, {"assumed_daily_limit": 100, "cap_fraction": 0.6}))
    base.update({k: v for k, v in cfg.items() if k in ("assumed_daily_limit", "cap_fraction")})
    return base


def effective_cap(connector: str) -> int:
    s = load_settings(connector)
    limit = int(s.get("assumed_daily_limit") or 0)
    if limit <= 0:
        return 0  # unmetered
    return max(1, int(limit * float(s.get("cap_fraction") or 0.6)))


def load_ledger() -> dict:
    try:
        with open(LEDGER_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_ledger(led: dict) -> None:
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "w") as f:
        json.dump(led, f, indent=2)
        f.write("\n")


def used_today(connector: str, led: dict | None = None) -> int:
    led = led if led is not None else load_ledger()
    return int((led.get(connector) or {}).get(date.today().isoformat(), 0))


def cmd_check(connector: str) -> int:
    cap = effective_cap(connector)
    if cap == 0:
        print(f"{connector}: unmetered — no cap configured", file=sys.stderr)
        return 0
    used = used_today(connector)
    remaining = cap - used
    if remaining <= 0:
        print(f"{connector}: BUDGET SPENT — {used}/{cap} calls used today. "
              f"Use another source, or raise the cap in config/user.json.",
              file=sys.stderr)
        return 1
    if remaining <= max(1, cap // 5):
        print(f"{connector}: {used}/{cap} used — only {remaining} left today",
              file=sys.stderr)
    else:
        print(f"{connector}: {used}/{cap} used, {remaining} remaining", file=sys.stderr)
    return 0


def cmd_record(connector: str, count: int) -> int:
    led = load_ledger()
    today = date.today().isoformat()
    led.setdefault(connector, {})
    led[connector][today] = used_today(connector, led) + count
    # Keep the ledger small — only the last 30 recorded days per connector.
    for c in led:
        days = sorted(led[c])
        for old in days[:-30]:
            led[c].pop(old, None)
    save_ledger(led)
    cap = effective_cap(connector)
    now = led[connector][today]
    suffix = f"/{cap}" if cap else " (unmetered)"
    print(f"{connector}: {now}{suffix} used today", file=sys.stderr)
    return 0


def cmd_status() -> int:
    led = load_ledger()
    names = sorted(set(list(DEFAULTS) + list(led)))
    print(f"Connector budgets — {date.today().isoformat()}", file=sys.stderr)
    for c in names:
        cap = effective_cap(c)
        used = used_today(c, led)
        if cap == 0:
            print(f"  {c:14} {used:>4} used    (unmetered)", file=sys.stderr)
            continue
        s = load_settings(c)
        bar_full = min(10, int(10 * used / cap)) if cap else 0
        bar = "#" * bar_full + "." * (10 - bar_full)
        flag = "  BUDGET SPENT" if used >= cap else ""
        print(f"  {c:14} {used:>4}/{cap:<4} [{bar}]  "
              f"{int(s['cap_fraction'] * 100)}% of assumed {s['assumed_daily_limit']}/day{flag}",
              file=sys.stderr)
    print("\nCaps are self-imposed, not provider-reported. Adjust "
          "assumed_daily_limit / cap_fraction in config/user.json.", file=sys.stderr)
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Track and cap connector usage")
    p.add_argument("action", choices=["status", "check", "record", "reset"])
    p.add_argument("connector", nargs="?", help="e.g. indeed, ziprecruiter, dice")
    p.add_argument("--count", type=int, default=1, help="Calls to record (default 1)")
    args = p.parse_args()

    if args.action == "status":
        sys.exit(cmd_status())

    if not args.connector:
        p.error(f"{args.action} needs a connector name")
    c = args.connector.lower().strip()

    if args.action == "check":
        sys.exit(cmd_check(c))
    if args.action == "record":
        sys.exit(cmd_record(c, args.count))
    if args.action == "reset":
        led = load_ledger()
        led.pop(c, None)
        save_ledger(led)
        print(f"{c}: usage cleared", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
