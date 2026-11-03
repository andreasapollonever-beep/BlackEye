"use strict";
// Erisma Structure — graphical workspace for whole buildings.
// The plan editor produces the inputs of the "building_frame" module (grid, storeys,
// walls and the "layout" of missing columns/beams, openings and member sizes); the
// calculation, report, 3D scene and licence are the same as everywhere in Erisma.
// The command ribbon follows the conventions of professional structural software
// (File · Home · Model · Loads · Seismic · Design · Results · View · Help).

Object.assign(UI.el, {
  "Erisma Structure": "Erisma Structure", "Member calculations": "Υπολογισμοί μελών",
  "Single members, foundations, retaining walls… — one calculation at a time.":
    "Μεμονωμένα μέλη, θεμελιώσεις, τοίχοι αντιστήριξης… — ένας υπολογισμός τη φορά.",
  "Whole buildings: draw the plan, get the 3D analysis, EC8 checks and the reinforcement of every member.":
    "Ολόκληρα κτίρια: σχεδιάστε την κάτοψη και πάρτε 3D ανάλυση, ελέγχους EC8 και τον οπλισμό κάθε μέλους.",
  "Open →": "Άνοιγμα →",
  // tabs
  "File": "Αρχείο", "Home": "Αρχική", "Model": "Μοντέλο", "Loads": "Φορτία", "Seismic": "Σεισμός",
  "Design": "Σχεδιασμός", "Results": "Αποτελέσματα", "View": "Προβολή", "Help": "Βοήθεια",
  // groups
  "Project": "Έργο", "Export": "Εξαγωγή", "Edit": "Επεξεργασία", "Selection": "Επιλογή",
  "Analysis": "Ανάλυση", "Views": "Προβολές", "Elements": "Στοιχεία", "Grid": "Κάνναβος",
  "Storeys": "Όροφοι", "Default sections": "Προεπιλεγμένες διατομές", "Area loads": "Φορτία επιφάνειας",
  "Line loads": "Γραμμικά φορτία", "Use": "Χρήση", "Site": "Τοποθεσία", "Structure": "Φορέας",
  "Analysis options": "Επιλογές ανάλυσης", "Materials": "Υλικά", "Options": "Επιλογές",
  "Member tables": "Πίνακες μελών", "Colour by": "Χρωματισμός", "Storey shown": "Όροφος προβολής",
  "Labels": "Ετικέτες", "Reports": "Τεύχη", "Navigate": "Πλοήγηση", "Show": "Εμφάνιση",
  "Window": "Παράθυρο", "Documentation": "Τεκμηρίωση",
  // buttons
  "New": "Νέο", "Open": "Άνοιγμα", "Save": "Αποθήκευση", "Print / PDF": "Εκτύπωση / PDF",
  "Report HTML": "Τεύχος HTML", "Table CSV": "Πίνακας CSV", "Undo": "Αναίρεση", "Redo": "Επανάληψη",
  "Delete": "Διαγραφή", "Select": "Επιλογή", "All columns": "Όλα τα υποστυλώματα",
  "All beams": "Όλες οι δοκοί", "All walls": "Όλα τα τοιχώματα", "Failing members": "Ανεπαρκή μέλη",
  "Clear": "Καθαρισμός", "Run": "Επίλυση", "Auto": "Αυτόματα", "Plan": "Κάτοψη", "Report": "Τεύχος",
  "Table": "Πίνακας", "Column": "Υποστύλωμα", "Wall X": "Τοίχωμα X", "Wall Y": "Τοίχωμα Y",
  "Beam": "Δοκός", "Opening": "Άνοιγμα πλάκας", "Grid wizard": "Οδηγός καννάβου",
  "+ Axis X": "+ Άξονας X", "+ Axis Y": "+ Άξονας Y", "− Axis X": "− Άξονας X", "− Axis Y": "− Άξονας Y",
  "+ Storey": "+ Όροφος", "− Storey": "− Όροφος", "Utilisation": "Εκμετάλλευση", "Steel ratio": "Ποσοστό οπλισμού",
  "Pass / fail": "Επάρκεια", "All storeys": "Όλοι οι όροφοι", "Reinforcement": "Οπλισμός",
  "Names": "Ονόματα", "Dimensions": "Διαστάσεις", "Axes": "Άξονες", "Slabs": "Πλάκες",
  "Zoom in": "Μεγέθυνση", "Zoom out": "Σμίκρυνση", "Fit": "Προσαρμογή", "Full screen": "Πλήρης οθόνη",
  "Theme": "Θέμα", "Manual": "Εγχειρίδιο", "Shortcuts": "Συντομεύσεις", "Modes": "Ιδιομορφές",
  "Storey checks": "Έλεγχοι ορόφων", "Quantities": "Ποσότητες", "Collapse ribbon": "Σύμπτυξη ribbon",
  "Seismic design": "Αντισεισμικός", "P-Δ": "P-Δ", "Capacity design": "Ικανοτικός", "Design members": "Διαστασιολόγηση",
  // tooltips / texts
  "Undo (Ctrl+Z)": "Αναίρεση (Ctrl+Z)", "Redo (Ctrl+Y)": "Επανάληψη (Ctrl+Y)",
  "Run the analysis (F5)": "Εκτέλεση ανάλυσης (F5)",
  "Re-analyse automatically after every change": "Αυτόματη επίλυση μετά από κάθε αλλαγή",
  "Changes not analysed — press Run (F5)": "Υπάρχουν αλλαγές χωρίς επίλυση — πατήστε Επίλυση (F5)",
  "Spans along X [m]": "Ανοίγματα κατά X [m]", "Spans along Y [m]": "Ανοίγματα κατά Y [m]",
  "Storey heights [m] (bottom up)": "Ύψη ορόφων [m] (από κάτω)", "Add": "Προσθήκη", "Remove": "Αφαίρεση",
  "Nothing selected": "Δεν έχει επιλεγεί στοιχείο",
  "Click a column, wall, beam or slab panel in the plan.": "Κάντε κλικ σε υποστύλωμα, τοίχωμα, δοκό ή φάτνωμα στην κάτοψη.",
  "Shift+click adds to the selection; drag a window to select several.": "Shift+κλικ προσθέτει στην επιλογή· σύρετε παράθυρο για πολλαπλή επιλογή.",
  "Width b [mm]": "Πλάτος b [mm]", "Depth h [mm]": "Ύψος h [mm]",
  "Side along X [mm]": "Πλευρά κατά X [mm]", "Side along Y [mm]": "Πλευρά κατά Y [mm]",
  "Length [m]": "Μήκος [m]", "Thickness [mm]": "Πάχος [mm]", "Direction": "Διεύθυνση",
  "Default size": "Προεπιλεγμένη διατομή", "Open in the member calculation": "Άνοιγμα στον υπολογισμό μέλους",
  "Slab panel": "Φάτνωμα πλάκας", "Open (no slab)": "Άνοιγμα (χωρίς πλάκα)", "Storey": "Όροφος",
  "Periods T [s]": "Ιδιοπερίοδοι T [s]", "Base shear [kN]": "Τέμνουσα βάσης [kN]",
  "Max drift d_r/h": "Μέγιστη σχετική μετακίνηση d_r/h", "Fails": "Ανεπαρκεί", "Passes": "Επαρκεί",
  "Click a grid point to place a column.": "Κάντε κλικ σε κόμβο του καννάβου για υποστύλωμα.",
  "Click a grid point to place a wall.": "Κάντε κλικ σε κόμβο του καννάβου για τοίχωμα.",
  "Click between two grid points to add or remove a beam.": "Κάντε κλικ ανάμεσα σε δύο κόμβους για να προσθέσετε ή να αφαιρέσετε δοκό.",
  "Click a slab panel to open or close it.": "Κάντε κλικ σε φάτνωμα για άνοιγμα / κλείσιμο.",
  "Calculating the building…": "Υπολογισμός του κτιρίου…", "Member": "Μέλος", "Wall": "Τοίχωμα",
  "Cost estimate": "Εκτίμηση κόστους", "Type": "Τύπος", "Section": "Διατομή", "Status": "Κατάσταση",
  "Only failing": "Μόνο ανεπαρκή", "Filter…": "Φίλτρο…", "selected": "επιλεγμένα",
  "Start a new building from the example? The current one will be replaced.":
    "Νέο κτίριο από το παράδειγμα; Το τρέχον θα αντικατασταθεί.",
  "Bays along X": "Φατνώματα κατά X", "Bays along Y": "Φατνώματα κατά Y", "Span X [m]": "Άνοιγμα X [m]",
  "Span Y [m]": "Άνοιγμα Y [m]", "Number of storeys": "Αριθμός ορόφων", "Storey height [m]": "Ύψος ορόφου [m]",
  "Create": "Δημιουργία", "Cancel": "Άκυρο",
  "A regular grid replaces the current one (walls and edits outside it are removed).":
    "Ένας κανονικός κάνναβος αντικαθιστά τον τρέχοντα (τοιχώματα και αλλαγές εκτός του αφαιρούνται).",
  "Messages": "Μηνύματα", "Properties": "Ιδιότητες", "Select all of this type": "Επιλογή όλων αυτού του τύπου",
  "Keyboard shortcuts": "Συντομεύσεις πληκτρολογίου", "Close": "Κλείσιμο",
  "Mode": "Ιδιομορφή", "θ": "θ", "Typical storey height [m]": "Τυπικό ύψος ορόφου [m]",
  "Ready": "Έτοιμο", "Members passing": "Επαρκή μέλη",
  "Apply to all selected": "Εφαρμογή σε όλα τα επιλεγμένα",
  // short labels of the ribbon controls (full label and help in the tooltip)
  "Column b_x": "Υποστ. b_x", "Column h_y": "Υποστ. h_y", "Beam b": "Δοκός b", "Beam h": "Δοκός h",
  "Slab t": "Πλάκα t", "Finishes g": "Επικαλύψεις g", "Imposed q": "Κινητό q", "Roof q": "Δώμα q",
  "Facade walls": "Τοιχοποιίες όψεων", "Category": "Κατηγορία", "Ground": "Έδαφος",
  "Importance": "Σπουδαιότητα", "EI cracked": "EI ρηγματ.", "Non-structural": "Μη φέροντα",
  "Concrete": "Σκυρόδεμα", "Cover": "Επικάλυψη",
  "Foundation": "Θεμελίωση", "Soil": "Έδαφος", "Type": "Τύπος", "Foundation beam": "Πεδιλοδοκός",
  "Footing": "Πέδιλο", "Slab": "Πλάκα", "Auto-size": "Αυτόματη διαστ.",
  "Enlarge members and adjust options until every Eurocode check passes":
    "Μεγέθυνση μελών και προσαρμογή επιλογών μέχρι να περάσουν όλοι οι έλεγχοι των Ευρωκωδίκων",
  "Automatic sizing…": "Αυτόματη διαστασιολόγηση…",
  "Running the complete calculation repeatedly — this can take a little while.":
    "Ο πλήρης υπολογισμός εκτελείται επανειλημμένα — μπορεί να διαρκέσει λίγο.",
  "All Eurocode checks pass after these changes:": "Όλοι οι έλεγχοι των Ευρωκωδίκων επαρκούν μετά από αυτές τις αλλαγές:",
  "Nothing to change — every check already passes.": "Δεν χρειάζεται αλλαγή — όλοι οι έλεγχοι ήδη επαρκούν.",
  "Still failing after the automatic changes — change these by hand:":
    "Εξακολουθούν να ανεπαρκούν μετά τις αυτόματες αλλαγές — αλλάξτε τα χειροκίνητα:",
  "Round": "Γύρος", "Apply": "Εφαρμογή", "Design slabs": "Πλάκες", "Design foundation": "Θεμελίωση",
  "Flange B": "Πέλμα B", "Web b_w": "Κορμός b_w", "Depth h": "Ύψος h", "k_s": "k_s", "D": "D",
  "φ'": "φ'", "c'": "c'", "γ": "γ", "Foundation beams": "Πεδιλοδοκοί",
  "Raft": "Κοιτόστρωση", "Thickness t": "Πάχος t", "Overhang": "Πρόβολος", "Mesh": "Πλέγμα",
  "Raft: demand / basic mesh": "Κοιτόστρωση: απαίτηση / βασικός οπλισμός",
  "additional bars": "πρόσθετος οπλισμός", "Punching": "Διάτρηση",
});
const SHORT = { col_b: "Column b_x", col_h: "Column h_y", beam_b: "Beam b", beam_h: "Beam h", slab_t: "Slab t",
  g_finish: "Finishes g", q: "Imposed q", q_roof: "Roof q", g_wall: "Facade walls", category: "Category",
  ag: "a_gR [g]", ground: "Ground", importance: "Importance", q_factor: "q", cracked: "EI cracked",
  drift: "Non-structural", n_modes: "Modes", phi_E: "φ (ψ_E)", concrete: "Concrete", fyk: "f_yk", cover: "Cover",
  found_type: "Type", raft_t: "Thickness t", raft_over: "Overhang", raft_mesh: "Mesh", fb_B: "Flange B", fb_bw: "Web b_w", fb_h: "Depth h", ks: "k_s", D_found: "D",
  phi_soil: "φ'", c_soil: "c'", gamma_soil: "γ" };

