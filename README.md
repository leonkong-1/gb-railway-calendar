# GB Railway Calendar

An open, reproducible implementation of the GB railway's own calendars: **railway periods**, **possession weeks**, and **timetable years with period blocks**.

Network Rail derives and maintains these calendars, but there has never been a good public source for them, and no published description of how the dates are generated. This repository provides:

- a small, dependency-free **algorithm** that generates every date (Python, with a line-for-line JavaScript port);
- **machine-readable data** for every financial year from 1995/96 to 2059/60;
- a **static website** that answers three questions: what period and week is it today, what are the dates of a given period or week, and what does the calendar look like;
- the **full test suite and its results**, cross-checking the algorithm against three independent published sources.

The algorithm was **entirely reverse engineered** from published outputs. It was then **systematically cross-checked** against the Office of Rail and Road's published railway period dates and against Planancy's published rail weeks calendar. Every check matches. The method is described in full below so anyone can verify it, challenge it, or reuse it.

## Contents

- [The three calendars](#the-three-calendars)
- [The algorithm](#the-algorithm)
- [Methodology](#methodology)
- [Test results](#test-results)
- [Using it](#using-it)
- [Repository layout](#repository-layout)
- [Limitations](#limitations)
- [Credits and sources](#credits-and-sources)

## The three calendars

| Calendar | Used for | Weeks run | Year |
|---|---|---|---|
| **Railway periods** | General operational and financial reporting across the industry | Sunday to Saturday | 1 April to 31 March, 13 periods |
| **Possession weeks** | Engineering possession planning only | Saturday to Friday | Starts on the Saturday nearest 1 April, 52 or 53 weeks in 13 periods |
| **Timetable** | Timetable change dates and period blocks A to J | Sunday to Saturday | December to December |

Possession weeks start on a Saturday because possessions are taken over weekends: Saturday and Sunday need to fall in the same week.

**A note on naming.** railwaycalendar.com calls railway periods "finance periods" and possession weeks "NR weeks". This repository uses "railway periods" and "possession weeks", which is how most people in the industry refer to them, and matches ORR, which publishes the former as "railway period dates". Railway periods are used well beyond finance, and possession weeks are used for nothing except possessions.

## The algorithm

The whole calendar hangs off three anchor dates. Everything else is counted from them.

### 1. Possession year

- Possession year *N/N+1* starts on the **Saturday nearest 1 April**. Equivalently, the first Saturday on or after 29 March, so it always falls between 29 March and 4 April.
- Weeks run Saturday to Friday and are numbered from 1.
- There are 13 periods of 4 weeks each. When the gap between one year's start and the next is 53 weeks, **week 53 is added to period 13**, which then has 5 weeks.

53-week possession years between 1995/96 and 2059/60: 1997/98, 2003/04, 2008/09, 2014/15, 2019/20, 2025/26, 2031/32, 2036/37, 2042/43, 2047/48, 2053/54, and 2059/60.

### 2. Railway periods

- The year runs from 1 April to 31 March. Weeks run Sunday to Saturday.
- Each railway period ends on the **Saturday after its possession period ends** (possession periods end on a Friday).
- P1 starts on 1 April and P13 ends on 31 March, so P1 and P13 vary in length (from 25 to 32 days). P2 to P12 are always 28 days.

In other words, railway periods are possession periods shifted forward by one day and clipped to the financial year.

### 3. Timetable year

- Timetable year *N* starts (the Principal, or December, timetable) on the **Sunday after the second Saturday in December** of year *N−1*. This is the European timetable change date.
- The Subsidiary, or May, timetable starts on the **third Sunday in May** of year *N*. The Principal timetable is therefore 22 or 23 weeks long.
- Period blocks:
  - A, B, and C run 3, 6, and 6 weeks from the December change; D runs to the May change.
  - E, F, G, and H run 5, 6, 6, and 6 weeks from the May change; J runs to the next December change.
  - Blocks change on a Monday, except at the two timetable changes, which fall on a Sunday. There is no block I.

### 4. Control periods

Five financial years each. CP7 is 2024/25 to 2028/29. From 2029/30 they are funding periods: FP1 is 2029/30 to 2033/34, and so on. The labels match ORR's for every year from 1995/96.

The reference implementation is [`railcal.py`](railcal.py), about 130 lines of standard-library Python.

## Methodology

### Step 1: reverse engineering from railwaycalendar.com

[railwaycalendar.com](https://railwaycalendar.com), built by Rizwan Khan, publishes year tables for railway periods, possession weeks, timetable years, and period blocks from 2004/05 to 2049/50. Its derivation method is deliberately not published. It was the first good public-facing source for these calendars, and this work would not have been possible without it.

The approach was:

1. **Capture the outputs.** The year table page for each financial year from 2004/05 to 2049/50 was rendered in a browser and its headline text and tables extracted: the possession year range and length, the period table, every possession week with its railway period, timetable, and block, and the timetable year and block tables. 46 years in total.
2. **Form hypotheses from the anchor dates.** Possession year start dates all fall between 29 March and 4 April, which points to "the Saturday nearest 1 April". Railway period ends are always the day after the matching possession period end. Timetable start dates match the European "Sunday after the second Saturday in December" rule.
3. **Test every value, then refine.** A first version assumed a fixed 22-week Principal timetable. It matched everything except 399 timetable values, all in years where the site shows a 23-week Principal. The Subsidiary start dates all fall between 15 and 21 May, which identified the "third Sunday in May" rule. Blocks E to H turned out to count from the May change rather than from December. With those two corrections, every value matched.

**Result: 4,700 out of 4,700 values match** (see [test results](#test-results)).

### Step 2: independent cross-check against ORR

The Office of Rail and Road publishes railway period dates (`railway-period-dates.ods`) for every period from April 1995 to March 2029 (442 periods). The algorithm was not fitted to this data. The comparison is particularly strong for 1995/96 to 2003/04, which is earlier than anything on railwaycalendar.com and so is a genuinely out-of-sample test of the anchor rules.

**Result: all 442 periods match exactly, and the control period labels match for all 34 years.**

### Step 3: independent cross-check against Planancy

Planancy publishes a [2026 to 2030 Rail Weeks Calendar](https://www.planancy.co.uk/ClientResources/2026%20-%202030%20Rail%20Weeks%20Calendar.pdf) showing possession week numbers and period end dates. The PDF is image only, so the values were transcribed by eye from the rendered pages:

- all 65 period end dates for 2026 to 2030;
- the possession week number on the first and last row of every month (120 values). Weeks are consecutive, so these pin down every week in between.

**Result: all 185 values match**, including week 53 in 2025/26 and the years where the possession year starts in March (2029 and 2030).

Planancy's key labels the yellow dates as the "NR Period End Date". They all fall on a Saturday, so they are railway period ends; the possession period ends on the Friday before. The calendar mixes railway period ends with possession week numbers. This is harmless, but worth knowing if the yellow dates are read as possession period boundaries.

### Step 4: JavaScript parity

The website runs a JavaScript port of the engine, [`site/railcal.js`](site/railcal.js). The data files are generated from the Python engine. The parity check compares the two for every year file, every timetable file, every day from 1 April 1996 to 31 March 2059, and a set of query-parser cases.

### Coverage by source

| Calendar | railwaycalendar.com | ORR | Planancy |
|---|:---:|:---:|:---:|
| Railway periods | ✔ | ✔ | ✔ |
| Possession weeks and periods | ✔ | (implied) | ✔ |
| Timetable years and blocks | ✔ | | |
| Control period labels | ✔ | ✔ | |

Railway periods are confirmed by three independent sources and possession weeks by two. Possession periods are also confirmed indirectly by ORR, because railway periods are derived from them. Timetable years and blocks rest on railwaycalendar.com alone.

## Test results

Latest run, from [`test-results/SUMMARY.md`](test-results/SUMMARY.md):

| Check | Checks | Mismatches | Result |
|---|---:|---:|---|
| railwaycalendar.com year tables, 2004/05 to 2049/50 | 4,700 | 0 | pass |
| ORR railway period dates, 1995/96 to 2028/29 | 476 | 0 | pass |
| Planancy 2026 to 2030 Rail Weeks Calendar | 185 | 0 | pass |
| JavaScript engine vs Python data files | 23,156 | 0 | pass |

Breakdown of the railwaycalendar.com checks:

| Item | Checks |
|---|---:|
| Possession week (number, period/week, dates, railway period, timetable, block) | 2,446 |
| Timetable block | 828 |
| Railway period (start, end, days) | 598 |
| Possession period (end, week range) | 598 |
| Possession year start and length | 92 |
| Timetable year (length, Principal, Subsidiary) | 92 |
| Control period label | 46 |

Full output for each check is in [`test-results/`](test-results/).

### Running the tests

Python 3.9 or later and, for the JavaScript parity check, Node.js. No packages need installing.

```bash
python run_tests.py
```

Each check can also be run on its own, for example `python tests/check_orr.py`. Each exits 0 on a full match, 1 on any mismatch, and 3 if its source data is not available locally.

### Reproducing the railwaycalendar.com comparison

The captured snapshot of railwaycalendar.com is **not** committed. The site's content is marked "all rights reserved", so it is not redistributed here. Without the snapshot, `tests/check_railwaycalendar.py` reports "skipped"; the committed result in `test-results/railwaycalendar.txt` is from a run with the snapshot present.

To reproduce it, render `https://railwaycalendar.com/tables.html?fy=<year>` for each year from 2004 to 2049 in a browser (the tables are generated client-side), and save `tests/fixtures/railwaycalendar_snapshot.json` as an object keyed by year, where each entry holds:

- `head`: the line beginning "Financial year …";
- `fin`: the period table rows, cells joined by `|`;
- `wk`: the possession week table rows (first seven cells), joined by `|`;
- `tt`: the lines beginning "Timetable year" or "Principal";
- `blocks`: the block tables, as lists of rows joined by `|`.

## Using it

### Python

```python
from datetime import date
import railcal

railcal.railway_periods(2026)          # [(1, date(2026, 4, 1), date(2026, 5, 2)), ...]
railcal.possession_weeks(2026)         # (week, period, week_in_period, start_sat, end_fri), ...
railcal.railway_period_of(date(2026, 10, 25))   # 8
railcal.timetable_of(date(2026, 10, 25))        # (2026, 'Subsidiary', 'H')
```

### JavaScript

[`site/railcal.js`](site/railcal.js) works in the browser (`window.RailCal`) and in Node (`require`).

```js
const R = require("./site/railcal.js");
R.describe(R.ymd(2026, 10, 25));   // everything about one date
R.lookup("P8W3 2026/27");          // free-text query: periods, weeks, dates, timetables
R.yearJSON(2026);                  // a whole financial year
```

`lookup` accepts the formats people actually type: `P8`, `P08`, `2026/27 P8`, `2627P08`, `wk 31`, `P8W3`, `25/12/2026`, `2026-12-25`, `25 Dec 2026`, `TT2027`, `TT2027 May`, `TT2027 block C`, and `2027/28`. Without a year, the current one is used.

### JSON data

[`site/data/`](site/data/) holds one file per financial year and one per timetable year, listed in [`site/data/index.json`](site/data/index.json). All dates are ISO 8601 and all ranges are inclusive.

```json
{
  "financial_year": "2026/27",
  "control_period": "CP7",
  "railway_periods": [
    { "period": 8, "label": "2026/27 P08", "start": "2026-10-18", "end": "2026-11-14", "days": 28 }
  ],
  "possession_year": {
    "start": "2026-04-04", "end": "2027-04-02", "weeks": 52,
    "periods": [ { "period": 8, "start": "2026-10-17", "end": "2026-11-13", "first_week": 29, "last_week": 32 } ],
    "weeks_list": [ { "week": 30, "period": 8, "week_in_period": 2, "start": "2026-10-24", "end": "2026-10-30" } ]
  }
}
```

(Abridged: each file lists all 13 periods and every week.) Regenerate with `python gen_json.py`.

### Website

[`site/`](site/) is a self-contained static site with no build step and no server-side code. It has three views:

- **Today**: the current railway period, possession week, and timetable block, using UK time.
- **Look up**: the date range for any period, week, date, or timetable, with a JSON view of every answer.
- **Calendar**: browsable grids for each calendar, with search and highlighting.

To run it locally:

```bash
python -m http.server 8000 --directory site
```

It can be hosted as-is on any static host, for example GitHub Pages.

## Repository layout

```
railcal.py                 Reference implementation of the algorithm
gen_json.py                Writes site/data/*.json from railcal.py
run_tests.py               Runs every check and writes test-results/
tests/
  check_railwaycalendar.py   vs railwaycalendar.com (needs local snapshot)
  check_orr.py               vs ORR railway period dates
  check_planancy.py          vs Planancy 2026-2030 calendar (transcribed values inline)
  check_js_parity.js         JavaScript engine vs Python data files
  fixtures/
    orr_railway_period_dates.csv
test-results/              Output of the latest run
site/
  index.html               The website
  railcal.js               JavaScript port of the engine
  data/                    Generated JSON, 1995/96 to 2059/60
```

## Limitations

- **No official source.** These rules reproduce published outputs exactly, but they are not Network Rail's own specification. If an official definition differs in an edge case not covered by the sources above, the official definition wins. Corrections are welcome.
- **Timetable rules have a single source.** Timetable years and blocks are only checked against railwaycalendar.com. Real timetable change dates can also be moved by industry agreement in a given year; this implementation gives the standard rule.
- **Bank holidays are not modelled.**
- **Range.** Data files cover 1995/96 to 2059/60. The engine works for any year, but control period labels before 1995/96 are not meaningful.

## Credits and sources

- **[railwaycalendar.com](https://railwaycalendar.com)**, created and maintained by Rizwan Khan. Its published year tables were the basis for reverse engineering the algorithm. It is independent and not affiliated with Network Rail, and neither is this repository.
- **Office of Rail and Road**, "Railway period dates, Great Britain, April 1995 to March 2029", first published 25 July 2023. Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Extracted to `tests/fixtures/orr_railway_period_dates.csv`.
- **[Planancy](https://www.planancy.co.uk)**, "2026 - 2030 Rail Weeks Calendar". Values transcribed for testing only; the PDF is not redistributed.
