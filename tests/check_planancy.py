"""Check railcal.py against Planancy's "2026 - 2030 Rail Weeks Calendar" (published PDF, image only).

Source: https://www.planancy.co.uk/ClientResources/2026%20-%202030%20Rail%20Weeks%20Calendar.pdf
The PDF has no usable text layer, so the values below were transcribed by eye from the rendered pages. The PDF
itself is not redistributed here.

How the calendar is drawn: each row runs Saturday to Friday; a blue circle at the row end is the possession week
number; a yellow Saturday with a black tag marks the end of a period (the key calls it "NR Period End Date", but
these are Saturdays, so they are railway period ends; the possession period ends on the Friday before).
Exits 0 on a full match, 1 on any mismatch.
"""
import calendar
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import railcal  # noqa: E402

# Yellow period-end tags per calendar year, Jan..Dec order (P10..P9): (period, month, day)
ENDS = {
    2026: [(10, 1, 3), (11, 1, 31), (12, 2, 28), (13, 3, 31), (1, 5, 2), (2, 5, 30), (3, 6, 27), (4, 7, 25), (5, 8, 22), (6, 9, 19), (7, 10, 17), (8, 11, 14), (9, 12, 12)],
    2027: [(10, 1, 9), (11, 2, 6), (12, 3, 6), (13, 3, 31), (1, 5, 1), (2, 5, 29), (3, 6, 26), (4, 7, 24), (5, 8, 21), (6, 9, 18), (7, 10, 16), (8, 11, 13), (9, 12, 11)],
    2028: [(10, 1, 8), (11, 2, 5), (12, 3, 4), (13, 3, 31), (1, 4, 29), (2, 5, 27), (3, 6, 24), (4, 7, 22), (5, 8, 19), (6, 9, 16), (7, 10, 14), (8, 11, 11), (9, 12, 9)],
    2029: [(10, 1, 6), (11, 2, 3), (12, 3, 3), (13, 3, 31), (1, 4, 28), (2, 5, 26), (3, 6, 23), (4, 7, 21), (5, 8, 18), (6, 9, 15), (7, 10, 13), (8, 11, 10), (9, 12, 8)],
    2030: [(10, 1, 5), (11, 2, 2), (12, 3, 2), (13, 3, 31), (1, 4, 27), (2, 5, 25), (3, 6, 22), (4, 7, 20), (5, 8, 17), (6, 9, 14), (7, 10, 12), (8, 11, 9), (9, 12, 7)],
}
# Blue week circles on the first and last row of each month, Jan..Dec. Weeks are consecutive, so these pin
# down every week in between.
FIRST_ROW = {2026: [40, 45, 49, 53, 4, 9, 13, 18, 22, 26, 31, 35], 2027: [39, 44, 48, 52, 5, 9, 13, 18, 22, 26, 31, 35],
             2028: [40, 44, 48, 1, 5, 9, 14, 18, 22, 27, 31, 35], 2029: [40, 44, 48, 1, 5, 9, 14, 18, 23, 27, 31, 36],
             2030: [40, 44, 48, 1, 5, 10, 14, 18, 23, 27, 31, 36]}
LAST_ROW = {2026: [45, 49, 53, 4, 9, 13, 17, 22, 26, 31, 35, 39], 2027: [44, 48, 52, 4, 9, 13, 18, 22, 26, 31, 35, 39],
            2028: [44, 48, 52, 5, 9, 13, 18, 22, 27, 31, 35, 40], 2029: [44, 48, 1, 5, 9, 14, 18, 22, 27, 31, 35, 40],
            2030: [44, 48, 1, 5, 9, 14, 18, 23, 27, 31, 36, 40]}


def financial_year(d):
    return d.year if d >= date(d.year, 4, 1) else d.year - 1


def possession_week(d):
    fy = d.year if d >= railcal.possession_year_start(d.year) else d.year - 1
    return (d - railcal.possession_year_start(fy)).days // 7 + 1


def main():
    fails, n_ends, n_weeks = [], 0, 0
    for y, lst in ENDS.items():
        for per, m, dd in lst:
            d = date(y, m, dd)
            n_ends += 1
            got = railcal.railway_periods(financial_year(d))[per - 1][2]
            if got != d:
                fails.append(f"P{per} end: Planancy {d}, got {got}")
    for which, tbl in (("first", FIRST_ROW), ("last", LAST_ROW)):
        for y, wks in tbl.items():
            for m, w in enumerate(wks, 1):
                d = date(y, m, 1 if which == "first" else calendar.monthrange(y, m)[1])
                n_weeks += 1
                if possession_week(d) != w:
                    fails.append(f"{which} row of {y}-{m:02d}: Planancy week {w}, got {possession_week(d)}")
    print("Planancy 2026-2030 Rail Weeks Calendar (transcribed)")
    print(f"  {'railway period end':32s} {n_ends:5d}")
    print(f"  {'possession week (month rows)':32s} {n_weeks:5d}")
    print(f"{n_ends + n_weeks} checks, {len(fails)} mismatches")
    for f in fails:
        print("  MISMATCH", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
