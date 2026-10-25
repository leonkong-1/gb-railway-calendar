# Test fixtures

## orr_railway_period_dates.csv

Extracted from the Office of Rail and Road's "Railway period dates, Great Britain, April 1995 to March 2029" (`railway-period-dates.ods`, first published 25 July 2023). The only changes are the format (ODS to CSV), the column names, and dates trimmed to `YYYY-MM-DD`.

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). This file is not covered by the repository's MIT licence.

## railwaycalendar_snapshot.json (not committed)

A local snapshot of railwaycalendar.com's year tables, used by `tests/check_railwaycalendar.py`. It is not redistributed because the site's content is "all rights reserved". See the main README for how to capture it.
