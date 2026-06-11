"""
patient_export.py — Download all assessments for a single patient.

Saves:
  <out>/<patient_id>/assessments.json    All assessments with full data payloads
  <out>/<patient_id>/assessments.csv     Flat summary table
  <out>/<patient_id>/<code>.json         One file per assessment type (grouped)

Usage:
  python examples/patient_export.py \
      --url     https://motaby.de \
      --key     mby_your_key_here \
      --patient P001 \
      [--out    ./output]        # default: current directory
      [--status final]           # optional: only export final assessments

Alternatively, set MOTABY_URL and MOTABY_API_KEY as environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from motaby import MOTABYClient, NotFoundError, MOTABYError


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export all assessments for one patient.")
    p.add_argument("--url", default=os.environ.get("MOTABY_URL"))
    p.add_argument("--key", default=os.environ.get("MOTABY_API_KEY"))
    p.add_argument("--patient", required=True, help="Patient identifier (e.g. P001)")
    p.add_argument("--out", default=".", help="Root output directory")
    p.add_argument("--status", default=None, choices=["preliminary", "final"])
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.url or not args.key:
        print("Error: --url and --key are required (or set MOTABY_URL / MOTABY_API_KEY).",
              file=sys.stderr)
        sys.exit(1)

    patient_dir = Path(args.out) / args.patient
    patient_dir.mkdir(parents=True, exist_ok=True)

    with MOTABYClient(base_url=args.url, api_key=args.key) as client:
        if not client.ping():
            print(f"Error: cannot reach {args.url}", file=sys.stderr)
            sys.exit(1)

        print(f"Fetching assessments for patient {args.patient!r}...", flush=True)
        assessments = client.assessments.list_all(
            patient_id=args.patient,
            status=args.status,
        )

        if not assessments:
            print(f"No assessments found for patient {args.patient!r}.")
            return

        print(f"  → {len(assessments)} assessments found")

        # ── Full JSON dump ────────────────────────────────────────────────
        all_path = patient_dir / "assessments.json"
        all_path.write_text(json.dumps([a.to_dict() for a in assessments], indent=2, default=str))
        print(f"  → {all_path}")

        # ── Per-type JSON files ───────────────────────────────────────────
        by_type: dict[str, list] = {}
        for a in assessments:
            by_type.setdefault(a.assessment_code, []).append(a.to_dict())

        for code, records in sorted(by_type.items()):
            type_path = patient_dir / f"{code}.json"
            type_path.write_text(json.dumps(records, indent=2, default=str))
            print(f"  → {type_path}  ({len(records)} records)")

        # ── CSV summary ───────────────────────────────────────────────────
        try:
            import pandas as pd

            df = pd.DataFrame([
                {
                    "id": str(a.id),
                    "assessment_code": a.assessment_code,
                    "status": a.status,
                    "created_at": a.created_at,
                    "effective_datetime": a.effective_datetime,
                    "study": a.study,
                    "notes": a.notes,
                    "media_count": a.media_count,
                }
                for a in assessments
            ])
            csv_path = patient_dir / "assessments.csv"
            df.to_csv(csv_path, index=False)
            print(f"  → {csv_path}")
        except ImportError:
            print("  (pandas not installed — CSV skipped)")

        # ── Summary ───────────────────────────────────────────────────────
        print(f"\nPatient {args.patient} — assessment summary:")
        for code, records in sorted(by_type.items()):
            print(f"  {code:<30} {len(records):>4} records")

    print("\nDone.")


if __name__ == "__main__":
    main()
