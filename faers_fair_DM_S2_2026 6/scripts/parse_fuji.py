"""Parse a F-UJI JSON report into a tidy per-metric CSV.

Reads `reports/fuji_baseline.json`, extracts one row per metric (17 rows for
the standard FsF specification), reconciles totals against the JSON's own
`summary` block, and writes `reports/fuji_baseline_summary.csv`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reports" / "fuji_baseline.json"
OUT = ROOT / "reports" / "fuji_baseline_summary.csv"


def _principle_of(metric_id: str) -> str:
    """FsF-F1-01MD -> 'F'."""
    return metric_id.split("-")[1][0]


def _short_reasoning(result: dict) -> str:
    """Pull a one-line justification from the test_debug log.

    For failures: prefer ERROR > WARNING > FATAL > last line.
    For passes (incl. partial): prefer SUCCESS first, only fall back to
    WARNING if no SUCCESS exists. This avoids surfacing a warning about an
    unrelated sub-test as the "reason" the metric passed.
    """
    log = result.get("test_debug", []) or []
    status = result.get("test_status", "")
    if status == "pass":
        order = ("SUCCESS", "INFO", "WARNING", "ERROR", "FATAL")
    else:
        order = ("ERROR", "FATAL", "WARNING", "SUCCESS", "INFO")
    for level in order:
        for line in reversed(log):
            if line.startswith(f"{level}:"):
                return line.split(":", 1)[1].strip()
    return ""


def _derived_status(test_status: str, earned: float, total: float) -> str:
    """Map (raw status, earned, total) to passed/failed/partial."""
    if test_status == "pass" and earned >= total > 0:
        return "passed"
    if test_status == "pass" and 0 < earned < total:
        return "partial"
    return "failed"


def main() -> None:
    data = json.loads(SRC.read_text())
    rows = []
    for r in data["results"]:
        mid = r["metric_identifier"]
        score = r.get("score", {})
        earned = float(score.get("earned", 0) or 0)
        total = float(score.get("total", 0) or 0)
        rows.append({
            "principle": _principle_of(mid),
            "metric_id": mid,
            "metric_name": r["metric_name"],
            "score_earned": earned,
            "score_max": total,
            "raw_status": r.get("test_status", ""),
            "status": _derived_status(r.get("test_status", ""), earned, total),
            "maturity": r.get("maturity", 0),
            "short_reasoning": _short_reasoning(r),
        })
    df = pd.DataFrame(rows, columns=[
        "principle", "metric_id", "metric_name",
        "score_earned", "score_max",
        "raw_status", "status", "maturity",
        "short_reasoning",
    ])
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(df)} rows)")

    # --- reconciliation ---------------------------------------------------
    earned = df["score_earned"].sum()
    total = df["score_max"].sum()
    summary = data["summary"]
    print(f"reconciliation: per-metric sum {earned:.0f}/{total:.0f}; "
          f"summary block FAIR {summary['score_earned']['FAIR']}/{summary['score_total']['FAIR']}")
    assert int(earned) == int(summary["score_earned"]["FAIR"]), "earned mismatch"
    assert int(total) == int(summary["score_total"]["FAIR"]), "total mismatch"
    print("  OK — totals reconcile.")

    # Per-principle breakdown
    by_p = df.groupby("principle").agg(
        earned=("score_earned", "sum"),
        total=("score_max", "sum"),
        passed=("status", lambda s: (s == "passed").sum()),
        partial=("status", lambda s: (s == "partial").sum()),
        failed=("status", lambda s: (s == "failed").sum()),
        n=("metric_id", "count"),
    )
    print("\nPer-principle:")
    print(by_p.to_string())


if __name__ == "__main__":
    main()
