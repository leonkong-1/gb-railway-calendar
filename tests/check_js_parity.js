// Check the JS engine (site/railcal.js) against the Python-generated data files (node tests/check_js_parity.js).
const fs = require("fs");
const path = require("path");
const R = require("../site/railcal.js");

const dir = path.join(__dirname, "..", "site", "data");
const index = JSON.parse(fs.readFileSync(path.join(dir, "index.json"), "utf8"));
let checks = 0, fails = 0;
const same = (label, a, b) => {
  checks++;
  if (JSON.stringify(a) !== JSON.stringify(b)) { fails++; if (fails <= 10) console.log("MISMATCH", label); }
};

for (const { financial_year, file } of index.financial_years) {
  const fy = +financial_year.slice(0, 4);
  same(file, R.yearJSON(fy), JSON.parse(fs.readFileSync(path.join(dir, file), "utf8")));
}
for (const { timetable_year, file } of index.timetable_years) {
  same(file, R.timetableJSON(timetable_year), JSON.parse(fs.readFileSync(path.join(dir, file), "utf8")));
}

// Every day: describe() must agree with the year and timetable files.
const years = {}, tts = {};
const load = (cache, f) => cache[f] || (cache[f] = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")));
for (let day = R.ymd(1996, 4, 1); day <= R.ymd(2059, 3, 31); day++) {
  const d = R.describe(day), iso = d.date;
  const fy = d.financial_year.slice(0, 4), fyf = load(years, `${fy}-${d.financial_year.slice(5)}.json`);
  const rp = fyf.railway_periods.find((r) => r.start <= iso && iso <= r.end);
  const py = d.possession_week.year, pyf = load(years, `${py.slice(0, 4)}-${py.slice(5)}.json`);
  const pw = pyf.possession_year.weeks_list.find((w) => w.start <= iso && iso <= w.end);
  const tt = load(tts, `timetable-${d.timetable.year}.json`);
  const blk = tt.blocks.find((b) => b.start <= iso && iso <= b.end);
  const part = iso <= tt.principal.end ? "Principal" : "Subsidiary";
  same(iso, [d.railway_period.period, d.possession_week.week, d.timetable.part, d.timetable.block],
    [rp.period, pw.week, part, blk.block]);
}

// Parser smoke tests (reference date: Sun 25 Oct 2026)
const ref = R.ymd(2026, 10, 25);
const q = (s) => R.lookup(s, ref);
const expect = (s, f, want) => same(`lookup ${s}`, f(q(s)), want);
expect("today", (r) => [r.type, r.result.railway_period.label, r.result.possession_week.week, r.result.timetable.block], ["date", "2026/27 P08", 30, "H"]);
expect("P8", (r) => [r.result.railway_period.start, r.result.railway_period.end, r.result.possession_period.end], ["2026-10-18", "2026-11-14", "2026-11-13"]);
expect("2627P08", (r) => r.result.railway_period.label, "2026/27 P08");
expect("2025/26 P13", (r) => [r.result.railway_period.days, r.result.possession_period.weeks], [31, 5]);
expect("wk 53 2025/26", (r) => [r.result.start, r.result.end], ["2026-03-28", "2026-04-03"]);
expect("wk 53", (r) => r.type, "error");
expect("P13W5 2025/26", (r) => r.result.week, 53);
expect("P8W3", (r) => [r.result.week, r.result.start], [31, "2026-10-31"]);
expect("25/12/2026", (r) => [r.result.possession_week.week, r.result.timetable.label], [38, "TT2027 Principal"]);
expect("25 Dec 2026", (r) => r.result.date, "2026-12-25");
expect("31/02/2026", (r) => r.type, "error");
expect("TT2027 block C", (r) => [r.result.start, r.result.end], ["2027-02-15", "2027-03-28"]);
expect("tt2027 may", (r) => r.result.start, "2027-05-16");
expect("TT", (r) => r.result.timetable_year, 2026);
expect("2026/27", (r) => [r.type, r.result.possession_year.weeks], ["year", 52]);
expect("block I", (r) => r.type, "error");

console.log(`${checks} checks, ${fails} mismatches`);
process.exit(fails ? 1 : 0);
