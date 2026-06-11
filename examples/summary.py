"""
summary.py — Print a quick overview of everything accessible via your API key.

Shows:
  • Total assessments, patients, and batteries
  • Assessment counts by type, with completion rates
  • Per-patient assessment counts (top 20)
  • Assessments by month (last 12 months)

Usage:
  python examples/summary.py \
      --url  https://motaby.de \
      --key  mby_your_key_here

Environment variables MOTABY_URL and MOTABY_API_KEY are also accepted.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

from motaby import MOTABYClient, MOTABYError


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Print a summary of your MOTABY data.")
    p.add_argument("--url", default=os.environ.get("MOTABY_URL"))
    p.add_argument("--key", default=os.environ.get("MOTABY_API_KEY"))
    return p.parse_args()


def bar(count: int, total: int, width: int = 20) -> str:
    filled = round(width * count / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def main() -> None:
    args = parse_args()

    if not args.url or not args.key:
        print("Error: --url and --key are required (or set MOTABY_URL / MOTABY_API_KEY).",
              file=sys.stderr)
        sys.exit(1)

    with MOTABYClient(base_url=args.url, api_key=args.key) as client:
        if not client.ping():
            print(f"Error: cannot reach {args.url}", file=sys.stderr)
            sys.exit(1)

        print("Loading data...", flush=True)
        assessments = client.assessments.list_all()
        patients = client.patients.list_all()
        batteries = client.batteries.list_all()

    # ── Headline ─────────────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  MOTABY — Data Summary")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═' * 60}")
    print(f"  Assessments : {len(assessments)}")
    print(f"  Patients    : {len(patients)}")
    print(f"  Batteries   : {len(batteries)}")

    if not assessments:
        print("\n  (no assessments found)")
        return

    # ── By assessment type ────────────────────────────────────────────────────
    by_code: Counter[str] = Counter(a.assessment_code for a in assessments)
    final_by_code: Counter[str] = Counter(
        a.assessment_code for a in assessments if a.status == "final"
    )

    print(f"\n{'─' * 60}")
    print("  Assessments by type")
    print(f"{'─' * 60}")
    print(f"  {'Code':<30} {'Count':>6}  {'Final%':>7}  ")
    print(f"  {'─' * 30} {'─' * 6}  {'─' * 7}")
    for code, count in by_code.most_common():
        final = final_by_code.get(code, 0)
        pct = f"{100 * final // count}%" if count else "—"
        print(f"  {code:<30} {count:>6}  {pct:>7}  {bar(count, by_code.most_common(1)[0][1])}")

    # ── Status breakdown ──────────────────────────────────────────────────────
    by_status: Counter[str] = Counter(a.status or "unknown" for a in assessments)
    print(f"\n{'─' * 60}")
    print("  Assessments by status")
    print(f"{'─' * 60}")
    for status, count in by_status.most_common():
        print(f"  {status:<20} {count:>6}  {bar(count, len(assessments))}")

    # ── Per-patient summary ───────────────────────────────────────────────────
    by_patient: Counter[str] = Counter(a.patient_id for a in assessments)
    print(f"\n{'─' * 60}")
    print("  Top patients by assessment count")
    print(f"{'─' * 60}")
    top = by_patient.most_common(20)
    max_count = top[0][1] if top else 1
    for pid, count in top:
        print(f"  {pid:<25} {count:>5}  {bar(count, max_count)}")
    if len(by_patient) > 20:
        print(f"  ... and {len(by_patient) - 20} more patients")

    # ── Monthly trend (last 12 months) ────────────────────────────────────────
    now = datetime.now(timezone.utc)
    monthly: Counter[str] = Counter()
    for a in assessments:
        if a.created_at:
            dt = a.created_at
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            if (now - dt) <= timedelta(days=366):
                monthly[dt.strftime("%Y-%m")] += 1

    if monthly:
        print(f"\n{'─' * 60}")
        print("  Assessments per month (last 12 months)")
        print(f"{'─' * 60}")
        max_m = max(monthly.values())
        for month in sorted(monthly):
            count = monthly[month]
            print(f"  {month}  {count:>5}  {bar(count, max_m)}")

    # ── Study breakdown (if studies are in use) ───────────────────────────────
    studies = {a.study for a in assessments if a.study}
    if studies:
        by_study: Counter[str] = Counter(
            a.study for a in assessments if a.study
        )
        print(f"\n{'─' * 60}")
        print("  Assessments by study")
        print(f"{'─' * 60}")
        for study, count in by_study.most_common():
            print(f"  {study:<30} {count:>6}  {bar(count, len(assessments))}")

    print(f"\n{'═' * 60}\n")


if __name__ == "__main__":
    main()
