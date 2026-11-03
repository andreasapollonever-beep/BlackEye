"use strict";
// Erisma Structure — graphical workspace for whole buildings.
// The plan editor produces the inputs of the "building_frame" module (grid, storeys,
// walls and the "layout" of missing columns/beams, openings and member sizes); the
// calculation, report, 3D scene and licence are the same as everywhere in Erisma.

Object.assign(UI.el, {
  "Erisma Structure": "Erisma Structure",
  "Member calculations": "Υπολογισμοί μελών",
  "Single members, foundations, retaining walls… — one calculation at a time.":
    "Μεμονωμένα μέλη, θεμελιώσεις, τοίχοι αντιστήριξης… — ένας υπολογισμός τη φορά.",
  "Whole buildings: draw the plan, get the 3D analysis, EC8 checks and the reinforcement of every member.":
    "Ολόκληρα κτίρια: σχεδιάστε την κάτοψη και πάρτε 3D ανάλυση, ελέγχους EC8 και τον οπλισμό κάθε μέλους.",
  "Open →": "Άνοιγμα →",
  "Select": "Επιλογή", "Column": "Υποστύλωμα", "Wall X": "Τοίχωμα X", "Wall Y": "Τοίχωμα Y",
  "Beam": "Δοκός", "Opening": "Άνοιγμα πλάκας", "Plan": "Κάτοψη", "Building": "Κτίριο",
  "Undo (Ctrl+Z)": "Αναίρεση (Ctrl+Z)", "Redo (Ctrl+Y)": "Επανάληψη (Ctrl+Y)",
  "Spans along X [m]": "Ανοίγματα κατά X [m]", "Spans along Y [m]": "Ανοίγματα κατά Y [m]",
  "Storey heights [m] (bottom up)": "Ύψη ορόφων [m] (από κάτω)", "Add": "Προσθήκη",
  "Remove": "Αφαίρεση", "Nothing selected": "Δεν έχει επιλεγεί στοιχείο",
  "Click a column, wall, beam or slab panel in the plan.":
    "Κάντε κλικ σε υποστύλωμα, τοίχωμα, δοκό ή φάτνωμα στην κάτοψη.",
  "Width b [mm]": "Πλάτος b [mm]", "Depth h [mm]": "Ύψος h [mm]",
  "Side along X [mm]": "Πλευρά κατά X [mm]", "Side along Y [mm]": "Πλευρά κατά Y [mm]",
  "Length [m]": "Μήκος [m]", "Thickness [mm]": "Πάχος [mm]", "Direction": "Διεύθυνση",
  "Default size": "Προεπιλεγμένη διατομή", "Delete": "Διαγραφή",
  "Open in the member calculation": "Άνοιγμα στον υπολογισμό μέλους",
  "Slab panel": "Φάτνωμα πλάκας", "Open (no slab)": "Άνοιγμα (χωρίς πλάκα)",
  "Results": "Αποτελέσματα", "Storey": "Όροφος", "η": "η",
  "Periods T [s]": "Ιδιοπερίοδοι T [s]", "Base shear [kN]": "Τέμνουσα βάσης [kN]",
  "Max drift d_r/h": "Μέγιστη σχετική μετακίνηση d_r/h",
  "Passes": "Επαρκεί", "Fails": "Ανεπαρκεί", "Not designed": "Χωρίς διαστασιολόγηση",
  "Tools: V select · C column · W wall · B beam · O opening · Del delete · Ctrl+Z undo · Ctrl+3 3D":
    "Εργαλεία: V επιλογή · C υποστύλωμα · W τοίχωμα · B δοκός · O άνοιγμα · Del διαγραφή · Ctrl+Z αναίρεση · Ctrl+3 3D",
  "Click a grid point to place a column.": "Κάντε κλικ σε κόμβο του καννάβου για υποστύλωμα.",
  "Click a grid point to place a wall.": "Κάντε κλικ σε κόμβο του καννάβου για τοίχωμα.",
  "Click between two grid points to add or remove a beam.": "Κάντε κλικ ανάμεσα σε δύο κόμβους για να προσθέσετε ή να αφαιρέσετε δοκό.",
  "Click a slab panel to open or close it.": "Κάντε κλικ σε φάτνωμα για άνοιγμα / κλείσιμο.",
  "Calculating the building…": "Υπολογισμός του κτιρίου…",
  "Reinforcement": "Οπλισμός", "Member": "Μέλος", "storeys": "όροφοι",
  "New building": "Νέο κτίριο", "Start a new building from the example? The current one will be replaced.":
    "Νέο κτίριο από το παράδειγμα; Το τρέχον θα αντικατασταθεί.",
  "Cost estimate": "Εκτίμηση κόστους", "Settings": "Ρυθμίσεις", "grid": "κάνναβος", "Wall": "Τοίχωμα",
});