const Structure = (() => {
  const KEY = "erisma.structure";
  const VKEY = "erisma.structure.view";
  const S = { schema: null, inp: null, tool: "select", sel: [], res: null, view: "plan", tab: "home",
    hist: [], hpos: -1, timer: null, runId: 0, built: false, auto: true, dirty: false, vb: null,
    opt: { colour: "util", storey: "all", labels: false, names: true, dims: true, axes: true, slabs: true,
      ribbonMin: false, onlyFail: false, filter: "", sort: ["member", 1] } };
  Object.assign(S.opt, store.get(VKEY, {}));
  const saveView = () => store.set(VKEY, S.opt);

  // ------------------------------------------------------------ helpers
  const cum = (a) => a.reduce((o, v) => (o.push(o[o.length - 1] + v), o), [0]);
  const yLabel = (j) => { let s = ""; j += 1; while (j > 0) { const r = (j - 1) % 26; s = String.fromCharCode(65 + r) + s; j = Math.floor((j - 1) / 26); } return s; };
  const gl = (i, j) => `${yLabel(j)}${i + 1}`;
  const lay = () => (S.inp.layout ||= {});
  const arr = (k) => (lay()[k] ||= []);
  const obj = (k) => (lay()[k] ||= {});
  const field = (n) => S.schema.fields.find((f) => f.name === n);
  const shownIf = (f) => {   // "name" (bool switch) or "name=value"
    if (!f?.show_if) return true;
    const [k, v] = f.show_if.split("=");
    return v === undefined ? !!S.inp[k] : String(S.inp[k]) === v;
  };
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
  const isSel = (kind, id) => S.sel.some((s) => s.kind === kind && s.id === id);
  const KIND = () => ({ column: t("Column"), wall: t("Wall"), beam: t("Beam"), panel: t("Slab panel"),
    slab: t("Slab"), fbeam: t("Foundation beam"), footing: t("Footing") });

  // ------------------------------------------------------------ icons (24×24, stroke)
  const P = {
    new: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M12 11v6M9 14h6"/>',
    open: '<path d="M3 7h6l2 2h10v10H3z"/><path d="M3 11h18"/>',
    save: '<path d="M4 4h13l3 3v13H4z"/><path d="M8 4v5h7V4"/><rect x="7" y="13" width="10" height="7"/>',
    print: '<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="1"/><path d="M7 14h10v7H7z"/>',
    html: '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13 6l-2 12"/>',
    csv: '<rect x="4" y="4" width="16" height="16" rx="1"/><path d="M4 9h16M4 14h16M10 4v16"/>',
    undo: '<path d="M9 7L4 12l5 5"/><path d="M4 12h10a6 6 0 0 1 0 12"/>',
    redo: '<path d="M15 7l5 5-5 5"/><path d="M20 12H10a6 6 0 0 0 0 12"/>',
    del: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    select: '<path d="M5 3l12 8-6 1 3 7-2 1-3-7-4 4z"/>',
    selcol: '<rect x="4" y="4" width="5" height="5"/><rect x="15" y="4" width="5" height="5"/><rect x="4" y="15" width="5" height="5"/><rect x="15" y="15" width="5" height="5"/>',
    selbeam: '<path d="M3 6h18M3 18h18M6 3v18M18 3v18" stroke-width="2.6"/>',
    selwall: '<rect x="3" y="9" width="18" height="6"/>',
    selfail: '<circle cx="12" cy="12" r="8"/><path d="M12 7v6M12 16v1"/>',
    clear: '<path d="M5 5l14 14M19 5L5 19"/>',
    run: '<path d="M7 4l13 8-13 8z"/>',
    auto: '<path d="M4 12a8 8 0 0 1 14-5l2-2v6h-6l2-2a5 5 0 1 0 1 5"/>',
    plan: '<rect x="3" y="3" width="18" height="18"/><path d="M3 12h18M12 3v18"/>',
    cube: '<path d="M12 2l9 5v10l-9 5-9-5V7z"/><path d="M12 22V12M3 7l9 5 9-5"/>',
    report: '<path d="M6 3h12v18H6z"/><path d="M9 8h6M9 12h6M9 16h4"/>',
    table: '<rect x="3" y="4" width="18" height="16"/><path d="M3 9h18M3 14h18M9 4v16"/>',
    column: '<rect x="8" y="8" width="8" height="8" fill="currentColor"/><path d="M3 12h5M16 12h5M12 3v5M12 16v5" stroke-dasharray="2 2"/>',
    wallx: '<rect x="3" y="9.5" width="18" height="5" fill="currentColor"/>',
    wally: '<rect x="9.5" y="3" width="5" height="18" fill="currentColor"/>',
    beam: '<path d="M3 12h18" stroke-width="4"/><rect x="2" y="9" width="4" height="6" fill="currentColor"/><rect x="18" y="9" width="4" height="6" fill="currentColor"/>',
    opening: '<rect x="4" y="4" width="16" height="16"/><path d="M4 12l8-8M4 20L20 4M12 20l8-8"/>',
    grid: '<path d="M3 8h18M3 16h18M8 3v18M16 3v18"/>',
    axisx: '<path d="M4 4v16M12 4v16M20 4v16" stroke-dasharray="3 2"/><circle cx="20" cy="4" r="2"/>',
    axisy: '<path d="M4 4h16M4 12h16M4 20h16" stroke-dasharray="3 2"/><circle cx="20" cy="20" r="2"/>',
    storeyadd: '<path d="M4 20h16M4 14h16M4 8h16M6 8v12M18 8v12"/><path d="M12 1v5M9.5 3.5h5"/>',
    storeydel: '<path d="M4 20h16M4 14h16M6 14v6M18 14v6"/><path d="M9 6h6"/>',
    zin: '<circle cx="10" cy="10" r="6"/><path d="M15 15l6 6M7 10h6M10 7v6"/>',
    zout: '<circle cx="10" cy="10" r="6"/><path d="M15 15l6 6M7 10h6"/>',
    fit: '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>',
    full: '<path d="M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6"/>',
    theme: '<circle cx="12" cy="12" r="5"/><path d="M12 1v3M12 20v3M1 12h3M20 12h3"/>',
    manual: '<path d="M4 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4z"/><path d="M20 4h-4a2 2 0 0 0-2 2"/>',
    keys: '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h1M10 10h1M14 10h1M18 10h1M7 14h10"/>',
    modes: '<path d="M4 20V4"/><path d="M4 20c6-2 10-8 12-16"/><path d="M4 20c3-4 8-6 16-6" stroke-dasharray="2 2"/>',
    drift: '<path d="M6 21V3M6 3l10 3M6 9l8 2M6 15l5 1"/>',
    qty: '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
    tag: '<path d="M3 12V3h9l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    min: '<path d="M6 15l6-6 6 6"/>',
    autosize: '<path d="M4 20L20 4"/><path d="M14 4h6v6"/><rect x="3" y="13" width="8" height="8"/><path d="M15 15l2 2 4-4"/>',
    found: '<path d="M3 20h18"/><rect x="5" y="14" width="14" height="4"/><path d="M9 14V4h6v10"/>',
  };
  const icon = (k) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${P[k] || ""}</svg>`;

  // ------------------------------------------------------------ history / persistence
  function commit(rerun = true) {
    const snap = JSON.stringify(S.inp);
    if (S.hist[S.hpos] !== snap) {
      S.hist = S.hist.slice(0, S.hpos + 1);
      S.hist.push(snap);
      if (S.hist.length > 150) S.hist.shift();
      S.hpos = S.hist.length - 1;
    }
    store.set(KEY, S.inp);
    redraw();
    if (rerun) changed();
  }
  function changed() {
    if (S.auto) schedule();
    else { S.dirty = true; statusDirty(); }
  }
  function undo(dir) {
    const p = S.hpos + dir;
    if (p < 0 || p >= S.hist.length) return;
    S.hpos = p;
    S.inp = JSON.parse(S.hist[p]);
    store.set(KEY, S.inp);
    prune();
    renderSettings(); renderRibbon(); redraw(); changed();
  }
  function redraw() { drawPlan(); renderProps(); if (S.view === "table") renderTable(); }

  // ------------------------------------------------------------ page skeleton
  function build() {
    if (S.built) return;
    S.built = true;
    const root = $("#structure");
    root.innerHTML = "";
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.id = "st-plan";
    root.append(
      el("div", { class: "rb", id: "st-ribbon" }),
      el("div", { class: "st-body" },
        el("aside", { class: "st-left", id: "st-settings" }),
        el("div", { class: "st-center" },
          el("div", { class: "st-pane on", "data-pane": "plan" }, el("div", { class: "st-hint", id: "st-hint" }), svg,
            el("div", { class: "st-zoom" },
              ...[["zin", "Zoom in", () => zoom(0.8)], ["zout", "Zoom out", () => zoom(1.25)], ["fit", "Fit", fit]]
                .map(([ic, tt, fn]) => { const b = el("button", { type: "button", title: t(tt), on: { click: fn } }); b.innerHTML = icon(ic); return b; }))),
          el("div", { class: "st-pane", "data-pane": "3d" }, el("div", { id: "st-3d" })),
          el("div", { class: "st-pane", "data-pane": "report" }, el("iframe", { id: "st-report", title: "Report" })),
          el("div", { class: "st-pane", "data-pane": "table" }, el("div", { id: "st-table", class: "st-tablewrap" }))),
        el("aside", { class: "st-right" },
          el("div", { id: "st-status", role: "status", "aria-live": "polite" }),
          el("div", { id: "st-props" }),
          el("div", { id: "st-summary" }))),
      el("div", { class: "st-sbar" },
        el("span", { id: "sb-tool" }), el("span", { id: "sb-sel" }), el("span", { id: "sb-xy" }),
        el("span", { id: "sb-msg", class: "grow" }), el("span", { id: "sb-units" }, "kN · m · mm")),
      el("div", { class: "st-menu", id: "st-menu", hidden: "" }));
    S.svg = svg;
    planEvents();
    document.addEventListener("keydown", onKey);
    document.addEventListener("click", () => { $("#st-menu").hidden = true; });
    new ResizeObserver(() => S.view === "plan" && drawPlan()).observe(root.querySelector(".st-center"));
  }

  // ------------------------------------------------------------ ribbon
  function btn(ic, label, title, fn, { big = false, on = false, disabled = false } = {}) {
    const b = el("button", { type: "button", class: `rb-btn${big ? " big" : ""}${on ? " on" : ""}`,
      title: title || label, on: { click: fn } });
    if (disabled) b.disabled = true;
    b.innerHTML = `${icon(ic)}<span>${label}</span>`;
    return b;
  }
  function ctl(name, { width = 70, label } = {}) {
    const f = field(name);
    if (!f) return "";
    if (!(name in S.inp)) S.inp[name] = structuredClone(f.default);
    const input = scalarInput(f, S.inp[name], (v) => {
      S.inp[name] = v;
      if (S.schema.fields.some((x) => x.show_if && x.show_if.split("=")[0] === name)) renderRibbon();
      renderSettings();
      commit();
    });
    input.style.width = `${width}px`;
    const hidden = !shownIf(f);
    const lab = el("label", { class: `rb-ctl${hidden ? " off" : ""}`, title: f.help ? `${f.label} — ${f.help}` : f.label },
      el("span", {}, label || (SHORT[name] ? t(SHORT[name]) : f.label)), input, el("small", {}, f.unit || ""));
    if (hidden) input.disabled = true;
    return lab;
  }
  function tog(name, label) {
    const f = field(name);
    const cb = el("input", { type: "checkbox", on: { change: (e) => {
      S.inp[name] = e.target.checked; renderRibbon(); renderSettings(); commit();
    } } });
    cb.checked = !!S.inp[name];
    if (!shownIf(f)) cb.disabled = true;
    return el("label", { class: "rb-chk", title: f?.help || label }, cb, el("span", {}, label));
  }
  function viewTog(key, label, fn) {
    const cb = el("input", { type: "checkbox", on: { change: (e) => { S.opt[key] = e.target.checked; saveView(); (fn || drawPlan)(); } } });
    cb.checked = !!S.opt[key];
    return el("label", { class: "rb-chk" }, cb, el("span", {}, label));
  }
  const group = (label, ...items) => el("div", { class: "rb-grp" }, el("div", { class: "rb-items" }, ...items), el("div", { class: "rb-gl" }, label));
  const col = (...items) => el("div", { class: "rb-col" }, ...items);

  function tabs() {
    const tl = (id) => S.tool === id;
    const v = (id) => S.view === id;
    const nStorey = S.inp.storeys.length;
    return [
      ["file", t("File"), [
        group(t("Project"), btn("new", t("New"), t("Start a new building from the example? The current one will be replaced."), newBuilding, { big: true }),
          btn("open", t("Open"), `${t("Open")} (Ctrl+O)`, () => $("#file-open").click(), { big: true }),
          btn("save", t("Save"), `${t("Save")} (Ctrl+S)`, save, { big: true })),
        group(t("Export"), btn("print", t("Print / PDF"), `${t("Print / PDF")} (Ctrl+P)`, print, { big: true }),
          col(btn("html", t("Report HTML"), "", html), btn("csv", t("Table CSV"), "", csv))),
      ]],
      ["home", t("Home"), [
        group(t("Edit"), col(btn("undo", t("Undo"), t("Undo (Ctrl+Z)"), () => undo(-1), { disabled: S.hpos <= 0 }),
          btn("redo", t("Redo"), t("Redo (Ctrl+Y)"), () => undo(1), { disabled: S.hpos >= S.hist.length - 1 }),
          btn("del", t("Delete"), `${t("Delete")} (Del)`, removeSel, { disabled: !S.sel.length }))),
        group(t("Selection"), btn("select", t("Select"), `${t("Select")} (V)`, () => setTool("select"), { big: true, on: tl("select") }),
          col(btn("selcol", t("All columns"), "", () => selectAll("column")), btn("selbeam", t("All beams"), "", () => selectAll("beam")),
            btn("selwall", t("All walls"), "", () => selectAll("wall"))),
          col(btn("selfail", t("Failing members"), "", selectFailing), btn("clear", t("Clear"), "Esc", () => setSel([])))),
        group(t("Analysis"), btn("run", t("Run"), t("Run the analysis (F5)"), () => run(), { big: true, on: S.dirty }),
          btn("auto", t("Auto"), t("Re-analyse automatically after every change"), () => { S.auto = !S.auto; renderRibbon(); if (S.auto && S.dirty) run(); }, { big: true, on: S.auto }),
          btn("autosize", t("Auto-size"), t("Enlarge members and adjust options until every Eurocode check passes"), autoSize, { big: true })),
        group(t("Views"), btn("plan", t("Plan"), t("Plan"), () => setView("plan"), { big: true, on: v("plan") }),
          btn("cube", "3D", "3D (Ctrl+3)", () => setView("3d"), { big: true, on: v("3d") }),
          btn("table", t("Table"), t("Table"), () => setView("table"), { big: true, on: v("table") }),
          btn("report", t("Report"), t("Report"), () => setView("report"), { big: true, on: v("report") })),
      ]],
      ["model", t("Model"), [
        group(t("Elements"), btn("select", t("Select"), `${t("Select")} (V)`, () => setTool("select"), { big: true, on: tl("select") }),
          btn("column", t("Column"), `${t("Click a grid point to place a column.")} (C)`, () => setTool("column"), { big: true, on: tl("column") }),
          btn("wallx", t("Wall X"), `${t("Click a grid point to place a wall.")} (W)`, () => setTool("wallX"), { big: true, on: tl("wallX") }),
          btn("wally", t("Wall Y"), `${t("Click a grid point to place a wall.")} (W)`, () => setTool("wallY"), { big: true, on: tl("wallY") }),
          btn("beam", t("Beam"), `${t("Click between two grid points to add or remove a beam.")} (B)`, () => setTool("beam"), { big: true, on: tl("beam") }),
          btn("opening", t("Opening"), `${t("Click a slab panel to open or close it.")} (O)`, () => setTool("opening"), { big: true, on: tl("opening") })),
        group(t("Grid"), btn("grid", t("Grid wizard"), t("A regular grid replaces the current one (walls and edits outside it are removed)."), gridWizard, { big: true }),
          col(btn("axisx", t("+ Axis X"), "", () => axis("x_spans", 1)), btn("axisx", t("− Axis X"), "", () => axis("x_spans", -1))),
          col(btn("axisy", t("+ Axis Y"), "", () => axis("y_spans", 1)), btn("axisy", t("− Axis Y"), "", () => axis("y_spans", -1)))),
        group(`${t("Storeys")} (${nStorey})`, col(btn("storeyadd", t("+ Storey"), "", () => storey(1)), btn("storeydel", t("− Storey"), "", () => storey(-1), { disabled: nStorey <= 1 }))),
        group(t("Default sections"), col(ctl("col_b", { width: 62 }), ctl("col_h", { width: 62 })),
          col(ctl("beam_b", { width: 62 }), ctl("beam_h", { width: 62 })), col(ctl("slab_t", { width: 62 }))),
      ]],
      ["loads", t("Loads"), [
        group(t("Area loads"), col(ctl("g_finish"), ctl("q")), col(ctl("q_roof"))),
        group(t("Line loads"), col(ctl("g_wall"))),
        group(t("Use"), col(ctl("category", { width: 60 }))),
      ]],
      ["seismic", t("Seismic"), [
        group(t("Seismic design"), col(tog("seismic", "EN 1998-1"))),
        group(t("Site"), col(ctl("ag"), ctl("ground", { width: 56 })), col(ctl("importance", { width: 56 }))),
        group(t("Structure"), col(ctl("q_factor"), ctl("cracked")), col(ctl("drift", { width: 190 }))),
        group(t("Analysis options"), col(ctl("n_modes"), ctl("phi_E")), col(tog("pdelta", t("P-Δ")))),
      ]],
      ["design", t("Design"), [
        group(t("Materials"), col(ctl("concrete", { width: 86 }), ctl("fyk")), col(ctl("cover"))),
        group(t("Options"), col(tog("design", t("Design members")), tog("capacity", t("Capacity design"))),
          col(tog("slabs", t("Design slabs")), tog("foundations", t("Design foundation")))),
        group(t("Auto-size"), btn("autosize", t("Auto-size"), t("Enlarge members and adjust options until every Eurocode check passes"), autoSize, { big: true })),
        group(t("Member tables"), btn("table", t("Table"), "", () => setView("table"), { big: true, on: v("table") }),
          btn("selfail", t("Failing members"), "", selectFailing, { big: true }), btn("csv", t("Table CSV"), "", csv, { big: true })),
      ]],
      ["found", t("Foundation"), [
        group(t("Foundation"), col(tog("foundations", t("Design foundation")), ctl("found_type", { width: 170 }))),
        group(t("Raft"), col(ctl("raft_t"), ctl("raft_over")), col(ctl("raft_mesh"), ctl("ks"))),
        group(t("Foundation beams"), col(ctl("fb_B"), ctl("fb_bw")), col(ctl("fb_h"))),
        group(t("Soil"), col(ctl("D_found"), ctl("phi_soil")), col(ctl("c_soil"), ctl("gamma_soil"))),
        group(t("View"), btn("found", t("Foundation"), "", () => { S.opt.storey = "found"; saveView(); setView("plan"); }, { big: true, on: S.opt.storey === "found" })),
      ]],
      ["results", t("Results"), [
        group(t("Colour by"), col(...[["util", t("Utilisation")], ["rho", t("Steel ratio")], ["status", t("Pass / fail")]]
          .map(([k, lab]) => { const r = el("input", { type: "radio", name: "rb-col", on: { change: () => { S.opt.colour = k; saveView(); drawPlan(); } } }); r.checked = S.opt.colour === k; return el("label", { class: "rb-chk" }, r, el("span", {}, lab)); }))),
        group(t("Storey shown"), col((() => {
          const s = el("select", { on: { change: (e) => { S.opt.storey = e.target.value; saveView(); drawPlan(); } } },
            el("option", { value: "all" }, t("All storeys")), ...S.inp.storeys.map((_, k) => el("option", { value: String(k + 1) }, `${t("Storey")} ${k + 1}`)),
            el("option", { value: "found" }, t("Foundation")));
          s.value = S.opt.storey in { all: 1, found: 1 } || +S.opt.storey <= nStorey ? S.opt.storey : "all";
          return s;
        })())),
        group(t("Labels"), col(viewTog("labels", t("Reinforcement")), viewTog("names", t("Names")))),
        group(t("Reports"), btn("modes", t("Modes"), "", () => gotoReport("Masses and modal analysis"), { big: true }),
          btn("drift", t("Storey checks"), "", () => gotoReport("Storey checks"), { big: true }),
          btn("qty", t("Quantities"), "", () => gotoReport("Quantities and cost estimate"), { big: true }),
          btn("report", t("Report"), "", () => setView("report"), { big: true })),
      ]],
      ["view", t("View"), [
        group(t("Views"), btn("plan", t("Plan"), "", () => setView("plan"), { big: true, on: v("plan") }),
          btn("cube", "3D", "Ctrl+3", () => setView("3d"), { big: true, on: v("3d") }),
          btn("table", t("Table"), "", () => setView("table"), { big: true, on: v("table") }),
          btn("report", t("Report"), "", () => setView("report"), { big: true, on: v("report") })),
        group(t("Navigate"), btn("zin", t("Zoom in"), `${t("Zoom in")} (+)`, () => zoom(0.8), { big: true }),
          btn("zout", t("Zoom out"), `${t("Zoom out")} (−)`, () => zoom(1.25), { big: true }),
          btn("fit", t("Fit"), `${t("Fit")} (F)`, fit, { big: true })),
        group(t("Show"), col(viewTog("axes", t("Axes")), viewTog("dims", t("Dimensions"))), col(viewTog("names", t("Names")), viewTog("slabs", t("Slabs"))), col(viewTog("labels", t("Reinforcement")))),
        group(t("Window"), btn("full", t("Full screen"), "F11", fullScreen, { big: true }),
          btn("theme", t("Theme"), "", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"), { big: true })),
      ]],
      ["help", t("Help"), [
        group(t("Documentation"), btn("manual", t("Manual"), "F1", () => window.open(`/manual?lang=${LANG}#structure`, "_blank"), { big: true }),
          btn("keys", t("Shortcuts"), "?", shortcuts, { big: true })),
      ]],
    ];
  }

  function renderRibbon() {
    const box = $("#st-ribbon");
    if (!box || !S.schema) return;
    const all = tabs();
    if (!all.some(([id]) => id === S.tab)) S.tab = "home";
    box.innerHTML = "";
    box.classList.toggle("min", !!S.opt.ribbonMin);
    const qat = el("div", { class: "rb-qat" },
      ...[["save", `${t("Save")} (Ctrl+S)`, save], ["undo", t("Undo (Ctrl+Z)"), () => undo(-1)], ["redo", t("Redo (Ctrl+Y)"), () => undo(1)],
        ["run", t("Run the analysis (F5)"), () => run()]].map(([ic, tt, fn]) => {
        const b = el("button", { type: "button", title: tt, on: { click: fn } }); b.innerHTML = icon(ic); return b;
      }));
    const tabsRow = el("div", { class: "rb-tabs" }, qat,
      ...all.map(([id, label]) => el("button", { type: "button", class: `rb-tab${id === S.tab ? " on" : ""}${id === "file" ? " file" : ""}`,
        on: { click: () => { S.tab = id; if (S.opt.ribbonMin) { S.opt.ribbonMin = false; saveView(); } renderRibbon(); },
          dblclick: () => { S.opt.ribbonMin = !S.opt.ribbonMin; saveView(); renderRibbon(); } } }, label)),
      el("span", { class: "grow" }),
      el("span", { class: "rb-title" }, "Erisma Structure"),
      (() => { const b = el("button", { type: "button", class: "rb-min", title: t("Collapse ribbon"), on: { click: () => { S.opt.ribbonMin = !S.opt.ribbonMin; saveView(); renderRibbon(); } } }); b.innerHTML = icon("min"); return b; })());
    box.append(tabsRow);
    const body = el("div", { class: "rb-body" }, ...all.find(([id]) => id === S.tab)[2]);
    box.append(body);
  }

  // ------------------------------------------------------------ tools, views, selection
  const HINTS = () => ({ select: `${t("Click a column, wall, beam or slab panel in the plan.")} ${t("Shift+click adds to the selection; drag a window to select several.")}`,
    column: t("Click a grid point to place a column."), wallX: t("Click a grid point to place a wall."),
    wallY: t("Click a grid point to place a wall."), beam: t("Click between two grid points to add or remove a beam."),
    opening: t("Click a slab panel to open or close it.") });
  const TOOLN = () => ({ select: t("Select"), column: t("Column"), wallX: t("Wall X"), wallY: t("Wall Y"), beam: t("Beam"), opening: t("Opening") });
  function setTool(id) {
    S.tool = id;
    $("#st-hint").textContent = HINTS()[id];
    $("#sb-tool").textContent = `✎ ${TOOLN()[id]}`;
    if (S.view !== "plan") setView("plan");
    renderRibbon();
  }
  function setView(v) {
    S.view = v;
    document.querySelectorAll(".st-pane").forEach((p) => p.classList.toggle("on", p.dataset.pane === v));
    if (v === "3d") window.dispatchEvent(new CustomEvent("erisma:show3d", { detail: { host: "st-3d" } }));
    if (v === "plan") drawPlan();
    if (v === "table") renderTable();
    renderRibbon();
  }
  function setSel(list) {
    S.sel = list;
    redraw();
    $("#sb-sel").textContent = S.sel.length ? `${S.sel.length} ${t("selected")}` : "";
    renderRibbon();
  }
  function allIds(kind) {
    const { nx, ny } = geom();
    const L = lay(), out = [];
    const omitC = new Set(L.omit_columns || []), omitB = new Set(L.omit_beams || []);
    if (kind === "column" || kind === "wall") {
      for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
        const g = gl(i, j), w = wallAt(g);
        if (kind === "wall" ? w : !w && !omitC.has(g)) out.push(g);
      }
    } else if (kind === "beam") {
      for (let j = 0; j < ny; j++) for (let i = 0; i < nx - 1; i++) out.push(`${gl(i, j)}-${gl(i + 1, j)}`);
      for (let i = 0; i < nx; i++) for (let j = 0; j < ny - 1; j++) out.push(`${gl(i, j)}-${gl(i, j + 1)}`);
      return out.filter((id) => !omitB.has(id));
    }
    return out;
  }
  const selectAll = (kind) => { setView("plan"); setSel(allIds(kind).map((id) => ({ kind, id }))); };
  function selectFailing() {
    const m = S.res?.structure?.members || {};
    const seen = new Set(), out = [];
    for (const [k, v] of Object.entries(m)) if (!v.ok) {
      const id = k.slice(k.indexOf(".") + 1);
      const kind = { beam: "beam", wall: "wall", slab: "panel", column: "column" }[v.kind];
      if (kind && !seen.has(kind + id)) { seen.add(kind + id); out.push({ kind, id }); }
    }
    setView("plan"); setSel(out);
  }

  function onKey(e) {
    if (!document.body.classList.contains("in-structure")) return;
    if (e.key === "F5") { e.preventDefault(); run(); return; }
    if (e.target.closest("input,select,textarea")) return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "a") { e.preventDefault(); selectAll("column"); return; }
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key.toLowerCase();
    const map = { v: "select", c: "column", b: "beam", o: "opening" };
    if (map[k]) { setTool(map[k]); e.preventDefault(); }
    else if (k === "w") { setTool(S.tool === "wallX" ? "wallY" : "wallX"); e.preventDefault(); }
    else if (k === "f") { fit(); e.preventDefault(); }
    else if (k === "+" || k === "=") { zoom(0.8); e.preventDefault(); }
    else if (k === "-") { zoom(1.25); e.preventDefault(); }
    else if (k === "?") { shortcuts(); e.preventDefault(); }
    else if ((e.key === "Delete" || e.key === "Backspace") && S.sel.length) { removeSel(); e.preventDefault(); }
    else if (e.key === "Escape") { setSel([]); $("#st-menu").hidden = true; }
  }

  // ------------------------------------------------------------ settings panel (left): grid & storeys
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
          if (rows.length > 1) { rows.splice(n, 1); prune(); renderSettings(); renderRibbon(); commit(); }
        } } }, "×")));
    });
    box.append(el("button", { type: "button", class: "mini add", on: { click: () => {
      rows.push(structuredClone(rows[rows.length - 1])); renderSettings(); renderRibbon(); commit();
    } } }, `+ ${t("Add")}`));
    return box;
  }
  function renderSettings() {
    const box = $("#st-settings");
    if (!box) return;
    box.innerHTML = "";
    box.append(el("div", { class: "st-ptitle" }, t("Grid")),
      listEditor(t("Spans along X [m]"), "x_spans", 1, 15),
      listEditor(t("Spans along Y [m]"), "y_spans", 1, 15),
      el("div", { class: "st-ptitle" }, t("Storeys")),
      listEditor(t("Storey heights [m] (bottom up)"), "storeys", 2, 8));
    const st = S.res?.structure?.storeys || [];
    if (st.length) {
      const tb = el("table", { class: "st-res" }, el("tr", {}, el("th", {}, t("Storey")), el("th", {}, "d_r/h X"), el("th", {}, "d_r/h Y"), el("th", {}, "θ")));
      for (const s of st) {
        tb.append(el("tr", {}, el("td", {}, String(s.index)), el("td", {}, `${(s.drift.X * 1000).toFixed(2)}‰`),
          el("td", {}, `${(s.drift.Y * 1000).toFixed(2)}‰`), el("td", {}, Math.max(s.theta.X, s.theta.Y).toFixed(3))));
      }
      box.append(el("div", { class: "st-ptitle" }, t("Storey checks")), tb);
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
    S.sel = S.sel.filter((s) => (s.kind === "beam" ? segs : s.kind === "panel" ? pans : pts).has(s.id));
  }

  // ------------------------------------------------------------ model commands
  function axis(key, dir) {
    const rows = S.inp[key];
    if (dir > 0) rows.push(structuredClone(rows[rows.length - 1]));
    else if (rows.length > 1) rows.pop();
    prune(); renderSettings(); renderRibbon(); commit(); fit();
  }
  function storey(dir) {
    const rows = S.inp.storeys;
    if (dir > 0) rows.push(structuredClone(rows[rows.length - 1]));
    else if (rows.length > 1) rows.pop();
    renderSettings(); renderRibbon(); commit();
  }
  function gridWizard() {
    const v = { nx: S.inp.x_spans.length, lx: S.inp.x_spans[0].L, ny: S.inp.y_spans.length, ly: S.inp.y_spans[0].L,
      ns: S.inp.storeys.length, h: S.inp.storeys[S.inp.storeys.length - 1].h };
    const row = (k, label, min, max, step) => el("label", { class: "st-f" }, el("span", {}, label),
      el("span", { class: "inp" }, el("input", { type: "number", min, max, step, value: v[k], "data-k": k })));
    const dlg = el("dialog", { class: "st-dlg" },
      el("h3", {}, t("Grid wizard")), el("p", { class: "muted" }, t("A regular grid replaces the current one (walls and edits outside it are removed).")),
      row("nx", t("Bays along X"), 1, 20, 1), row("lx", t("Span X [m]"), 1, 15, 0.05),
      row("ny", t("Bays along Y"), 1, 20, 1), row("ly", t("Span Y [m]"), 1, 15, 0.05),
      row("ns", t("Number of storeys"), 1, 30, 1), row("h", t("Storey height [m]"), 2, 8, 0.05),
      el("div", { class: "btns" },
        el("button", { type: "button", class: "ghost", on: { click: () => dlg.close() } }, t("Cancel")),
        el("button", { type: "button", class: "primary", on: { click: () => {
          const g = {};
          for (const i of dlg.querySelectorAll("input")) g[i.dataset.k] = parseFloat(i.value);
          if (!(g.nx >= 1 && g.ny >= 1 && g.ns >= 1 && g.lx >= 1 && g.ly >= 1 && g.h >= 2)) return;
          S.inp.x_spans = Array.from({ length: Math.round(g.nx) }, () => ({ L: g.lx }));
          S.inp.y_spans = Array.from({ length: Math.round(g.ny) }, () => ({ L: g.ly }));
          S.inp.storeys = Array.from({ length: Math.round(g.ns) }, () => ({ h: g.h }));
          prune(); dlg.close(); renderSettings(); renderRibbon(); commit(); fit();
        } } }, t("Create"))));
    document.body.append(dlg);
    dlg.addEventListener("close", () => dlg.remove());
    dlg.showModal();
  }
  function shortcuts() {
    const rows = [["V", t("Select")], ["C", t("Column")], ["W", `${t("Wall X")} / ${t("Wall Y")}`], ["B", t("Beam")],
      ["O", t("Opening")], ["Shift + click", t("Shift+click adds to the selection; drag a window to select several.")],
      ["Del", t("Delete")], ["Esc", t("Clear")], ["Ctrl+Z / Ctrl+Y", `${t("Undo")} / ${t("Redo")}`], ["Ctrl+A", t("All columns")],
      ["F5", t("Run")], ["Ctrl+3", "3D"], ["+ / − / F", `${t("Zoom in")} / ${t("Zoom out")} / ${t("Fit")}`],
      [t("Wheel / middle button"), `${t("Zoom in")} / Pan`], ["Ctrl+S / Ctrl+O / Ctrl+P", `${t("Save")} / ${t("Open")} / ${t("Print / PDF")}`]];
    const dlg = el("dialog", { class: "st-dlg" }, el("h3", {}, t("Keyboard shortcuts")),
      el("table", { class: "st-res" }, ...rows.map(([k, d]) => el("tr", {}, el("td", {}, el("kbd", {}, k)), el("td", {}, d)))),
      el("div", { class: "btns" }, el("button", { type: "button", class: "primary", on: { click: () => dlg.close() } }, t("Close"))));
    document.body.append(dlg);
    dlg.addEventListener("close", () => dlg.remove());
    dlg.showModal();
  }
  const fullScreen = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.());
  function gotoReport(heading) {
    setView("report");
    const doc = $("#st-report").contentDocument;
    const want = t(heading) === heading ? heading : t(heading);
    const h = [...(doc?.querySelectorAll("h1,h2,h3") || [])].find((x) => x.textContent.includes(want) || x.textContent.includes(heading));
    h?.scrollIntoView({ block: "start" });
  }

  // ------------------------------------------------------------ results per plan element
  function resultsFor(kind, id) {
    const m = S.res?.structure?.members || {};
    const pref = { beam: "B", wall: "W", column: "C", panel: "S", slab: "S", fbeam: "FB", footing: "F" }[kind];
    return Object.entries(m).filter(([k]) => k.split(".")[0].replace(/\d+$/, "") === pref && k.slice(k.indexOf(".") + 1) === id)
      .map(([k, v]) => ({ id: k, ...v })).sort((a, b) => a.storey - b.storey);
  }
  function shown(kind, id) {
    const r = resultsFor(kind, id);
    if (S.opt.storey === "all" || S.opt.storey === "found" || ["wall", "fbeam", "footing"].includes(kind)) return r;
    return r.filter((x) => String(x.storey) === S.opt.storey);
  }
  function colourFor(kind, id) {
    const r = shown(kind, id);
    if (!r.length) return null;
    if (r.some((x) => !x.ok)) return "#e03b3b";
    if (S.opt.colour === "status") return "#2e9b5f";
    if (S.opt.colour === "rho") {
      const rho = Math.max(...r.map((x) => x.rho));
      const tt = kind === "column" ? (rho - 0.01) / 0.03 : kind === "wall" ? rho / 0.02 : kind === "panel" ? rho / 0.006 : rho / 0.03;
      return heat(0.85 * tt);
    }
    return heat(0.85 * Math.max(...r.map((x) => x.util)) ** 2);
  }

  // ------------------------------------------------------------ plan (SVG): drawing
  const NS = "http://www.w3.org/2000/svg";
  const sv = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.append(e);
    return e;
  };
  function extents() {
    const { xs, ys, nx, ny } = geom();
    const W = xs[nx - 1] * 1000, H = ys[ny - 1] * 1000;
    const pad = Math.max(W, H) * 0.12 + 1500;
    return { x: -pad, y: -pad, w: W + 2 * pad, h: H + 2 * pad };
  }
  function fit() { S.vb = null; drawPlan(); }
  function zoom(f, cx, cy) {
    const vb = S.vb || extents();
    cx ??= vb.x + vb.w / 2; cy ??= vb.y + vb.h / 2;
    S.vb = { x: cx - (cx - vb.x) * f, y: cy - (cy - vb.y) * f, w: vb.w * f, h: vb.h * f };
    S.svg.setAttribute("viewBox", `${S.vb.x} ${S.vb.y} ${S.vb.w} ${S.vb.h}`);
  }
  const toModel = (e) => {
    const p = S.svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
    return p.matrixTransform(S.svg.getScreenCTM().inverse());
  };

  function drawPlan() {
    if (!S.inp || !S.svg) return;
    const svg = S.svg;
    svg.innerHTML = "";
    const { xs, ys, nx, ny } = geom();
    const W = xs[nx - 1] * 1000, H = ys[ny - 1] * 1000;
    const vb = S.vb || extents();
    svg.setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
    S.H = H;
    const Y = (y) => H - y;                         // plan with Y upwards
    const X = (x) => x;
    const L = lay();
    const omitC = new Set(L.omit_columns || []), omitB = new Set(L.omit_beams || []);
    const open = new Set(L.openings || []);
    const unit = Math.max(W, H) / 100;
    S.unit = unit;
    const defs = sv("defs", {}, svg);
    const pat = sv("pattern", { id: "st-hatch", width: unit * 3, height: unit * 3, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    sv("line", { x1: 0, y1: 0, x2: 0, y2: unit * 3, stroke: "var(--muted)", "stroke-width": unit * 0.4 }, pat);
    const gPan = sv("g", {}, svg), gGrid = sv("g", {}, svg), gBeam = sv("g", {}, svg), gCol = sv("g", {}, svg), gTxt = sv("g", {}, svg);
    const tag = (node, kind, id) => { node.dataset.kind = kind; node.dataset.id = id; };

    for (let i = 0; i < nx - 1; i++) for (let j = 0; j < ny - 1; j++) {
      const id = gl(i, j);
      const r = sv("rect", { x: X(xs[i] * 1000), y: Y(ys[j + 1] * 1000), width: (xs[i + 1] - xs[i]) * 1000,
        height: (ys[j + 1] - ys[j]) * 1000, class: `st-panel${open.has(id) ? " open" : ""}${isSel("panel", id) ? " sel" : ""}${S.opt.slabs ? "" : " hide"}`,
        fill: open.has(id) ? "url(#st-hatch)" : "" }, gPan);
      const sr = open.has(id) ? [] : shown("panel", id);
      const pc = sr.length ? colourFor("panel", id) : null;
      if (pc && S.opt.storey !== "found") { r.style.fill = pc; r.style.fillOpacity = "0.28"; }
      sv("title", {}, r).textContent = `${t("Slab panel")} ${id}${open.has(id) ? ` — ${t("Open (no slab)")}` : ""}` +
        (sr.length ? `\n${sr.map((x) => `${t("Storey")} ${x.storey}: ${x.reinforcement} (η = ${x.util.toFixed(2)})`).join("\n")}` : "");
      tag(r, "panel", id);
      if (S.opt.labels && sr.length && S.opt.storey !== "found") sv("text", { x: X((xs[i] + xs[i + 1]) * 500), y: Y((ys[j] + ys[j + 1]) * 500), "font-size": unit * 1.1, class: "st-rlbl", "text-anchor": "middle" }, gTxt)
        .textContent = sr[sr.length - 1].reinforcement;
    }
    const ext = unit * 6, rb = unit * 2.2;
    for (let i = 0; i < nx; i++) {
      const x = X(xs[i] * 1000);
      sv("line", { x1: x, y1: Y(-ext), x2: x, y2: Y(H + ext), class: "st-grid", "stroke-width": unit * 0.15, "stroke-dasharray": `${unit} ${unit * 0.6}` }, gGrid);
      if (S.opt.axes) for (const yy of [Y(-ext - rb), Y(H + ext + rb)]) {
        sv("circle", { cx: x, cy: yy, r: rb, class: "st-bubble", "stroke-width": unit * 0.2 }, gGrid);
        sv("text", { x, y: yy, "font-size": rb * 1.1, class: "st-btxt" }, gGrid).textContent = i + 1;
      }
      if (S.opt.dims && i < nx - 1) sv("text", { x: (xs[i] + xs[i + 1]) * 500, y: Y(-ext - rb * 0.2), "font-size": unit * 1.6, class: "st-dim" }, gTxt)
        .textContent = `${(+(xs[i + 1] - xs[i]).toFixed(2))} m`;
    }
    for (let j = 0; j < ny; j++) {
      const y = Y(ys[j] * 1000);
      sv("line", { x1: X(-ext), y1: y, x2: X(W + ext), y2: y, class: "st-grid", "stroke-width": unit * 0.15, "stroke-dasharray": `${unit} ${unit * 0.6}` }, gGrid);
      if (S.opt.axes) for (const xx of [X(-ext - rb), X(W + ext + rb)]) {
        sv("circle", { cx: xx, cy: y, r: rb, class: "st-bubble", "stroke-width": unit * 0.2 }, gGrid);
        sv("text", { x: xx, y, "font-size": rb * 1.1, class: "st-btxt" }, gGrid).textContent = yLabel(j);
      }
      if (S.opt.dims && j < ny - 1) {
        const tx = X(-ext - rb * 0.2), ty = Y((ys[j] + ys[j + 1]) * 500);
        sv("text", { x: tx, y: ty, "font-size": unit * 1.6, class: "st-dim", transform: `rotate(-90 ${tx} ${ty})` }, gTxt)
          .textContent = `${(+(ys[j + 1] - ys[j]).toFixed(2))} m`;
      }
    }
    const lbl = (r) => r.map((x) => `${t("Storey")} ${x.storey}: ${x.reinforcement} (η = ${x.util.toFixed(2)})`).join("\n");
    const bsz = L.beam_sizes || {};
    const beam = (i1, j1, i2, j2) => {
      const id = `${gl(i1, j1)}-${gl(i2, j2)}`;
      const x1 = X(xs[i1] * 1000), y1 = Y(ys[j1] * 1000), x2 = X(xs[i2] * 1000), y2 = Y(ys[j2] * 1000);
      const hit = sv("line", { x1, y1, x2, y2, class: "st-hit", "stroke-width": unit * 3 }, gBeam);
      tag(hit, "beam", id);
      if (omitB.has(id)) {
        const g = sv("line", { x1, y1, x2, y2, class: "st-ghost", "stroke-width": unit * 0.3, "stroke-dasharray": `${unit} ${unit}` }, gBeam);
        g.style.pointerEvents = "none";
        sv("title", {}, hit).textContent = `${t("Beam")} ${id} — ${t("Remove")}`;
        return;
      }
      const [b, h] = bsz[id] || [S.inp.beam_b, S.inp.beam_h];
      const ln = sv("line", { x1, y1, x2, y2, class: `st-beam${isSel("beam", id) ? " sel" : ""}`, "stroke-width": Math.max(b, unit * 0.8) }, gBeam);
      ln.style.pointerEvents = "none";
      const c = colourFor("beam", id);
      if (c) ln.style.stroke = c;
      const r = shown("beam", id);
      sv("title", {}, hit).textContent = `${t("Beam")} ${id} — ${b}×${h}` + (r.length ? `\n${lbl(r)}` : "");
      const horiz = j1 === j2;
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
      if (S.opt.names && bsz[id]) sv("text", { x: mx, y: my + (horiz ? -unit * 1.3 : 0), dx: horiz ? 0 : unit * 1.3, "font-size": unit * 1.25, class: "st-mname", "text-anchor": horiz ? "middle" : "start" }, gTxt).textContent = `${b}×${h}`;
      if (S.opt.labels && r.length) {
        const txt = S.opt.storey === "all" ? r[0].reinforcement + (r.length > 1 ? " …" : "") : r[0].reinforcement;
        const e = sv("text", { x: mx, y: my + (horiz ? unit * 1.9 : 0), dx: horiz ? 0 : -unit * 1.3, "font-size": unit * 1.1, class: "st-rlbl", "text-anchor": horiz ? "middle" : "end" }, gTxt);
        e.textContent = txt.replace(/ \(.*\)$/, "");
      }
    };
    const foundView = S.opt.storey === "found";
    if (!foundView) {
      for (let j = 0; j < ny; j++) for (let i = 0; i < nx - 1; i++) beam(i, j, i + 1, j);
      for (let i = 0; i < nx; i++) for (let j = 0; j < ny - 1; j++) beam(i, j, i, j + 1);
    } else {
      const m = S.res?.structure?.members || {};
      const isBeams = String(S.inp.found_type || "").startsWith("Foundation beams");
      const raft = S.res?.structure?.raft;
      if (raft && String(S.inp.found_type || "").startsWith("Raft")) {
        for (const e of raft.elements) {
          const r = sv("rect", { x: X(e.x0), y: Y(e.y1), width: e.x1 - e.x0, height: e.y1 - e.y0, class: "st-raft" }, gPan);
          r.style.fill = e.util > 1 ? "#e8752a" : heat(0.7 * e.util);
          sv("title", {}, r).textContent = `${e.id}: ${t("Raft: demand / basic mesh")} = ${e.util.toFixed(2)}` + (e.util > 1 ? ` (${t("additional bars")})` : "");
        }
        for (const p of raft.punching) {
          const [i0, j0] = idx(p.grid);
          const c = sv("circle", { cx: X(xs[i0] * 1000), cy: Y(ys[j0] * 1000), r: unit * 3.2, class: "st-punch" }, gBeam);
          c.style.stroke = p.util > 1 ? "#e03b3b" : heat(0.85 * p.util ** 2);
          sv("title", {}, c).textContent = `${t("Punching")} ${p.grid}: η = ${p.util.toFixed(2)}`;
          if (S.opt.labels) sv("text", { x: X(xs[i0] * 1000) + unit * 3.6, y: Y(ys[j0] * 1000) + unit * 3.6, "font-size": unit * 1.2, class: "st-rlbl" }, gTxt).textContent = `η ${p.util.toFixed(2)}`;
        }
        const rr = m["R.raft"];
        if (rr) $("#st-hint").textContent = `${t("Raft")}: ${rr.reinforcement}`;
      }
      for (const [k, v] of Object.entries(m)) {
        if (v.kind === "fbeam" && isBeams) {
          const [a, b] = k.slice(3).split("-").map(idx);
          const x1 = X(xs[a[0]] * 1000), y1 = Y(ys[a[1]] * 1000), x2 = X(xs[b[0]] * 1000), y2 = Y(ys[b[1]] * 1000);
          const ln = sv("line", { x1, y1, x2, y2, class: "st-beam", "stroke-width": (S.inp.fb_B || 1.2) * 1000 }, gBeam);
          ln.style.stroke = v.ok ? heat(0.85 * Math.min(v.rho / 0.03, 1)) : "#e03b3b";
          ln.style.strokeOpacity = "0.75";
          sv("title", {}, ln).textContent = `${t("Foundation beam")} ${k.slice(3)}\n${v.reinforcement} (η = ${v.util.toFixed(2)})`;
          if (S.opt.labels) sv("text", { x: (x1 + x2) / 2, y: (y1 + y2) / 2 + (y1 === y2 ? unit * 3 : 0), dx: y1 === y2 ? 0 : -unit * 3, "font-size": unit * 1.1, class: "st-rlbl", "text-anchor": y1 === y2 ? "middle" : "end" }, gTxt)
            .textContent = v.reinforcement;
        } else if (v.kind === "footing") {
          const [i0, j0] = idx(k.slice(2));
          const fx = v.inputs.Bx * 1000, fy = v.inputs.By * 1000;
          const r = sv("rect", { x: X(xs[i0] * 1000) - fx / 2, y: Y(ys[j0] * 1000) - fy / 2, width: fx, height: fy, class: "st-pad" }, gBeam);
          r.style.fill = v.ok ? heat(0.85 * v.util ** 2) : "#e03b3b";
          sv("title", {}, r).textContent = `${t("Footing")} ${k.slice(2)}\n${v.reinforcement} (η = ${v.util.toFixed(2)})`;
          if (S.opt.labels) sv("text", { x: X(xs[i0] * 1000), y: Y(ys[j0] * 1000) + fy / 2 + unit * 1.5, "font-size": unit * 1.1, class: "st-rlbl", "text-anchor": "middle" }, gTxt)
            .textContent = v.reinforcement;
        }
      }
    }
    const csz = L.col_sizes || {};
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
      const id = gl(i, j), cx = X(xs[i] * 1000), cy = Y(ys[j] * 1000);
      const w = wallAt(id);
      let node, kind;
      if (w) {
        kind = "wall";
        const [bx, by] = w.dir === "X" ? [w.L * 1000, w.t] : [w.t, w.L * 1000];
        node = sv("rect", { x: cx - bx / 2, y: cy - by / 2, width: bx, height: by, class: `st-wall${isSel("wall", id) ? " sel" : ""}` }, gCol);
        const r = shown("wall", id);
        sv("title", {}, node).textContent = `${t("Wall")} ${id} — ${w.L} m × ${w.t} mm` + (r.length ? `\n${r[0].reinforcement}` : "");
      } else if (omitC.has(id)) {
        kind = "point";
        node = sv("circle", { cx, cy, r: unit * 1.2, class: "st-empty" }, gCol);
        sv("title", {}, node).textContent = id;
      } else {
        kind = "column";
        const [b, h] = csz[id] || [S.inp.col_b, S.inp.col_h];
        node = sv("rect", { x: cx - b / 2, y: cy - h / 2, width: b, height: h, class: `st-col${isSel("column", id) ? " sel" : ""}` }, gCol);
        const r = shown("column", id);
        sv("title", {}, node).textContent = `${t("Column")} ${id} — ${b}×${h}` + (r.length ? `\n${lbl(r)}` : "");
        if (S.opt.labels && r.length) sv("text", { x: cx + unit * 1.2, y: cy + unit * 2.2, "font-size": unit * 1.1, class: "st-rlbl", "text-anchor": "start" }, gTxt)
          .textContent = (S.opt.storey === "all" ? r[0] : r[0]).reinforcement;
      }
      const c = kind === "point" ? null : colourFor(kind, id);
      if (c) node.style.fill = c;
      tag(node, kind, id);
      if (S.opt.names) sv("text", { x: cx + unit * 1.2, y: cy - unit * 1.2, "font-size": unit * 1.7, class: "st-plbl" }, gTxt).textContent = id;
      if (S.opt.names && csz[id] && kind === "column") sv("text", { x: cx + unit * 1.2, y: cy + unit * 1.0, "font-size": unit * 1.2, class: "st-mname" }, gTxt).textContent = `${csz[id][0]}×${csz[id][1]}`;
    }
    S.gSel = sv("g", {}, svg);
  }

  // ------------------------------------------------------------ plan (SVG): interaction
  function planEvents() {
    const svg = S.svg;
    let drag = null;
    svg.addEventListener("mousedown", (e) => {
      if (e.button === 1 || (e.button === 0 && e.altKey)) {          // pan
        e.preventDefault();
        drag = { pan: true, x: e.clientX, y: e.clientY, vb: { ...(S.vb || extents()) } };
        return;
      }
      if (e.button !== 0) return;
      const target = e.target.closest("[data-kind]");
      if (S.tool === "select" && (!target || target.dataset.kind === "panel")) {
        const p = toModel(e);
        drag = { box: true, x0: p.x, y0: p.y, moved: false, target };
      }
    });
    window.addEventListener("mousemove", (e) => {
      if (!document.body.classList.contains("in-structure")) return;
      if (drag?.pan) {
        const r = svg.getBoundingClientRect();
        const k = drag.vb.w / r.width;
        S.vb = { ...drag.vb, x: drag.vb.x - (e.clientX - drag.x) * k, y: drag.vb.y - (e.clientY - drag.y) * k };
        svg.setAttribute("viewBox", `${S.vb.x} ${S.vb.y} ${S.vb.w} ${S.vb.h}`);
        return;
      }
      if (e.target.closest?.("#st-plan")) {
        const p = toModel(e);
        $("#sb-xy").textContent = `x = ${(p.x / 1000).toFixed(2)} m · y = ${((S.H - p.y) / 1000).toFixed(2)} m`;
      }
      if (drag?.box) {
        const p = toModel(e);
        if (Math.hypot(p.x - drag.x0, p.y - drag.y0) > (S.unit || 50) * 1.5) drag.moved = true;
        if (!drag.moved) return;
        S.gSel.innerHTML = "";
        sv("rect", { x: Math.min(p.x, drag.x0), y: Math.min(p.y, drag.y0), width: Math.abs(p.x - drag.x0), height: Math.abs(p.y - drag.y0),
          class: `st-box${p.x < drag.x0 ? " cross" : ""}`, "stroke-width": S.unit * 0.25 }, S.gSel);
      }
    });
    window.addEventListener("mouseup", (e) => {
      if (!drag) return;
      const d = drag;
      drag = null;
      if (d.box && d.moved) {
        const p = toModel(e);
        boxSelect(Math.min(p.x, d.x0), Math.min(p.y, d.y0), Math.max(p.x, d.x0), Math.max(p.y, d.y0), e.shiftKey);
        d.swallow = true;
        S.swallowClick = true;
      }
    });
    svg.addEventListener("click", (e) => {
      if (S.swallowClick) { S.swallowClick = false; return; }
      const target = e.target.closest("[data-kind]");
      if (!target) { if (S.tool === "select" && !e.shiftKey) setSel([]); return; }
      act(target.dataset.kind, target.dataset.id, e.shiftKey || e.ctrlKey || e.metaKey);
    });
    svg.addEventListener("wheel", (e) => {
      e.preventDefault();
      const p = toModel(e);
      zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, p.x, p.y);
    }, { passive: false });
    svg.addEventListener("contextmenu", (e) => {
      const target = e.target.closest("[data-kind]");
      if (!target || target.dataset.kind === "point") return;
      e.preventDefault();
      const { kind, id } = target.dataset;
      if (!isSel(kind, id)) setSel([{ kind, id }]);
      contextMenu(e.clientX, e.clientY, kind, id);
    });
  }

  function boxSelect(x1, y1, x2, y2, add) {
    const { xs, ys, nx, ny } = geom();
    const inside = (x, y) => x >= x1 && x <= x2 && y >= y1 && y <= y2;
    const P = (i, j) => [xs[i] * 1000, S.H - ys[j] * 1000];
    const out = add ? [...S.sel] : [];
    const push = (kind, id) => { if (!out.some((s) => s.kind === kind && s.id === id)) out.push({ kind, id }); };
    for (const id of allIds("column")) { const [i, j] = idx(id); if (inside(...P(i, j))) push("column", id); }
    for (const id of allIds("wall")) { const [i, j] = idx(id); if (inside(...P(i, j))) push("wall", id); }
    for (const id of allIds("beam")) {
      const [a, b] = id.split("-").map(idx);
      if (inside(...P(...a)) && inside(...P(...b))) push("beam", id);
    }
    if (!out.length) for (let i = 0; i < nx - 1; i++) for (let j = 0; j < ny - 1; j++) {
      if (inside(...P(i, j)) && inside(...P(i + 1, j + 1))) push("panel", gl(i, j));
    }
    setSel(out);
  }
  function idx(g) {
    const m = /^([A-Z]+)(\d+)$/.exec(g);
    let j = 0;
    for (const ch of m[1]) j = j * 26 + (ch.charCodeAt(0) - 64);
    return [+m[2] - 1, j - 1];
  }

  function contextMenu(x, y, kind, id) {
    const menu = $("#st-menu");
    menu.innerHTML = "";
    const item = (label, fn, cls = "") => menu.append(el("button", { type: "button", class: cls, on: { click: (e) => { e.stopPropagation(); menu.hidden = true; fn(); } } }, label));
    menu.append(el("div", { class: "mh" }, `${KIND()[kind]} ${id}${S.sel.length > 1 ? ` (+${S.sel.length - 1})` : ""}`));
    item(`⚙ ${t("Properties")}`, () => { setView("plan"); renderProps(); $("#st-props").scrollIntoView({ block: "nearest" }); });
    item(`⬚ ${t("Select all of this type")}`, () => selectAll(kind === "panel" ? "beam" : kind));
    const r = kind === "panel" ? [] : resultsFor(kind, id);
    if (r.length) {
      const worst = [...r].sort((a, b) => (a.ok - b.ok) || (b.util - a.util))[0];
      item(`↗ ${t("Open in the member calculation")}`, () => openModule(worst.module, worst.inputs));
    }
    if (kind === "panel") item(`▢ ${t("Open (no slab)")}`, () => act("panel", id, false, "opening"));
    else item(`🗑 ${t("Delete")}`, removeSel, "danger");
    menu.hidden = false;
    const r0 = menu.getBoundingClientRect();
    menu.style.left = `${Math.min(x, innerWidth - r0.width - 8)}px`;
    menu.style.top = `${Math.min(y, innerHeight - r0.height - 8)}px`;
  }

  // ------------------------------------------------------------ editing actions
  function act(kind, id, add = false, tool = S.tool) {
    const L = lay();
    const point = ["column", "wall", "point"].includes(kind);
    if (tool === "select") {
      if (kind === "point") return;
      if (add) setSel(isSel(kind, id) ? S.sel.filter((s) => !(s.kind === kind && s.id === id)) : [...S.sel, { kind, id }]);
      else setSel([{ kind, id }]);
      return;
    }
    if (tool === "column" && point) {
      S.inp.walls = (S.inp.walls || []).filter((w) => String(w.at).toUpperCase() !== id);
      L.omit_columns = arr("omit_columns").filter((g) => g !== id);
      S.sel = [{ kind: "column", id }];
    } else if ((tool === "wallX" || tool === "wallY") && point) {
      const dir = tool === "wallX" ? "X" : "Y";
      const w = wallAt(id);
      if (w) w.dir = dir; else (S.inp.walls ||= []).push({ at: id, dir, L: 2.0, t: 250 });
      L.omit_columns = arr("omit_columns").filter((g) => g !== id);
      S.sel = [{ kind: "wall", id }];
    } else if (tool === "beam" && kind === "beam") {
      const a = arr("omit_beams");
      L.omit_beams = a.includes(id) ? a.filter((g) => g !== id) : [...a, id];
      S.sel = L.omit_beams.includes(id) ? [] : [{ kind: "beam", id }];
    } else if (tool === "opening" && kind === "panel") {
      const a = arr("openings");
      L.openings = a.includes(id) ? a.filter((g) => g !== id) : [...a, id];
      S.sel = [{ kind: "panel", id }];
    } else return;
    commit();
    renderRibbon();
  }

  function removeSel() {
    if (!S.sel.length) return;
    const L = lay();
    for (const { kind, id } of S.sel) {
      if (kind === "column") L.omit_columns = [...new Set([...arr("omit_columns"), id])];
      if (kind === "wall") { S.inp.walls = S.inp.walls.filter((w) => String(w.at).toUpperCase() !== id); L.omit_columns = [...new Set([...arr("omit_columns"), id])]; }
      if (kind === "beam") L.omit_beams = [...new Set([...arr("omit_beams"), id])];
      if (kind === "panel") L.openings = [...new Set([...arr("openings"), id])];
    }
    S.sel = [];
    commit();
    renderRibbon();
  }

  // ------------------------------------------------------------ properties (right)
  function numField(label, value, min, max, onSet) {
    const inp = el("input", { type: "number", value: value ?? "", min, max, step: "any", placeholder: value == null ? "—" : "", on: { change: (e) => {
      const v = parseFloat(String(e.target.value).replace(",", "."));
      if (!(v >= min && v <= max)) { e.target.classList.add("bad"); return; }
      onSet(v);
    } } });
    return el("label", { class: "st-f" }, el("span", {}, label), el("span", { class: "inp" }, inp));
  }
  const same = (vals) => (vals.every((v) => v === vals[0]) ? vals[0] : null);

  function renderProps() {
    const box = $("#st-props");
    if (!box) return;
    box.innerHTML = "";
    const sel = S.sel;
    if (!sel.length) {
      box.append(el("h4", {}, t("Properties")), el("p", { class: "muted" }, t("Click a column, wall, beam or slab panel in the plan.")),
        el("p", { class: "muted small" }, t("Shift+click adds to the selection; drag a window to select several.")));
      return;
    }
    const kinds = [...new Set(sel.map((s) => s.kind))];
    const L = lay();
    const ids = sel.map((s) => s.id);
    box.append(el("h4", {}, sel.length === 1 ? `${KIND()[sel[0].kind]} ${sel[0].id}` :
      `${sel.length} ${t("selected")}: ${kinds.map((k) => KIND()[k]).join(", ")}`));
    if (kinds.length === 1) {
      const kind = kinds[0];
      if (kind === "column") {
        const cur = ids.map((id) => obj("col_sizes")[id] || [S.inp.col_b, S.inp.col_h]);
        box.append(numField(t("Side along X [mm]"), same(cur.map((c) => c[0])), 200, 1500, (v) => { ids.forEach((id, n) => { obj("col_sizes")[id] = [v, cur[n][1]]; }); commit(); }),
          numField(t("Side along Y [mm]"), same(cur.map((c) => c[1])), 200, 1500, (v) => { ids.forEach((id, n) => { obj("col_sizes")[id] = [cur[n][0], v]; }); commit(); }));
        if (ids.some((id) => L.col_sizes?.[id])) box.append(el("button", { type: "button", class: "ghost", on: { click: () => { ids.forEach((id) => delete L.col_sizes[id]); commit(); } } }, t("Default size")));
      } else if (kind === "wall") {
        const ws = ids.map(wallAt);
        const dir = el("select", { on: { change: (e) => { ws.forEach((w) => { w.dir = e.target.value; }); commit(); } } }, el("option", { value: "" }, "—"), el("option", { value: "X" }, "X"), el("option", { value: "Y" }, "Y"));
        dir.value = same(ws.map((w) => w.dir)) || "";
        box.append(el("label", { class: "st-f" }, el("span", {}, t("Direction")), el("span", { class: "inp" }, dir)),
          numField(t("Length [m]"), same(ws.map((w) => w.L)), 1, 10, (v) => { ws.forEach((w) => { w.L = v; }); commit(); }),
          numField(t("Thickness [mm]"), same(ws.map((w) => w.t)), 150, 600, (v) => { ws.forEach((w) => { w.t = v; }); commit(); }));
      } else if (kind === "beam") {
        const cur = ids.map((id) => obj("beam_sizes")[id] || [S.inp.beam_b, S.inp.beam_h]);
        box.append(numField(t("Width b [mm]"), same(cur.map((c) => c[0])), 150, 800, (v) => { ids.forEach((id, n) => { obj("beam_sizes")[id] = [v, cur[n][1]]; }); commit(); }),
          numField(t("Depth h [mm]"), same(cur.map((c) => c[1])), 250, 1500, (v) => { ids.forEach((id, n) => { obj("beam_sizes")[id] = [cur[n][0], v]; }); commit(); }));
        if (ids.some((id) => L.beam_sizes?.[id])) box.append(el("button", { type: "button", class: "ghost", on: { click: () => { ids.forEach((id) => delete L.beam_sizes[id]); commit(); } } }, t("Default size")));
      } else if (kind === "panel") {
        const cb = el("input", { type: "checkbox", on: { change: (e) => {
          const set = new Set(arr("openings"));
          ids.forEach((id) => (e.target.checked ? set.add(id) : set.delete(id)));
          L.openings = [...set]; commit();
        } } });
        cb.checked = ids.every((id) => (L.openings || []).includes(id));
        box.append(el("label", { class: "st-f chk" }, cb, el("span", {}, t("Open (no slab)"))));
      }
    }
    if (!(kinds.length === 1 && kinds[0] === "panel")) box.append(el("button", { type: "button", class: "ghost danger", on: { click: removeSel } }, `🗑 ${t("Delete")}`));
    if (sel.length === 1 && sel[0].kind !== "panel") {
      const res = resultsFor(sel[0].kind, sel[0].id);
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
  }

  // ------------------------------------------------------------ table view
  function tableRows() {
    const m = S.res?.structure?.members || {};
    const L = lay();
    const size = (kind, id) => {
      if (kind === "wall") { const w = wallAt(id); return w ? `${w.L} m × ${w.t}` : ""; }
      if (kind === "panel") return `t = ${S.inp.slab_t}`;
      if (kind === "fbeam") return `${S.inp.fb_bw}×${S.inp.fb_h}, B = ${S.inp.fb_B} m`;
      if (kind === "footing") return "";
      const s = kind === "beam" ? (L.beam_sizes?.[id] || [S.inp.beam_b, S.inp.beam_h]) : (L.col_sizes?.[id] || [S.inp.col_b, S.inp.col_h]);
      return `${s[0]}×${s[1]}`;
    };
    return Object.entries(m).map(([k, v]) => {
      const id = k.slice(k.indexOf(".") + 1);
      const kind = { beam: "beam", wall: "wall", slab: "panel", fbeam: "fbeam", footing: "footing" }[v.kind] || "column";
      return { member: k, id, kind, type: KIND()[v.kind] || KIND()[kind], storey: v.storey, section: size(kind, id), reinforcement: v.reinforcement,
        rho: v.rho * 100, util: v.util, ok: v.ok, status: v.ok ? t("Passes") : t("Fails"), notes: v.notes.join("; ") };
    });
  }
  function filteredRows() {
    const q = S.opt.filter.trim().toLowerCase();
    const [key, dir] = S.opt.sort;
    return tableRows().filter((r) => (!S.opt.onlyFail || !r.ok) && (!q || `${r.member} ${r.type} ${r.reinforcement}`.toLowerCase().includes(q)))
      .sort((a, b) => (a[key] > b[key] ? 1 : a[key] < b[key] ? -1 : 0) * dir);
  }
  function renderTable() {
    const box = $("#st-table");
    if (!box) return;
    box.innerHTML = "";
    const cols = [["member", t("Member")], ["type", t("Type")], ["storey", t("Storey")], ["section", t("Section")],
      ["reinforcement", t("Reinforcement")], ["rho", "ρ [%]"], ["util", "η"], ["status", t("Status")]];
    const rows = filteredRows();
    const all = tableRows();
    const filt = el("input", { type: "search", placeholder: t("Filter…"), value: S.opt.filter, on: { input: (e) => { S.opt.filter = e.target.value; renderTable(); setTimeout(() => { const i = $("#st-table input[type=search]"); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }); } } });
    const only = el("input", { type: "checkbox", on: { change: (e) => { S.opt.onlyFail = e.target.checked; saveView(); renderTable(); } } });
    only.checked = S.opt.onlyFail;
    box.append(el("div", { class: "st-tbar" }, filt, el("label", { class: "rb-chk" }, only, el("span", {}, t("Only failing"))),
      el("span", { class: "muted" }, `${t("Members passing")}: ${all.filter((r) => r.ok).length} / ${all.length}`),
      el("span", { class: "grow" }), btn("csv", t("Table CSV"), "", csv)));
    const tb = el("table", { class: "st-grid-table" });
    tb.append(el("tr", {}, ...cols.map(([k, lab]) => el("th", { class: S.opt.sort[0] === k ? "sorted" : "", on: { click: () => {
      S.opt.sort = [k, S.opt.sort[0] === k ? -S.opt.sort[1] : 1]; saveView(); renderTable();
    } } }, lab + (S.opt.sort[0] === k ? (S.opt.sort[1] > 0 ? " ▲" : " ▼") : "")))));
    for (const r of rows) {
      tb.append(el("tr", { class: `${r.ok ? "" : "bad"}${isSel(r.kind, r.id) ? " sel" : ""}`, title: r.notes,
        on: { click: () => setSel([{ kind: r.kind, id: r.id }]), dblclick: () => { setSel([{ kind: r.kind, id: r.id }]); setView("plan"); } } },
        ...cols.map(([k]) => el("td", {}, k === "rho" ? r.rho.toFixed(2) : k === "util" ? r.util.toFixed(2) : String(r[k])))));
    }
    box.append(tb);
  }
  function csv() {
    const rows = filteredRows();
    const head = ["member", "type", "storey", "section", "reinforcement", "rho_percent", "utilisation", "status", "notes"];
    const q = (v) => `"${String(v).replace(/"/g, '""')}"`;
    const text = [head.join(";"), ...rows.map((r) => [r.member, r.type, r.storey, r.section, r.reinforcement, r.rho.toFixed(2),
      r.util.toFixed(3), r.status, r.notes].map(q).join(";"))].join("\r\n");
    download(`${fileName()}_members.csv`, "﻿" + text, "text/csv");
  }

  // ------------------------------------------------------------ automatic sizing
  async function autoSize() {
    const dlg = el("dialog", { class: "st-dlg" }, el("h3", {}, t("Automatic sizing…")),
      el("p", { class: "muted" }, t("Running the complete calculation repeatedly — this can take a little while.")),
      el("div", { class: "st-spin" }));
    document.body.append(dlg);
    dlg.addEventListener("close", () => dlg.remove());
    dlg.addEventListener("cancel", (e) => e.preventDefault());
    dlg.showModal();
    let res;
    try {
      res = await api("/api/structure/autosize", { inputs: S.inp, project: state.project });
    } catch (err) {
      dlg.close();
      alert(err.message);
      if (err.license) licenseDialog();
      return;
    }
    dlg.innerHTML = "";
    const changes = res.log.flat().length;
    dlg.append(el("h3", {}, `${res.passed ? "✔" : "⚠"} ${t("Auto-size")}`));
    if (res.passed && !changes) dlg.append(el("p", {}, t("Nothing to change — every check already passes.")));
    else if (res.passed) dlg.append(el("p", { class: "ok" }, t("All Eurocode checks pass after these changes:")));
    if (changes) {
      const list = el("ol", { class: "st-log" });
      res.log.forEach((round, n) => list.append(el("li", {}, el("b", {}, `${t("Round")} ${n + 1}`),
        el("ul", {}, ...round.map((c) => el("li", {}, c))))));
      dlg.append(list);
    }
    if (!res.passed) {
      dlg.append(el("p", { class: "bad" }, res.error || t("Still failing after the automatic changes — change these by hand:")),
        el("ul", { class: "st-log" }, ...(res.failing || []).slice(0, 12).map((f) => el("li", {}, f))));
    }
    dlg.append(el("div", { class: "btns" },
      el("button", { type: "button", class: "ghost", on: { click: () => dlg.close() } }, t("Cancel")),
      el("button", { type: "button", class: "primary", disabled: changes ? null : "", on: { click: () => {
        S.inp = res.inputs; dlg.close(); renderSettings(); renderRibbon(); commit();
        if (!S.auto) run();
      } } }, t("Apply"))));
  }

  // ------------------------------------------------------------ run
  function statusDirty() {
    const st = $("#st-status");
    st.className = "err";
    st.textContent = `⟳ ${t("Changes not analysed — press Run (F5)")}`;
    $("#sb-msg").textContent = t("Changes not analysed — press Run (F5)");
    renderRibbon();
  }
  function schedule() {
    clearTimeout(S.timer);
    $("#st-status").className = "busy";
    $("#st-status").textContent = t("Calculating the building…");
    $("#sb-msg").textContent = t("Calculating the building…");
    S.timer = setTimeout(run, 500);
  }
  async function run() {
    clearTimeout(S.timer);
    const my = ++S.runId;
    $("#sb-msg").textContent = t("Calculating the building…");
    try {
      const res = await api("/api/modules/building_frame/run", { inputs: S.inp, project: state.project });
      if (my !== S.runId) return;
      S.res = res;
      S.dirty = false;
      $("#st-report").srcdoc = res.html;
      if (res.model3d) window.dispatchEvent(new CustomEvent("erisma:model3d", { detail: { host: "st-3d", model: res.model3d, summary: res.summary } }));
      renderResult(res);
      renderSettings(); redraw(); renderRibbon();
    } catch (err) {
      if (my !== S.runId) return;
      const st = $("#st-status");
      st.className = "err";
      st.textContent = `⚠ ${err.message}`;
      $("#sb-msg").textContent = `⚠ ${err.message}`;
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
    const members = Object.values(res.structure?.members || {});
    $("#sb-msg").textContent = `${s.passed ? "✔" : "✖"} ${t("Ready")} · ${t("Members passing")}: ${members.filter((m) => m.ok).length}/${members.length}` +
      (s.warnings.length ? ` · ⚠ ${s.warnings.length} ${t("Messages").toLowerCase()}` : "");
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
    if (s.warnings.length) {
      sm.append(el("details", { class: "st-msgs" }, el("summary", {}, `⚠ ${t("Messages")} (${s.warnings.length})`),
        el("ul", {}, ...s.warnings.map((w) => el("li", {}, w)))));
    }
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
    renderRibbon();
    setTool(S.tool);
    setView(S.view);
    renderProps();
    run();
  }
  function newBuilding() {
    if (!confirm(t("Start a new building from the example? The current one will be replaced."))) return;
    S.inp = defaults(); S.sel = []; S.vb = null;
    renderSettings(); renderRibbon(); commit();
  }
  function load(inputs) {
    S.inp = { ...(S.schema ? defaults() : {}), ...inputs };
    S.sel = []; S.vb = null;
    store.set(KEY, S.inp);
    S.hist = [JSON.stringify(S.inp)]; S.hpos = 0;
    if (S.built && S.schema) { renderSettings(); renderRibbon(); redraw(); run(); }
  }
  const fileName = () => (state.project.job_no || state.project.project || "building").replace(/[^\w.-]+/g, "_");
  function save() {
    download(`${fileName()}_structure.erisma`, JSON.stringify({ format: "erisma", version: 1, module: "building_frame",
      workspace: "structure", project: state.project, inputs: S.inp }, null, 2), "application/json");
  }
  const print = () => { setView("report"); setTimeout(() => $("#st-report").contentWindow.print(), 300); };
  const html = () => S.res && download(`${fileName()}_structure.html`, S.res.html, "text/html");
  const toggle3d = () => setView(S.view === "3d" ? "plan" : "3d");

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
