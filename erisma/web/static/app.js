"use strict";
// Erisma web client: schema-driven input forms with live calculation preview.
// Usability rules: never lose work (autosave), point at the wrong field, always explain
// failures with a hint, keyboard shortcuts for the common actions, Greek & English UI.

const UI = {
  el: {
    "Open": "Άνοιγμα", "Save": "Αποθήκευση", "Export HTML": "Εξαγωγή HTML", "Print / PDF": "Εκτύπωση / PDF",
    "Open project file (Ctrl+O)": "Άνοιγμα αρχείου έργου (Ctrl+O)", "Save project file (Ctrl+S)": "Αποθήκευση αρχείου έργου (Ctrl+S)",
    "Download report as HTML": "Λήψη τεύχους ως HTML", "Print or save as PDF (Ctrl+P)": "Εκτύπωση ή αποθήκευση ως PDF (Ctrl+P)",
    "structural calculations": "στατικοί υπολογισμοί", "Project details": "Στοιχεία έργου",
    "Company": "Εταιρεία", "Project": "Έργο", "Job no.": "Αρ. έργου", "Client": "Πελάτης",
    "Element": "Στοιχείο", "Calc. by": "Συντάκτης", "Checked by": "Έλεγχος", "Date": "Ημερομηνία",
    "Report": "Τεύχος", "3D model": "3D μοντέλο", "Search calculations…": "Αναζήτηση υπολογισμών…",
    "Reset to defaults": "Επαναφορά προεπιλογών", "Inputs restored from your last session": "Επαναφέρθηκαν τα δεδομένα της τελευταίας συνεδρίας",
    "All checks pass": "Όλοι οι έλεγχοι επαρκούν", "Design fails": "Ο σχεδιασμός ανεπαρκεί",
    "max utilisation": "μέγιστη αξιοποίηση", "Analysis complete": "Η ανάλυση ολοκληρώθηκε",
    "Calculating…": "Υπολογισμός…", "failing check(s) — what to change": "έλεγχοι ανεπαρκούν — τι να αλλάξετε",
    "+ Add row": "+ Προσθήκη γραμμής", "Remove row": "Διαγραφή γραμμής", "Not an Erisma project file": "Δεν είναι αρχείο έργου Erisma",
    "Layers": "Επίπεδα", "Labels": "Ετικέτες", "Front": "Όψη", "Top": "Κάτοψη", "Save image": "Αποθήκευση εικόνας",
    "Drag to rotate · right-drag to pan · scroll to zoom": "Σύρετε για περιστροφή · δεξί κλικ για μετακίνηση · ροδέλα για zoom",
    "Shortcuts: Ctrl+S save · Ctrl+O open · Ctrl+P print · Ctrl+3 3D · Ctrl+Z undo · Enter next field · ↑↓ change value · F1 manual": "Συντομεύσεις: Ctrl+S αποθήκευση · Ctrl+O άνοιγμα · Ctrl+P εκτύπωση · Ctrl+3 3D",
    "No calculations match": "Δεν βρέθηκαν υπολογισμοί",
    "Home": "Αρχική", "Welcome to Erisma": "Καλώς ήρθατε στο Erisma",
    "Choose a calculation to start. Results, checks and the report update while you type.":
      "Επιλέξτε έναν υπολογισμό για να ξεκινήσετε. Τα αποτελέσματα, οι έλεγχοι και το τεύχος ενημερώνονται καθώς γράφετε.",
    "Open project file…": "Άνοιγμα αρχείου έργου…", "Continue": "Συνέχεια",
    "Choose a calculation": "Επιλέξτε υπολογισμό",
    "Enter your data — the defaults are a realistic worked example": "Συμπληρώστε τα δεδομένα σας — οι προεπιλογές είναι ένα ρεαλιστικό παράδειγμα",
    "Check the results and print the report (PDF)": "Δείτε τα αποτελέσματα και εκτυπώστε το τεύχος (PDF)",
    "last used": "τελευταίος", "National Annex": "Εθνικό Προσάρτημα",
    "Favourites": "Αγαπημένα", "Recent": "Πρόσφατα", "Add to favourites": "Προσθήκη στα αγαπημένα",
    "Remove from favourites": "Αφαίρεση από τα αγαπημένα", "Collapse / expand the menu": "Σύμπτυξη / ανάπτυξη μενού",
    "Dark / light theme": "Σκούρο / ανοιχτό θέμα", "Zone": "Ζώνη", "Project site": "Τοποθεσία έργου",
    "No site selected": "Δεν έχει επιλεγεί τοποθεσία", "Map": "Χάρτης", "From map": "Από χάρτη",
    "Project site — seismic zone from the map": "Τοποθεσία έργου — σεισμική ζώνη από τον χάρτη",
    "📍 Use my location": "📍 Η θέση μου", "Click on the map, choose a place or give coordinates.":
      "Κάντε κλικ στον χάρτη, επιλέξτε τοποθεσία ή δώστε συντεταγμένες.",
    "Cancel": "Άκυρο", "Use this site": "Χρήση αυτής της θέσης", "Selected point": "Επιλεγμένο σημείο",
    "Outside the zonation map": "Εκτός του χάρτη ζωνών", "Coordinates": "Συντεταγμένες", "My location": "Η θέση μου",
    "Near a zone boundary — the higher zone within 1 km is used (safe side).":
      "Κοντά σε όριο ζωνών — λαμβάνεται η δυσμενέστερη ζώνη σε ακτίνα 1 km (υπέρ της ασφαλείας).",
    "NA to CYS EN 1998-1, zonation map": "χάρτης ζωνών ΕΠ CYS EN 1998-1",
    "Location is not available in this browser.": "Η θέση δεν είναι διαθέσιμη σε αυτόν τον browser.",
    "Search places…": "Αναζήτηση τοποθεσίας…",
    "Arithmetic allowed, e.g. 2*3,5": "Επιτρέπονται πράξεις, π.χ. 2*3,5", "Not a number": "Δεν είναι αριθμός",
    "Duplicate row": "Αντιγραφή γραμμής", "Tip: paste rows from Excel (Ctrl+V)": "Συμβουλή: επικόλληση γραμμών από Excel (Ctrl+V)",
    "Changed from the example values": "Αλλαγμένα από τις τιμές του παραδείγματος",
    "Click to collapse / expand": "Κλικ για σύμπτυξη / ανάπτυξη", "Back to the example value": "Επαναφορά στην τιμή του παραδείγματος",
    "Shortcuts: Ctrl+S save · Ctrl+O open · Ctrl+P print · Ctrl+3 3D · Ctrl+Z undo · Enter next field · ↑↓ change value · F1 manual":
      "Συντομεύσεις: Ctrl+S αποθήκευση · Ctrl+O άνοιγμα · Ctrl+P εκτύπωση · Ctrl+3 3D · Ctrl+Z αναίρεση · Enter επόμενο πεδίο · ↑↓ αλλαγή τιμής · F1 εγχειρίδιο",
  },
};
let LANG = (() => { try { return localStorage.getItem("erisma.lang") || "el"; } catch { return "el"; } })();
const t = (k) => (LANG !== "en" && UI[LANG]?.[k]) || k;
window.ErismaI18n = t;

