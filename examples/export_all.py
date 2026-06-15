"""
export_all.py — Download every assessment (with full data) to disk.

Saves two files:
  assessments.json   All records with complete data payloads
  assessments.csv    Flat summary (one row per assessment, data columns omitted)

Usage:
  python examples/export_all.py \
      --url  https://motaby.de \
      --key  mby_your_key_here \
      [--out ./output]            # default: current directory
      [--study my-trial]          # optional: filter by study identifier
      [--status final]            # optional: filter by status (preliminary|final)

Alternatively, set environment variables:
  MOTABY_URL=https://motaby.de
  MOTABY_API_KEY=mby_your_key_here
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from motaby import MOTABYClient, MOTABYError
from motaby.exceptions import AuthenticationError


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export all MOTABY assessments to disk.")
    p.add_argument("--url", default=os.environ.get("MOTABY_URL"), help="Backend base URL")
    p.add_argument("--key", default=os.environ.get("MOTABY_API_KEY"), help="API key (mby_...)")
    p.add_argument("--out", default="./motaby_export", help="Output directory (default: ./motaby_export)")
    p.add_argument("--study", default=None, help="Filter by study identifier")
    p.add_argument("--status", default=None, choices=["preliminary", "final"],
                   help="Filter by status")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.url or not args.key:
        print("Error: --url and --key are required (or set MOTABY_URL / MOTABY_API_KEY).",
              file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with MOTABYClient(base_url=args.url, api_key=args.key) as client:
        if not client.ping():
            print(f"Error: cannot reach {args.url}", file=sys.stderr)
            sys.exit(1)

        print("Fetching assessments...", flush=True)
        try:
            assessments = client.assessments.list_all(status=args.status)
        except AuthenticationError:
            print(
                "Error: API key is invalid or expired. Create a new key in the MOTABY app "
                "(Settings → API Keys) and pass it with --key.",
                file=sys.stderr,
            )
            sys.exit(1)

        if args.study:
            assessments = [a for a in assessments if a.study == args.study]

        print(f"  → {len(assessments)} assessments found")

        # ── JSON export ──────────────────────────────────────────────────────
        records = [a.to_dict() for a in assessments]
        json_path = out_dir / "assessments.json"
        json_path.write_text(json.dumps(records, indent=2, default=str))
        print(f"  → {json_path} written")

        # ── CSV export (flat summary, no nested data) ─────────────────────
        try:
            import pandas as pd

            df = pd.DataFrame([
                {
                    "id": str(a.id),
                    "patient_id": a.patient_id,
                    "assessment_code": a.assessment_code,
                    "assessment_type": a.assessment_type,
                    "status": a.status,
                    "created_at": a.created_at,
                    "effective_datetime": a.effective_datetime,
                    "study": a.study,
                    "notes": a.notes,
                    "media_count": a.media_count,
                }
                for a in assessments
            ])
            csv_path = out_dir / "assessments.csv"
            df.to_csv(csv_path, index=False)
            print(f"  → {csv_path} written ({len(df)} rows)")

        except ImportError:
            print("  (pandas not installed — CSV skipped; run: pip install motaby-client[pandas])")

        # ── Readout download ─────────────────────────────────────────────────
        # Readouts are the processed output files (CSV, JSON, etc.) from each
        # assessment. QC files and video files are excluded server-side.
        assessments_with_readouts = [a for a in assessments if a.readouts]
        print(
            f"\nDownloading readout files ({sum(len(a.readouts) for a in assessments_with_readouts)} files"
            f" across {len(assessments_with_readouts)} assessments)...",
            flush=True,
        )
        readouts_dir = out_dir / "readouts"
        readouts_dir.mkdir(exist_ok=True)
        downloaded = 0
        skipped = 0
        for a in assessments_with_readouts:
            assessment_dir = readouts_dir / str(a.id)
            assessment_dir.mkdir(exist_ok=True)
            for r in a.readouts:
                try:
                    saved = client.assessments.download_readout(
                        str(a.id), r.name, assessment_dir
                    )
                    downloaded += 1
                    print(f"  ✓ [{r.layer}] {saved.name}", flush=True)
                except Exception as exc:
                    skipped += 1
                    print(f"  ✗ {r.name}: {exc}", flush=True)
        print(f"  → {downloaded} readout files downloaded, {skipped} skipped")

        # ── Quick summary ────────────────────────────────────────────────────
        by_code: dict[str, int] = {}
        for a in assessments:
            by_code[a.assessment_code] = by_code.get(a.assessment_code, 0) + 1

        print("\nAssessments by type:")
        for code, count in sorted(by_code.items(), key=lambda x: -x[1]):
            print(f"  {code:<30} {count:>5}")

        exported_at = datetime.now(timezone.utc).isoformat()
        meta = {
            "exported_at": exported_at,
            "total": len(assessments),
            "filters": {"study": args.study, "status": args.status},
            "by_code": by_code,
        }
        (out_dir / "export_meta.json").write_text(json.dumps(meta, indent=2))

    print("\nDone.")


if __name__ == "__main__":
    main()
