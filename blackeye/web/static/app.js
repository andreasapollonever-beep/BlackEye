"use strict";
// BlackEye web client: schema-driven input forms with live calculation preview.

const PROJECT_FIELDS = [
  ["company", "Company"], ["project", "Project"], ["job_no", "Job no."],
  ["client", "Client"], ["section", "Element"], ["calc_by", "Calc. by"],
  ["checked_by", "Checked by"], ["date", "Date"],
];

const state = { modules: [], schema: null, inputs: {}, project: {}, lastHtml: "" };
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

function loadPrefs() {
  try { return JSON.parse(localStorage.getItem("blackeye.project") || "{}"); } catch { return {}; }
}
function savePrefs() {
  try { localStorage.setItem("blackeye.project", JSON.stringify(state.project)); } catch { /* ignore */ }
}

async function api(path, body) {
  const res = await fetch(path, body ? {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  } : undefined);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function renderNav() {
  const nav = $("#modules");
  nav.innerHTML = "";
  const cats = {};
  state.modules.forEach((m) => (cats[m.category] ||= []).push(m));
  for (const [cat, mods] of Object.entries(cats)) {
    nav.append(el("h3", {}, cat));
    mods.forEach((m) => nav.append(el("a", {
      href: `#${m.id}`, "data-id": m.id,
      on: { click: (e) => { e.preventDefault(); selectModule(m.id); } },
    }, m.title, el("small", {}, m.standard))));
  }
}

function renderProject() {
  const box = $("#project-fields");
  box.innerHTML = "";
  if (!state.project.date) state.project.date = new Date().toISOString().slice(0, 10);
  for (const [key, label] of PROJECT_FIELDS) {
    const input = el("input", { value: state.project[key] || "", type: key === "date" ? "date" : "text",
      on: { input: (e) => { state.project[key] = e.target.value; savePrefs(); schedule(); } } });
    box.append(el("div", {}, el("label", {}, label), input));
  }
}

function scalarInput(f, value, onChange) {
  if (f.kind === "choice") {
    const s = el("select", { on: { change: (e) => onChange(e.target.value) } },
      ...f.choices.map((c) => el("option", { value: c }, c)));
    s.value = value ?? f.default;
    return s;
  }
  if (f.kind === "bool") {
    const c = el("input", { type: "checkbox", on: { change: (e) => onChange(e.target.checked) } });
    c.checked = !!(value ?? f.default);
    return c;
  }
  return el("input", { type: "number", step: "any", value: value ?? f.default ?? "",
    min: f.min ?? undefined, max: f.max ?? undefined,
    on: { input: (e) => onChange(e.target.value === "" ? null : Number(e.target.value)) } });
}

function tableEditor(f) {
  const rows = state.inputs[f.name] ||= structuredClone(f.default || []);
  const wrap = el("div", { class: "tblwrap" });
  const draw = () => {
    wrap.innerHTML = "";
    const head = el("tr", {}, ...f.columns.map((c) => el("th", {}, c.label + (c.unit ? ` [${c.unit}]` : ""))), el("th"));
    const body = rows.map((r, i) => el("tr", {},
      ...f.columns.map((c) => el("td", {}, scalarInput(c, r[c.name], (v) => { r[c.name] = v; schedule(); }))),
      el("td", {}, el("button", { type: "button", class: "tbl-del", title: "Remove row",
        on: { click: () => { rows.splice(i, 1); draw(); schedule(); } } }, "×"))));
    wrap.append(el("table", { class: "tbl" }, el("thead", {}, head), el("tbody", {}, ...body)),
      el("button", { type: "button", class: "tbl-add", on: { click: () => {
        rows.push(Object.fromEntries(f.columns.map((c) => [c.name, c.default])));
        draw(); schedule();
      } } }, "+ Add row"));
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
      const input = scalarInput(f, state.inputs[f.name], (v) => { state.inputs[f.name] = v; schedule(); });
      input.id = id;
      const row = el("div", { class: "field" }, el("label", { for: id }, f.label),
        el("div", { class: "inp" }, input, el("span", {}, f.unit || "")));
      if (f.help) row.append(el("div", { class: "help" }, f.help));
      fs.append(row);
    }
    form.append(fs);
  }
}

async function selectModule(id, inputs) {
  state.schema = await api(`/api/modules/${id}`);
  state.inputs = inputs ? structuredClone(inputs) : {};
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("active", a.dataset.id === id));
  $("#mod-title").textContent = state.schema.title;
  $("#mod-desc").textContent = `${state.schema.standard} — ${state.schema.description}`;
  history.replaceState(null, "", `#${id}`);
  renderForm();
  run();
}

let timer;
function schedule() { clearTimeout(timer); timer = setTimeout(run, 300); }

async function run() {
  const status = $("#status");
  try {
    const res = await api(`/api/modules/${state.schema.id}/run`, { inputs: state.inputs, project: state.project });
    state.lastHtml = res.html;
    $("#report").srcdoc = res.html;
    const s = res.summary;
    if (!s.checks.length) { status.className = "pass"; status.textContent = "Analysis complete"; }
    else {
      status.className = s.passed ? "pass" : "fail";
      status.textContent = `${s.passed ? "✔ All checks pass" : "✖ Design fails"} — max utilisation ${s.max_utilisation.toFixed(3)}`;
    }
  } catch (err) {
    status.className = "err";
    status.textContent = `⚠ ${err.message}`;
  }
}

function download(name, text, type) {
  const a = el("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name });
  document.body.append(a); a.click(); a.remove();
}
const fileBase = () => (state.project.job_no || "calc").replace(/[^\w.-]+/g, "_") + "_" + state.schema.id;

$("#btn-print").onclick = () => $("#report").contentWindow.print();
$("#btn-html").onclick = () => download(`${fileBase()}.html`, state.lastHtml, "text/html");
$("#btn-save").onclick = () => download(`${fileBase()}.bkeye`, JSON.stringify({
  format: "blackeye", version: 1, module: state.schema.id, project: state.project, inputs: state.inputs,
}, null, 2), "application/json");
$("#btn-open").onclick = () => $("#file-open").click();
$("#file-open").onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const doc = JSON.parse(await file.text());
    if (doc.format !== "blackeye") throw new Error("Not a BlackEye project file");
    state.project = doc.project || {};
    renderProject();
    await selectModule(doc.module, doc.inputs);
  } catch (err) { alert(err.message); }
  e.target.value = "";
};

(async function init() {
  state.project = loadPrefs();
  renderProject();
  state.modules = await api("/api/modules");
  renderNav();
  const wanted = location.hash.slice(1);
  selectModule(state.modules.some((m) => m.id === wanted) ? wanted : state.modules[0].id);
})();