const PROJECT_FIELDS = [
  ["company", "Company"], ["project", "Project"], ["job_no", "Job no."],
  ["client", "Client"], ["section", "Element"], ["calc_by", "Calc. by"],
  ["checked_by", "Checked by"], ["date", "Date"],
];

const state = { modules: [], schema: null, inputs: {}, project: {}, lastHtml: "", lastSummary: null };
const $ = (s) => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "on") Object.entries(v).forEach(([ev, fn]) => e.addEventListener(ev, fn));
    else if (v !== undefined && v !== null) e.setAttribute(k, v);
  }
  kids.flat().forEach((c) => e.append(c instanceof Node ? c : document.createTextNode(c)));
  return e;
};

// ------------------------------------------------------------------ storage
const store = {
  get(key, fallback) {
    try {
      // fall back to data saved under the program's former name
      const v = localStorage.getItem(key) ?? localStorage.getItem(key.replace(/^erisma\./, "blackeye."));
      return JSON.parse(v) ?? fallback;
    } catch { return fallback; }
  },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ } },
  del(key) { try { localStorage.removeItem(key); } catch { /* ignore */ } },
};
const inputsKey = (id) => `erisma.inputs.${id}`;

async function api(path, body) {
  const sep = path.includes("?") ? "&" : "?";
  const res = await fetch(body ? path : `${path}${sep}lang=${LANG}`, body ? {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, lang: LANG }),
  } : undefined);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    const err = new Error(typeof d === "object" && d ? d.message : d || res.statusText);
    err.field = d?.field;
    throw err;
  }
  return data;
}

// ---------------------------------------------------------------- chrome
function translateChrome() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-t]").forEach((n) => { n.textContent = t(n.dataset.t); });
  document.querySelectorAll("[data-tt]").forEach((n) => { n.title = t(n.dataset.tt); });
  $("#search").placeholder = t("Search calculations…");
  $("#home-search").placeholder = t("Search calculations…");
  $("#map-search").placeholder = t("Search places…");
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === LANG));
  $("#shortcuts").textContent = t("Shortcuts: Ctrl+S save · Ctrl+O open · Ctrl+P print · Ctrl+3 3D · Ctrl+Z undo · Enter next field · ↑↓ change value · F1 manual");
}

// ------------------------------------------------------------- sidebar
const favs = () => store.get("erisma.favs", []);
const recent = () => store.get("erisma.recent", []);
function toggleFav(id) {
  const f = favs();
  store.set("erisma.favs", f.includes(id) ? f.filter((x) => x !== id) : [...f, id]);
  renderNav();
}
function pushRecent(id) {
  store.set("erisma.recent", [id, ...recent().filter((x) => x !== id)].slice(0, 4));
}
function navItem(m) {
  const on = favs().includes(m.id);
  const a = el("a", { href: `#${m.id}`, class: `item${state.schema?.id === m.id ? " active" : ""}`,
    "data-id": m.id, title: `${m.title} — ${m.standard}`,
    on: { click: (e) => { e.preventDefault(); openModule(m.id); } } });
  a.innerHTML = `<span class="ico">${typeof pic === "function" ? pic(m.id) : ""}</span>`;
  const star = el("button", { class: `star${on ? " on" : ""}`, type: "button",
    title: t(on ? "Remove from favourites" : "Add to favourites"),
    on: { click: (e) => { e.preventDefault(); e.stopPropagation(); toggleFav(m.id); } } }, on ? "★" : "☆");
  a.append(el("span", { class: "t" }, m.title, el("span", { class: "s" }, m.standard)),
    el("span", { class: "meta" }, m.has_3d ? el("span", { class: "mini3d" }, "3D") : "", star));
  return a;
}
function navSection(key, title, mods) {
  if (!mods.length) return null;
  const closed = store.get("erisma.closed", []).includes(key);
  const sec = el("div", { class: `sec${closed ? " closed" : ""}` });
  const head = el("button", { class: "sec-h", type: "button", on: { click: () => {
    const c = store.get("erisma.closed", []);
    store.set("erisma.closed", c.includes(key) ? c.filter((x) => x !== key) : [...c, key]);
    sec.classList.toggle("closed");
  } } }, el("span", { class: "chev" }, "▾"), el("span", {}, title), el("span", { class: "count" }, String(mods.length)));
  sec.append(head, el("div", { class: "items" }, ...mods.map(navItem)));
  return sec;
}
function renderNav() {
  const nav = $("#modules");
  nav.innerHTML = "";
  const q = $("#search").value.trim().toLowerCase();
  const match = (m) => !q || `${m.title} ${m.standard} ${m.category} ${m.description}`.toLowerCase().includes(q);
  const mods = state.modules.filter(match);
  const byId = (id) => mods.find((m) => m.id === id);
  if (!q) {
    for (const sec of [navSection("fav", `★ ${t("Favourites")}`, favs().map(byId).filter(Boolean)),
      navSection("recent", t("Recent"), recent().map(byId).filter(Boolean))]) if (sec) nav.append(sec);
  }
  const cats = {};
  mods.forEach((m) => (cats[m.category] ||= []).push(m));
  Object.entries(cats).sort((a, b) => b[1].length - a[1].length)
    .forEach(([cat, ms]) => nav.append(navSection(`cat:${cat}`, cat, ms)));
  if (!mods.length) nav.append(el("p", { class: "muted pad" }, t("No calculations match")));
}

// ----------------------------------------------------------- theme & side
function setTheme(th) {
  document.documentElement.dataset.theme = th;
  try { localStorage.setItem("erisma.theme", th); } catch { /* ignore */ }
  $("#btn-theme").textContent = th === "dark" ? "☀" : "☾";
  window.dispatchEvent(new Event("erisma:theme"));
}
function setSide(collapsed) {
  document.body.classList.toggle("side-collapsed", collapsed);
  $("#side-toggle").textContent = collapsed ? "»" : "«";
  try { localStorage.setItem("erisma.side", collapsed ? "collapsed" : "open"); } catch { /* ignore */ }
  window.dispatchEvent(new Event("erisma:show3d"));
}

