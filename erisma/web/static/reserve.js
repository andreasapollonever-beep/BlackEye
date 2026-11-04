"use strict";
// Reserve factor λ on the loads and inverse solution on any input (see erisma/reserve.py).

const RUI = {
  el: {
    "📈 Reserve": "📈 Εφεδρεία", "How much more can it carry? — reserve and inverse solution":
      "Πόσο ακόμα αντέχει; — εφεδρεία και αντίστροφη λύση",
    "Reserve factor λ on the loads": "Συντελεστής εφεδρείας λ στα φορτία",
    "The chosen loads are multiplied by λ and the whole calculation is run again; λ is the largest factor for which every check that depends on the loads still passes.":
      "Τα φορτία που επιλέγετε πολλαπλασιάζονται επί λ και ξανατρέχει ολόκληρος ο υπολογισμός· λ είναι ο μεγαλύτερος συντελεστής για τον οποίο επαρκούν όλοι οι έλεγχοι που εξαρτώνται από τα φορτία.",
    "Calculate": "Υπολογισμός", "Calculating…": "Υπολογισμός…", "Close": "Κλείσιμο",
    "The chosen loads can be multiplied by": "Τα επιλεγμένα φορτία μπορούν να πολλαπλασιαστούν επί",
    "First to fail": "Πρώτος αστοχεί", "Verification": "Επαλήθευση", "passes": "επαρκεί", "fails": "αστοχεί",
    "Scaled inputs": "Πεδία που πολλαπλασιάστηκαν",
    "Loads computed by the program itself (e.g. self-weight of the member, earth pressure) are not scaled.":
      "Φορτία που υπολογίζει το ίδιο το πρόγραμμα (π.χ. ίδιο βάρος του μέλους, ωθήσεις γαιών) δεν πολλαπλασιάζονται.",
    "Not limited by the loads (unchanged utilisation)": "Δεν εξαρτώνται από τα φορτία (σταθερή αξιοποίηση)",
    "No check fails up to λ =": "Κανένας έλεγχος δεν αστοχεί έως λ =",
    "The calculation stops being valid (input or geometry limit):": "Ο υπολογισμός παύει να ισχύει (όριο δεδομένων ή γεωμετρίας):",
    "Inverse solution — range of one input": "Αντίστροφη λύση — εύρος ενός δεδομένου",
    "One input is varied over its range with everything else unchanged; the result is the interval in which every check passes.":
      "Ένα δεδομένο μεταβάλλεται στο εύρος του με όλα τα άλλα σταθερά· το αποτέλεσμα είναι το διάστημα στο οποίο επαρκούν όλοι οι έλεγχοι.",
    "Input": "Δεδομένο", "All checks pass for": "Όλοι οι έλεγχοι επαρκούν για",
    "from": "από", "to": "έως", "current value": "τρέχουσα τιμή", "lower limit": "κάτω όριο", "upper limit": "άνω όριο",
    "not limited within the range of the input": "δεν περιορίζεται μέσα στο εύρος του δεδομένου",
    "limited by": "το όριο θέτει", "Option": "Επιλογή", "Result": "Αποτέλεσμα", "PASS": "ΕΠΑΡΚΕΙ", "FAIL": "ΑΝΕΠΑΡΚΕΙ",
    "trials": "δοκιμές", "This calculation has no loads to scale.": "Ο υπολογισμός αυτός δεν έχει φορτία για πολλαπλασιασμό.",
    "Apply this value": "Εφαρμογή της τιμής",
  },
};
const rt = (k) => (LANG !== "en" && RUI[LANG]?.[k]) || t(k);
const num = (v, d = 3) => (v == null ? "—" : fmtNum(+(+v).toFixed(d)));

