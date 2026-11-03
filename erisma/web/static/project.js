"use strict";
// Erisma projects: several calculations in one project, links between them (chain) and one
// combined report.  Loaded after app.js and uses its globals (state, el, t, api, store …).

const PUI = {
  el: {
    "Project": "Έργο", "Add this calculation to the project": "Προσθήκη αυτού του υπολογισμού στο έργο",
    "+ Add to project": "+ Στο έργο", "Project report": "Τεύχος έργου", "New project": "Νέο έργο",
    "Start a new, empty project? Unsaved changes are lost.": "Νέο, κενό έργο; Οι μη αποθηκευμένες αλλαγές χάνονται.",
    "Name of this element (e.g. Footing F1)": "Όνομα στοιχείου (π.χ. Πέδιλο Π1)",
    "Rename": "Μετονομασία", "Remove from project": "Αφαίρεση από το έργο", "Move up": "Μετακίνηση πάνω",
    "Remove this calculation from the project?": "Αφαίρεση του υπολογισμού από το έργο;",
    "Link to a result of another calculation": "Σύνδεση με αποτέλεσμα άλλου υπολογισμού",
    "Linked": "Συνδεδεμένο", "from": "από", "Remove link": "Κατάργηση σύνδεσης",
    "Link value": "Σύνδεση τιμής", "Source calculation": "Υπολογισμός προέλευσης", "Result": "Αποτέλεσμα",
    "Factor": "Συντελεστής", "Use absolute value": "Απόλυτη τιμή", "Link": "Σύνδεση", "Cancel": "Άκυρο",
    "No compatible results (same kind of unit) in the other calculations of the project.":
      "Δεν υπάρχουν συμβατά αποτελέσματα (ίδιο είδος μονάδας) στους άλλους υπολογισμούς του έργου.",
    "Add at least two calculations to the project to link them.": "Προσθέστε τουλάχιστον δύο υπολογισμούς στο έργο για να τους συνδέσετε.",
    "Link broken — the source result is missing or has another unit": "Η σύνδεση δεν ισχύει — το αποτέλεσμα λείπει ή έχει άλλη μονάδα",
    "e.g. 1/1.35 to turn a design value into a characteristic one": "π.χ. 1/1,35 για μετατροπή τιμής σχεδιασμού σε χαρακτηριστική",
    "Company logo": "Λογότυπο εταιρείας", "Remove logo": "Αφαίρεση λογοτύπου",
    "The project is empty — open a calculation and press “+ Add to project”.":
      "Το έργο είναι κενό — ανοίξτε έναν υπολογισμό και πατήστε «+ Στο έργο».",
    "Circular links": "Κυκλικές συνδέσεις", "Compare": "Σύγκριση",
  },
};
const pt = (k) => (LANG !== "en" && PUI[LANG]?.[k]) || t(k);

