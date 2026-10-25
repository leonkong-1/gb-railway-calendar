/* GB railway calendar engine: railway periods, possession weeks, timetable years and period blocks.
 * JavaScript port of railcal.py; see that file for the rules and how they were validated.
 * Dates are handled as whole day numbers (days since 1970-01-01, UTC) so there is no time-of-day or DST drift.
 */
(function (root) {
  "use strict";

  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const BLOCKS = "ABCDEFGHJ";

  // ---- day-number helpers -------------------------------------------------------------------------------
  const ymd = (y, m, d) => Math.floor(Date.UTC(y, m - 1, d) / 86400000);
  const parts = (day) => {
    const t = new Date(day * 86400000);
    return { y: t.getUTCFullYear(), m: t.getUTCMonth() + 1, d: t.getUTCDate() };
  };
  const dow = (day) => (((day + 4) % 7) + 7) % 7; // Sun=0 .. Sat=6
  const iso = (day) => {
    const p = parts(day);
    return `${p.y}-${String(p.m).padStart(2, "0")}-${String(p.d).padStart(2, "0")}`;
  };
  const nextDow = (day, target) => day + ((target - dow(day) + 7) % 7);
  const fyLabel = (fy) => `${fy}/${String((fy + 1) % 100).padStart(2, "0")}`;
  const pad2 = (n) => String(n).padStart(2, "0");

  function londonToday() {
    const s = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit",
    }).format(new Date()); // dd/mm/yyyy
    const [d, m, y] = s.split("/").map(Number);
    return ymd(y, m, d);
  }

  // ---- possession year: Saturday nearest 1 April, Sat-Fri weeks, 13 x 4 weeks, week 53 joins P13 --------
  const possessionYearStart = (fy) => nextDow(ymd(fy, 3, 29), 6);
  const possessionYearWeeks = (fy) => (possessionYearStart(fy + 1) - possessionYearStart(fy)) / 7;
  const possessionYearOf = (day) => {
    const y = parts(day).y;
    return day >= possessionYearStart(y) ? y : y - 1;
  };

  function possessionPeriods(fy) {
    const start = possessionYearStart(fy), n = possessionYearWeeks(fy), out = [];
    for (let p = 1; p <= 13; p++) {
      const fw = (p - 1) * 4 + 1, lw = p === 13 ? n : fw + 3;
      out.push({ period: p, start: start + (fw - 1) * 7, end: start + lw * 7 - 1, first_week: fw, last_week: lw });
    }
    return out;
  }

  function possessionWeek(fy, week) {
    const s = possessionYearStart(fy) + (week - 1) * 7;
    const period = Math.min(Math.floor((week - 1) / 4) + 1, 13);
    return { year: fyLabel(fy), week, period, week_in_period: week - (period - 1) * 4, start: s, end: s + 6 };
  }

  // ---- railway periods: 1 Apr - 31 Mar, each ends the Saturday after its possession period's Friday ------
  const financialYearOf = (day) => {
    const y = parts(day).y;
    return day >= ymd(y, 4, 1) ? y : y - 1;
  };

  function railwayPeriods(fy) {
    let prevEnd = ymd(fy, 4, 1) - 1;
    return possessionPeriods(fy).map((pp) => {
      const end = pp.period === 13 ? ymd(fy + 1, 3, 31) : pp.end + 1;
      const r = { period: pp.period, start: prevEnd + 1, end, days: end - prevEnd };
      prevEnd = end;
      return r;
    });
  }

  // ---- timetable: starts Sunday after 2nd Saturday of December; Subsidiary from 3rd Sunday of May --------
  const timetableStart = (y) => nextDow(ymd(y - 1, 12, 8), 6) + 1;
  const subsidiaryStart = (y) => nextDow(ymd(y, 5, 15), 0);
  const timetableYearOf = (day) => {
    const y = parts(day).y;
    return day >= timetableStart(y + 1) ? y + 1 : y;
  };

  function timetable(y) {
    const s = timetableStart(y), sub = subsidiaryStart(y), nxt = timetableStart(y + 1);
    // A-C: 3/6/6 weeks from December, D to May; E-H: 5/6/6/6 weeks from May, J to December.
    // Blocks change on Mondays, except at the two timetable changes (Sundays).
    const b = [s, s + 21 + 1, s + 63 + 1, s + 105 + 1, sub, sub + 35 + 1, sub + 77 + 1, sub + 119 + 1, sub + 161 + 1, nxt];
    return {
      year: y, start: s, end: nxt - 1, weeks: (nxt - s) / 7,
      principal: { start: s, end: sub - 1, weeks: (sub - s) / 7 },
      subsidiary: { start: sub, end: nxt - 1, weeks: (nxt - sub) / 7 },
      blocks: [...BLOCKS].map((name, i) => ({
        block: name, start: b[i], end: b[i + 1] - 1, weeks: Math.round((b[i + 1] - b[i]) / 7),
      })),
    };
  }

  function controlPeriod(fy) {
    const n = Math.floor((fy - 1994) / 5), yr = ((fy - 1994) % 5) + 1;
    return { name: n < 7 ? `CP${n + 1}` : `FP${n - 6}`, year: yr };
  }

  // ---- JSON shapes (dates as ISO strings) ----------------------------------------------------------------
  const isoRange = (o) => {
    const r = { ...o };
    for (const k of ["start", "end"]) if (typeof r[k] === "number") r[k] = iso(r[k]);
    return r;
  };

  function railwayPeriodJSON(fy, p) {
    const r = railwayPeriods(fy)[p - 1];
    return { year: fyLabel(fy), period: p, label: `${fyLabel(fy)} P${pad2(p)}`, start: iso(r.start), end: iso(r.end), days: r.days };
  }

  function possessionPeriodJSON(fy, p) {
    const r = possessionPeriods(fy)[p - 1];
    return {
      year: fyLabel(fy), period: p, label: `${fyLabel(fy)} P${pad2(p)}`, start: iso(r.start), end: iso(r.end),
      first_week: r.first_week, last_week: r.last_week, weeks: r.last_week - r.first_week + 1,
    };
  }

  function possessionWeekJSON(fy, w) {
    const r = possessionWeek(fy, w);
    return { ...r, label: `${r.year} W${pad2(w)} (P${pad2(r.period)} wk ${r.week_in_period})`, start: iso(r.start), end: iso(r.end) };
  }

  function timetableJSON(y) {
    const t = timetable(y);
    return {
      timetable_year: y, label: `TT${y}`, start: iso(t.start), end: iso(t.end), weeks: t.weeks,
      principal: isoRange(t.principal), subsidiary: isoRange(t.subsidiary),
      blocks: t.blocks.map(isoRange),
    };
  }

  /** Everything about one date. */
  function describe(day) {
    const fy = financialYearOf(day), cp = controlPeriod(fy);
    const rp = railwayPeriods(fy).find((r) => r.start <= day && day <= r.end);
    const py = possessionYearOf(day), w = Math.floor((day - possessionYearStart(py)) / 7) + 1;
    const pw = possessionWeekJSON(py, w);
    const ty = timetableYearOf(day), t = timetable(ty);
    const part = day < t.subsidiary.start ? "Principal" : "Subsidiary";
    const blk = t.blocks.find((b) => b.start <= day && day <= b.end);
    return {
      date: iso(day), weekday: DAYS[dow(day)],
      financial_year: fyLabel(fy), control_period: cp.name, control_period_year: cp.year,
      railway_period: { ...railwayPeriodJSON(fy, rp.period), day: day - rp.start + 1 },
      possession_week: { ...pw, day: day - possessionYearStart(py) - (w - 1) * 7 + 1 },
      possession_period: possessionPeriodJSON(py, pw.period),
      timetable: {
        year: ty, label: `TT${ty} ${part}`, part,
        start: iso(part === "Principal" ? t.principal.start : t.subsidiary.start),
        end: iso(part === "Principal" ? t.principal.end : t.subsidiary.end),
        block: blk.block, block_start: iso(blk.start), block_end: iso(blk.end),
      },
    };
  }

  /** Whole financial year, same shape as the published data/<yyyy-yy>.json files. */
  function yearJSON(fy) {
    const cp = controlPeriod(fy), n = possessionYearWeeks(fy);
    return {
      financial_year: fyLabel(fy), start: iso(ymd(fy, 4, 1)), end: iso(ymd(fy + 1, 3, 31)),
      control_period: cp.name, control_period_year: cp.year,
      railway_periods: railwayPeriods(fy).map((r) => railwayPeriodJSON(fy, r.period)),
      possession_year: {
        year: fyLabel(fy), start: iso(possessionYearStart(fy)), end: iso(possessionYearStart(fy + 1) - 1), weeks: n,
        periods: possessionPeriods(fy).map((p) => possessionPeriodJSON(fy, p.period)),
        weeks_list: Array.from({ length: n }, (_, i) => possessionWeekJSON(fy, i + 1)),
      },
    };
  }

  // ---- query parser --------------------------------------------------------------------------------------
  const MONTH_RE = "(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*";

  function validDate(y, m, d) {
    if (m < 1 || m > 12 || d < 1 || d > 31) return null;
    const day = ymd(y, m, d), p = parts(day);
    return p.m === m && p.d === d ? day : null;
  }

  function parseDate(s) {
    let m;
    if ((m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/))) return validDate(+m[1], +m[2], +m[3]);
    if ((m = s.match(/^(\d{1,2})[\/.](\d{1,2})[\/.](\d{2}|\d{4})$/))) {
      const y = m[3].length === 2 ? 2000 + +m[3] : +m[3];
      return validDate(y, +m[2], +m[1]);
    }
    if ((m = s.match(new RegExp(`^(?:[a-z]+,? )?(\\d{1,2})(?:st|nd|rd|th)? ${MONTH_RE},? (\\d{4})$`)))) {
      return validDate(+m[3], MONTHS.findIndex((x) => x.toLowerCase() === m[2]) + 1, +m[1]);
    }
    return undefined; // not a date-shaped query
  }

  const fail = (query, error) => ({ query, type: "error", error });

  /**
   * Parse a free-text query. Accepts dates ("25/12/2026", "2026-12-25", "25 Dec 2026", "today"),
   * railway/possession periods ("P8", "2026/27 P08", "2627P8"), possession weeks ("wk 31", "P8W3"),
   * financial years ("2026/27") and timetables ("TT2027", "TT2027 May", "TT2027 block C").
   * A missing year means the one containing `ref` (default: today in London).
   */
  function lookup(query, ref) {
    ref = ref == null ? londonToday() : ref;
    const raw = String(query || "").trim();
    let s = raw.toLowerCase().replace(/\s+/g, " ");
    if (!s) return fail(raw, "Type a date, period, week or timetable, for example \u201cP8\u201d or \u201cwk 31\u201d.");
    if (s === "today" || s === "now") return { query: raw, type: "date", result: describe(ref) };

    const d = parseDate(s);
    if (d === null) return fail(raw, `\u201c${raw}\u201d looks like a date but isn\u2019t a real one.`);
    if (d !== undefined) return { query: raw, type: "date", result: describe(d) };

    // Split letters from digits so "p8w3", "tt2027" and "2627p08" tokenise the same as "p 8 w 3".
    s = s.replace(/([a-z])(\d)/g, "$1 $2").replace(/(\d)([a-z])/g, "$1 $2");

    // Year: "2026/27", "2026-27", "2026/2027", "26/27", "2627", or a bare "2026".
    let fy = null, plainYear = null, m;
    if ((m = s.match(/\b(\d{4}) ?[\/-] ?(\d{2}|\d{4})\b/))) {
      const a = +m[1], b = +m[2];
      if (b !== a + 1 && b !== (a + 1) % 100) return fail(raw, `${m[0]} isn\u2019t a financial year. Try ${fyLabel(a)}.`);
      fy = a; s = s.replace(m[0], " ");
    } else if ((m = s.match(/\b(\d{2})\/?(\d{2})\b/)) && +m[2] === (+m[1] + 1) % 100) {
      fy = (+m[1] >= 90 ? 1900 : 2000) + +m[1]; s = s.replace(m[0], " ");
    } else if ((m = s.match(/\b(19|20)\d{2}\b/))) {
      plainYear = +m[0]; s = s.replace(m[0], " ");
    }
    s = s.replace(/\bfy\b/g, " ").replace(/\s+/g, " ").trim();
    const startYear = fy ?? plainYear;
    if (startYear != null && (startYear < 1995 || startYear > 2099)) return fail(raw, "Years from 1995/96 to 2099/00 are supported.");

    // Timetables
    if (/\b(tt|timetable|block|principal|subsidiary|december|may)\b/.test(s)) {
      const ty = plainYear ?? (fy != null ? fy + 1 : timetableYearOf(ref));
      const t = timetableJSON(ty);
      if ((m = s.match(/\bblock ?([a-z])\b/))) {
        const b = t.blocks.find((x) => x.block.toLowerCase() === m[1]);
        if (!b) return fail(raw, "Period blocks are A to H and J (there is no block I).");
        return { query: raw, type: "timetable_block", result: { timetable_year: ty, label: `TT${ty} block ${b.block}`, ...b } };
      }
      if (/\b(principal|december)\b/.test(s)) return { query: raw, type: "timetable_part", result: { timetable_year: ty, label: `TT${ty} Principal`, part: "Principal", ...t.principal } };
      if (/\b(subsidiary|may)\b/.test(s)) return { query: raw, type: "timetable_part", result: { timetable_year: ty, label: `TT${ty} Subsidiary`, part: "Subsidiary", ...t.subsidiary } };
      return { query: raw, type: "timetable_year", result: t };
    }

    // Possession week inside a period: "p8 w3", "period 8 week 3"
    if ((m = s.match(/\b(?:p|period) ?(\d{1,2}) ?(?:w|wk|week) ?(\d)\b/))) {
      const y = fy ?? plainYear ?? possessionYearOf(ref), p = +m[1], wk = +m[2];
      const maxWk = p === 13 ? possessionYearWeeks(y) - 48 : 4;
      if (p < 1 || p > 13) return fail(raw, "Periods run from P1 to P13.");
      if (wk < 1 || wk > maxWk) return fail(raw, `P${pad2(p)} of ${fyLabel(y)} has ${maxWk} possession weeks.`);
      return { query: raw, type: "possession_week", result: possessionWeekJSON(y, (p - 1) * 4 + wk) };
    }
    // Possession week: "wk 31", "week 31", "w31"
    if ((m = s.match(/\b(?:w|wk|week|pw) ?(\d{1,2})\b/))) {
      const y = fy ?? plainYear ?? possessionYearOf(ref), w = +m[1], n = possessionYearWeeks(y);
      if (w < 1 || w > n) return fail(raw, `${fyLabel(y)} has ${n} possession weeks.`);
      return { query: raw, type: "possession_week", result: possessionWeekJSON(y, w) };
    }
    // Period: both the railway period and the possession period with that number
    if ((m = s.match(/\b(?:p|period|rp) ?(\d{1,2})\b/))) {
      const y = fy ?? plainYear ?? financialYearOf(ref), p = +m[1];
      if (p < 1 || p > 13) return fail(raw, "Periods run from P1 to P13.");
      return {
        query: raw, type: "period",
        result: { year: fyLabel(y), period: p, railway_period: railwayPeriodJSON(y, p), possession_period: possessionPeriodJSON(y, p) },
      };
    }
    if (s === "" && startYear != null) return { query: raw, type: "year", result: yearJSON(startYear) };
    return fail(raw, `Couldn\u2019t read \u201c${raw}\u201d. Try \u201cP8\u201d, \u201cwk 31\u201d, \u201cP8W3 2026/27\u201d, \u201c25/12/2026\u201d or \u201cTT2027 block C\u201d.`);
  }

  const api = {
    ymd, parts, dow, iso, fyLabel, londonToday, MONTHS, DAYS,
    possessionYearStart, possessionYearWeeks, possessionYearOf, possessionPeriods, possessionWeek,
    financialYearOf, railwayPeriods, timetableStart, subsidiaryStart, timetableYearOf, timetable, controlPeriod,
    describe, yearJSON, timetableJSON, lookup,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RailCal = api;
})(typeof self !== "undefined" ? self : this);