const Structure = (() => {
  const KEY = "erisma.structure";
  const S = { schema: null, inp: null, tool: "select", sel: null, res: null, view: "plan",
    hist: [], hpos: -1, timer: null, runId: 0, built: false };

  // ------------------------------------------------------------ helpers
  const sum = (a) => a.reduce((x, y) => x + y, 0);
  const cum = (a) => a.reduce((o, v) => (o.push(o[o.length - 1] + v), o), [0]);
  const yLabel = (j) => { let s = ""; j += 1; while (j > 0) { const r = (j - 1) % 26; s = String.fromCharCode(65 + r) + s; j = Math.floor((j - 1) / 26); } return s; };
  const gl = (i, j) => `${yLabel(j)}${i + 1}`;
  const lay = () => (S.inp.layout ||= {});
  const arr = (k) => (lay()[k] ||= []);
  const obj = (k) => (lay()[k] ||= {});
  const heat = (x) => {
    const st = [[0, [47, 111, 216]], [0.35, [46, 155, 95]], [0.7, [240, 196, 40]], [1, [224, 59, 59]]];
    x = Math.max(0, Math.min(1, x));
    for (let k = 1; k < st.length; k++) if (x <= st[k][0]) {
      const [t1, c1] = st[k - 1], [t2, c2] = st[k], q = (x - t1) / (t2 - t1);
      return `rgb(${c1.map((c, n) => Math.round(c + (c2[n] - c) * q)).join(",")})`;
    }
    return "rgb(224,59,59)";
  };
  const defaults = () => Object.fromEntries(S.schema.fields.map((f) => [f.name, structuredClone(f.default)]));
  const geom = () => {
    const xs = cum(S.inp.x_spans.map((r) => +r.L));
    const ys = cum(S.inp.y_spans.map((r) => +r.L));
    return { xs, ys, nx: xs.length, ny: ys.length };
  };
  const wallAt = (g) => (S.inp.walls || []).find((w) => String(w.at).toUpperCase() === g);

  // ------------------------------------------------------------ history / persistence
  function commit(rerun = true) {
    const snap = JSON.stringify(S.inp);
    if (S.hist[S.hpos] !== snap) {
      S.hist = S.hist.slice(0, S.hpos + 1);
      S.hist.push(snap);
      if (S.hist.length > 100) S.hist.shift();
      S.hpos = S.hist.length - 1;
    }
    store.set(KEY, S.inp);
    drawPlan(); renderProps();
    if (rerun) schedule();
  }
  function undo(dir) {
    const p = S.hpos + dir;
    if (p < 0 || p >= S.hist.length) return;
    S.hpos = p;
    S.inp = JSON.parse(S.hist[p]);
    store.set(KEY, S.inp);
    renderSettings(); drawPlan(); renderProps(); schedule();
  }

  // ------------------------------------------------------------ layout of the page
  function build() {
    if (S.built) return;
    S.built = true;
    const tool = (id, label, key, title) => el("button", { type: "button", class: "st-tool", "data-tool": id,
      title: `${title} (${key})`, on: { click: () => setTool(id) } }, label);
    const view = (id, label) => el("button", { type: "button", class: "st-view", "data-view": id,
      on: { click: () => setView(id) } }, label);
    const root = $("#structure");
    root.innerHTML = "";
    root.append(
      el("div", { class: "st-bar" },
        el("div", { class: "st-group" },
          tool("select", `⬚ ${t("Select")}`, "V", t("Select")),
          tool("column", `■ ${t("Column")}`, "C", t("Click a grid point to place a column.")),
          tool("wallX", `▬ ${t("Wall X")}`, "W", t("Click a grid point to place a wall.")),
          tool("wallY", `▮ ${t("Wall Y")}`, "W", t("Click a grid point to place a wall.")),
          tool("beam", `━ ${t("Beam")}`, "B", t("Click between two grid points to add or remove a beam.")),
          tool("opening", `▢ ${t("Opening")}`, "O", t("Click a slab panel to open or close it."))),
        el("div", { class: "st-group" },
          el("button", { type: "button", title: t("Undo (Ctrl+Z)"), on: { click: () => undo(-1) } }, "↶"),
          el("button", { type: "button", title: t("Redo (Ctrl+Y)"), on: { click: () => undo(1) } }, "↷"),
          el("button", { type: "button", on: { click: newBuilding } }, t("New building"))),
        el("div", { class: "st-group" }, view("plan", t("Plan")), view("3d", "3D"), view("report", t("Report")))),
      el("div", { class: "st-body" },
        el("aside", { class: "st-left", id: "st-settings" }),
        el("div", { class: "st-center" },
          el("div", { class: "st-pane on", "data-pane": "plan" },
            el("div", { class: "st-hint", id: "st-hint" }),
            document.createElementNS("http://www.w3.org/2000/svg", "svg")),
          el("div", { class: "st-pane", "data-pane": "3d" }, el("div", { id: "st-3d" })),
          el("div", { class: "st-pane", "data-pane": "report" }, el("iframe", { id: "st-report", title: "Report" }))),
        el("aside", { class: "st-right" },
          el("div", { id: "st-status", role: "status", "aria-live": "polite" }),
          el("div", { id: "st-props" }),
          el("div", { id: "st-summary" }))),
      el("div", { class: "st-foot" }, t("Tools: V select · C column · W wall · B beam · O opening · Del delete · Ctrl+Z undo · Ctrl+3 3D")));
    S.svg = root.querySelector("svg");
    S.svg.id = "st-plan";
    document.addEventListener("keydown", onKey);
    new ResizeObserver(() => S.view === "plan" && drawPlan()).observe(root.querySelector(".st-center"));
  }

  function setTool(id) {
    S.tool = id;
    document.querySelectorAll(".st-tool").forEach((b) => b.classList.toggle("on", b.dataset.tool === id));
    const hints = { select: t("Click a column, wall, beam or slab panel in the plan."),
      column: t("Click a grid point to place a column."), wallX: t("Click a grid point to place a wall."),
      wallY: t("Click a grid point to place a wall."), beam: t("Click between two grid points to add or remove a beam."),
      opening: t("Click a slab panel to open or close it.") };
    $("#st-hint").textContent = hints[id];
    if (S.view !== "plan") setView("plan");
  }
  function setView(v) {
    S.view = v;
    document.querySelectorAll(".st-view").forEach((b) => b.classList.toggle("on", b.dataset.view === v));
    document.querySelectorAll(".st-pane").forEach((p) => p.classList.toggle("on", p.dataset.pane === v));
    if (v === "3d") window.dispatchEvent(new CustomEvent("erisma:show3d", { detail: { host: "st-3d" } }));
    if (v === "plan") drawPlan();
  }

  function onKey(e) {
    if (!document.body.classList.contains("in-structure")) return;
    if (e.target.closest("input,select,textarea") || e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    const map = { v: "select", c: "column", b: "beam", o: "opening" };
    if (map[k]) { setTool(map[k]); e.preventDefault(); }
    else if (k === "w") { setTool(S.tool === "wallX" ? "wallY" : "wallX"); e.preventDefault(); }
    else if ((e.key === "Delete" || e.key === "Backspace") && S.sel) { removeSel(); e.preventDefault(); }
    else if (e.key === "Escape") { S.sel = null; drawPlan(); renderProps(); }
  }

  // ------------------------------------------------------------ settings panel (left)
  function listEditor(title, key, min, max) {
    const box = el("div", { class: "st-list" }, el("div", { class: "st-lt" }, title));
    const rows = S.inp[key];
    rows.forEach((r, n) => {
      const v = key === "storeys" ? r.h : r.L;
      const inp = el("input", { type: "number", step: "0.05", min, max, value: v,
        on: { change: (e) => {
          const x = parseFloat(String(e.target.value).replace(",", "."));
          if (!(x >= min && x <= max)) { e.target.classList.add("bad"); return; }
          e.target.classList.remove("bad");
          if (key === "storeys") r.h = x; else r.L = x;
          commit();
        } } });
      box.append(el("div", { class: "st-li" }, el("span", {}, key === "storeys" ? `${n + 1}` : key === "x_spans" ? `${n + 1}–${n + 2}` : `${yLabel(n)}–${yLabel(n + 1)}`),
        inp, el("button", { type: "button", class: "mini", title: t("Remove"), on: { click: () => {
          if (rows.length > 1) { rows.splice(n, 1); prune(); renderSettings(); commit(); }
        } } }, "×")));
    });
    box.append(el("button", { type: "button", class: "mini add", on: { click: () => {
      rows.push(structuredClone(rows[rows.length - 1])); renderSettings(); commit();
    } } }, `+ ${t("Add")}`));
    return box;
  }

  function renderSettings() {
    const box = $("#st-settings");
    box.innerHTML = "";
    box.append(el("details", { open: "" }, el("summary", {}, `${t("Building")} — ${t("grid")}`),
      listEditor(t("Spans along X [m]"), "x_spans", 1, 15),
      listEditor(t("Spans along Y [m]"), "y_spans", 1, 15),
      listEditor(t("Storey heights [m] (bottom up)"), "storeys", 2, 8)));
    const groups = {};
    for (const f of S.schema.fields) {
      if (["table", "json"].includes(f.kind)) continue;
      (groups[f.group] ||= []).push(f);
    }
    for (const [g, fields] of Object.entries(groups)) {
      const det = el("details", {}, el("summary", {}, g));
      for (const f of fields) {
        if (f.show_if && !S.inp[f.show_if]) continue;
        if (!(f.name in S.inp)) S.inp[f.name] = f.default;
        const input = scalarInput(f, S.inp[f.name], (v) => {
          S.inp[f.name] = v;
          if (fields.some((x) => x.show_if === f.name) || S.schema.fields.some((x) => x.show_if === f.name)) renderSettings();
          commit();
        });
        det.append(el("label", { class: "st-f", title: f.help || "" },
          el("span", {}, f.label), el("span", { class: "inp" }, input, el("small", {}, f.unit || ""))));
      }
      box.append(det);
    }
  }

  // drop layout entries that refer to grid points/segments that no longer exist
  function prune() {
    const { nx, ny } = geom();
    const pts = new Set(); for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) pts.add(gl(i, j));
    const segs = new Set();
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx - 1; i++) segs.add(`${gl(i, j)}-${gl(i + 1, j)}`);
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny - 1; j++) segs.add(`${gl(i, j)}-${gl(i, j + 1)}`);
    const pans = new Set(); for (let i = 0; i < nx - 1; i++) for (let j = 0; j < ny - 1; j++) pans.add(gl(i, j));
    const L = lay();
    L.omit_columns = (L.omit_columns || []).filter((g) => pts.has(g));
    L.omit_beams = (L.omit_beams || []).filter((g) => segs.has(g));
    L.openings = (L.openings || []).filter((g) => pans.has(g));
    for (const k of ["col_sizes", "beam_sizes"]) for (const g of Object.keys(L[k] || {})) if (!(k === "col_sizes" ? pts : segs).has(g)) delete L[k][g];
    S.inp.walls = (S.inp.walls || []).filter((w) => pts.has(String(w.at).toUpperCase()));
    if (S.sel && !pts.has(S.sel.id) && !segs.has(S.sel.id) && !pans.has(S.sel.id)) S.sel = null;
  }

  // ------------------------------------------------------------ results per plan element
  function resultsFor(kind, id) {
    const m = S.res?.structure?.members || {};
    const pref = kind === "beam" ? "B" : kind === "wall" ? "W" : "C";
    return Object.entries(m).filter(([k]) => k.startsWith(pref) && k.slice(k.indexOf(".") + 1) === id)
      .map(([k, v]) => ({ id: k, ...v })).sort((a, b) => a.storey - b.storey);
  }
  function colourFor(kind, id) {
    const r = resultsFor(kind, id);
    if (!r.length) return null;
    if (r.some((x) => !x.ok)) return "#e03b3b";
    return heat(0.85 * Math.max(...r.map((x) => x.util)) ** 2);
  }

  // ------------------------------------------------------------ plan (SVG)
  const NS = "http://www.w3.org/2000/svg";
  const sv = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.append(e);
    return e;
  };

  function drawPlan() {
    if (!S.inp || !S.svg) return;
    const svg = S.svg;
    svg.innerHTML = "";
    const { xs, ys, nx, ny } = geom();
    const W = xs[nx - 1] * 1000, H = ys[ny - 1] * 1000;
    const pad = Math.max(W, H) * 0.12 + 1500;
    svg.setAttribute("viewBox", `${-pad} ${-pad} ${W + 2 * pad} ${H + 2 * pad}`);
    const Y = (y) => H - y;                         // plan with Y upwards
    const X = (x) => x;
    const L = lay();
    const omitC = new Set(L.omit_columns || []), omitB = new Set(L.omit_beams || []);
    const open = new Set(L.openings || []);
    const unit = Math.max(W, H) / 100;              // visual unit for strokes/text
    const defs = sv("defs", {}, svg);
    const pat = sv("pattern", { id: "st-hatch", width: unit * 3, height: unit * 3, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    sv("line", { x1: 0, y1: 0, x2: 0, y2: unit * 3, stroke: "var(--muted)", "stroke-width": unit * 0.4 }, pat);
    const gPan = sv("g", {}, svg), gGrid = sv("g", {}, svg), gBeam = sv("g", {}, svg), gCol = sv("g", {}, svg), gTxt = sv("g", {}, svg);
    const isSel = (kind, id) => S.sel && S.sel.kind === kind && S.sel.id === id;
    const click = (node, kind, id) => node.addEventListener("click", (e) => { e.stopPropagation(); act(kind, id); });

    // slab panels
    for (let i = 0; i < nx - 1; i++) for (let j = 0; j < ny - 1; j++) {
      const id = gl(i, j);
      const r = sv("rect", { x: X(xs[i] * 1000), y: Y(ys[j + 1] * 1000), width: (xs[i + 1] - xs[i]) * 1000,
        height: (ys[j + 1] - ys[j]) * 1000, class: `st-panel${open.has(id) ? " open" : ""}${isSel("panel", id) ? " sel" : ""}`,
        fill: open.has(id) ? "url(#st-hatch)" : "" }, gPan);
      sv("title", {}, r).textContent = `${t("Slab panel")} ${id}${open.has(id) ? ` — ${t("Open (no slab)")}` : ""}`;
      click(r, "panel", id);
    }
    // grid lines + bubbles
    const ext = unit * 6, rb = unit * 2.2;
    for (let i = 0; i < nx; i++) {
      const x = X(xs[i] * 1000);
      sv("line", { x1: x, y1: Y(-ext), x2: x, y2: Y(H + ext), class: "st-grid", "stroke-width": unit * 0.15, "stroke-dasharray": `${unit} ${unit * 0.6}` }, gGrid);
      for (const yy of [Y(-ext - rb), Y(H + ext + rb)]) {
        sv("circle", { cx: x, cy: yy, r: rb, class: "st-bubble", "stroke-width": unit * 0.2 }, gGrid);
        const tx = sv("text", { x, y: yy, "font-size": rb * 1.1, class: "st-btxt" }, gGrid); tx.textContent = i + 1;
      }
      if (i < nx - 1) {
        const tx = sv("text", { x: (xs[i] + xs[i + 1]) * 500, y: Y(-ext - rb * 0.2), "font-size": unit * 1.6, class: "st-dim" }, gTxt);
        tx.textContent = `${(+(xs[i + 1] - xs[i]).toFixed(2))} m`;
      }
    }
    for (let j = 0; j < ny; j++) {
      const y = Y(ys[j] * 1000);
      sv("line", { x1: X(-ext), y1: y, x2: X(W + ext), y2: y, class: "st-grid", "stroke-width": unit * 0.15, "stroke-dasharray": `${unit} ${unit * 0.6}` }, gGrid);
      for (const xx of [X(-ext - rb), X(W + ext + rb)]) {
        sv("circle", { cx: xx, cy: y, r: rb, class: "st-bubble", "stroke-width": unit * 0.2 }, gGrid);
        const tx = sv("text", { x: xx, y, "font-size": rb * 1.1, class: "st-btxt" }, gGrid); tx.textContent = yLabel(j);
      }
      if (j < ny - 1) {
        const tx = sv("text", { x: X(-ext - rb * 0.2), y: Y((ys[j] + ys[j + 1]) * 500), "font-size": unit * 1.6, class: "st-dim",
          transform: `rotate(-90 ${X(-ext - rb * 0.2)} ${Y((ys[j] + ys[j + 1]) * 500)})` }, gTxt);
        tx.textContent = `${(+(ys[j + 1] - ys[j]).toFixed(2))} m`;
      }
    }
    // beams
    const bsz = L.beam_sizes || {};
    const beam = (i1, j1, i2, j2) => {
      const id = `${gl(i1, j1)}-${gl(i2, j2)}`;
      const x1 = X(xs[i1] * 1000), y1 = Y(ys[j1] * 1000), x2 = X(xs[i2] * 1000), y2 = Y(ys[j2] * 1000);
      const hit = sv("line", { x1, y1, x2, y2, class: "st-hit", "stroke-width": unit * 3 }, gBeam);
      click(hit, "beam", id);
      if (omitB.has(id)) {
        sv("line", { x1, y1, x2, y2, class: "st-ghost", "stroke-width": unit * 0.3, "stroke-dasharray": `${unit} ${unit}` }, gBeam).style.pointerEvents = "none";
        sv("title", {}, hit).textContent = `${t("Beam")} ${id} — ${t("Remove")}`;
        return;
      }
      const b = (bsz[id]?.[0] ?? S.inp.beam_b);
      const col = colourFor("beam", id);
      const ln = sv("line", { x1, y1, x2, y2, class: `st-beam${isSel("beam", id) ? " sel" : ""}`, "stroke-width": Math.max(b, unit * 0.8) }, gBeam);
      if (col) ln.style.stroke = col;
      ln.style.pointerEvents = "none";
      const r = resultsFor("beam", id);
      sv("title", {}, hit).textContent = `${t("Beam")} ${id} — ${b}×${bsz[id]?.[1] ?? S.inp.beam_h}` +
        (r.length ? "\n" + r.map((x) => `${t("Storey")} ${x.storey}: ${x.reinforcement} (η = ${x.util.toFixed(2)})`).join("\n") : "");
    };
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx - 1; i++) beam(i, j, i + 1, j);
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny - 1; j++) beam(i, j, i, j + 1);
    // columns / walls / empty points
    const csz = L.col_sizes || {};
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
      const id = gl(i, j), cx = X(xs[i] * 1000), cy = Y(ys[j] * 1000);
      const w = wallAt(id);
      let node;
      if (w) {
        const [bx, by] = w.dir === "X" ? [w.L * 1000, w.t] : [w.t, w.L * 1000];
        node = sv("rect", { x: cx - bx / 2, y: cy - by / 2, width: bx, height: by,
          class: `st-wall${isSel("wall", id) ? " sel" : ""}` }, gCol);
        if (colourFor("wall", id)) node.style.fill = colourFor("wall", id);
        const r = resultsFor("wall", id);
        sv("title", {}, node).textContent = `${t("Wall")} ${id} — ${w.L} m × ${w.t} mm` + (r.length ? `\n${r[0].reinforcement}` : "");
        click(node, "wall", id);
      } else if (omitC.has(id)) {
        node = sv("circle", { cx, cy, r: unit * 1.2, class: "st-empty" }, gCol);
        sv("title", {}, node).textContent = `${id}`;
        click(node, "point", id);
      } else {
        const [b, h] = csz[id] || [S.inp.col_b, S.inp.col_h];
        node = sv("rect", { x: cx - b / 2, y: cy - h / 2, width: b, height: h,
          class: `st-col${isSel("column", id) ? " sel" : ""}` }, gCol);
        if (colourFor("column", id)) node.style.fill = colourFor("column", id);
        const r = resultsFor("column", id);
        sv("title", {}, node).textContent = `${t("Column")} ${id} — ${b}×${h}` +
          (r.length ? "\n" + r.map((x) => `${t("Storey")} ${x.storey}: ${x.reinforcement} (η = ${x.util.toFixed(2)})`).join("\n") : "");
        click(node, "column", id);
      }
      const lbl = sv("text", { x: cx + unit * 1.2, y: cy - unit * 1.2, "font-size": unit * 1.7, class: "st-plbl" }, gTxt);
      lbl.textContent = id;
    }
    svg.onclick = () => { if (S.tool === "select") { S.sel = null; drawPlan(); renderProps(); } };
  }

  // ------------------------------------------------------------ editing actions
  function act(kind, id) {
    const L = lay();
    const point = ["column", "wall", "point"].includes(kind);
    const tool = S.tool;
    if (tool === "select") {
      S.sel = kind === "point" ? null : { kind, id };
      drawPlan(); renderProps();
      return;
    }
    if (tool === "column" && point) {
      S.inp.walls = (S.inp.walls || []).filter((w) => String(w.at).toUpperCase() !== id);
      L.omit_columns = arr("omit_columns").filter((g) => g !== id);
      S.sel = { kind: "column", id };
    } else if ((tool === "wallX" || tool === "wallY") && point) {
      const dir = tool === "wallX" ? "X" : "Y";
      const w = wallAt(id);
      if (w) w.dir = dir; else (S.inp.walls ||= []).push({ at: id, dir, L: 2.0, t: 250 });
      L.omit_columns = arr("omit_columns").filter((g) => g !== id);
      S.sel = { kind: "wall", id };
    } else if (tool === "beam" && kind === "beam") {
      const a = arr("omit_beams");
      L.omit_beams = a.includes(id) ? a.filter((g) => g !== id) : [...a, id];
      S.sel = L.omit_beams.includes(id) ? null : { kind: "beam", id };
    } else if (tool === "opening" && kind === "panel") {
      const a = arr("openings");
      L.openings = a.includes(id) ? a.filter((g) => g !== id) : [...a, id];
      S.sel = { kind: "panel", id };
    } else return;
    commit();
  }

  function removeSel() {
    const { kind, id } = S.sel;
    const L = lay();
    if (kind === "column") L.omit_columns = [...new Set([...arr("omit_columns"), id])];
    if (kind === "wall") { S.inp.walls = S.inp.walls.filter((w) => String(w.at).toUpperCase() !== id); L.omit_columns = [...new Set([...arr("omit_columns"), id])]; }
    if (kind === "beam") L.omit_beams = [...new Set([...arr("omit_beams"), id])];
    if (kind === "panel") L.openings = [...new Set([...arr("openings"), id])];
    S.sel = null;
    commit();
  }

  // ------------------------------------------------------------ properties (right)
  function numField(label, value, min, max, onSet) {
    const inp = el("input", { type: "number", value, min, max, step: "any", on: { change: (e) => {
      const v = parseFloat(String(e.target.value).replace(",", "."));
      if (!(v >= min && v <= max)) { e.target.classList.add("bad"); return; }
      onSet(v);
    } } });
    return el("label", { class: "st-f" }, el("span", {}, label), el("span", { class: "inp" }, inp));
  }

  function renderProps() {
    const box = $("#st-props");
    if (!box) return;
    box.innerHTML = "";
    if (!S.sel) {
      box.append(el("h4", {}, t("Nothing selected")), el("p", { class: "muted" }, t("Click a column, wall, beam or slab panel in the plan.")));
      return;
    }
    const { kind, id } = S.sel;
    const L = lay();
    const title = { column: t("Column"), wall: t("Wall"), beam: t("Beam"), panel: t("Slab panel") }[kind];
    box.append(el("h4", {}, `${title} ${id}`));
    if (kind === "column") {
      const cur = obj("col_sizes")[id] || [S.inp.col_b, S.inp.col_h];
      box.append(numField(t("Side along X [mm]"), cur[0], 200, 1500, (v) => { obj("col_sizes")[id] = [v, cur[1]]; commit(); }),
        numField(t("Side along Y [mm]"), cur[1], 200, 1500, (v) => { obj("col_sizes")[id] = [cur[0], v]; commit(); }));
      if (L.col_sizes?.[id]) box.append(el("button", { type: "button", class: "ghost", on: { click: () => { delete L.col_sizes[id]; commit(); } } }, t("Default size")));
    } else if (kind === "wall") {
      const w = wallAt(id);
      const dir = el("select", { on: { change: (e) => { w.dir = e.target.value; commit(); } } }, el("option", { value: "X" }, "X"), el("option", { value: "Y" }, "Y"));
      dir.value = w.dir;
      box.append(el("label", { class: "st-f" }, el("span", {}, t("Direction")), el("span", { class: "inp" }, dir)),
        numField(t("Length [m]"), w.L, 1, 10, (v) => { w.L = v; commit(); }),
        numField(t("Thickness [mm]"), w.t, 150, 600, (v) => { w.t = v; commit(); }));
    } else if (kind === "beam") {
      const cur = obj("beam_sizes")[id] || [S.inp.beam_b, S.inp.beam_h];
      box.append(numField(t("Width b [mm]"), cur[0], 150, 800, (v) => { obj("beam_sizes")[id] = [v, cur[1]]; commit(); }),
        numField(t("Depth h [mm]"), cur[1], 250, 1500, (v) => { obj("beam_sizes")[id] = [cur[0], v]; commit(); }));
      if (L.beam_sizes?.[id]) box.append(el("button", { type: "button", class: "ghost", on: { click: () => { delete L.beam_sizes[id]; commit(); } } }, t("Default size")));
    } else if (kind === "panel") {
      const isOpen = (L.openings || []).includes(id);
      const cb = el("input", { type: "checkbox", on: { change: (e) => {
        L.openings = e.target.checked ? [...arr("openings"), id] : arr("openings").filter((g) => g !== id); commit();
      } } });
      cb.checked = isOpen;
      box.append(el("label", { class: "st-f chk" }, cb, el("span", {}, t("Open (no slab)"))));
    }
    if (kind !== "panel") box.append(el("button", { type: "button", class: "ghost danger", on: { click: removeSel } }, `🗑 ${t("Delete")}`));
    const res = kind === "panel" ? [] : resultsFor(kind, id);
    if (res.length) {
      const tb = el("table", { class: "st-res" }, el("tr", {}, el("th", {}, t("Storey")), el("th", {}, t("Reinforcement")), el("th", {}, "η"), el("th", {}, "")));
      for (const r of res) {
        tb.append(el("tr", { class: r.ok ? "" : "bad", title: r.notes.join("\n") }, el("td", {}, String(r.storey)), el("td", {}, r.reinforcement),
          el("td", {}, r.util.toFixed(2)), el("td", {}, el("button", { type: "button", class: "mini", title: t("Open in the member calculation"),
            on: { click: () => openModule(r.module, r.inputs) } }, "↗"))));
      }
      box.append(el("h4", {}, t("Results")), tb);
      const notes = [...new Set(res.flatMap((r) => r.notes))];
      if (notes.length) box.append(el("ul", { class: "st-notes" }, ...notes.map((n) => el("li", {}, n))));
    }
  }

  // ------------------------------------------------------------ run
  function schedule() {
    clearTimeout(S.timer);
    $("#st-status").className = "busy";
    $("#st-status").textContent = t("Calculating the building…");
    S.timer = setTimeout(run, 500);
  }
  async function run() {
    const my = ++S.runId;
    try {
      const res = await api("/api/modules/building_frame/run", { inputs: S.inp, project: state.project });
      if (my !== S.runId) return;
      S.res = res;
      $("#st-report").srcdoc = res.html;
      if (res.model3d) {
        window.dispatchEvent(new CustomEvent("erisma:model3d", { detail: { host: "st-3d", model: res.model3d, summary: res.summary } }));
      }
      renderResult(res);
      drawPlan(); renderProps();
    } catch (err) {
      if (my !== S.runId) return;
      const st = $("#st-status");
      st.className = "err";
      st.textContent = `⚠ ${err.message}`;
      if (err.license) licenseDialog();
    }
  }

  function renderResult(res) {
    const s = res.summary, st = $("#st-status");
    st.innerHTML = "";
    st.className = s.passed ? "pass" : "fail";
    const u = Math.min(s.max_utilisation, 9.99).toFixed(2);
    st.append(el("div", { class: "head" }, `${s.passed ? "✔ " + t("All checks pass") : "✖ " + t("Design fails")} — ${t("max utilisation")} ${u}`),
      el("div", { class: "ubar" }, el("i", { style: `width:${Math.min(s.max_utilisation, 1.2) / 1.2 * 100}%` })));
    const failing = s.checks.filter((c) => !c.passed).sort((a, b) => b.utilisation - a.utilisation);
    if (failing.length) {
      st.append(el("ul", { class: "fails" }, ...failing.slice(0, 6).map((c) => el("li", {}, el("b", {}, `${c.description} — U = ${Math.min(c.utilisation, 9.99).toFixed(2)}`),
        c.hint ? el("div", { class: "hint" }, `💡 ${c.hint}`) : ""))));
    }
    const sm = $("#st-summary");
    sm.innerHTML = "";
    const r = res.structure || {};
    const rows = [];
    if (r.periods?.length) rows.push([t("Periods T [s]"), r.periods.slice(0, 3).map((x) => x.toFixed(3)).join(" · ")]);
    if (r.base_shear) rows.push([t("Base shear [kN]"), `X ${r.base_shear.X.toFixed(0)} · Y ${r.base_shear.Y.toFixed(0)}`]);
    if (r.storeys?.length) {
      const d = Math.max(...r.storeys.flatMap((x) => Object.values(x.drift)));
      rows.push([t("Max drift d_r/h"), `${(d * 1000).toFixed(2)} ‰`]);
    }
    if (res.quantities) rows.push([t("Cost estimate"), `≈ ${Math.round(res.quantities.total).toLocaleString(LANG === "el" ? "el-GR" : "en-GB")} €`]);
    if (rows.length) sm.append(el("h4", {}, t("Results")), el("table", { class: "st-sum" }, ...rows.map(([a, b]) => el("tr", {}, el("td", {}, a), el("td", {}, b)))));
    sm.append(el("div", { class: "st-legend" },
      el("span", {}, el("i", { style: `background:${heat(0.1)}` }), "η ≈ 0.3"),
      el("span", {}, el("i", { style: `background:${heat(0.8)}` }), "η ≈ 1"),
      el("span", {}, el("i", { style: "background:#e03b3b" }), t("Fails"))));
  }

  // ------------------------------------------------------------ entry points
  async function ensure() {
    if (!S.schema || S.schema.lang !== LANG) {
      S.schema = await api("/api/modules/building_frame");
      S.schema.lang = LANG;
    }
    if (!S.inp) {
      S.inp = store.get(KEY, null) || defaults();
      for (const f of S.schema.fields) if (!(f.name in S.inp)) S.inp[f.name] = structuredClone(f.default);
      S.hist = [JSON.stringify(S.inp)]; S.hpos = 0;
    }
  }
  async function show() {
    build();
    await ensure();
    document.title = "Erisma Structure";
    renderSettings();
    setTool(S.tool);
    setView(S.view);
    renderProps();
    run();
  }
  function newBuilding() {
    if (!confirm(t("Start a new building from the example? The current one will be replaced."))) return;
    S.inp = defaults(); S.sel = null;
    renderSettings(); commit();
  }
  function load(inputs) {
    S.inp = { ...(S.schema ? defaults() : {}), ...inputs };
    S.sel = null;
    store.set(KEY, S.inp);
    S.hist = [JSON.stringify(S.inp)]; S.hpos = 0;
    if (S.built && S.schema) { renderSettings(); drawPlan(); renderProps(); schedule(); }
  }
  const fileName = () => (state.project.job_no || state.project.project || "building").replace(/[^\w.-]+/g, "_");
  function save() {
    download(`${fileName()}_structure.erisma`, JSON.stringify({ format: "erisma", version: 1, module: "building_frame",
      workspace: "structure", project: state.project, inputs: S.inp }, null, 2), "application/json");
  }
  const print = () => { setView("report"); setTimeout(() => $("#st-report").contentWindow.print(), 300); };
  const html = () => S.res && download(`${fileName()}_structure.html`, S.res.html, "text/html");
  const toggle3d = () => setView(S.view === "3d" ? "plan" : "3d");

  // re-render texts when the language changes
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
    if (!S.built) return;
    S.built = false;
    S.schema = null;
    if (document.body.classList.contains("in-structure")) setTimeout(show, 0);
  }));

  return { show, load, save, print, html, undo, toggle3d, _state: S };
})();
window.Structure = Structure;

// ---------------------------------------------------------------- the two spaces on the home page
(function homeSpaces() {
  const wrap = document.querySelector("#home .home-wrap");
  if (!wrap) return;
  const box = el("div", { class: "spaces" });
  const draw = () => {
    box.innerHTML = "";
    box.append(
      el("button", { type: "button", class: "space", on: { click: () => document.querySelector("#home-cards")?.scrollIntoView({ behavior: "smooth" }) } },
        el("div", { class: "sp-ic" }, "▦"), el("div", { class: "sp-t" }, t("Member calculations")),
        el("div", { class: "sp-d" }, t("Single members, foundations, retaining walls… — one calculation at a time."))),
      el("button", { type: "button", class: "space st", on: { click: () => { location.hash = "structure"; } } },
        el("div", { class: "sp-ic" }, "🏢"), el("div", { class: "sp-t" }, t("Erisma Structure")),
        el("div", { class: "sp-d" }, t("Whole buildings: draw the plan, get the 3D analysis, EC8 checks and the reinforcement of every member.")),
        el("div", { class: "sp-go" }, t("Open →"))));
  };
  draw();
  wrap.querySelector(".hero")?.after(box);
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => setTimeout(draw, 0)));
})();