const Reserve = {
  async open() {
    const sp = await api(`/api/modules/${state.schema.id}/reserve`);
    const labels = Object.fromEntries(state.schema.fields.map((f) => [f.name, f]));
    const out1 = el("div", { class: "optout" });
    const out2 = el("div", { class: "optout" });
    const boxes = sp.groups.map((g) => {
      const c = el("input", { type: "checkbox", class: "chk" });
      c.checked = g !== "E";
      if (sp.groups.length === 1) c.checked = true;
      return { g, c, row: el("label", { class: "lrow" }, c, sp.group_labels[g]) };
    });
    const go1 = el("button", { type: "button", class: "primary" }, `📈 ${rt("Calculate")}`);
    const sel = el("select", {}, ...sp.fields.map((f) => el("option", { value: f.name },
      `${f.label}${f.unit ? ` [${f.unit}]` : ""}`)));
    const go2 = el("button", { type: "button", class: "primary" }, `🔍 ${rt("Calculate")}`);
    const sec1 = sp.groups.length
      ? [el("h4", {}, rt("Reserve factor λ on the loads")),
        el("p", { class: "muted small" }, rt("The chosen loads are multiplied by λ and the whole calculation is run again; λ is the largest factor for which every check that depends on the loads still passes.")),
        ...boxes.map((b) => b.row), el("div", { class: "btns" }, go1), out1]
      : [el("p", { class: "muted" }, rt("This calculation has no loads to scale."))];
    const d = el("dialog", { class: "linkdlg wide" }, el("h3", {}, rt("How much more can it carry? — reserve and inverse solution")),
      ...sec1, el("hr"),
      el("h4", {}, rt("Inverse solution — range of one input")),
      el("p", { class: "muted small" }, rt("One input is varied over its range with everything else unchanged; the result is the interval in which every check passes.")),
      el("label", { class: "lrow" }, rt("Input"), sel), el("div", { class: "btns" }, go2), out2,
      el("div", { class: "btns" }, el("button", { type: "button", class: "ghost", on: { click: () => d.close() } }, rt("Close"))));
    document.body.append(d);
    d.addEventListener("close", () => d.remove());
    d.showModal();

    const busy = (o) => { o.innerHTML = ""; o.append(el("p", { class: "busy" }, rt("Calculating…"))); };
    const fail = (o, err) => { o.innerHTML = ""; o.append(el("p", { class: "err" }, err.message)); if (err.license) { d.close(); licenseDialog(); } };

    go1.onclick = async () => {
      const groups = boxes.filter((b) => b.c.checked).map((b) => b.g);
      busy(out1); go1.disabled = true;
      try {
        const r = await api(`/api/modules/${state.schema.id}/reserve`, { inputs: state.inputs, project: state.project, mode: "loads", groups });
        out1.innerHTML = "";
        if (r.lam == null) {
          out1.append(el("p", { class: "big ok" }, `${rt("No check fails up to λ =")} ${num(r.beyond, 0)}`));
        } else {
          const pct = Math.round((r.lam - 1) * 100);
          out1.append(el("p", { class: `big ${r.lam >= 1 ? "ok" : "ko"}` },
            `${rt("The chosen loads can be multiplied by")} λ = ${num(r.lam, 3)} (${pct >= 0 ? "+" : ""}${pct} %)`));
          out1.append(r.limit_is_error
            ? el("p", {}, `${rt("The calculation stops being valid (input or geometry limit):")} ${r.governing}`)
            : el("p", {}, `${rt("First to fail")}: `, el("b", {}, r.governing), r.ref ? ` (${r.ref})` : ""));
          const v = r.verify;
          out1.append(el("p", { class: "small" }, `${rt("Verification")}: λ = ${num(v.at.lam, 5)} → U_max = ${num(v.at.umax, 5)} ≤ 1 (${rt("passes")}); `
            + `λ = ${num(v.beyond.lam, 5)} → ${v.beyond.umax == null ? v.beyond.gov : `U = ${num(v.beyond.umax, 5)} > 1`} (${rt("fails")})`));
        }
        out1.append(el("p", { class: "muted small" }, `${rt("Scaled inputs")}: ${r.fields.map((f) => labels[f.split(".")[0]]?.label + (f.includes(".") ? ` (${f.split(".")[1]})` : "")).join(", ")}. `
          + rt("Loads computed by the program itself (e.g. self-weight of the member, earth pressure) are not scaled.")));
        if (r.fixed?.length) {
          out1.append(el("details", { class: "small" }, el("summary", {}, `${rt("Not limited by the loads (unchanged utilisation)")} (${r.fixed.length})`),
            el("ul", {}, ...r.fixed.map(([dsc, u]) => el("li", {}, `${dsc}: U = ${num(u, 2)}`)))));
        }
        out1.append(el("p", { class: "muted small" }, `${r.evaluations} ${rt("trials")} · ${num(r.seconds, 2)} s`));
      } catch (err) { fail(out1, err); } finally { go1.disabled = false; }
    };

    go2.onclick = async () => {
      busy(out2); go2.disabled = true;
      const f = labels[sel.value];
      try {
        const r = await api(`/api/modules/${state.schema.id}/reserve`, { inputs: state.inputs, project: state.project, mode: "field", field: sel.value });
        out2.innerHTML = "";
        const unit = f?.unit ? ` ${f.unit}` : "";
        if (r.kind === "choice" || r.kind === "int") {
          out2.append(el("table", { class: "tbl cmp" }, el("thead", {}, el("tr", {}, el("th", {}, rt("Option")), el("th", {}, rt("Result")), el("th", {}, "U"), el("th", {}, rt("limited by")))),
            el("tbody", {}, ...r.rows.map((x) => el("tr", { class: String(x.value) === String(r.current) ? "best" : "" },
              el("td", {}, String(x.value)), el("td", { class: x.ok ? "ok" : "ko" }, rt(x.ok ? "PASS" : "FAIL")),
              el("td", { class: "num" }, num(x.umax, 2)), el("td", { class: "small" }, x.ok ? "" : x.gov))))));
        } else if (r.message) {
          out2.append(el("p", { class: "err" }, r.message));
        } else {
          const side = (b, name) => {
            if (!b) return el("li", {}, `${rt(name)}: ${rt("not limited within the range of the input")}`);
            if (b.range_end) return el("li", {}, `${rt(name)}: ${num(b.value, 4)}${unit} — ${rt("not limited within the range of the input")}`);
            return el("li", {}, `${rt(name)}: `, el("b", {}, `${num(b.value, 4)}${unit}`), ` — ${rt("limited by")} «${b.gov}» `
              + `(${rt("Verification")}: U = ${num(b.umax, 5)} ≤ 1 ${rt("passes")}, ${num(b.fail_at, 4)}${unit} → ${b.umax_beyond == null ? b.gov : `U = ${num(b.umax_beyond, 5)} > 1`} ${rt("fails")})`,
              el("button", { type: "button", class: "mini", on: { click: () => { state.inputs[sel.value] = +(+b.value).toPrecision(4); snapshot(); renderForm(); schedule(); d.close(); } } }, rt("Apply this value")));
          };
          out2.append(el("p", {}, `${rt("All checks pass for")} ${f?.label}: ${rt("from")} ${r.low && !r.low.range_end ? num(r.low.value, 4) : "…"} ${rt("to")} ${r.high && !r.high.range_end ? num(r.high.value, 4) : "…"}${unit} (${rt("current value")} ${num(r.current, 4)}${unit})`),
            el("ul", { class: "small" }, side(r.low, "lower limit"), side(r.high, "upper limit")));
        }
        out2.append(el("p", { class: "muted small" }, `${r.evaluations} ${rt("trials")}`));
      } catch (err) { fail(out2, err); } finally { go2.disabled = false; }
    };
  },
};
window.Reserve = Reserve;
document.getElementById("btn-reserve")?.addEventListener("click", () => Reserve.open());
