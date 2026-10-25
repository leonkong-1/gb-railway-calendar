"""Check railcal.py against the year tables published on railwaycalendar.com (2004/05 to 2049/50).

Needs a local snapshot at tests/fixtures/railwaycalendar_snapshot.json. The snapshot is not committed: the site's
content is "all rights reserved", so it is not redistributed here. See README.md ("Reproducing the
railwaycalendar.com comparison") for how it was captured. Exits 0 on a full match, 1 on any mismatch,
3 if the snapshot is missing.

railwaycalendar.com calls railway periods "finance periods" and possession weeks "NR weeks"; its own labels
are kept below only where the code parses its columns.
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import railcal  # noqa: E402

SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "railwaycalendar_snapshot.json")


def p(s):
    return datetime.strptime(s.strip(), "%a %d %b %Y").date()


fails, checks = [], Counter()


def check(category, label, got, want):
    checks[category] += 1
    if got != want:
        fails.append(f"{label}: got {got!r}, site {want!r}")


def main():
    if not os.path.exists(SNAPSHOT):
        print(f"SKIPPED: no snapshot at {SNAPSHOT}")
        return 3
    with open(SNAPSHOT, encoding="utf-8") as f:
        site = json.loads(re.sub(r"\\u(00a0|202f|2009)", " ", f.read()))

    for y, v in sorted(site.items()):
        fy = int(y)
        # Year header: control period, possession year start and length
        m = re.search(r"([CF]P\d+) year (\d)[^A-Z]+NR possession year runs (.+?) to (.+?), (\d+) weeks", v["head"])
        cp, cpy, s, e, n = m.groups()
        check("control period label", f"{fy} CP", railcal.control_period(fy), (cp, int(cpy)))
        check("possession year start/length", f"{fy} possession start", railcal.possession_year_start(fy), p(s))
        check("possession year start/length", f"{fy} possession weeks", railcal.possession_year_weeks(fy), int(n))

        # Period table: railway period start/end/days, and the possession period alongside it
        rail = {r[0]: r for r in railcal.railway_periods(fy)}
        poss = {q[0]: q for q in railcal.possession_periods(fy)}
        for row in v["fin"]:
            per, st, en, days, _, nwk, nend = row.split("|")
            per = int(per)
            _, rs, re_ = rail[per]
            _, _, pe, fw, lw = poss[per]
            check("railway period", f"{fy} railway P{per}", (rs, re_, (re_ - rs).days + 1), (p(st), p(en), int(days)))
            check("possession period", f"{fy} possession P{per}", (pe, f"{fw} to {lw}"), (p(nend), nwk))

        # Every possession week: number, period/week, dates, railway period(s), timetable and block
        weeks = list(railcal.possession_weeks(fy))
        check("possession week", f"{fy} week count", len(weeks), len(v["wk"]))
        for (w, per, wip, ws, we), row in zip(weeks, v["wk"]):
            no, pw, st, en, rper, tt, blk = row.split("|")
            ra, rb = railcal.railway_period_of(ws), railcal.railway_period_of(we)
            rper_got = f"P{ra}" if ra == rb else f"P{ra} to P{rb}"
            ty, part, b = railcal.timetable_of(ws)
            check("possession week", f"{fy} wk{w}", (str(w), f"{per}/{wip}", ws, we, rper_got, f"TT{ty} {part}", b),
                  (no, pw, p(st), p(en), rper, tt, blk))

        # Timetable period blocks (each page shows two timetable years)
        for tbl in v["blocks"]:
            t = railcal.timetable(p(tbl[0].split("|")[1]).year + 1)
            for (name, bs, be, bw), row in zip(t["blocks"], tbl):
                cells = row.split("|")
                check("timetable block", f"TT{t['year']} block {name}", (name, bs, be, str(bw)),
                      (cells[0], p(cells[1]), p(cells[2]), cells[3]))

        # Timetable headline: length, Principal and Subsidiary ranges
        for blob in v["tt"]:
            for ty, wks, ps, pe, pw, ss, se, sw in re.findall(
                    r"Timetable year (\d+): (\d+) weeksPrincipal \(December\) (.+?) to (.+?), (\d+) weeks\. "
                    r"Subsidiary \(May\) (.+?) to (.+?), (\d+) weeks", blob):
                t = railcal.timetable(int(ty))
                check("timetable year", f"TT{ty} header",
                      (t["weeks"], t["principal"][0], t["principal"][1], t["principal"][2],
                       t["subsidiary"][0], t["subsidiary"][1], t["subsidiary"][2]),
                      (int(wks), p(ps), p(pe), int(pw), p(ss), p(se), int(sw)))

    total = sum(checks.values())
    lo, hi = int(min(site)), int(max(site))
    print(f"railwaycalendar.com year tables, financial years {lo}/{(lo + 1) % 100:02d} to {hi}/{(hi + 1) % 100:02d}")
    for cat, n in checks.items():
        print(f"  {cat:32s} {n:5d}")
    print(f"{total} checks, {len(fails)} mismatches")
    for f in fails[:40]:
        print("  MISMATCH", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