const Proj = {
  ws: store.get("erisma.workspace", { calcs: [] }),
  status: {},           // uid -> {passed, util, error}
  outputs: {},          // uid -> outputs (display units)
  dims: null,
  save() { store.set("erisma.workspace", this.ws); },
  item(uid) { return this.ws.calcs.find((c) => c.uid === uid); },
  current() { return state.uid ? this.item(state.uid) : null; },
  doc() { return { format: "erisma", version: 2, project: state.project, calcs: this.ws.calcs }; },

  add() {
    const name = prompt(pt("Name of this element (e.g. Footing F1)"),
      `${state.schema.title} ${this.ws.calcs.filter((c) => c.module === state.schema.id).length + 1}`);
    if (name === null) return;
    const uid = `c${Date.now().toString(36)}`;
    this.ws.calcs.push({ uid, module: state.schema.id, name, inputs: structuredClone(state.inputs), links: {} });
    this.save();
    location.hash = `p/${uid}`;
  },
  remove(uid) {
    if (!confirm(pt("Remove this calculation from the project?"))) return;
    this.ws.calcs = this.ws.calcs.filter((c) => c.uid !== uid);
    this.ws.calcs.forEach((c) => Object.entries(c.links || {}).forEach(([k, l]) => { if (l.from === uid) delete c.links[k]; }));
    this.save();
    if (state.uid === uid) { state.uid = null; location.hash = state.schema?.id || "home"; }
    renderNav();
  },
  rename(uid) {
    const c = this.item(uid);
    const n = prompt(pt("Rename"), c.name);
    if (n) { c.name = n; this.save(); renderNav(); if (state.uid === uid) $("#mod-title").textContent = `${n} — ${state.schema.title}`; }
  },
  move(uid) {
    const i = this.ws.calcs.findIndex((c) => c.uid === uid);
    if (i > 0) { const [c] = this.ws.calcs.splice(i, 1); this.ws.calcs.splice(i - 1, 0, c); this.save(); renderNav(); }
  },
  newProject() {
    if (this.ws.calcs.length && !confirm(pt("Start a new, empty project? Unsaved changes are lost."))) return;
    this.ws = { calcs: [] }; this.status = {}; this.save(); state.uid = null; renderNav();
  },

  // -------------------------------------------------------------- sidebar
  navSection() {
    const sec = el("div", { class: "sec proj" });
    const head = el("div", { class: "proj-h" }, el("span", {}, `📁 ${pt("Project")}`),
      el("span", { class: "proj-btns" },
        el("button", { type: "button", class: "mini", title: pt("Project report"), on: { click: () => this.report() } }, "📄"),
        el("button", { type: "button", class: "mini", title: pt("Compare"), on: { click: () => this.compare() } }, "⚖"),
        el("button", { type: "button", class: "mini", title: pt("New project"), on: { click: () => this.newProject() } }, "✚")));
    sec.append(head);
    if (!this.ws.calcs.length) sec.append(el("p", { class: "muted pad small" }, pt("The project is empty — open a calculation and press “+ Add to project”.")));
    for (const c of this.ws.calcs) {
      const m = state.modules.find((x) => x.id === c.module);
      const st = this.status[c.uid];
      const dot = el("span", { class: `pdot ${st ? (st.error ? "err" : st.passed ? "ok" : "ko") : ""}`,
        title: st ? (st.error || `U = ${st.util?.toFixed(2)}`) : "" });
      const links = Object.keys(c.links || {}).length;
      const a = el("a", { href: `#p/${c.uid}`, class: `item pitem${state.uid === c.uid ? " active" : ""}`,
        on: { click: (e) => { e.preventDefault(); location.hash = `p/${c.uid}`; } } },
        dot, el("span", { class: "t" }, c.name, el("span", { class: "s" }, `${m?.title || c.module}${links ? ` · 🔗${links}` : ""}`)),
        el("span", { class: "meta" },
          el("button", { type: "button", class: "star", title: pt("Move up"), on: { click: (e) => { e.preventDefault(); e.stopPropagation(); this.move(c.uid); } } }, "↑"),
          el("button", { type: "button", class: "star", title: pt("Rename"), on: { click: (e) => { e.preventDefault(); e.stopPropagation(); this.rename(c.uid); } } }, "✎"),
          el("button", { type: "button", class: "star", title: pt("Remove from project"), on: { click: (e) => { e.preventDefault(); e.stopPropagation(); this.remove(c.uid); } } }, "×")));
      sec.append(a);
    }
    return sec;
  },

  // ------------------------------------------------------------ head button
  headButton() {
    const box = $("#proj-add");
    if (!box) return;
    box.innerHTML = "";
    if (!state.schema) return;
    if (state.uid) return;
    box.append(el("button", { type: "button", class: "ghost", title: pt("Add this calculation to the project"),
      on: { click: () => this.add() } }, pt("+ Add to project")));
  },

  // ---------------------------------------------------------------- runs
  async refresh() {
    if (!this.ws.calcs.length) return null;
    try {
      const res = await api("/api/project/run", { doc: this.doc() });
      this.dims = res.dims || this.dims;
      for (const [uid, r] of Object.entries(res.results || {})) {
        this.status[uid] = r.error ? { error: r.error } : { passed: r.summary.passed, util: r.summary.max_utilisation };
        this.outputs[uid] = { name: r.name, outputs: r.outputs || {}, links: r.links || {}, inputs: r.inputs };
      }
      this.cycle = res.error || null;
      return res;
    } catch { return null; }
  },
  // before running the current calculation: put the linked values into its inputs
  async resolve() {
    const c = this.current();
    if (!c || !Object.keys(c.links || {}).length) return;
    await this.refresh();
    const r = this.outputs[c.uid];
    if (!r) return;
    for (const [name, info] of Object.entries(r.links || {})) {
      if (info.ok) {
        state.inputs[name] = info.value;
        const inp = document.getElementById(`f-${name}`);
        if (inp && document.activeElement !== inp) inp.value = fmtNum(+(+info.value).toPrecision(6));
      }
      const row = document.querySelector(`.field[data-name="${name}"]`);
      row?.classList.toggle("linkbad", !info.ok);
    }
  },
  afterRun() {
    clearTimeout(this._t);
    this._t = setTimeout(async () => { await this.refresh(); renderNav(); }, 400);
  },

  // ---------------------------------------------------------- link buttons
  decorate(row, f, input) {
    const c = this.current();
    if (!c || !["float", "int"].includes(f.kind)) return;
    const ln = c.links?.[f.name];
    const label = row.querySelector("label");
    if (ln) {
      const src = this.item(ln.from);
      input.readOnly = true;
      row.classList.add("linked");
      const tag = el("div", { class: "linktag" }, `🔗 ${pt("from")} ${src?.name || "?"}: ${ln.symbol}` +
        (ln.factor && ln.factor !== 1 ? ` × ${fmtNum(+(+ln.factor).toPrecision(4))}` : "") + (ln.abs ? " |…|" : ""),
        el("button", { type: "button", class: "fld-reset", style: "display:inline-block", title: pt("Remove link"),
          on: { click: () => { delete c.links[f.name]; this.save(); renderForm(); schedule(); } } }, "×"));
      row.append(tag);
    } else {
      label.append(el("button", { type: "button", class: "fld-link", tabindex: "-1", title: pt("Link to a result of another calculation"),
        on: { click: () => this.linkDialog(f) } }, "🔗"));
    }
  },
  async linkDialog(f) {
    const c = this.current();
    const others = this.ws.calcs.filter((x) => x.uid !== c.uid);
    if (!others.length) { alert(pt("Add at least two calculations to the project to link them.")); return; }
    await this.refresh();
    const dims = this.dims || {};
    const same = (u) => u === f.unit || (dims[u] !== undefined && dims[u] === dims[f.unit]);
    const dlg = el("dialog", { class: "linkdlg" });
    const sel = el("select", {}, ...others.map((o) => el("option", { value: o.uid }, o.name)));
    const list = el("div", { class: "outlist" });
    const fac = el("input", { type: "text", class: "num", value: "1", title: pt("e.g. 1/1.35 to turn a design value into a characteristic one") });
    const absC = el("input", { type: "checkbox", class: "chk" });
    let chosen = null;
    const draw = () => {
      list.innerHTML = ""; chosen = null;
      const outs = Object.entries(this.outputs[sel.value]?.outputs || {}).filter(([, o]) => same(o.unit));
      if (!outs.length) list.append(el("p", { class: "muted" }, pt("No compatible results (same kind of unit) in the other calculations of the project.")));
      for (const [sym, o] of outs) {
        const r = el("label", { class: "outrow" }, el("input", { type: "radio", name: "out", on: { change: () => (chosen = sym) } }),
          el("span", { class: "sym" }, sym), el("span", { class: "desc" }, o.description || ""),
          el("span", { class: "val" }, `${fmtNum(+o.value.toPrecision(5))} ${o.unit}`));
        list.append(r);
      }
    };
    sel.onchange = draw;
    const ok = el("button", { type: "button", class: "primary", on: { click: () => {
      if (!chosen) return;
      const factor = parseNum(fac.value);
      c.links ||= {};
      c.links[f.name] = { from: sel.value, symbol: chosen, factor: Number.isFinite(factor) ? factor : 1, abs: absC.checked };
      this.save(); dlg.close(); dlg.remove(); renderForm(); schedule();
    } } }, pt("Link"));
    dlg.append(el("h3", {}, `${pt("Link value")}: ${f.label}${f.unit ? ` [${f.unit}]` : ""}`),
      el("label", { class: "lrow" }, pt("Source calculation"), sel), list,
      el("label", { class: "lrow" }, pt("Factor"), fac),
      el("label", { class: "lrow" }, absC, pt("Use absolute value")),
      el("div", { class: "btns" }, el("button", { type: "button", class: "ghost", on: { click: () => { dlg.close(); dlg.remove(); } } }, pt("Cancel")), ok));
    document.body.append(dlg);
    draw();
    dlg.showModal();
  },

  // ------------------------------------------------------- report / compare
  async report() {
    if (!this.ws.calcs.length) { alert(pt("The project is empty — open a calculation and press “+ Add to project”.")); return; }
    const res = await fetch(`/api/project/report`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doc: this.doc(), lang: LANG }) });
    if (res.status === 402) { licenseDialog(); return; }
    const w = window.open("", "erisma-project-report");
    const html = await res.text();
    w.document.open(); w.document.write(html); w.document.close();
  },
  compare() { window.ErismaCompare?.open(); },
};