function renderProject() {
  const box = $("#project-fields");
  box.innerHTML = "";
  if (!state.project.date) state.project.date = new Date().toISOString().slice(0, 10);
  if (state.annexes?.length) {
    const sel = el("select", { id: "p-annex", on: { change: (e) => {
      state.project.annex = e.target.value; store.set("erisma.project", state.project);
      renderProject(); if (state.schema) renderForm(); schedule();
    } } }, ...state.annexes.map((a) => el("option", { value: a.code, title: a.reference }, a.label)));
    sel.value = state.project.annex || "EN";
    const na = state.annexes.find((a) => a.code === sel.value);
    box.append(el("div", { class: "wide" }, el("label", { for: "p-annex" }, t("National Annex")), sel,
      ...(na?.notes || []).map((n) => el("div", { class: "help" }, n))));
  }
  const naSel = (state.annexes || []).find((a) => a.code === (state.project.annex || "EN"));
  if (naSel?.map) {
    const p = state.project;
    const txt = p.lat ? `${p.site || "—"} · ${Number(p.lat).toFixed(4)}°N ${Number(p.lon).toFixed(4)}°E` +
      (p.zone ? ` · ${t("Zone")} ${p.zone} (${p.ag} g)` : "") : t("No site selected");
    box.append(el("div", { class: "wide" }, el("label", {}, t("Project site")),
      el("div", { class: "site-row" }, el("span", { class: "site-txt" }, txt),
        el("button", { class: "ghost", type: "button", on: { click: () => openMap() } }, `📍 ${t("Map")}`))));
  }
  for (const [key, label] of PROJECT_FIELDS) {
    const id = `p-${key}`;
    const input = el("input", { id, value: state.project[key] || "", type: key === "date" ? "date" : "text",
      on: { input: (e) => { state.project[key] = e.target.value; store.set("erisma.project", state.project); schedule(); } } });
    box.append(el("div", {}, el("label", { for: id }, t(label)), input));
  }
}

// ------------------------------------------------------------------ form
// Numbers: Greek comma decimals ("1,5") and simple arithmetic ("2*3,5", "(4+2)/2", "1,5^2").
function parseNum(str) {
  if (typeof str === "number") return str;
  const s = String(str ?? "").trim().replace(/,/g, ".").replace(/\^/g, "**");
  if (s === "") return null;
  if (!/^[0-9+\-*/().\s eE]+$/.test(s)) return NaN;
  try {
    const v = Function(`"use strict"; return (${s});`)();  // only digits and operators reach here
    return typeof v === "number" && Number.isFinite(v) ? v : NaN;
  } catch { return NaN; }
}
const fmtNum = (v) => (v === null || v === undefined || v === "" ? "" :
  (LANG === "el" ? String(+(+v).toPrecision(10)).replace(".", ",") : String(+(+v).toPrecision(10))));
const isExpr = (s) => /[+*/()^]|\d\s*-\s*\d/.test(String(s));

function stepFor(v) {
  const a = Math.abs(v);
  if (!a) return 0.1;
  return 10 ** (Math.floor(Math.log10(a)) - 1);
}

function scalarInput(f, value, onChange) {
  if (f.kind === "choice") {
    const labels = f.choice_labels || f.choices;
    const s = el("select", { on: { change: (e) => onChange(e.target.value) } },
      ...f.choices.map((c, i) => el("option", { value: c }, labels[i])));
    s.value = value ?? f.default;
    return s;
  }
  if (f.kind === "text") {
    return el("input", { type: "text", value: value ?? f.default ?? "",
      on: { input: (e) => onChange(e.target.value) } });
  }
  if (f.kind === "bool") {
    const c = el("input", { type: "checkbox", class: "chk", on: { change: (e) => onChange(e.target.checked) } });
    c.checked = !!(value ?? f.default);
    return c;
  }
  const range = [f.min != null ? `≥ ${fmtNum(f.min)}` : "", f.max != null ? `≤ ${fmtNum(f.max)}` : ""]
    .filter(Boolean).join(" · ");
  const inp = el("input", { type: "text", inputmode: "decimal", class: "num", value: fmtNum(value ?? f.default),
    title: [range, t("Arithmetic allowed, e.g. 2*3,5")].filter(Boolean).join(" — "), spellcheck: "false" });
  const commit = (raw, final) => {
    const v = parseNum(raw);
    const bad = Number.isNaN(v) || (v !== null && ((f.min != null && v < f.min) || (f.max != null && v > f.max)));
    inp.classList.toggle("bad", bad);
    inp.dataset.eval = !bad && v !== null && isExpr(raw) ? `= ${fmtNum(v)}` : "";
    inp.parentElement?.setAttribute("data-eval", inp.dataset.eval);
    if (bad) {
      inp.title = Number.isNaN(v) ? t("Not a number") : range;
      return;
    }
    if (final && v !== null && isExpr(raw)) { inp.value = fmtNum(v); inp.parentElement?.setAttribute("data-eval", ""); }
    onChange(f.kind === "int" && v !== null ? Math.round(v) : v);
  };
  inp.addEventListener("input", () => commit(inp.value, false));
  inp.addEventListener("blur", () => { if (inp.isConnected) commit(inp.value, true); });
  inp.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      const v = parseNum(inp.value) ?? 0;
      if (Number.isNaN(v)) return;
      e.preventDefault();
      let st = f.kind === "int" ? 1 : stepFor(v);
      if (e.shiftKey) st *= 10;
      let nv = +(v + (e.key === "ArrowUp" ? st : -st)).toPrecision(12);
      if (f.min != null) nv = Math.max(nv, f.min);
      if (f.max != null) nv = Math.min(nv, f.max);
      inp.value = fmtNum(nv);
      commit(inp.value, true);
    }
  });
  return inp;
}

// Enter moves to the next input (like a spreadsheet); Shift+Enter goes back.
document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || !e.target.closest?.("#inputs") || e.target.tagName === "BUTTON") return;
  const all = [...document.querySelectorAll("#inputs input, #inputs select")]
    .filter((n) => n.offsetParent !== null);
  const i = all.indexOf(e.target);
  if (i < 0) return;
  e.preventDefault();
  e.target.blur();
  all[Math.max(0, Math.min(all.length - 1, i + (e.shiftKey ? -1 : 1)))]?.focus();
  all[i + (e.shiftKey ? -1 : 1)]?.select?.();
});

// ---------------------------------------------------------- undo / redo
const hist = { stack: [], pos: -1, timer: null };
function snapshot() {
  if (hist.lock) return;
  clearTimeout(hist.timer);
  hist.timer = setTimeout(() => {
    const snap = JSON.stringify(state.inputs);
    if (hist.stack[hist.pos] === snap) return;
    hist.stack = hist.stack.slice(0, hist.pos + 1);
    hist.stack.push(snap);
    if (hist.stack.length > 100) hist.stack.shift();
    hist.pos = hist.stack.length - 1;
  }, 500);
}
function resetHistory() { hist.stack = [JSON.stringify(state.inputs)]; hist.pos = 0; }
function undo(dir) {
  const np = hist.pos + dir;
  if (np < 0 || np >= hist.stack.length) return;
  hist.lock = true;  // the focused field's blur must not record a new step
  document.activeElement?.blur?.();
  clearTimeout(hist.timer);
  hist.pos = np;
  state.inputs = JSON.parse(hist.stack[np]);
  renderForm();
  hist.lock = false;
  schedule();
}

