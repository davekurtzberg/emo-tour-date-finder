#!/usr/bin/env python3
"""Build the Emo Tour Date Finder snapshot site (single-file index.html).

Reads data/overview.json (bands + shows pulled from the private Muse app)
and emits index.html with the data embedded. Visitor interactions
(band include/exclude, travel-buffer toggle, hand-added shows) persist
in the visitor's own browser via localStorage.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "overview.json"
OUT_PATH = ROOT / "index.html"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Emo Tour Date Finder — October 2027 Snapshot</title>
<style>
  :root { --bg:#101014; --panel:#1a1a21; --panel2:#22222c; --ink:#eceaf2; --mut:#9a97ab;
          --red:#e5484d; --amber:#f5a524; --green:#46a758; --line:#2e2e3a; --acc:#8e7cf0; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  header, main { max-width:1060px; margin:0 auto; padding:20px 16px; }
  h1 { font-size:28px; margin:8px 0 4px; }
  h2 { font-size:19px; margin:26px 0 10px; }
  .sub { color:var(--mut); font-size:14px; line-height:1.5; }
  .badge { display:inline-block; background:var(--panel2); border:1px solid var(--line);
           border-radius:999px; padding:2px 10px; font-size:12px; color:var(--mut); margin-right:6px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px; margin-top:14px; }
  .cal { display:grid; grid-template-columns:repeat(7,1fr); gap:6px; }
  .dow { text-align:center; color:var(--mut); font-size:12px; padding:4px 0; }
  .day { min-height:74px; border:1px solid var(--line); border-radius:9px; padding:6px 7px;
         background:var(--panel2); cursor:pointer; font-size:12px; line-height:1.35; }
  .day:hover { border-color:var(--acc); }
  .day .n { font-weight:700; font-size:14px; }
  .day.show { border-color:var(--red); box-shadow:inset 0 0 0 1px var(--red); }
  .day.travel { border-color:var(--amber); }
  .day.clear { border-color:var(--green); }
  .day.sel { outline:2px solid var(--acc); }
  .day .tag { display:block; margin-top:3px; font-size:11px; }
  .tag.show { color:var(--red); } .tag.travel { color:var(--amber); } .tag.clear { color:var(--green); }
  .legend { display:flex; gap:16px; flex-wrap:wrap; font-size:13px; color:var(--mut); margin-top:10px; }
  .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th, td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  th { color:var(--mut); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
  a { color:var(--acc); }
  .band { display:flex; gap:10px; align-items:flex-start; padding:9px 8px; border-bottom:1px solid var(--line); }
  .band:last-child { border-bottom:none; }
  .band .meta { color:var(--mut); font-size:12px; }
  .band.off { opacity:.45; }
  button, input, select { font:inherit; }
  button { background:var(--panel2); color:var(--ink); border:1px solid var(--line);
           border-radius:8px; padding:6px 12px; cursor:pointer; }
  button:hover { border-color:var(--acc); }
  input, select { background:var(--panel2); color:var(--ink); border:1px solid var(--line);
                  border-radius:8px; padding:6px 8px; }
  .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
  .win { font-size:15px; padding:8px 0; border-bottom:1px solid var(--line); }
  .win:last-child { border-bottom:none; }
  .win b { color:var(--green); }
  details summary { cursor:pointer; color:var(--mut); font-size:13px; margin-top:4px; }
  .shows { font-size:13px; color:var(--mut); margin:6px 0 2px 26px; line-height:1.6; }
  .warn { background:#2a2113; border:1px solid #57431c; color:#f3d9a4; border-radius:10px;
          padding:10px 14px; font-size:13px; line-height:1.5; margin-top:14px; }
  footer { color:var(--mut); font-size:12px; text-align:center; padding:26px 16px 40px; line-height:1.6; }
  @media (max-width:640px){ .day{ min-height:60px; font-size:11px; } h1{ font-size:23px; } }
</style>
</head>
<body>
<header>
  <h1>🎸 Emo Tour Date Finder</h1>
  <div class="sub">Who's free in <b>October 2027</b>? A snapshot of announced tour dates for a starter
  roster of __BAND_COUNT__ emo / emo-adjacent bands, and the days none of them are playing.</div>
  <div style="margin-top:10px">
    <span class="badge">Snapshot: __GENERATED_AT__</span>
    <span class="badge">__SHOW_COUNT__ announced shows pulled</span>
    <span class="badge">__OCT_COUNT__ show(s) in Oct 2027 so far</span>
  </div>
  <div class="warn"><b>How to read this:</b> a day marked <b>clear</b> means no selected band has an
  <i>announced</i> show that day — it does not prove the band is available. Most bands have not announced
  October 2027 yet. Your band picks, the travel-buffer toggle, and any shows you add by hand are saved
  <b>only in this browser</b> (localStorage) — they are never uploaded anywhere.</div>
</header>
<main>
  <div class="card">
    <div class="row" style="justify-content:space-between">
      <h2 style="margin:0">October 2027</h2>
      <label class="sub"><input type="checkbox" id="bufferToggle"> Travel buffer (day before/after a show counts as busy)</label>
    </div>
    <div class="cal" id="dowRow"></div>
    <div class="cal" id="cal"></div>
    <div class="legend">
      <span><span class="dot" style="background:var(--red)"></span>Show day</span>
      <span><span class="dot" style="background:var(--amber)"></span>Travel buffer</span>
      <span><span class="dot" style="background:var(--green)"></span>All selected bands clear</span>
    </div>
    <div id="dayDetail" style="margin-top:12px"></div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Best common open windows</h2>
    <div id="windows"></div>
    <div class="sub" style="margin-top:8px">Longest runs of days where no selected band has an announced show
    (travel buffers respected when the toggle is on). Windows are ranked by length.</div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Roster</h2>
    <div class="sub">Uncheck a band to remove it from the calendar math. Saved locally.</div>
    <div id="bands" style="margin-top:8px"></div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Add a show the snapshot missed</h2>
    <div class="row">
      <select id="addBand"></select>
      <input type="date" id="addDate" min="2026-01-01" max="2028-12-31">
      <input type="text" id="addVenue" placeholder="Venue" size="18">
      <input type="text" id="addCity" placeholder="City" size="14">
      <button id="addBtn">Add show</button>
    </div>
    <div id="manualList" style="margin-top:10px"></div>
    <div class="row" style="margin-top:14px">
      <button id="resetBtn">Reset my local changes</button>
    </div>
  </div>
</main>
<footer>
  Built from public tour listings; every show in the underlying data carries a source link
  (open a band's shows under Roster). Snapshot regenerated daily — the calendar only changes
  when bands announce new dates.<br>Emo Tour Date Finder — a fan tool, not affiliated with any band.
</footer>
<script>
const DATA = __DATA_JSON__;
const LS_KEY = "emoFinderStateV1";
let state = { excluded: [], manualShows: [], bufferOn: true };
try { const s = JSON.parse(localStorage.getItem(LS_KEY)); if (s) state = Object.assign(state, s); } catch (e) {}
function save() { localStorage.setItem(LS_KEY, JSON.stringify(state)); }

const bandById = {}; DATA.bands.forEach(b => bandById[b.id] = b);
function allShows() {
  return DATA.shows.concat(state.manualShows.map((m, i) => ({
    bandId: m.bandId, date: m.date, venue: m.venue, city: m.city,
    sourceUrl: "", origin: "manual", mid: i })));
}
function selectedBands() { return DATA.bands.filter(b => !state.excluded.includes(b.id)); }
function iso(y, m, d) { return y + "-" + String(m).padStart(2,"0") + "-" + String(d).padStart(2,"0"); }
function shift(dateStr, days) {
  const d = new Date(dateStr + "T12:00:00"); d.setDate(d.getDate() + days);
  return iso(d.getFullYear(), d.getMonth()+1, d.getDate());
}
function dayInfo(dateStr) {
  const sel = new Set(selectedBands().map(b => b.id));
  const shows = allShows().filter(s => s.date === dateStr && sel.has(s.bandId));
  let travelBands = [];
  if (state.bufferOn) {
    const near = new Set();
    allShows().forEach(s => {
      if (!sel.has(s.bandId)) return;
      if (s.date === shift(dateStr, -1) || s.date === shift(dateStr, 1)) near.add(s.bandId);
    });
    travelBands = [...near].filter(id => !shows.some(s => s.bandId === id));
  }
  const busy = new Set(shows.map(s => s.bandId).concat(travelBands));
  const clear = selectedBands().filter(b => !busy.has(b.id));
  return { shows, travelBands, clear,
           status: shows.length ? "show" : (travelBands.length ? "travel" : "clear") };
}

let selectedDay = null;
function renderCalendar() {
  const dow = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  document.getElementById("dowRow").innerHTML = dow.map(d => `<div class="dow">${d}</div>`).join("");
  const first = new Date("2027-10-01T12:00:00");
  const lead = (first.getDay() + 6) % 7; // Monday-first offset
  let html = "";
  for (let i = 0; i < lead; i++) html += `<div></div>`;
  for (let d = 1; d <= 31; d++) {
    const ds = iso(2027, 10, d), info = dayInfo(ds);
    const names = info.shows.map(s => bandById[s.bandId].name).join(", ");
    const tag = info.status === "show" ? `<span class="tag show">▶ ${names}</span>`
      : info.status === "travel" ? `<span class="tag travel">✈ travel</span>`
      : `<span class="tag clear">✓ all clear</span>`;
    html += `<div class="day ${info.status}${selectedDay === ds ? " sel" : ""}" data-day="${ds}">
               <span class="n">${d}</span>${tag}</div>`;
  }
  const cal = document.getElementById("cal");
  cal.innerHTML = html;
  cal.querySelectorAll(".day").forEach(el =>
    el.addEventListener("click", () => { selectedDay = el.dataset.day; renderCalendar(); renderDayDetail(); }));
}
function fmtDate(ds) {
  return new Date(ds + "T12:00:00").toLocaleDateString("en-US",
    { weekday:"short", month:"short", day:"numeric", year:"numeric" });
}
function renderDayDetail() {
  const box = document.getElementById("dayDetail");
  if (!selectedDay) { box.innerHTML = `<div class="sub">Tap a day for the breakdown.</div>`; return; }
  const info = dayInfo(selectedDay);
  let html = `<h3 style="margin:4px 0 8px">${fmtDate(selectedDay)}</h3>`;
  if (info.shows.length) {
    html += `<div><b style="color:var(--red)">Playing:</b></div>` + info.shows.map(s => {
      const b = bandById[s.bandId];
      const src = s.sourceUrl ? ` — <a href="${s.sourceUrl}" target="_blank" rel="noopener">source</a>` : " — added by you";
      return `<div class="shows">▶ <b>${b.name}</b> — ${s.venue || "TBA"}, ${s.city || ""}${src}</div>`;
    }).join("");
  }
  if (info.travelBands.length) {
    html += `<div style="margin-top:8px"><b style="color:var(--amber)">On a travel buffer:</b>
             <span class="sub">${info.travelBands.map(id => bandById[id].name).join(", ")}</span></div>`;
  }
  html += `<div style="margin-top:8px"><b style="color:var(--green)">Clear (${info.clear.length}):</b>
           <span class="sub">${info.clear.map(b => b.name).join(", ") || "nobody"}</span></div>`;
  html += `<div class="sub" style="margin-top:6px">“Clear” = no announced show in the snapshot data, not confirmed availability.</div>`;
  box.innerHTML = html;
}
function renderWindows() {
  const runs = []; let cur = null;
  for (let d = 1; d <= 31; d++) {
    const ds = iso(2027, 10, d);
    if (dayInfo(ds).status === "clear") { if (!cur) cur = { start: ds, end: ds, len: 0 }; cur.end = ds; cur.len++; }
    else if (cur) { runs.push(cur); cur = null; }
  }
  if (cur) runs.push(cur);
  runs.sort((a, b) => b.len - a.len);
  document.getElementById("windows").innerHTML = runs.length
    ? runs.slice(0, 6).map(r => `<div class="win"><b>${fmtDate(r.start)} → ${fmtDate(r.end)}</b>
        <span class="sub"> — ${r.len} day${r.len > 1 ? "s" : ""}, all ${selectedBands().length} selected bands clear</span></div>`).join("")
    : `<div class="sub">No fully-clear days for the current selection.</div>`;
}
function renderBands() {
  const shows = allShows();
  document.getElementById("bands").innerHTML = DATA.bands.map(b => {
    const mine = shows.filter(s => s.bandId === b.id)
      .sort((a, c) => a.date < c.date ? -1 : 1);
    const oct = mine.filter(s => s.date.startsWith("2027-10")).length;
    const checked = b.lastCheckedAt ? new Date(b.lastCheckedAt).toLocaleDateString("en-US",
      { month:"short", day:"numeric", year:"numeric" }) : "—";
    const list = mine.map(s => `${fmtDate(s.date)} — ${s.venue || "TBA"}, ${s.city || ""}` +
      (s.sourceUrl ? ` (<a href="${s.sourceUrl}" target="_blank" rel="noopener">source</a>)` : " (yours)")).join("<br>");
    return `<div class="band${state.excluded.includes(b.id) ? " off" : ""}">
      <input type="checkbox" data-band="${b.id}" ${state.excluded.includes(b.id) ? "" : "checked"} style="margin-top:3px">
      <div><b>${b.name}</b> <span class="meta">${b.era || ""}</span><br>
      <span class="meta">${mine.length} announced show(s) · ${oct} in Oct 2027 · dates checked ${checked}</span>
      ${mine.length ? `<details><summary>shows</summary><div class="shows">${list}</div></details>` : ""}
      </div></div>`;
  }).join("");
  document.querySelectorAll("[data-band]").forEach(cb => cb.addEventListener("change", () => {
    const id = Number(cb.dataset.band);
    state.excluded = cb.checked ? state.excluded.filter(x => x !== id)
                                : state.excluded.concat(id);
    save(); renderAll();
  }));
}
function renderManual() {
  const sel = document.getElementById("addBand");
  sel.innerHTML = DATA.bands.map(b => `<option value="${b.id}">${b.name}</option>`).join("");
  document.getElementById("manualList").innerHTML = state.manualShows.length
    ? state.manualShows.map((m, i) => `<div class="shows">✎ <b>${bandById[m.bandId].name}</b> — ${fmtDate(m.date)} — ${m.venue || "TBA"}, ${m.city || ""}
        <button data-del="${i}">remove</button></div>`).join("")
    : `<div class="sub">No hand-added shows yet.</div>`;
  document.querySelectorAll("[data-del]").forEach(btn => btn.addEventListener("click", () => {
    state.manualShows.splice(Number(btn.dataset.del), 1); save(); renderAll();
  }));
}
function renderAll() { renderCalendar(); renderDayDetail(); renderWindows(); renderBands(); renderManual(); }
document.getElementById("bufferToggle").checked = state.bufferOn;
document.getElementById("bufferToggle").addEventListener("change", e => {
  state.bufferOn = e.target.checked; save(); renderAll();
});
document.getElementById("addBtn").addEventListener("click", () => {
  const date = document.getElementById("addDate").value;
  if (!date) { alert("Pick a date first."); return; }
  state.manualShows.push({ bandId: Number(document.getElementById("addBand").value), date,
    venue: document.getElementById("addVenue").value.trim(),
    city: document.getElementById("addCity").value.trim() });
  save(); renderAll();
});
document.getElementById("resetBtn").addEventListener("click", () => {
  if (confirm("Clear your local picks and hand-added shows?")) {
    state = { excluded: [], manualShows: [], bufferOn: true };
    document.getElementById("bufferToggle").checked = true; save(); renderAll();
  }
});
renderAll();
</script>
</body>
</html>
"""


