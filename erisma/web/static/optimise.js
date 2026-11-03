"use strict";
// Automatic design (cheapest passing design), unit prices and comparison of project items.

const OUI = {
  el: {
    "Find the most economical design": "Βρες την πιο οικονομική λύση", "Optimise": "Βελτιστοποίηση",
    "Design variables": "Μεταβλητές σχεδιασμού", "From": "Από", "To": "Έως", "Step": "Βήμα",
    "All options": "Όλες οι επιλογές", "Search": "Αναζήτηση", "Searching…": "Αναζήτηση…",
    "Current design": "Τρέχουσα λύση", "Optimum": "Βέλτιστη λύση", "Cost": "Κόστος", "Utilisation": "Αξιοποίηση",
    "Apply": "Εφαρμογή", "Close": "Κλείσιμο", "No passing design found in these ranges — widen the ranges.":
      "Δεν βρέθηκε λύση που επαρκεί σε αυτά τα εύρη — διευρύνετε τα όρια.",
    "trials": "δοκιμές", "exhaustive": "πλήρης αναζήτηση", "coordinate descent": "αναζήτηση ανά μεταβλητή", "Cost estimate": "Εκτίμηση κόστους", "Unit prices": "Τιμές μονάδας",
    "Unit prices for the cost estimate (€)": "Τιμές μονάδας για την εκτίμηση κόστους (€)", "Save": "Αποθήκευση",
    "Reset prices": "Προεπιλεγμένες τιμές", "Comparison of the project calculations": "Σύγκριση υπολογισμών έργου",
    "Element": "Στοιχείο", "Calculation": "Υπολογισμός", "Result": "Αποτέλεσμα", "Quantities": "Ποσότητες",
    "cheapest passing of its type": "φθηνότερη επαρκής λύση του είδους της", "PASS": "ΕΠΑΡΚΕΙ", "FAIL": "ΑΝΕΠΑΡΚΕΙ",
    "This calculation has no design variables to optimise.": "Ο υπολογισμός αυτός δεν έχει μεταβλητές για βελτιστοποίηση.",
    "Only the variables you tick are changed; all checks must pass. Cost from the quantities and unit prices.":
      "Αλλάζουν μόνο οι μεταβλητές που επιλέγετε· όλοι οι έλεγχοι πρέπει να επαρκούν. Κόστος από ποσότητες και τιμές μονάδας.",
  },
};
const ot = (k) => (LANG !== "en" && OUI[LANG]?.[k]) || t(k);
const ITEM_LABELS = {
  concrete: ["Concrete", "Σκυρόδεμα", "m³", 130], rebar: ["Reinforcement", "Οπλισμός", "kg", 1.3],
  steel: ["Structural steel", "Δομικός χάλυβας", "kg", 3.2], timber: ["Timber", "Ξυλεία", "m³", 950],
  masonry: ["Masonry", "Τοιχοποιία", "m³", 160], gabion: ["Gabions", "Συρματοκιβώτια", "m³", 95],
  formwork: ["Formwork", "Ξυλότυποι", "m²", 25], excavation: ["Excavation", "Εκσκαφή", "m³", 12],
  drilling: ["Pile boring", "Διάτρηση πασσάλων", "m", 70], anchor: ["Ground anchors", "Αγκύρια", "m", 90],
  frp: ["FRP wrapping", "Περιτύλιξη ΙΟΠ", "m²", 120],
};
const itemName = (k) => (ITEM_LABELS[k] ? ITEM_LABELS[k][LANG === "el" ? 1 : 0] : k);
const eur = (v) => (v == null ? "—" : `${Math.round(v).toLocaleString(LANG === "el" ? "el-GR" : "en-GB")} €`);

function dialog(title, ...body) {
  const d = el("dialog", { class: "linkdlg wide" }, el("h3", {}, title), ...body);
  document.body.append(d);
  d.addEventListener("close", () => d.remove());
  d.showModal();
  return d;
}