// ------------------------------------------------------------- tables
function tableEditor(f) {
  const rows = state.inputs[f.name] ||= structuredClone(f.default || []);
  const wrap = el("div", { class: "tblwrap", id: `f-${f.name}` });
  const changed = () => { snapshot(); schedule(); };
  const draw = () => {
    wrap.innerHTML = "";
    const head = el("tr", {}, el("th", { class: "rn" }, "#"),
      ...f.columns.map((c) => el("th", {}, c.label + (c.unit ? ` [${c.unit}]` : ""))), el("th"));
    const body = rows.map((r, i) => el("tr", {}, el("td", { class: "rn" }, String(i + 1)),
      ...f.columns.map((c, j) => {
        const cell = scalarInput(c, r[c.name], (v) => { r[c.name] = v; changed(); });
        cell.dataset.row = i; cell.dataset.col = j;
        return el("td", {}, cell);
      }),
      el("td", { class: "rowbtns" },
        el("button", { type: "button", class: "tbl-dup", title: t("Duplicate row"),
          on: { click: () => { rows.splice(i + 1, 0, structuredClone(r)); draw(); changed(); } } }, "⧉"),
        el("button", { type: "button", class: "tbl-del", title: t("Remove row"),
          on: { click: () => { rows.splice(i, 1); draw(); changed(); } } }, "×"))));
    wrap.append(el("div", { class: "tbl-title" }, f.label,
      el("span", { class: "tbl-tip" }, t("Tip: paste rows from Excel (Ctrl+V)"))),
      el("table", { class: "tbl" }, el("thead", {}, head), el("tbody", {}, ...body)),
      el("button", { type: "button", class: "tbl-add", on: { click: () => {
        const last = rows[rows.length - 1];
        rows.push(last ? structuredClone(last) : Object.fromEntries(f.columns.map((c) => [c.name, c.default])));
        draw(); changed();
        wrap.querySelector(`[data-row="${rows.length - 1}"][data-col="0"]`)?.focus();
      } } }, t("+ Add row")));
  };
  // Paste a block of cells copied from Excel / LibreOffice (tab-separated).
  wrap.addEventListener("paste", (e) => {
    const cell = e.target.closest?.("[data-row]");
    const text = e.clipboardData?.getData("text/plain") || "";
    if (!cell || !/[\t\n]/.test(text.trim())) return;
    e.preventDefault();
    cell.blur();  // commit the cell first so its blur cannot overwrite the pasted value
    const r0 = +cell.dataset.row, c0 = +cell.dataset.col;
    text.replace(/\r/g, "").split("\n").filter((l) => l.trim() !== "").forEach((line, di) => {
      const ri = r0 + di;
      if (!rows[ri]) rows[ri] = Object.fromEntries(f.columns.map((c) => [c.name, c.default]));
      line.split("\t").forEach((val, dj) => {
        const col = f.columns[c0 + dj];
        if (!col) return;
        if (col.kind === "choice") {
          const k = col.choices.findIndex((c, idx) => c === val.trim() || (col.choice_labels || [])[idx] === val.trim());
          if (k >= 0) rows[ri][col.name] = col.choices[k];
        } else if (col.kind === "text") rows[ri][col.name] = val.trim();
        else { const v = parseNum(val); if (v !== null && !Number.isNaN(v)) rows[ri][col.name] = v; }
      });
    });
    draw(); changed();
  });
  draw();
  return wrap;
}

// --------------------------------------------------------------- form
const sameVal = (a, b) => (a === b) || (a != null && b != null && String(a) === String(b)) ||
  (typeof a === "number" && typeof b === "number" && Math.abs(a - b) < 1e-12);
const collapsedKey = () => `erisma.collapsed.${state.schema.id}`;

function markChanged(row, f) {
  const ch = !sameVal(state.inputs[f.name], f.default);
  row.classList.toggle("changed", ch);
  const fs = row.closest("fieldset");
  if (fs) {
    const n = fs.querySelectorAll(".field.changed").length;
    const badge = fs.querySelector("legend .cnt");
    if (badge) { badge.textContent = n ? `● ${n}` : ""; badge.title = t("Changed from the example values"); }
  }
}

function renderForm() {
  const form = $("#inputs");
  form.innerHTML = "";
  const groups = {};
  state.schema.fields.forEach((f) => (groups[f.group] ||= []).push(f));
  const collapsed = new Set(store.get(collapsedKey(), []));
  for (const [g, fields] of Object.entries(groups)) {
    const legend = el("legend", { tabindex: "0", title: t("Click to collapse / expand") },
      el("span", { class: "chev" }, "▾"), g, el("span", { class: "cnt" }));
    const fs = el("fieldset", { class: collapsed.has(g) ? "closed" : "" }, legend);
    const toggle = () => {
      fs.classList.toggle("closed");
      const cur = new Set(store.get(collapsedKey(), []));
      fs.classList.contains("closed") ? cur.add(g) : cur.delete(g);
      store.set(collapsedKey(), [...cur]);
    };
    legend.addEventListener("click", toggle);
    legend.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    for (const f of fields) {
      if (f.kind === "table") { fs.append(tableEditor(f)); continue; }
      if (!(f.name in state.inputs)) state.inputs[f.name] = f.default;
      const id = `f-${f.name}`;
      let row;
      const input = scalarInput(f, state.inputs[f.name], (v) => {
        state.inputs[f.name] = v; clearInvalid(); updateVisibility(); markChanged(row, f); snapshot(); schedule();
      });
      input.id = id;
      const reset = el("button", { type: "button", class: "fld-reset", tabindex: "-1",
        title: `${t("Back to the example value")}: ${f.kind === "choice" ? (f.choice_labels || f.choices)[f.choices.indexOf(f.default)] ?? f.default : f.kind === "bool" ? (f.default ? "✓" : "✗") : fmtNum(f.default)}`,
        on: { click: () => {
          state.inputs[f.name] = f.default;
          renderForm(); snapshot(); schedule();
        } } }, "↺");
      const info = f.help ? el("button", { type: "button", class: "fld-info", tabindex: "-1", title: f.help,
        on: { click: () => row.classList.toggle("showhelp") } }, "i") : "";
      row = el("div", { class: "field", "data-name": f.name, "data-show-if": f.show_if || null },
        el("label", { for: id }, f.label, info, reset),
        el("div", { class: "inp" }, input, el("span", {}, f.unit || "")));
      if (f.help) row.append(el("div", { class: "help" }, f.help));
      if (f.name === "ag") row.append(zoneChips(input));
      input.addEventListener("focus", () => row.classList.add("focus"));
      input.addEventListener("blur", () => row.classList.remove("focus"));
      fs.append(row);
      markChanged(row, f);
    }
    form.append(fs);
    fs.querySelectorAll(".field").forEach((r) => {
      const f = fields.find((x) => x.name === r.dataset.name);
      if (f) markChanged(r, f);
    });
  }
  updateVisibility();
}

