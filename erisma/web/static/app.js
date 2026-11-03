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
    "Shortcuts: Ctrl+S save · Ctrl+O open · Ctrl+P print · Ctrl+3 3D view": "Συντομεύσεις: Ctrl+S αποθήκευση · Ctrl+O άνοιγμα · Ctrl+P εκτύπωση · Ctrl+3 3D",
    "No calculations match": "Δεν βρέθηκαν υπολογισμοί",
    "Home": "Αρχική", "Welcome to Erisma": "Καλώς ήρθατε στο Erisma",
    "Choose a calculation to start. Results, checks and the report update while you type.":
      "Επιλέξτε έναν υπολογισμό για να ξεκινήσετε. Τα αποτελέσματα, οι έλεγχοι και το τεύχος ενημερώνονται καθώς γράφετε.",
    "Open project file…": "Άνοιγμα αρχείου έργου…", "Continue": "Συνέχεια",
    "Choose a calculation": "Επιλέξτε υπολογισμό",
    "Enter your data — the defaults are a realistic worked example": "Συμπληρώστε τα δεδομένα σας — οι προεπιλογές είναι ένα ρεαλιστικό παράδειγμα",
    "Check the results and print the report (PDF)": "Δείτε τα αποτελέσματα και εκτυπώστε το τεύχος (PDF)",
    "last used": "τελευταίος",
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
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === LANG));
  $("#shortcuts").textContent = t("Shortcuts: Ctrl+S save · Ctrl+O open · Ctrl+P print · Ctrl+3 3D view");
}

function renderNav() {
  const nav = $("#modules");
  nav.innerHTML = "";
  const q = $("#search").value.trim().toLowerCase();
  const cats = {};
  state.modules.filter((m) => !q || `${m.title} ${m.standard} ${m.category} ${m.description}`.toLowerCase().includes(q))
    .forEach((m) => (cats[m.category] ||= []).push(m));
  for (const [cat, mods] of Object.entries(cats)) {
    nav.append(el("h3", {}, cat));
    mods.forEach((m) => nav.append(el("a", {
      href: `#${m.id}`, "data-id": m.id, class: state.schema?.id === m.id ? "active" : null, title: m.description,
      on: { click: (e) => { e.preventDefault(); openModule(m.id); } },
    }, m.title, el("small", {}, m.standard))));
  }
  if (!Object.keys(cats).length) nav.append(el("p", { class: "muted pad" }, t("No calculations match")));
}

function renderProject() {
  const box = $("#project-fields");
  box.innerHTML = "";
  if (!state.project.date) state.project.date = new Date().toISOString().slice(0, 10);
  for (const [key, label] of PROJECT_FIELDS) {
    const id = `p-${key}`;
    const input = el("input", { id, value: state.project[key] || "", type: key === "date" ? "date" : "text",
      on: { input: (e) => { state.project[key] = e.target.value; store.set("erisma.project", state.project); schedule(); } } });
    box.append(el("div", {}, el("label", { for: id }, t(label)), input));
  }
}

// ------------------------------------------------------------------ form
function scalarInput(f, value, onChange) {
  if (f.kind === "choice") {
    const labels = f.choice_labels || f.choices;
    const s = el("select", { on: { change: (e) => onChange(e.target.value) } },
      ...f.choices.map((c, i) => el("option", { value: c }, labels[i])));
    s.value = value ?? f.default;
    return s;
  }
  if (f.kind === "bool") {
    const c = el("input", { type: "checkbox", class: "chk", on: { change: (e) => onChange(e.target.checked) } });
    c.checked = !!(value ?? f.default);
    return c;
  }
  return el("input", { type: "number", step: "any", inputmode: "decimal", value: value ?? f.default ?? "",
    min: f.min ?? undefined, max: f.max ?? undefined,
    on: { input: (e) => onChange(e.target.value === "" ? null : Number(e.target.value)) } });
}

function tableEditor(f) {
  const rows = state.inputs[f.name] ||= structuredClone(f.default || []);
  const wrap = el("div", { class: "tblwrap", id: `f-${f.name}` });
  const draw = () => {
    wrap.innerHTML = "";
    const head = el("tr", {}, ...f.columns.map((c) => el("th", {}, c.label + (c.unit ? ` [${c.unit}]` : ""))), el("th"));
    const body = rows.map((r, i) => el("tr", {},
      ...f.columns.map((c) => el("td", {}, scalarInput(c, r[c.name], (v) => { r[c.name] = v; schedule(); }))),
      el("td", {}, el("button", { type: "button", class: "tbl-del", title: t("Remove row"),
        on: { click: () => { rows.splice(i, 1); draw(); schedule(); } } }, "×"))));
    wrap.append(el("div", { class: "tbl-title" }, f.label),
      el("table", { class: "tbl" }, el("thead", {}, head), el("tbody", {}, ...body)),
      el("button", { type: "button", class: "tbl-add", on: { click: () => {
        rows.push(Object.fromEntries(f.columns.map((c) => [c.name, c.default])));
        draw(); schedule();
      } } }, t("+ Add row")));
  };
  draw();
  return wrap;
}

function renderForm() {
  const form = $("#inputs");
  form.innerHTML = "";
  const groups = {};
  state.schema.fields.forEach((f) => (groups[f.group] ||= []).push(f));
  for (const [g, fields] of Object.entries(groups)) {
    const fs = el("fieldset", {}, el("legend", {}, g));
    for (const f of fields) {
      if (f.kind === "table") { fs.append(tableEditor(f)); continue; }
      if (!(f.name in state.inputs)) state.inputs[f.name] = f.default;
      const id = `f-${f.name}`;
      const input = scalarInput(f, state.inputs[f.name], (v) => {
        state.inputs[f.name] = v; clearInvalid(); if (f.kind === "bool") updateVisibility(); schedule();
      });
      input.id = id;
      const row = el("div", { class: "field", "data-name": f.name, "data-show-if": f.show_if || null }, el("label", { for: id }, f.label),
        el("div", { class: "inp" }, input, el("span", {}, f.unit || "")));
      if (f.help) row.append(el("div", { class: "help" }, f.help));
      fs.append(row);
    }
    form.append(fs);
  }
  updateVisibility();
}

// Fields with show_if appear only when their switch is on (keeps the form short).
function updateVisibility() {
  document.querySelectorAll("#inputs [data-show-if]").forEach((row) => {
    const on = !!state.inputs[row.dataset.showIf];
    row.hidden = !on;
    row.classList.toggle("sub", on);
  });
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
  renderForm();
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
  const map = { s: actions.save, o: actions.open, p: actions.print, 3: () => showTab(currentTab === "model" ? "report" : "model") };
  if (map[k]) { e.preventDefault(); map[k](); }
});
$("#search").addEventListener("input", renderNav);
document.querySelectorAll(".lang button").forEach((b) => (b.onclick = async () => {
  LANG = b.dataset.lang;
  try { localStorage.setItem("erisma.lang", LANG); } catch { /* ignore */ }
  translateChrome();
  renderProject();
  state.modules = await api("/api/modules");
  renderNav();
  if (document.body.classList.contains("at-home")) renderHome();
  else selectModule(state.schema.id, state.inputs);
}));

(async function init() {
  state.project = store.get("erisma.project", {});
  translateChrome();
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
