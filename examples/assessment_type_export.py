"""
assessment_type_export.py — Download all assessments of one type across all patients.

Useful for feeding a single task type (e.g. all spiral-drawing sessions) into a
downstream analysis pipeline.

Saves:
  <out>/<code>/all.json              All records with full data payloads
  <out>/<code>/all.csv               One row per assessment (data columns flattened)
  <out>/<code>/per_patient.json      Records grouped by patient_id

Common assessment codes:
  spiral-drawing      finger-tapping    nine-hole-peg
  line-tracing        target-chase      pata-pata
  fifteen-white-dots  reading-passage   free-speech
  sustained-phonation diadochokinetic   forearm-rolling
  hand-open-close     heel-shin         finger-nose

Usage:
  python examples/assessment_type_export.py \
      --url   https://motaby.de \
      --key   mby_your_key_here \
      --code  spiral-drawing \
      [--out  ./output] \
      [--status final] \
      [--date-from 2025-01-01] \
      [--date-to   2025-12-31]

Environment variables MOTABY_URL and MOTABY_API_KEY are also accepted.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from motaby import MOTABYClient, MOTABYError


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Export all assessments of a given type across all patients."
    )
    p.add_argument("--url", default=os.environ.get("MOTABY_URL"))
    p.add_argument("--key", default=os.environ.get("MOTABY_API_KEY"))
    p.add_argument("--code", required=True,
                   help="Assessment code, e.g. spiral-drawing")
    p.add_argument("--out", default=".", help="Root output directory")
    p.add_argument("--status", default=None, choices=["preliminary", "final"])
    p.add_argument("--date-from", dest="date_from", default=None,
                   help="Include only assessments on/after this date (YYYY-MM-DD)")
    p.add_argument("--date-to", dest="date_to", default=None,
                   help="Include only assessments on/before this date (YYYY-MM-DD)")
    return p.parse_args()


def flatten_data(data: dict | None, prefix: str = "data.") -> dict:
    """Flatten one level of the data dict into dot-prefixed columns."""
    if not data:
        return {}
    return {f"{prefix}{k}": v for k, v in data.items()
            if not isinstance(v, (dict, list))}


def main() -> None:
    args = parse_args()

    if not args.url or not args.key:
        print("Error: --url and --key are required (or set MOTABY_URL / MOTABY_API_KEY).",
              file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out) / args.code
    out_dir.mkdir(parents=True, exist_ok=True)

    with MOTABYClient(base_url=args.url, api_key=args.key) as client:
        if not client.ping():
            print(f"Error: cannot reach {args.url}", file=sys.stderr)
            sys.exit(1)

        print(f"Fetching all '{args.code}' assessments...", flush=True)
        assessments = client.assessments.list_all(
            code=args.code,
            status=args.status,
            date_from=args.date_from,
            date_to=args.date_to,
        )

        if not assessments:
            print(f"No '{args.code}' assessments found.")
            return

        print(f"  → {len(assessments)} records across "
              f"{len({a.patient_id for a in assessments})} patients")

        # ── Flat JSON dump ────────────────────────────────────────────────
        all_path = out_dir / "all.json"
        all_path.write_text(json.dumps([a.to_dict() for a in assessments], indent=2, default=str))
        print(f"  → {all_path}")

        # ── Per-patient grouping ──────────────────────────────────────────
        by_patient: dict[str, list] = {}
        for a in assessments:
            by_patient.setdefault(a.patient_id, []).append(a.to_dict())

        grouped_path = out_dir / "per_patient.json"
        grouped_path.write_text(json.dumps(by_patient, indent=2, default=str))
        print(f"  → {grouped_path}")

        # ── CSV with flattened data columns ───────────────────────────────
        try:
            import pandas as pd

            rows = []
            for a in assessments:
                base = {
                    "id": str(a.id),
                    "patient_id": a.patient_id,
                    "status": a.status,
                    "created_at": a.created_at,
                    "effective_datetime": a.effective_datetime,
                    "study": a.study,
                    "notes": a.notes,
                    "media_count": a.media_count,
                }
                base.update(flatten_data(a.data))
                rows.append(base)

            df = pd.DataFrame(rows)
            csv_path = out_dir / "all.csv"
            df.to_csv(csv_path, index=False)
            print(f"  → {csv_path}  ({len(df)} rows × {len(df.columns)} columns)")

            # Show which data keys were present
            data_cols = [c for c in df.columns if c.startswith("data.")]
            if data_cols:
                print(f"\n  Data fields extracted: {', '.join(c[5:] for c in data_cols)}")

        except ImportError:
            print("  (pandas not installed — CSV skipped)")

        # ── Per-patient summary ───────────────────────────────────────────
        print(f"\nPatients with '{args.code}' assessments:")
        for pid, records in sorted(by_patient.items()):
            dates = sorted(r["created_at"] for r in records if r.get("created_at"))
            span = f"{dates[0][:10]} → {dates[-1][:10]}" if len(dates) >= 2 else (dates[0][:10] if dates else "—")
            print(f"  {pid:<20} {len(records):>4} records   {span}")

    print("\nDone.")


if __name__ == "__main__":
    main()