// Fields with show_if appear only when their switch is on (keeps the form short).
function updateVisibility() {
  document.querySelectorAll("#inputs [data-show-if]").forEach((row) => {
    const cond = row.dataset.showIf;  // "switch" or "field=value"
    const [k, v] = cond.split("=");
    const on = v === undefined ? !!state.inputs[k] : String(state.inputs[k]) === v;
    row.hidden = !on;
    row.classList.toggle("sub", on);
  });
}

// One-click seismic zones of the selected National Annex (sets a_gR, γI = 1.0).
function zoneChips(input) {
  const na = (state.annexes || []).find((a) => a.code === (state.project.annex || "EN"));
  const box = el("div", { class: "chips" });
  if (!na?.zones?.length) return box;
  if (na.map) {
    box.append(el("button", { type: "button", class: "chip map", title: t("Project site — seismic zone from the map"),
      on: { click: () => openMap(input) } }, `📍 ${t("From map")}`));
  }
  for (const z of na.zones) {
    box.append(el("button", { type: "button", class: "chip", title: `a_gR = ${z.ag} g`,
      on: { click: () => { input.value = z.ag; state.inputs.ag = z.ag; markChips(box, z.ag); schedule(); } } },
      `${z.label} · ${z.ag} g`));
  }
  markChips(box, Number(state.inputs.ag));
  return box;
}
function markChips(box, ag) {
  box.querySelectorAll(".chip").forEach((c) => c.classList.toggle("on", c.title === `a_gR = ${ag} g`));
}

function clearInvalid() {
  document.querySelectorAll(".invalid").forEach((n) => n.classList.remove("invalid"));
}

function markInvalid(name) {
  clearInvalid();
  const row = document.querySelector(`.field[data-name="${name}"]`) || document.getElementById(`f-${name}`);
  if (!row) return;
  row.classList.add("invalid");
  row.scrollIntoView({ block: "center", behavior: "smooth" });
}


