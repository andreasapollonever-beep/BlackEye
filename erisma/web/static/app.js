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
      on: { click: (e) => { e.preventDefault(); selectModule(m.id); } },
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
      const input = scalarInput(f, state.inputs[f.name], (v) => { state.inputs[f.name] = v; clearInvalid(); schedule(); });
      input.id = id;
      const row = el("div", { class: "field", "data-name": f.name }, el("label", { for: id }, f.label),
        el("div", { class: "inp" }, input, el("span", {}, f.unit || "")));
      if (f.help) row.append(el("div", { class: "help" }, f.help));
      fs.append(row);
    }
    form.append(fs);
  }
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

async function selectModule(id, inputs) {
  state.schema = await api(`/api/modules/${id}`);
  const saved = store.get(inputsKey(id), null);
  state.inputs = inputs ? structuredClone(inputs) : saved ? saved : {};
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.id === id));
  $("#mod-title").textContent = state.schema.title;
  $("#mod-desc").textContent = `${state.schema.standard} — ${state.schema.description}`;
  $("#restored").hidden = !(saved && !inputs);
  history.replaceState(null, "", `#${id}`);
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
    await selectModule(doc.module, doc.inputs);
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
  selectModule(state.schema.id, state.inputs);
}));

(async function init() {
  state.project = store.get("erisma.project", {});
  translateChrome();
  renderProject();
  state.modules = await api("/api/modules");
  renderNav();
  const wanted = location.hash.slice(1) || store.get("erisma.last", "");
  selectModule(state.modules.some((m) => m.id === wanted) ? wanted : state.modules[0].id);
})();
