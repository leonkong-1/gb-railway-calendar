"""GB railway calendar: possession weeks, railway periods, timetable years and period blocks.

Naming: "railway periods" are the Sunday-Saturday periods used for general operational reporting (what
railwaycalendar.com calls finance periods; ORR publishes them as "railway period dates"). "Possession weeks"
run Saturday-Friday so a weekend's possessions fall in one week (railwaycalendar.com calls them NR weeks).

The whole calendar hangs off two anchor rules:

  * Possession year N/N+1 starts on the Saturday nearest 1 April (i.e. the first Saturday on or after 29 March).
    Weeks run Saturday-Friday; 13 periods of 4 weeks, with any 53rd week added to period 13.
  * Timetable year N starts on the Sunday after the second Saturday in December of year N-1, and its
    Subsidiary (May) timetable starts on the third Sunday in May (so the Principal is 22 or 23 weeks).

Everything else is derived from those:

  * Railway periods cover the financial year, 1 April - 31 March. Their weeks run Sunday-Saturday, so each
    railway period ends on the Saturday after the matching possession period's Friday. P1 starts 1 April;
    P13 ends 31 March.
  * Period blocks A-J: A/B/C are 3/6/6 weeks from the December change, D runs to the May change,
    E/F/G/H are 5/6/6/6 weeks from the May change, J runs to the next December change.

Validated against every table on railwaycalendar.com for 2004/05 to 2049/50 (see validate.py), and railway
periods against ORR's published "railway period dates" for 1995/96 to 2028/29 (442 periods, all match).
"""
from datetime import date, timedelta

DAY = timedelta(days=1)
WEEK = timedelta(weeks=1)


def possession_year_start(fy):
    """First day (Saturday) of possession year fy/fy+1: the Saturday nearest 1 April."""
    d = date(fy, 3, 29)
    return d + (5 - d.weekday()) % 7 * DAY  # weekday(): Mon=0 .. Sat=5


def possession_year_weeks(fy):
    return (possession_year_start(fy + 1) - possession_year_start(fy)).days // 7


def possession_weeks(fy):
    """Yield (week_no, period, week_in_period, start_sat, end_fri) for possession year fy."""
    start = possession_year_start(fy)
    for w in range(1, possession_year_weeks(fy) + 1):
        period = min((w - 1) // 4 + 1, 13)
        wk_in_p = w - (period - 1) * 4
        s = start + (w - 1) * WEEK
        yield w, period, wk_in_p, s, s + 6 * DAY


def possession_periods(fy):
    """Return [(period, start_sat, end_fri, first_week, last_week)]."""
    start, n = possession_year_start(fy), possession_year_weeks(fy)
    out = []
    for p in range(1, 14):
        fw = (p - 1) * 4 + 1
        lw = n if p == 13 else fw + 3
        out.append((p, start + (fw - 1) * WEEK, start + lw * WEEK - DAY, fw, lw))
    return out


def railway_periods(fy):
    """Return [(period, start, end)] for financial year fy/fy+1 (1 Apr - 31 Mar)."""
    out, prev_end = [], date(fy, 4, 1) - DAY
    for p, _, poss_end, _, _ in possession_periods(fy):
        end = date(fy + 1, 3, 31) if p == 13 else poss_end + DAY  # Saturday after the possession Friday
        out.append((p, prev_end + DAY, end))
        prev_end = end
    return out


def railway_period_of(d):
    fy = d.year if d >= date(d.year, 4, 1) else d.year - 1
    for p, s, e in railway_periods(fy):
        if s <= d <= e:
            return p


def timetable_start(tt_year):
    """Start (Sunday) of timetable year tt_year: Sunday after the 2nd Saturday of December tt_year-1."""
    d = date(tt_year - 1, 12, 8)
    sat = d + (5 - d.weekday()) % 7 * DAY
    return sat + DAY


def subsidiary_start(tt_year):
    """Start (Sunday) of the Subsidiary (May) timetable: the third Sunday in May."""
    d = date(tt_year, 5, 15)
    return d + (6 - d.weekday()) % 7 * DAY


BLOCK_NAMES = "ABCDEFGHJ"


def timetable(tt_year):
    """Return dict with principal/subsidiary ranges and blocks [(name, start, end, weeks)]."""
    s, sub, nxt = timetable_start(tt_year), subsidiary_start(tt_year), timetable_start(tt_year + 1)
    # A-C are 3/6/6 weeks from the December change and D runs to the May change; E-H are 5/6/6/6 weeks from
    # the May change and J runs to the next December change. Blocks change on a Monday, except at the two
    # timetable changes themselves (Sunday).
    bounds = ([s] + [s + w * WEEK + DAY for w in (3, 9, 15)]
              + [sub] + [sub + w * WEEK + DAY for w in (5, 11, 17, 23)] + [nxt])
    blocks = []
    for i, name in enumerate(BLOCK_NAMES):
        blocks.append((name, bounds[i], bounds[i + 1] - DAY, round((bounds[i + 1] - bounds[i]).days / 7)))
    return {
        "year": tt_year,
        "weeks": (nxt - s).days // 7,
        "principal": (s, sub - DAY, (sub - s).days // 7),
        "subsidiary": (sub, nxt - DAY, (nxt - sub).days // 7),
        "blocks": blocks,
    }


def timetable_of(d):
    """Return (tt_year, 'Principal'|'Subsidiary', block) for date d."""
    y = d.year + 1 if d >= timetable_start(d.year + 1) else d.year
    t = timetable(y)
    part = "Principal" if d <= t["principal"][1] else "Subsidiary"
    block = next(b[0] for b in t["blocks"] if b[1] <= d <= b[2])
    return y, part, block


def control_period(fy):
    """CP/FP label and year-of-period for financial year fy/fy+1 (matches ORR labels from 1995/96). FP1 = 2029/30."""
    n, yr = divmod(fy - 1994, 5)
    return (f"CP{n + 1}" if n < 7 else f"FP{n - 6}"), yr + 1