// Small pictograms for the home cards (stroke drawings, 96×48).
const PICS = {
  beam_analysis: '<path d="M10 22h76" stroke-width="4"/><path d="M14 24l-5 9h10z M48 24l-5 9h10z M82 24l-5 9h10z" fill="#2a6f97" stroke="none"/><path d="M20 10v8M30 10v8M40 10v8M56 10v8M66 10v8M76 10v8" stroke="#c47a2c"/>',
  ec2_rc_beam: '<rect x="34" y="6" width="28" height="36" rx="2" fill="#e3e4e6"/><rect x="38" y="10" width="20" height="28" rx="3" stroke="#8a5a2b"/><circle cx="41" cy="35" r="2.6" fill="#333" stroke="none"/><circle cx="48" cy="35" r="2.6" fill="#333" stroke="none"/><circle cx="55" cy="35" r="2.6" fill="#333" stroke="none"/><circle cx="42" cy="13" r="1.8" fill="#555" stroke="none"/><circle cx="54" cy="13" r="1.8" fill="#555" stroke="none"/>',
  ec3_steel_beam: '<path d="M30 8h36M30 40h36M48 8v32" stroke="#5a6b7d" stroke-width="5"/>',
  ec7_retaining_wall: '<path d="M2 42h92" stroke="#a08060"/><path d="M44 6h50v32H50z" fill="#e9d8b8" stroke="none"/><path d="M40 6h6l2 30H40z M20 36h52v6H20z" fill="#b4b8bf"/><path d="M60 12h-8M64 20h-12M68 28h-16" stroke="#c47a2c"/>',
  ec7_gravity_wall: '<path d="M2 42h92" stroke="#a08060"/><path d="M50 6h44v36H56z" fill="#e9d8b8" stroke="none"/><path d="M38 6h10l10 36H32z" fill="#b4b8bf"/>',
  ec7_pad_footing: '<path d="M2 26h92" stroke="#a08060"/><rect x="42" y="4" width="12" height="24" fill="#9aa0a8"/><rect x="24" y="28" width="48" height="10" fill="#b4b8bf"/><path d="M26 44h44" stroke="#2e9b5f" stroke-width="3"/><path d="M32 46v-5M48 46v-5M64 46v-5" stroke="#2e9b5f"/>',
  ec7_slope_stability: '<path d="M2 14h28l36 26h28v6H2z" fill="#e9d8b8" stroke="#8a6d3b"/><path d="M24 14q18 34 46 27" stroke="#e03b3b" stroke-width="3" fill="none"/><circle cx="58" cy="6" r="2.5" fill="#e03b3b" stroke="none"/>',
  ec7_berlin_wall: '<path d="M2 30h40" stroke="#a08060"/><path d="M46 4h48v42H46z" fill="#e9d8b8" stroke="none"/><path d="M42 4v42M48 4v42" stroke="#5a6b7d" stroke-width="3"/><path d="M42 8h6M42 13h6M42 18h6M42 23h6M42 28h6" stroke="#a0703c" stroke-width="2"/><path d="M48 12l30 10" stroke="#111"/><path d="M72 20l16 5" stroke="#9ca3af" stroke-width="5"/>',
  ec2_rc_column: '<rect x="40" y="4" width="16" height="40" fill="#b4b8bf"/><path d="M44 4v40M52 4v40" stroke="#8a5a2b"/><path d="M40 12h16M40 20h16M40 28h16M40 36h16" stroke="#555" stroke-width="1"/>',
  ec2_rc_slab: '<path d="M8 20l20-12h60l-20 12z" fill="#b4b8bf"/><path d="M8 20h60v6H8z M68 20l20-12v6l-20 12z" fill="#9aa0a8"/><path d="M16 26v16M60 26v16" stroke="#9aa0a8" stroke-width="5"/>',
  ec7_strip_footing: '<path d="M2 26h92" stroke="#a08060"/><rect x="20" y="4" width="10" height="24" fill="#9aa0a8"/><rect x="8" y="28" width="34" height="8" fill="#b4b8bf"/><rect x="66" y="4" width="10" height="24" fill="#9aa0a8"/><rect x="54" y="28" width="34" height="8" fill="#b4b8bf"/><path d="M42 31h12" stroke="#7d8794" stroke-width="5"/>',
  ec1_wind_snow: '<path d="M6 14h40q8 0 8-6M6 24h56q8 0 8 6M6 34h34" stroke="#2f8fd8"/><path d="M70 40l12-14 12 14z" fill="#e3e4e6"/><circle cx="78" cy="10" r="2" fill="#9ab"/><circle cx="88" cy="16" r="2" fill="#9ab"/>',
  ec8_lateral_force: '<path d="M30 44V8h26v36" stroke="#334"/><path d="M30 17h26M30 26h26M30 35h26" stroke="#334" stroke-width="1"/><path d="M58 11h16M58 20h12M58 29h8" stroke="#e03b3b" stroke-width="3"/><path d="M4 44q6-8 10 0t10 0" stroke="#e03b3b"/>',
  en1990_combinations: '<path d="M18 10h60M18 20h60M18 30h60M18 40h60" stroke="#8892a0" stroke-width="1"/><text x="20" y="27" font-size="16" fill="#2a6f97" stroke="none" font-family="sans-serif">γ·ψ</text>',
  ec7_pile: '<path d="M2 12h92" stroke="#a08060"/><path d="M2 30h92" stroke="#c9b48a" stroke-dasharray="3 3"/><rect x="42" y="4" width="12" height="40" fill="#b4b8bf"/><path d="M36 18h6M36 26h6M36 34h6M60 18h-6M60 26h-6M60 34h-6" stroke="#2e9b5f"/><path d="M48 48v-3" stroke="#2e9b5f" stroke-width="3"/>',
  ec7_settlement: '<rect x="36" y="6" width="24" height="6" fill="#b4b8bf"/><path d="M28 14q20 44 40 0" fill="#f0c428" fill-opacity="0.35" stroke="#e03b3b"/><path d="M38 14q10 22 20 0" fill="#e03b3b" fill-opacity="0.35" stroke="none"/><path d="M4 12h88" stroke="#a08060"/>',
  ec7_gabion_wall: '<path d="M2 42h92" stroke="#a08060"/><path d="M58 6h36v36H58z" fill="#e9d8b8" stroke="none"/><rect x="20" y="30" width="38" height="12" fill="#9c9486"/><rect x="30" y="18" width="28" height="12" fill="#9c9486"/><rect x="40" y="6" width="18" height="12" fill="#9c9486"/><path d="M20 36h38M30 24h28M40 12h18" stroke="#666" stroke-width="1"/>',
  ec7_embedded_wall: '<path d="M2 32h44" stroke="#a08060"/><path d="M50 4h44v42H50z" fill="#e9d8b8" stroke="none"/><rect x="44" y="4" width="6" height="42" fill="#b4b8bf"/><path d="M50 12l24 9M50 22l24 9" stroke="#333"/><path d="M74 21l12 4M74 31l12 4" stroke="#7d8794" stroke-width="4"/>',
  ec3_steel_column: '<path d="M38 4h20M38 44h20M48 4v40" stroke="#5a6b7d" stroke-width="5"/><path d="M28 2v8M68 2v8" stroke="#e03b3b" stroke-dasharray="2 2"/>',
  ec3_bolted_connection: '<rect x="10" y="14" width="50" height="20" fill="#5a6b7d"/><rect x="36" y="18" width="50" height="12" fill="#7d8794"/><circle cx="42" cy="24" r="3" fill="#222"/><circle cx="52" cy="24" r="3" fill="#222"/><path d="M60 24h20" stroke="#e03b3b"/>',
  ec3_base_plate: '<path d="M38 4h20M38 30h20M48 4v26" stroke="#5a6b7d" stroke-width="4"/><rect x="24" y="30" width="48" height="5" fill="#7d8794"/><rect x="16" y="35" width="64" height="11" fill="#b4b8bf"/><path d="M30 28v16M66 28v16" stroke="#222" stroke-width="2"/>',
  ec5_timber_beam: '<rect x="6" y="16" width="84" height="14" fill="#c8955a"/><path d="M6 21h84M6 25h84" stroke="#8a5a2b" stroke-width="1"/><path d="M10 30l-5 8h10zM86 30l-5 8h10z" fill="#9aa0a8" stroke="none"/>',
  ec6_masonry_wall: '<rect x="20" y="6" width="56" height="36" fill="#b5653e"/><path d="M20 15h56M20 24h56M20 33h56M34 6v9M58 6v9M46 15v9M70 15v9M34 24v9M58 24v9M46 33v9" stroke="#e6e0d6" stroke-width="1.2"/>',
  ec2_tank: '<path d="M14 8v34h68V8" stroke="#8a8f96" stroke-width="5" fill="none"/><rect x="17" y="16" width="62" height="24" fill="#2f8fd8" fill-opacity="0.45" stroke="none"/><path d="M17 16q8-3 16 0t16 0 16 0 14 0" stroke="#2f8fd8"/>',
  ec8_3_assessment: '<rect x="38" y="4" width="20" height="40" fill="#b4b8bf"/><path d="M42 12l6 6-4 4 6 6" stroke="#e03b3b" stroke-width="2" fill="none"/><rect x="33" y="4" width="30" height="40" fill="none" stroke="#2e9b5f" stroke-width="2" stroke-dasharray="4 2"/>',
};
const pic = (id) => `<svg viewBox="0 0 96 48" fill="none" stroke="#334" stroke-width="2" stroke-linejoin="round">${PICS[id] || '<rect x="30" y="8" width="36" height="32" rx="4"/>'}</svg>`;

function renderHome() {
  const box = $("#home-cards");
  box.innerHTML = "";
  const q = $("#home-search").value.trim().toLowerCase();
  const last = store.get("erisma.last", "");
  const cats = {};
  state.modules.filter((m) => !q || `${m.title} ${m.standard} ${m.category} ${m.description}`.toLowerCase().includes(q))
    .forEach((m) => (cats[m.category] ||= []).push(m));
  const ordered = Object.entries(cats).sort((a, b) => b[1].length - a[1].length);
  for (const [cat, mods] of ordered) {
    box.append(el("div", { class: "cat-title" }, cat));
    const grid = el("div", { class: "cards" });
    for (const m of mods) {
      const card = el("button", { class: `card${m.id === last ? " last" : ""}`, type: "button", title: m.description,
        on: { click: () => openModule(m.id) } });
      card.innerHTML = `<div class="pic">${pic(m.id)}</div>`;
      card.append(el("div", { class: "ttl" }, m.title), el("div", { class: "std" }, m.standard),
        el("div", { class: "dsc" }, m.description),
        el("div", { class: "badges" }, m.has_3d ? el("span", { class: "badge3d" }, "3D") : "",
          m.id === last ? el("span", { class: "std" }, `· ${t("last used")}`) : ""));
      grid.append(card);
    }
    box.append(grid);
  }
  if (!Object.keys(cats).length) box.append(el("p", { class: "empty" }, t("No calculations match")));
  const lm = state.modules.find((m) => m.id === last);
  const cont = $("#home-continue");
  cont.hidden = !lm;
  if (lm) { cont.textContent = `${t("Continue")}: ${lm.title} →`; cont.onclick = () => openModule(lm.id); }
}

