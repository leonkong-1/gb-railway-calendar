# Test results

Run 2026-10-25 23:00 UTC with Python 3.14.3 and Node v24.14.0.

| Check | Checks | Mismatches | Result | Full output |
|---|---:|---:|---|---|
| railwaycalendar.com year tables | 4700 | 0 | pass | [railwaycalendar.txt](railwaycalendar.txt) |
| ORR railway period dates | 476 | 0 | pass | [orr.txt](orr.txt) |
| Planancy 2026-2030 Rail Weeks Calendar | 185 | 0 | pass | [planancy.txt](planancy.txt) |
| JavaScript engine vs Python data files | 23156 | 0 | pass | [js_parity.txt](js_parity.txt) |

Regenerate with `python run_tests.py`. See the README for what each check covers.