const Opt = {
  async open() {
    const vars = await api(`/api/modules/${state.schema.id}/optimise`);
    if (!vars.length) { alert(ot("This calculation has no design variables to optimise.")); return; }
    const rows = vars.map((v) => {
      const on = el("input", { type: "checkbox", class: "chk" });
      on.checked = true;
      if (v.choices) {
        return { v, on, tr: el("tr", {}, el("td", {}, on), el("td", {}, v.label), el("td", { colspan: 3, class: "muted" }, `${ot("All options")} (${v.choices.length})`)) };
      }
      const lo = el("input", { type: "text", class: "num", value: fmtNum(v.lo) });
      const hi = el("input", { type: "text", class: "num", value: fmtNum(v.hi) });
      const st = el("input", { type: "text", class: "num", value: fmtNum(v.step) });
      return { v, on, lo, hi, st, tr: el("tr", {}, el("td", {}, on), el("td", {}, `${v.label}${v.unit ? ` [${v.unit}]` : ""}`),
        el("td", {}, lo), el("td", {}, hi), el("td", {}, st)) };
    });
    const out = el("div", { class: "optout" });
    const go = el("button", { type: "button", class: "primary" }, `🎯 ${ot("Search")}`);
    const d = dialog(`🎯 ${ot("Find the most economical design")}`,
      el("p", { class: "muted small" }, ot("Only the variables you tick are changed; all checks must pass. Cost from the quantities and unit prices.")),
      el("table", { class: "tbl" }, el("thead", {}, el("tr", {}, el("th"), el("th", {}, ot("Design variables")),
        el("th", {}, ot("From")), el("th", {}, ot("To")), el("th", {}, ot("Step")))), el("tbody", {}, ...rows.map((r) => r.tr))),
      out, el("div", { class: "btns" }, el("button", { type: "button", class: "ghost", on: { click: () => d.close() } }, ot("Close")), go));
    go.onclick = async () => {
      const variables = rows.filter((r) => r.on.checked).map((r) => r.v.choices
        ? { name: r.v.name, choices: r.v.choices, kind: r.v.kind }
        : { name: r.v.name, lo: parseNum(r.lo.value), hi: parseNum(r.hi.value), step: parseNum(r.st.value), kind: r.v.kind });
      if (!variables.length) return;
      go.disabled = true; out.innerHTML = ""; out.append(el("p", { class: "busy" }, ot("Searching…")));
      try {
        const r = await api(`/api/modules/${state.schema.id}/optimise`, { inputs: state.inputs, project: state.project, variables });
        out.innerHTML = "";
        if (!r.passed) { out.append(el("p", { class: "err" }, ot("No passing design found in these ranges — widen the ranges."))); return; }
        const lab = Object.fromEntries(vars.map((v) => [v.name, v]));
        const show = (n, val) => (lab[n]?.choices ? String(val) : fmtNum(val));
        out.append(el("table", { class: "tbl res" },
          el("thead", {}, el("tr", {}, el("th"), el("th", {}, ot("Current design")), el("th", {}, ot("Optimum")))),
          el("tbody", {}, ...Object.keys(r.best).map((n) => el("tr", { class: String(r.best[n]) !== String(r.start[n]) ? "chg" : "" },
            el("td", {}, lab[n]?.label || n), el("td", {}, show(n, r.start[n])), el("td", {}, show(n, r.best[n])))),
            el("tr", {}, el("td", {}, ot("Cost")), el("td", {}, eur(r.start_cost)), el("td", { class: "big" }, eur(r.cost))),
            el("tr", {}, el("td", {}, ot("Utilisation")), el("td", {}, r.start_util != null ? fmtNum(+r.start_util.toFixed(2)) + (r.start_passed ? " ✓" : " ✗") : "—"),
              el("td", {}, `${fmtNum(+r.util.toFixed(2))} ✓`)))),
          el("p", { class: "muted small" }, `${r.evaluations} ${ot("trials")} · ${ot(r.method)} · ${fmtNum(r.seconds)} s`),
          el("div", { class: "btns" }, el("button", { type: "button", class: "primary", on: { click: () => {
            Object.assign(state.inputs, r.best); snapshot(); renderForm(); schedule(); d.close();
          } } }, `✓ ${ot("Apply")}`)));
      } catch (err) {
        out.innerHTML = ""; out.append(el("p", { class: "err" }, err.message));
        if (err.license) { d.close(); licenseDialog(); }
      }
      finally { go.disabled = false; }
    };
  },

  prices() {
    let cur = {};
    try { cur = JSON.parse(state.project.prices || "{}"); } catch { cur = {}; }
    const inputs = {};
    const d = dialog(`💶 ${ot("Unit prices for the cost estimate (€)")}`,
      el("table", { class: "tbl" }, el("tbody", {}, ...Object.entries(ITEM_LABELS).map(([k, [, , u, def]]) => {
        inputs[k] = el("input", { type: "text", class: "num", value: fmtNum(cur[k] ?? def) });
        return el("tr", {}, el("td", {}, itemName(k)), el("td", {}, inputs[k]), el("td", { class: "muted" }, `€/${u}`));
      }))),
      el("div", { class: "btns" },
        el("button", { type: "button", class: "ghost", on: { click: () => { delete state.project.prices; store.set("erisma.project", state.project); d.close(); schedule(); } } }, ot("Reset prices")),
        el("button", { type: "button", class: "primary", on: { click: () => {
          const p = {};
          for (const [k, i] of Object.entries(inputs)) { const v = parseNum(i.value); if (Number.isFinite(v)) p[k] = v; }
          state.project.prices = JSON.stringify(p); store.set("erisma.project", state.project); d.close(); schedule();
        } } }, ot("Save"))));
  },

  async compare() {
    if (!Proj.ws.calcs.length) { alert(pt("The project is empty — open a calculation and press “+ Add to project”.")); return; }
    let res;
    try { res = await api("/api/project/run", { doc: Proj.doc() }); } catch (err) {
      if (err.license) licenseDialog(); else alert(err.message);
      return;
    }
    const items = Proj.ws.calcs.map((c) => ({ c, r: res.results?.[c.uid] || {} }));
    const best = {};
    for (const { c, r } of items) {
      if (r.summary?.passed && r.quantities) {
        if (!best[c.module] || r.quantities.total < best[c.module].total) best[c.module] = { uid: c.uid, total: r.quantities.total };
      }
    }
    const total = items.reduce((s, { r }) => s + (r.quantities?.total || 0), 0);
    dialog(`⚖ ${ot("Comparison of the project calculations")}`,
      el("table", { class: "tbl cmp" }, el("thead", {}, el("tr", {}, el("th", {}, ot("Element")), el("th", {}, ot("Calculation")),
        el("th", {}, ot("Result")), el("th", {}, "U"), el("th", {}, ot("Quantities")), el("th", {}, ot("Cost")))),
      el("tbody", {}, ...items.map(({ c, r }) => {
        const s = r.summary;
        const q = r.quantities;
        const cheapest = best[c.module]?.uid === c.uid && items.filter((x) => x.c.module === c.module).length > 1;
        return el("tr", { class: cheapest ? "best" : "" }, el("td", {}, c.name), el("td", {}, r.title || c.module),
          el("td", { class: s ? (s.passed ? "ok" : "ko") : "ko" }, s ? ot(s.passed ? "PASS" : "FAIL") : (r.error || "—")),
          el("td", {}, s ? fmtNum(+s.max_utilisation.toFixed(2)) : "—"),
          el("td", { class: "small" }, q ? q.rows.map((x) => `${itemName(x.item)} ${fmtNum(+x.qty.toFixed(2))} ${x.unit}`).join(" · ") : "—"),
          el("td", { class: "num" }, q ? eur(q.total) + (cheapest ? " ★" : "") : "—"));
      }), el("tr", { class: "tot" }, el("td", { colspan: 5 }, "Σ"), el("td", { class: "num" }, eur(total))))),
      el("p", { class: "muted small" }, `★ ${ot("cheapest passing of its type")}`));
  },
};
window.ErismaCompare = { open: () => Opt.compare() };
window.Opt = Opt;

document.getElementById("btn-opt")?.addEventListener("click", () => Opt.open());