function showHome() {
  document.body.classList.add("at-home");
  document.title = "Erisma";
  renderHome();
  setTimeout(() => $("#home-search").focus(), 50);
}

let pendingInputs = null;
function openModule(id, inputs) {
  pendingInputs = inputs ?? null;
  if (location.hash.slice(1) === id) route();
  else location.hash = id;
}

function route() {
  const id = location.hash.slice(1);
  if (state.modules.some((m) => m.id === id)) {
    document.body.classList.remove("at-home");
    const inp = pendingInputs;
    pendingInputs = null;
    selectModule(id, inp ?? undefined);
  } else {
    showHome();
  }
}

async function selectModule(id, inputs) {
  state.schema = await api(`/api/modules/${id}`);
  const saved = store.get(inputsKey(id), null);
  state.inputs = inputs ? structuredClone(inputs) : saved ? saved : {};
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.id === id));
  $("#mod-title").textContent = state.schema.title;
  $("#mod-desc").textContent = `${state.schema.standard} — ${state.schema.description}`;
  $("#restored").hidden = !(saved && !inputs);
  document.title = `${state.schema.title} — Erisma`;
  store.set("erisma.last", id);
  pushRecent(id);
  renderNav();
  renderForm();
  resetHistory();
  run();
}

// ------------------------------------------------------------------ tabs
let currentTab = "report";
function showTab(name) {
  if (name === "model" && $("#tab-model").hidden) return;
  currentTab = name;
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".pane").forEach((p) => p.classList.toggle("on", p.dataset.pane === name));
  if (name === "model") window.dispatchEvent(new Event("erisma:show3d"));
}
document.querySelectorAll(".tabs button").forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));

// ------------------------------------------------------------------- run
let timer;
function schedule() {
  clearTimeout(timer);
  $("#status").classList.add("busy");
  timer = setTimeout(run, 300);
}

let runId = 0;
async function run() {
  const status = $("#status");
  const my = ++runId;
  store.set(inputsKey(state.schema.id), state.inputs);
  try {
    const res = await api(`/api/modules/${state.schema.id}/run`, { inputs: state.inputs, project: state.project });
    if (my !== runId) return; // a newer run is in flight
    clearInvalid();
    state.lastHtml = res.html;
    state.lastSummary = res.summary;
    const frame = $("#report");
    const scroll = frame.contentWindow?.scrollY || 0;
    frame.onload = () => frame.contentWindow.scrollTo(0, scroll);
    frame.srcdoc = res.html;
    const has3d = !!res.model3d;
    $("#tab-model").hidden = !has3d;
    if (!has3d && currentTab === "model") showTab("report");
    if (has3d) {
      window.__erismaModel = { model: res.model3d, summary: res.summary };
      window.dispatchEvent(new CustomEvent("erisma:model3d", { detail: window.__erismaModel }));
    }
    renderStatus(res.summary);
  } catch (err) {
    if (my !== runId) return;
    status.className = "err";
    status.textContent = `⚠ ${err.message}`;
    if (err.field) markInvalid(err.field);
  }
}

function renderStatus(s) {
  const status = $("#status");
  status.innerHTML = "";
  if (!s.checks.length) {
    status.className = "pass";
    status.textContent = `✔ ${t("Analysis complete")}`;
    return;
  }
  status.className = s.passed ? "pass" : "fail";
  const u = Math.min(s.max_utilisation, 9.99).toFixed(3);
  status.append(el("div", { class: "head" }, `${s.passed ? "✔ " + t("All checks pass") : "✖ " + t("Design fails")} — ${t("max utilisation")} ${u}`),
    el("div", { class: "ubar" }, el("i", { style: `width:${Math.min(s.max_utilisation, 1.2) / 1.2 * 100}%` })));
  const failing = s.checks.filter((c) => !c.passed);
  if (failing.length) {
    const seen = new Set();
    const list = el("ul", { class: "fails" });
    for (const c of failing.sort((a, b) => b.utilisation - a.utilisation)) {
      const key = c.description;
      if (seen.has(key)) continue;
      seen.add(key);
      list.append(el("li", {}, el("b", {}, `${c.description} — U = ${Math.min(c.utilisation, 9.99).toFixed(2)}`),
        c.hint ? el("div", { class: "hint" }, `💡 ${c.hint}`) : ""));
    }
    status.append(el("details", { open: "" }, el("summary", {}, `${failing.length} ${t("failing check(s) — what to change")}`), list));
  }
}

