"""Check railcal.railway_periods() against ORR's published railway period dates (1995/96 to 2028/29).

Source: Office of Rail and Road, "Railway period dates, Great Britain, April 1995 to March 2029"
first published 25 July 2023: https://dataportal.orr.gov.uk/media/2250/railway-period-dates.ods
Extracted to tests/fixtures/orr_railway_period_dates.csv.
Contains public sector information licensed under the Open Government Licence v3.0.
Exits 0 on a full match, 1 on any mismatch.
"""
import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import railcal  # noqa: E402

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "orr_railway_period_dates.csv")


def main():
    with open(CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fails, checks, cp_years = [], Counter(), {}
    for r in rows:
        fy = int(re.search(r"Apr (\d{4})", r["time_period"]).group(1))
        per = int(re.search(r"Period (\d+)", r["time_period"]).group(1))
        _, s, e = railcal.railway_periods(fy)[per - 1]
        checks["railway period start/end"] += 1
        if (s.isoformat(), e.isoformat()) != (r["start_date"], r["end_date"]):
            fails.append(f"{fy} P{per}: got {s}..{e}, ORR {r['start_date']}..{r['end_date']}")
        cp_years[fy] = r["control_period"]
    for fy, cp in sorted(cp_years.items()):
        checks["control period label"] += 1
        if railcal.control_period(fy)[0] != cp:
            fails.append(f"{fy}: got {railcal.control_period(fy)[0]}, ORR {cp}")

    print(f"ORR railway period dates, {min(cp_years)}/{(min(cp_years) + 1) % 100:02d} "
          f"to {max(cp_years)}/{(max(cp_years) + 1) % 100:02d} ({len(rows)} periods)")
    for cat, n in checks.items():
        print(f"  {cat:32s} {n:5d}")
    print(f"{sum(checks.values())} checks, {len(fails)} mismatches")
    for f in fails[:40]:
        print("  MISMATCH", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