// logo in the project details
function logoField() {
  const box = $("#project-fields");
  if (!box || box.querySelector(".logo-row")) return;
  const file = el("input", { type: "file", accept: "image/*", hidden: "" });
  const img = el("img", { class: "logo-prev", alt: "" });
  const upd = () => { img.src = state.project.logo || ""; img.hidden = !state.project.logo; rm.hidden = !state.project.logo; };
  const rm = el("button", { type: "button", class: "ghost", on: { click: () => { delete state.project.logo; store.set("erisma.project", state.project); upd(); schedule(); } } }, pt("Remove logo"));
  file.onchange = async () => {
    const f = file.files[0];
    if (!f) return;
    const url = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(r.result); r.readAsDataURL(f); });
    const im = new Image();
    im.onload = () => {  // shrink to keep project files small
      const k = Math.min(1, 360 / Math.max(im.width, im.height));
      const cv = document.createElement("canvas");
      cv.width = Math.round(im.width * k); cv.height = Math.round(im.height * k);
      cv.getContext("2d").drawImage(im, 0, 0, cv.width, cv.height);
      state.project.logo = cv.toDataURL("image/png");
      store.set("erisma.project", state.project); upd(); schedule();
    };
    im.src = url;
  };
  box.append(el("div", { class: "wide logo-row" }, el("label", {}, pt("Company logo")),
    el("div", { class: "site-row" }, img, el("button", { type: "button", class: "ghost", on: { click: () => file.click() } }, "🖼 …"), rm, file)));
  upd();
}
window.Proj = Proj;
window.logoField = logoField;