// ------------------------------------------------------------ site map
const mapState = { pick: null, input: null, places: [] };
async function openMap(input) {
  const na = (state.annexes || []).find((a) => a.code === (state.project.annex || "EN"));
  if (!na?.map) return;
  mapState.input = input || null;
  const img = $("#map-img");
  if (!img.src.endsWith(na.map)) img.src = na.map;
  if (!mapState.places.length) mapState.places = await api(`/api/site/places?annex=${na.code}`).catch(() => []);
  $("#map-search").value = "";
  renderPlaces();
  const p = state.project;
  if (p.lat && p.lon) await pickSite({ lat: p.lat, lon: p.lon, name: p.site }); else showPick(null);
  $("#map-dlg").showModal();
}
function renderPlaces() {
  const q = $("#map-search").value.trim().toLowerCase();
  const box = $("#map-places");
  box.innerHTML = "";
  mapState.places.filter((p) => !q || `${p.name_el} ${p.name_en}`.toLowerCase().includes(q)).forEach((p) => {
    const name = LANG === "el" ? p.name_el : p.name_en;
    box.append(el("button", { class: "place", type: "button", on: { click: () => pickSite({ lat: p.lat, lon: p.lon, name }) } },
      el("span", {}, name), el("span", { class: `zb z${p.zone}` }, `${t("Zone")} ${p.zone}`)));
  });
}
async function pickSite(q) {
  const na = state.project.annex || "EN";
  const qs = q.x !== undefined ? `x=${q.x}&y=${q.y}` : `lat=${q.lat}&lon=${q.lon}`;
  const r = await api(`/api/site/zone?annex=${na}&${qs}`).catch(() => null);
  if (!r) return;
  r.name = q.name || (q.x !== undefined ? t("Selected point") : q.name) || t("Selected point");
  showPick(r);
}
function showPick(r) {
  mapState.pick = r;
  const pin = $("#map-pin"), res = $("#map-result"), apply = $("#map-apply");
  $("#map-lat").value = r ? r.lat : "";
  $("#map-lon").value = r ? r.lon : "";
  if (!r) { pin.style.display = "none"; res.textContent = t("Click on the map, choose a place or give coordinates."); apply.disabled = true; return; }
  const img = $("#map-img");
  pin.style.display = "block";
  pin.style.left = `${img.offsetLeft + (r.x / r.width) * img.clientWidth}px`;
  pin.style.top = `${img.offsetTop + (r.y / r.height) * img.clientHeight}px`;
  if (!r.zone) { res.innerHTML = ""; res.append(t("Outside the zonation map")); apply.disabled = true; return; }
  res.innerHTML = "";
  res.append(`${r.name}: ${t("Zone")} ${r.zone} · a_gR = ${r.ag} g`,
    el("small", {}, r.near_boundary ? t("Near a zone boundary — the higher zone within 1 km is used (safe side).")
      : `${r.lat.toFixed(4)}°N, ${r.lon.toFixed(4)}°E · ${t("NA to CYS EN 1998-1, zonation map")}`));
  apply.disabled = false;
}
$("#map-img").addEventListener("click", (e) => {
  const img = e.currentTarget, rect = img.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width) * img.naturalWidth;
  const y = ((e.clientY - rect.top) / rect.height) * img.naturalHeight;
  pickSite({ x: x.toFixed(1), y: y.toFixed(1) });
});
$("#map-img").addEventListener("load", () => mapState.pick && showPick(mapState.pick));
window.addEventListener("resize", () => mapState.pick && $("#map-dlg").open && showPick(mapState.pick));
$("#map-search").addEventListener("input", renderPlaces);
for (const id of ["#map-lat", "#map-lon"]) {
  $(id).addEventListener("change", () => {
    const lat = Number($("#map-lat").value), lon = Number($("#map-lon").value);
    if (lat && lon) pickSite({ lat, lon, name: t("Coordinates") });
  });
}
$("#map-gps").onclick = () => {
  if (!navigator.geolocation) return alert(t("Location is not available in this browser."));
  navigator.geolocation.getCurrentPosition((p) => pickSite({ lat: p.coords.latitude, lon: p.coords.longitude, name: t("My location") }),
    () => alert(t("Location is not available in this browser.")), { enableHighAccuracy: true, timeout: 10000 });
};
const closeMap = () => $("#map-dlg").close();
$("#map-close").onclick = closeMap;
$("#map-cancel").onclick = closeMap;
$("#map-apply").onclick = () => {
  const r = mapState.pick;
  if (!r?.zone) return;
  Object.assign(state.project, { site: r.name, lat: String(r.lat), lon: String(r.lon), zone: r.zone, ag: r.ag });
  store.set("erisma.project", state.project);
  if (state.schema?.fields.some((f) => f.name === "ag")) {
    state.inputs.ag = r.ag;
    const inp = document.getElementById("f-ag");
    if (inp) inp.value = r.ag;
  }
  closeMap();
  renderProject();
  if (state.schema) renderForm();
  schedule();
};

// --------------------------------------------------------------- actions
function download(name, text, type) {
  const a = el("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name });
  document.body.append(a); a.click(); a.remove();
}
const fileBase = () => (state.project.job_no || "calc").replace(/[^\w.-]+/g, "_") + "_" + state.schema.id;
const actions = {
  print: () => $("#report").contentWindow.print(),
  html: () => download(`${fileBase()}.html`, state.lastHtml, "text/html"),
  save: () => download(`${fileBase()}.erisma`, JSON.stringify({
    format: "erisma", version: 1, module: state.schema.id, project: state.project, inputs: state.inputs,
  }, null, 2), "application/json"),
  open: () => $("#file-open").click(),
  reset: () => { store.del(inputsKey(state.schema.id)); selectModule(state.schema.id, {}); },
};
$("#btn-print").onclick = actions.print;
$("#btn-html").onclick = actions.html;
$("#btn-save").onclick = actions.save;
$("#btn-open").onclick = actions.open;
$("#btn-reset").onclick = actions.reset;
$("#file-open").onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const doc = JSON.parse(await file.text());
    if (doc.format !== "erisma" && doc.format !== "blackeye") throw new Error(t("Not an Erisma project file"));
    state.project = doc.project || {};
    store.set("erisma.project", state.project);
    renderProject();
    openModule(doc.module, doc.inputs);
  } catch (err) { alert(err.message); }
  e.target.value = "";
};
document.addEventListener("keydown", (e) => {
  if (!(e.ctrlKey || e.metaKey)) return;
  const k = e.key.toLowerCase();
  if ((k === "z" || k === "y") && state.schema && !document.body.classList.contains("at-home")) {
    e.preventDefault(); undo(k === "y" || e.shiftKey ? 1 : -1); return;
  }
  const map = { s: actions.save, o: actions.open, p: actions.print, 3: () => showTab(currentTab === "model" ? "report" : "model"),
    k: () => { const box = document.body.classList.contains("at-home") ? $("#home-search") : $("#search"); setSide(false); box.focus(); box.select(); } };
  if (map[k]) { e.preventDefault(); map[k](); }
});
$("#search").addEventListener("input", renderNav);
document.querySelectorAll(".lang button").forEach((b) => (b.onclick = async () => {
  LANG = b.dataset.lang;
  try { localStorage.setItem("erisma.lang", LANG); } catch { /* ignore */ }
  translateChrome();
  state.annexes = await api("/api/annexes").catch(() => []);
  renderProject();
  state.modules = await api("/api/modules");
  renderNav();
  if (document.body.classList.contains("at-home")) renderHome();
  else selectModule(state.schema.id, state.inputs);
}));

$("#btn-theme").onclick = () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
$("#side-toggle").onclick = () => setSide(!document.body.classList.contains("side-collapsed"));

(async function init() {
  setTheme(document.documentElement.dataset.theme || "dark");
  setSide(document.documentElement.classList.contains("pre-collapsed"));
  state.project = store.get("erisma.project", {});
  translateChrome();
  state.annexes = await api("/api/annexes").catch(() => []);
  renderProject();
  state.modules = await api("/api/modules");
  renderNav();
  window.addEventListener("hashchange", route);
  $("#home-search").addEventListener("input", renderHome);
  $("#home-search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { const first = $("#home-cards .card"); if (first) first.click(); }
  });
  $("#home-open").onclick = actions.open;
  const home = (e) => { e.preventDefault(); location.hash = "home"; };
  $("#go-home").onclick = home;
  $("#btn-home").onclick = home;
  route();
})();