def main() -> int:
    raw = json.loads(DATA_PATH.read_text())
    data = raw.get("data", raw)
    bands = data["bands"]
    shows = data["shows"]
    payload = {
        "bands": [
            {"id": b["id"], "name": b["name"], "era": b.get("era", ""),
             "lastCheckedAt": b.get("lastCheckedAt")}
            for b in bands
        ],
        "shows": [
            {"bandId": s["bandId"], "date": s["date"], "venue": s.get("venue", ""),
             "city": s.get("city", ""), "sourceUrl": s.get("sourceUrl", ""),
             "origin": s.get("origin", "search")}
            for s in shows
        ],
    }
    generated = datetime.now(timezone.utc).astimezone().strftime("%b %d, %Y")
    html = (
        TEMPLATE
        .replace("__DATA_JSON__", json.dumps(payload))
        .replace("__BAND_COUNT__", str(len(bands)))
        .replace("__SHOW_COUNT__", str(len(shows)))
        .replace("__OCT_COUNT__", str(sum(1 for s in shows if s["date"].startswith("2027-10"))))
        .replace("__GENERATED_AT__", generated)
    )
    OUT_PATH.write_text(html)
    print(f"Wrote {OUT_PATH} ({len(html)} bytes) from {len(bands)} bands / {len(shows)} shows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
