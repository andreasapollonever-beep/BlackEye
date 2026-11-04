"use strict";
// Erisma Structure — graphical workspace for whole buildings.
// The plan editor produces the inputs of the "building_frame" module (grid, storeys,
// walls and the "layout" of missing columns/beams, openings and member sizes); the
// calculation, report, 3D scene and licence are the same as everywhere in Erisma.
// The command ribbon follows the conventions of professional structural software
// (File · Home · Model · Loads · Seismic · Design · Results · View · Help).

Object.assign(UI.el, {
  // design results window (Tekla-style)
  "Span (sagging)": "Άνοιγμα (θετική ροπή)", "Supports (hogging)": "Στηρίξεις (αρνητική ροπή)",
  "Pass": "Επαρκεί", "Fail": "Ανεπαρκές", "Check mode": "Λειτουργία ελέγχου", "Design mode": "Αυτόματη διαστασιολόγηση",
  "Checks": "Έλεγχοι", "Design forces": "Εντατικά σχεδιασμού", "Check": "Έλεγχος", "Demand": "Δράση",
  "Resistance": "Αντοχή", "Clause": "Άρθρο", "Open the full calculation for the checks.": "Ανοίξτε τον πλήρη υπολογισμό για τους ελέγχους.",
  "Shear": "Τέμνουσα", "Value": "Τιμή", "Governing": "Κρίσιμος συνδυασμός", "Top bars": "Άνω ράβδοι",
  "Bottom bars": "Κάτω ράβδοι", "Links (span)": "Συνδετήρες (άνοιγμα)", "Bars per side": "Ράβδοι ανά πλευρά",
  "Links": "Συνδετήρες",
  "Check mode: the member is checked with these bars instead of the automatic design; the whole building is re-analysed.":
    "Λειτουργία ελέγχου: το μέλος ελέγχεται με αυτούς τους οπλισμούς αντί για την αυτόματη διαστασιολόγηση· όλο το κτίριο ξαναϋπολογίζεται.",
  "Back to automatic design": "Επιστροφή στην αυτόματη διαστασιολόγηση", "Elevation": "Όψη",
  "Full calculation": "Πλήρης υπολογισμός", "Close": "Κλείσιμο",
  "Select a designed member (after the analysis) to see its design results.": "Επιλέξτε ένα διαστασιολογημένο μέλος (μετά την ανάλυση) για να δείτε τα αποτελέσματά του.",
  "Design results": "Αποτελέσματα διαστασιολόγησης",
  "Design results of the selected member (double-click a member)": "Αποτελέσματα διαστασιολόγησης του επιλεγμένου μέλους (διπλό κλικ σε μέλος)",
  "Member design": "Διαστασιολόγηση μέλους", "Top": "Άνω", "Bottom": "Κάτω",
  "EN 1998-1 detailing (critical regions)": "Κατασκευαστικές διατάξεις EN 1998-1 (κρίσιμες περιοχές)",
  "Web": "Κορμός", "compression": "θλίψη", "bottom bars": "κάτω οπλισμός", "top bars": "άνω οπλισμός",
  "continuous edge": "συνεχής παρειά", "simply supported": "ελεύθερη έδραση", "critical region h_cr": "κρίσιμη περιοχή h_cr",
  "boundary elements": "άκρα (περισφιγμένα)", "Every design combination": "Όλοι οι συνδυασμοί σχεδιασμού", "Combination": "Συνδυασμός",
  "blue: bending about h · purple: about b (first-order design actions)": "μπλε: κάμψη κατά h · μωβ: κατά b (εντατικά 1ης τάξης)",
  "Design interaction curve (EN 1992-1-1 6.1, ε_cu = 3.5 ‰); dots = design actions of every combination — green inside, red outside.":
    "Καμπύλη αλληλεπίδρασης σχεδιασμού (EN 1992-1-1 6.1, ε_cu = 3.5 ‰)· σημεία = εντατικά κάθε συνδυασμού — πράσινα εντός, κόκκινα εκτός.",
  "Boundary element bars": "Ράβδοι άκρου (ανά άκρο)", "Boundary hoops": "Συνδετήρες άκρων",
  "Web vertical (each face)": "Κορμός κατακόρυφοι (ανά παρειά)", "Web horizontal (each face)": "Κορμός οριζόντιοι (ανά παρειά)",
  "Bottom bars (both directions)": "Κάτω οπλισμός (και στις δύο διευθύνσεις)", "Top bars over supports": "Άνω οπλισμός στις στηρίξεις",
  "Section in the critical region": "Διατομή στην κρίσιμη περιοχή",
});
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
  "Plan + 3D": "Κάτοψη + 3D", "Diagrams": "Διαγράμματα", "Moments M": "Ροπές M",
  "Shear V": "Τέμνουσες V", "Axial N": "Αξονικές N", "Deformed": "Παραμόρφωση",
  "Mode 1": "Ιδιομορφή 1", "Mode 2": "Ιδιομορφή 2", "Mode 3": "Ιδιομορφή 3",
  "Show / hide in the 3D view": "Εμφάνιση / απόκρυψη στο 3D", "Regularity": "Κανονικότητα",
  "plan": "κάτοψη", "elevation": "όψη", "regular": "κανονικό", "not regular": "μη κανονικό",
  "torsionally flexible": "στρεπτικά εύκαμπτο", "torsionally stiff": "στρεπτικά δύσκαμπτο",
  "q used": "q που χρησιμοποιήθηκε", "Mode": "Ιδιομορφή", "torsion": "στρέψη",
  "Drift d_r·ν / (α·h) per storey": "Σχετική μετακίνηση d_r·ν / (α·h) ανά όροφο",
  "National Annex": "Εθνικό Προσάρτημα", "Code": "Κανονισμός", "Seismic zone": "Σεισμική ζώνη",
  "Foundation plan": "Κάτοψη θεμελίωσης", "Members": "Μέλη", "Design members": "Διαστασιολόγηση μελών",
  "Layers": "Επίπεδα", "Draw": "Σχεδίαση", "Define": "Ορισμοί", "Analyse": "Ανάλυση", "Modify": "Τροποποίηση",
  "Project details": "Στοιχεία έργου", "Company, project, job number, engineer — printed on every report page":
    "Εταιρεία, έργο, αριθμός έργου, μηχανικός — τυπώνονται σε κάθε σελίδα του τεύχους",
  "Concrete": "Σκυρόδεμα", "Sections": "Διατομές",
  "Sizes used where no member has its own (select a member to change only that one)":
    "Διαστάσεις για όσα μέλη δεν έχουν δική τους (επιλέξτε ένα μέλος για να αλλάξετε μόνο αυτό)",
  "Seismic action": "Σεισμική δράση", "Wind": "Άνεμος", "Wind on the building": "Άνεμος στο κτίριο",
  "Include wind (EN 1991-1-4)": "Συμπερίληψη ανέμου (EN 1991-1-4)", "Wind forces": "Δυνάμεις ανέμου", "NA wind map": "Χάρτης ανέμου ΕΠ", "Terrain": "Έδαφος", "Response spectrum": "Φάσμα απόκρισης", "Spectrum": "Φάσμα",
  "Stiffness": "Δυσκαμψία", "Apply to q": "Εφαρμογή στο q", "Show mode": "Εμφάνιση",
  "Animate": "Κίνηση", "Stop": "Διακοπή", "Speed": "Ταχύτητα",
  "Animate the mode / deformed shape in the 3D view": "Κίνηση της ιδιομορφής / παραμόρφωσης στο 3D",
  "Include the destabilising effect of the gravity loads": "Επιρροή των κατακόρυφων φορτίων στη δυσκαμψία (2ας τάξης)",
  "Load case": "Φόρτιση", "New case": "Νέα φόρτιση", "Rename": "Μετονομασία", "Delete case": "Διαγραφή φόρτισης",
  "Permanent G": "Μόνιμα G", "Imposed Q": "Κινητά Q", "Snow S": "Χιόνι S", "Apply loads": "Εφαρμογή φορτίων",
  "Area load": "Επιφανειακό", "Line load": "Γραμμικό", "Point load": "Σημειακό", "Value": "Τιμή",
  "On storeys": "Σε ορόφους", "All floors": "Όλοι οι όροφοι", "Roof": "Δώμα", "Combinations": "Συνδυασμοί",
  "Combinations…": "Συνδυασμοί…", "Built-in case — edit its loads in the Loads tab values":
    "Ενσωματωμένη φόρτιση — αλλάξτε τις τιμές της στα πεδία της καρτέλας",
  "Click slab panels to add / remove the area load of the current case.":
    "Κάντε κλικ σε φατνώματα για προσθήκη / αφαίρεση του επιφανειακού φορτίου της τρέχουσας φόρτισης.",
  "Click beams to add / remove the line load of the current case.":
    "Κάντε κλικ σε δοκούς για προσθήκη / αφαίρεση του γραμμικού φορτίου της τρέχουσας φόρτισης.",
  "Click grid points to add / remove the point load of the current case.":
    "Κάντε κλικ σε κόμβους για προσθήκη / αφαίρεση του σημειακού φορτίου της τρέχουσας φόρτισης.",
  "Name of the new load case": "Όνομα νέας φόρτισης", "New name": "Νέο όνομα",
  "Generated (EN 1990)": "Αυτόματοι (EN 1990)", "User combinations": "Συνδυασμοί χρήστη",
  "Add combination": "Προσθήκη συνδυασμού", "Save": "Αποθήκευση", "Kind": "Είδος", "Expression": "Έκφραση",
  "Run the analysis to see the generated combinations.": "Εκτελέστε την ανάλυση για να δείτε τους αυτόματους συνδυασμούς.",
  "Category": "Κατηγορία",
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
    hist: [], hpos: -1, timer: null, runId: 0, built: false, auto: true, dirty: false, vb: null, layers: {},
    lcase: null, lval: { area: 2.0, line: 5.0, point: 20.0 }, lstorey: "all", mode: 1, anim: false, animSpeed: 1,
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

  // ------------------------------------------------------------ icons
  // 24×24, two-tone: strokes in the text colour, ".f" faces tinted with the accent colour,
  // ".r" red accents (loads, seismic). Drawn to be recognisable at a glance, as in
  // ETABS / Revit / Tekla ribbons.
  const P = {
    // file
    new: '<path class="f" d="M6 2.5h8l4 4V21.5H6z"/><path d="M6 2.5h8l4 4V21.5H6z"/><path d="M14 2.5v4h4"/><path d="M12 11v6M9 14h6"/>',
    open: '<path class="f" d="M2.5 19.5l3-9h16l-3 9z"/><path d="M2.5 19.5V5.5h6l2 2h7v3"/><path d="M2.5 19.5l3-9h16l-3 9z"/>',
    save: '<path class="f" d="M4 4h12.5L20 7.5V20H4z"/><path d="M4 4h12.5L20 7.5V20H4z"/><path d="M7.5 4v5h8V4"/><rect x="7" y="13" width="10" height="7"/>',
    print: '<path d="M7 8V3h10v5"/><rect class="f" x="3" y="8" width="18" height="9" rx="1.5"/><rect x="3" y="8" width="18" height="9" rx="1.5"/><path d="M7 14h10v7H7z"/>',
    html: '<path class="f" d="M5 3h10l4 4v14H5z"/><path d="M5 3h10l4 4v14H5z"/><path d="M9.5 11l-2 2.5 2 2.5M14.5 11l2 2.5-2 2.5"/>',
    csv: '<rect class="f" x="3" y="4" width="18" height="16" rx="1"/><rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14.5h18M9 4v16M15 4v16"/>',
    project: '<rect class="f" x="4" y="3" width="16" height="18" rx="1.5"/><rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    annex: '<circle class="f" cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
    // edit / selection
    undo: '<path d="M9 6L4 11l5 5"/><path d="M4 11h11a5 5 0 0 1 0 10h-3"/>',
    redo: '<path d="M15 6l5 5-5 5"/><path d="M20 11H9a5 5 0 0 0 0 10h3"/>',
    del: '<path d="M4 7h16"/><path d="M9.5 7V4h5v3"/><path class="f" d="M6 7l1 13.5h10L18 7z"/><path d="M6 7l1 13.5h10L18 7z"/><path d="M10 11v6M14 11v6"/>',
    select: '<path class="f" d="M5 3l13 8.5-6 1.5 3.5 7-2.5 1.2-3.4-7L5 18z"/><path d="M5 3l13 8.5-6 1.5 3.5 7-2.5 1.2-3.4-7L5 18z"/>',
    selcol: '<rect class="f" x="3" y="3" width="5" height="5"/><rect class="f" x="16" y="3" width="5" height="5"/><rect class="f" x="3" y="16" width="5" height="5"/><rect class="f" x="16" y="16" width="5" height="5"/><path d="M3 3h5v5H3zM16 3h5v5h-5zM3 16h5v5H3zM16 16h5v5h-5z"/><path d="M8 5.5h8M8 18.5h8M5.5 8v8M18.5 8v8" stroke-dasharray="1.5 2"/>',
    selbeam: '<rect class="f" x="2.5" y="10" width="19" height="4"/><rect x="2.5" y="10" width="19" height="4"/><path d="M2.5 5h19M2.5 19h19" stroke-dasharray="1.5 2"/>',
    selwall: '<rect class="f" x="9" y="2.5" width="6" height="19"/><rect x="9" y="2.5" width="6" height="19"/><path d="M5 2.5v19M19 2.5v19" stroke-dasharray="1.5 2"/>',
    selfail: '<path class="f r" d="M12 3l9.5 17h-19z"/><path d="M12 3l9.5 17h-19z"/><path d="M12 9.5v5M12 17.2v.3"/>',
    clear: '<rect x="3" y="3" width="18" height="18" rx="2" stroke-dasharray="2.5 2"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/>',
    // analysis
    run: '<path class="f" d="M7 4.5l12 7.5-12 7.5z"/><path d="M7 4.5l12 7.5-12 7.5z"/>',
    auto: '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4v4.5h-4.5"/><path class="f" d="M10 8.5l5 3.5-5 3.5z"/><path d="M10 8.5l5 3.5-5 3.5z"/>',
    autosize: '<path d="M4 20L15.5 8.5"/><path class="f" d="M15.5 8.5l2-2 2.5 2.5-2 2z"/><path d="M15.5 8.5l2-2 2.5 2.5-2 2z"/><path d="M8 3.5v3M6.5 5h3M19 14.5v3M17.5 16h3M12 2.5v1.5"/>',
    check: '<rect class="f" x="4" y="3" width="16" height="18" rx="1.5"/><rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M7.5 8l1.5 1.5L12 6.5M7.5 14l1.5 1.5 3-3M14 8h3M14 14h3"/>',
    // views
    plan: '<rect class="f" x="3" y="3" width="18" height="18"/><path d="M3 3h18v18H3zM3 12h18M12 3v18"/><rect x="10.5" y="10.5" width="3" height="3" fill="currentColor"/>',
    cube: '<path class="f" d="M12 2.5l8.5 4.8v9.4L12 21.5l-8.5-4.8V7.3z"/><path d="M12 2.5l8.5 4.8v9.4L12 21.5l-8.5-4.8V7.3z"/><path d="M3.5 7.3L12 12l8.5-4.7M12 12v9.5"/>',
    split: '<rect x="2" y="4" width="20" height="16" rx="1.5"/><path d="M12 4v16"/><path class="f" d="M4 6.5h6v11H4z"/><path d="M4 12h6M7 6.5v11"/><path d="M17 8l3 1.7v3.6L17 15l-3-1.7V9.7z"/>',
    table: '<rect class="f" x="3" y="4" width="18" height="16" rx="1"/><rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14.5h18M9 9v11"/>',
    report: '<path class="f" d="M6 2.5h9l3.5 3.5V21.5H6z"/><path d="M6 2.5h9l3.5 3.5V21.5H6z"/><path d="M9 9h6M9 12.5h6M9 16h4"/>',
    // model
    column: '<path class="f" d="M8 6.5l4-2 4 2v12l-4 2-4-2z"/><path d="M8 6.5l4-2 4 2v12l-4 2-4-2z"/><path d="M8 6.5l4 2 4-2M12 8.5v12"/>',
    wallx: '<path class="f" d="M2.5 9l6-3h13l-6 3z"/><path d="M2.5 9h13v9.5h-13zM15.5 9l6-3v9.5l-6 3M2.5 9l6-3h13"/>',
    wally: '<path class="f" d="M8 4l3-1.5v17L8 21z"/><path d="M8 4l3-1.5 5 2.5v17l-5-2.5-3 1.5zM11 2.5v17M8 4l5 2.5V21"/>',
    beam: '<path class="f" d="M2.5 10l3-2h16l-3 2z"/><path d="M2.5 10h16v4h-16zM18.5 10l3-2v4l-3 2M2.5 10l3-2h16"/><path d="M4 14v6M17 14v6" stroke-dasharray="1.5 1.5"/>',
    opening: '<path class="f" d="M2.5 15l5-7h14l-5 7z"/><path d="M2.5 15l5-7h14l-5 7z"/><path d="M10 13l2.2-3h4.3l-2.2 3z" fill="var(--panel)"/>',
    slab: '<path class="f" d="M2.5 14l5-6h14l-5 6z"/><path d="M2.5 14l5-6h14l-5 6zM2.5 14v2.5h14l5-6V8M16.5 14v2.5"/>',
    grid: '<path d="M7 5v15M17 5v15M3 9h18M3 16h18" stroke-dasharray="2 1.5"/><circle class="f" cx="7" cy="3" r="2"/><circle class="f" cx="17" cy="3" r="2"/><circle cx="7" cy="3" r="2"/><circle cx="17" cy="3" r="2"/>',
    axisx: '<path d="M6 7v14M13 7v14" stroke-dasharray="2 1.5"/><circle cx="6" cy="4" r="2"/><circle cx="13" cy="4" r="2"/><path class="r" d="M19 9v8M15 13h8"/>',
    axisy: '<path d="M7 7h14M7 14h14" stroke-dasharray="2 1.5"/><circle cx="4" cy="7" r="2"/><circle cx="4" cy="14" r="2"/><path class="r" d="M14 17v6M11 20h6"/>',
    storeyadd: '<path class="f" d="M4 21V11h12v10"/><path d="M4 21V11h12v10M4 16h12M2 21h16M8 11V8h4v3"/><path class="r" d="M19.5 3v6M16.5 6h6"/>',
    storeydel: '<path class="f" d="M4 21V14h12v7"/><path d="M4 21V14h12v7M2 21h16"/><path d="M4 9h12" stroke-dasharray="2 1.5"/><path class="r" d="M16.5 5h6"/>',
    section: '<path class="f" d="M5 4h14v3H13.5v10H19v3H5v-3h5.5V7H5z"/><path d="M5 4h14v3H13.5v10H19v3H5v-3h5.5V7H5z"/>',
    material: '<path class="f" d="M3 9l9-5 9 5-9 5z"/><path d="M3 9l9-5 9 5-9 5zM3 9v7l9 5 9-5V9M12 14v7"/><circle cx="8" cy="15" r=".6" fill="currentColor"/><circle cx="16" cy="15.5" r=".6" fill="currentColor"/>',
    // loads
    aload: '<path class="f" d="M2.5 18l4-4h15l-4 4z"/><path d="M2.5 18l4-4h15l-4 4z"/><path class="r" d="M7 3v8M12 3v8M17 3v8M5.5 9l1.5 2 1.5-2M10.5 9l1.5 2 1.5-2M15.5 9l1.5 2 1.5-2"/>',
    lload: '<path class="f" d="M2.5 16h19v3h-19z"/><path d="M2.5 16h19v3h-19z"/><path class="r" d="M3 5h18M5 5v8.5M9.7 5v8.5M14.3 5v8.5M19 5v8.5M3.8 12l1.2 1.5 1.2-1.5M8.5 12l1.2 1.5 1.2-1.5M13.1 12l1.2 1.5 1.2-1.5M17.8 12l1.2 1.5 1.2-1.5"/>',
    pload: '<path class="f" d="M3 18h18v3H3z"/><path d="M3 18h18v3H3z"/><path class="r" d="M12 2.5v13M8.5 12.5l3.5 3.5 3.5-3.5"/>',
    combo: '<path d="M17.5 4H6.5l6 8-6 8h11"/>',
    newcase: '<path class="f" d="M5 3h9.5L19 7.5V21H5z"/><path d="M5 3h9.5L19 7.5V21H5z"/><path class="r" d="M12 10v7M8.5 13.5h7"/>',
    rename: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path class="f" d="M15 5l4 4 2-2-4-4z"/>',
    // seismic / analysis options
    seismic: '<path d="M2 12h3l2-6 3 12 3-15 3 15 2-6h4"/>',
    wind: '<path class="r" d="M3 8h11a3 3 0 1 0-3-3"/><path d="M3 12h16a3 3 0 1 1-3 3"/><path class="r" d="M3 16h7"/>',
    spectrum: '<path d="M3 3v18h18"/><path class="r" d="M4 17l3-10h5c2 0 3 2 4 4.5S19 17 21 17.5"/>',
    pdelta: '<path d="M8 21V4" stroke-dasharray="2 1.5"/><path d="M8 21C8 14 11 8 16 4"/><path class="r" d="M16 1v4M14 3l2 2 2-2"/><path d="M8 4h8"/>',
    regular: '<circle cx="12" cy="12" r="8.5"/><circle class="f" cx="12" cy="12" r="3.5"/><circle cx="12" cy="12" r="3.5"/><path d="M12 1.5v4M12 18.5v4M1.5 12h4M18.5 12h4"/>',
    drift: '<path class="f" d="M5 21V5h7v16"/><path d="M5 21V5h7v16M2 21h13"/><path d="M5 5l3 0M12 5h0" /><path class="r" d="M14 8h7M18.5 5.5L21 8l-2.5 2.5"/>',
    found: '<path d="M8 3v10h8V3"/><path class="f" d="M3 13h18v4H3z"/><path d="M3 13h18v4H3z"/><path d="M2 21h20" stroke-dasharray="2 1.5"/>',
    soil: '<path class="f" d="M2 9h20v12H2z"/><path d="M2 9h20M2 13.5h20M2 18h20"/><path d="M5 11l1 .8M10 15.5l1 .8M15 11l1 .8M18 19.8l1 .8"/>',
    // design
    design: '<path class="f" d="M8 4h8v16H8z"/><path d="M8 4h8v16H8z"/><path d="M10 7v10M14 7v10M8 9h8M8 15h8"/>',
    capacity: '<path d="M12 3v18M4 7h16"/><path class="f" d="M4 7l-2.5 6h5z"/><path d="M4 7l-2.5 6h5zM20 7l-2.5 4h5z"/><path d="M8 21h8"/>',
    // results
    diagM: '<path d="M2.5 9h19"/><path class="f r" d="M2.5 9c3 9 16 9 19 0z"/><path class="r" d="M2.5 9c3 9 16 9 19 0"/><path d="M2.5 6v6M21.5 6v6"/>',
    diagV: '<path d="M2.5 12h19"/><path class="f r" d="M2.5 12V6h9.5v6zM12 12v6h9.5v-6z"/><path class="r" d="M2.5 12V6h9.5v12h9.5v-6"/>',
    diagN: '<path d="M2.5 12h19"/><path class="f r" d="M2.5 7h19v5h-19z"/><path class="r" d="M2.5 7h19v5"/><path d="M4 14.5l-1.5 1.5 1.5 1.5M20 14.5l1.5 1.5-1.5 1.5M2.5 16h19"/>',
    defl: '<path d="M2.5 6h19" stroke-dasharray="2 1.5"/><path class="r" d="M2.5 6c5 10 14 10 19 0"/><path d="M2.5 4v4M21.5 4v4"/>',
    mode: '<path d="M7 21V4M17 21V4M7 9h10M7 14.5h10" stroke-dasharray="1.6 1.4"/><path class="r" d="M7 21c0-6 1.5-11 4.5-17M17 21c0-6 1.5-11 4.5-17M8.5 14.5h10M10 9h10.5"/>',
    play: '<circle class="f" cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="9.5"/><path d="M10 8l6 4-6 4z" fill="currentColor"/>',
    pause: '<circle class="f" cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="9.5"/><path d="M9.5 8v8M14.5 8v8" stroke-width="2.4"/>',
    modes: '<path d="M3 21V3"/><path d="M3 20c7-2 12-9 14-17"/><path class="r" d="M3 20c4-4 10-6 18-6"/>',
    qty: '<path class="f" d="M5 21v-8h3v8zM10.5 21V5h3v16zM16 21v-11h3v11z"/><path d="M5 21v-8h3v8zM10.5 21V5h3v16zM16 21v-11h3v11zM2.5 21h19"/>',
    tag: '<path class="f" d="M3 12V3h9l9 9-9 9z"/><path d="M3 12V3h9l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    // navigation / window / help
    zin: '<circle class="f" cx="10" cy="10" r="6.5"/><circle cx="10" cy="10" r="6.5"/><path d="M15 15l6 6M7 10h6M10 7v6"/>',
    zout: '<circle class="f" cx="10" cy="10" r="6.5"/><circle cx="10" cy="10" r="6.5"/><path d="M15 15l6 6M7 10h6"/>',
    fit: '<path d="M3 8.5V3h5.5M15.5 3H21v5.5M21 15.5V21h-5.5M8.5 21H3v-5.5"/><rect class="f" x="7.5" y="7.5" width="9" height="9"/><rect x="7.5" y="7.5" width="9" height="9"/>',
    full: '<path d="M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6"/><path d="M3 3l6 6M21 3l-6 6M21 21l-6-6M3 21l6-6"/>',
    theme: '<path class="f" d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z"/><path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z"/>',
    manual: '<path class="f" d="M3 4.5h7a2 2 0 0 1 2 2V20a2 2 0 0 0-2-2H3z"/><path d="M3 4.5h7a2 2 0 0 1 2 2V20a2 2 0 0 0-2-2H3zM21 4.5h-7a2 2 0 0 0-2 2V20a2 2 0 0 1 2-2h7z"/>',
    keys: '<rect class="f" x="2" y="6" width="20" height="12" rx="2"/><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.5M10 10h.5M14 10h.5M18 10h.5M7 14h10"/>',
    min: '<path d="M6 15l6-6 6 6"/>',
  };
  const icon = (k) => `<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${P[k] || P.tag}</svg>`;

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
    // Workflow order of professional programs (ETABS / Revit / Tekla):
    // File → Home → Draw → Define → Loads → Analyse → Design → Results → View → Help
    const tl = (id) => S.tool === id;
    const v = (id) => S.view === id;
    const nStorey = S.inp.storeys.length;
    const ft = String(S.inp.found_type || "");
    const nModes = Math.min(6, S.res?.structure?.modes?.length || 3);
    return [
      ["file", t("File"), [
        group(t("Project"), btn("new", t("New"), t("Start a new building from the example? The current one will be replaced."), newBuilding, { big: true }),
          btn("open", t("Open"), `${t("Open")} (Ctrl+O)`, () => $("#file-open").click(), { big: true }),
          btn("save", t("Save"), `${t("Save")} (Ctrl+S)`, save, { big: true }),
          btn("project", t("Project details"), t("Company, project, job number, engineer — printed on every report page"), projectDialog, { big: true })),
        group(t("Code"), btn("annex", t("National Annex"), t("National Annex"), () => {}, { big: true }), col(annexSelect(true))),
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
          btn("auto", t("Auto"), t("Re-analyse automatically after every change"), toggleAuto, { big: true, on: S.auto }),
          btn("autosize", t("Auto-size"), t("Enlarge members and adjust options until every Eurocode check passes"), autoSize, { big: true })),
        group(t("Views"), btn("plan", t("Plan"), t("Plan"), () => setView("plan"), { big: true, on: v("plan") }),
          btn("cube", "3D", "3D (Ctrl+3)", () => setView("3d"), { big: true, on: v("3d") }),
          btn("split", t("Plan + 3D"), t("Plan + 3D"), () => setView("split"), { big: true, on: v("split") }),
          btn("table", t("Table"), t("Table"), () => setView("table"), { big: true, on: v("table") }),
          btn("report", t("Report"), t("Report"), () => setView("report"), { big: true, on: v("report") })),
      ]],
      ["draw", t("Draw"), [
        group(t("Elements"), btn("select", t("Select"), `${t("Select")} (V)`, () => setTool("select"), { big: true, on: tl("select") }),
          btn("column", t("Column"), `${t("Click a grid point to place a column.")} (C)`, () => setTool("column"), { big: true, on: tl("column") }),
          btn("wallx", t("Wall X"), `${t("Click a grid point to place a wall.")} (W)`, () => setTool("wallX"), { big: true, on: tl("wallX") }),
          btn("wally", t("Wall Y"), `${t("Click a grid point to place a wall.")} (W)`, () => setTool("wallY"), { big: true, on: tl("wallY") }),
          btn("beam", t("Beam"), `${t("Click between two grid points to add or remove a beam.")} (B)`, () => setTool("beam"), { big: true, on: tl("beam") }),
          btn("opening", t("Opening"), `${t("Click a slab panel to open or close it.")} (O)`, () => setTool("opening"), { big: true, on: tl("opening") })),
        group(t("Grid"), btn("grid", t("Grid wizard"), t("A regular grid replaces the current one (walls and edits outside it are removed)."), gridWizard, { big: true }),
          col(btn("axisx", t("+ Axis X"), "", () => axis("x_spans", 1)), btn("axisx", t("− Axis X"), "", () => axis("x_spans", -1))),
          col(btn("axisy", t("+ Axis Y"), "", () => axis("y_spans", 1)), btn("axisy", t("− Axis Y"), "", () => axis("y_spans", -1)))),
        group(`${t("Storeys")} (${nStorey})`, btn("storeyadd", t("+ Storey"), "", () => storey(1), { big: true }),
          btn("storeydel", t("− Storey"), "", () => storey(-1), { big: true, disabled: nStorey <= 1 })),
        group(t("Modify"), btn("del", t("Delete"), `${t("Delete")} (Del)`, removeSel, { big: true, disabled: !S.sel.length })),
      ]],
      ["define", t("Define"), [
        group(t("Materials"), btn("material", t("Concrete"), "", () => {}, { big: true }), col(ctl("concrete", { width: 80 }), ctl("fyk", { width: 56 }), ctl("cover", { width: 56 }))),
        group(t("Default sections"), btn("section", t("Sections"), t("Sizes used where no member has its own (select a member to change only that one)"), () => {}, { big: true }),
          col(ctl("col_b", { width: 56 }), ctl("col_h", { width: 56 })), col(ctl("beam_b", { width: 56 }), ctl("beam_h", { width: 56 }), ctl("slab_t", { width: 56 }))),
        group(t("Seismic action"), col(tog("seismic", "EN 1998-1"), ctl("ag", { width: 56 })), col(ctl("ground", { width: 56 }), ctl("importance", { width: 56 })),
          ...(curAnnex()?.zones?.length ? [col(...curAnnex().zones.map((z) =>
            btn("seismic", z.label, `a_gR = ${z.ag} g`, () => { S.inp.ag = z.ag; renderRibbon(); commit(); }, { on: Math.abs(S.inp.ag - z.ag) < 1e-9 })))] : [])),
      ]],
      ["found", t("Foundation"), [
        group(t("Foundation"), btn("found", t("Foundation plan"), "", () => { S.opt.storey = "found"; saveView(); setView("plan"); renderRibbon(); }, { big: true, on: S.opt.storey === "found" }),
          col(tog("foundations", t("Design foundation")), ctl("found_type", { width: 150 }))),
        ...(ft.startsWith("Raft") ? [group(t("Raft"), col(ctl("raft_t", { width: 56 }), ctl("raft_over", { width: 56 }), ctl("raft_mesh", { width: 56 })))] :
          ft.startsWith("Foundation beams") ? [group(t("Foundation beams"), col(ctl("fb_B", { width: 56 }), ctl("fb_bw", { width: 56 }), ctl("fb_h", { width: 56 })))] : []),
        group(t("Soil"), btn("soil", t("Soil"), "", () => {}, { big: true }), col(ctl("D_found", { width: 52 }), ctl("phi_soil", { width: 52 }), ctl("ks", { width: 52 })),
          col(ctl("c_soil", { width: 52 }), ctl("gamma_soil", { width: 52 }))),
      ]],
      ["loads", t("Loads"), [
        group(t("Area loads"), col(ctl("g_finish", { width: 52 }), ctl("q", { width: 52 }), ctl("category", { width: 52 })),
          col(ctl("q_roof", { width: 52 }), ctl("g_wall", { width: 52 }))),
        group(t("Wind"), btn("wind", t("Wind"), t("Include wind (EN 1991-1-4)"), () => { S.inp.wind = !S.inp.wind; renderRibbon(); commit(); }, { big: true, on: !!S.inp.wind }),
          col(tog("wind_site", t("NA wind map")), ctl("wind_vb0", { width: 52, label: "v_b,0 [m/s]" })), col(ctl("wind_terrain", { width: 52, label: t("Terrain") }), ctl("wind_co", { width: 52, label: "c_o" }))),
        group(t("Load case"), col((() => {
          const sel = el("select", { on: { change: (e) => { S.lcase = e.target.value || null; renderRibbon(); drawPlan(); } } },
            el("option", { value: "", title: t("Built-in case — edit its loads in the Loads tab values") }, "G / Q"),
            ...ucases().map((c) => el("option", { value: c.name }, c.name)));
          sel.value = S.lcase || "";
          sel.style.width = "150px";
          return sel;
        })(), (() => {
          const c = curCase();
          const ty = el("select", { disabled: c ? null : "", on: { change: (e) => { c.type = e.target.value; commit(); renderRibbon(); } } },
            el("option", { value: "G" }, t("Permanent G")), el("option", { value: "Q" }, t("Imposed Q")), el("option", { value: "S" }, t("Snow S")));
          ty.value = c?.type || "G";
          ty.style.width = "92px";
          const cat = el("select", { disabled: c && c.type === "Q" ? null : "", title: t("Category"), on: { change: (e) => { c.category = e.target.value; commit(); } } },
            ..."ABCDE".split("").map((x) => el("option", { value: x }, x)));
          cat.value = c?.category || "A";
          return el("div", { class: "rb-row" }, ty, cat);
        })()), col(btn("newcase", t("New case"), "", newCase), btn("rename", t("Rename"), "", renameCase, { disabled: !curCase() }),
          btn("del", t("Delete case"), "", deleteCase, { disabled: !curCase() }))),
        group(t("Apply loads"), btn("aload", t("Area load"), t("Click slab panels to add / remove the area load of the current case."), () => setTool("aload"), { big: true, on: S.tool === "aload" }),
          btn("lload", t("Line load"), t("Click beams to add / remove the line load of the current case."), () => setTool("lload"), { big: true, on: S.tool === "lload" }),
          btn("pload", t("Point load"), t("Click grid points to add / remove the point load of the current case."), () => setTool("pload"), { big: true, on: S.tool === "pload" }),
          col(...[["area", "q", "kN/m²"], ["line", "w", "kN/m"], ["point", "F", "kN"]].map(([k, sym, u]) => el("label", { class: "rb-ctl", title: t({ area: "Area load", line: "Line load", point: "Point load" }[k]) },
            el("span", {}, sym),
            el("input", { type: "number", step: "0.5", value: S.lval[k], style: "width:52px", on: { change: (e) => { S.lval[k] = parseFloat(e.target.value) || 0; } } }),
            el("small", {}, u)))),
          col(el("label", { class: "rb-ctl" }, el("span", {}, t("On storeys")), (() => {
            const ss = el("select", { on: { change: (e) => { S.lstorey = e.target.value; } } },
              el("option", { value: "all" }, t("All floors")), el("option", { value: "roof" }, t("Roof")),
              ...S.inp.storeys.map((_, k) => el("option", { value: String(k + 1) }, `${t("Storey")} ${k + 1}`)));
            ss.value = S.lstorey;
            return ss;
          })(), el("small", {}, "")))),
        group(t("Combinations"), btn("combo", t("Combinations…"), "", combosDialog, { big: true })),
      ]],
      ["analyse", t("Analyse"), [
        group(t("Run"), btn("run", t("Run"), t("Run the analysis (F5)"), () => run(), { big: true, on: S.dirty }),
          btn("auto", t("Auto"), t("Re-analyse automatically after every change"), toggleAuto, { big: true, on: S.auto })),
        group(t("Response spectrum"), btn("spectrum", t("Spectrum"), "", () => gotoReport("Design spectrum"), { big: true }),
          col(ctl("q_factor", { width: 52 }), ctl("n_modes", { width: 52 }), ctl("phi_E", { width: 52 }))),
        group(t("Wind"), btn("wind", t("Wind"), t("Include wind (EN 1991-1-4)"), () => { S.inp.wind = !S.inp.wind; renderRibbon(); commit(); }, { big: true, on: !!S.inp.wind }),
          btn("table", t("Wind forces"), "", () => gotoReport("Wind on the building"), { big: true, disabled: !S.inp.wind })),
        group(t("Stiffness"), col(ctl("cracked", { width: 52 }), tog("pdelta", t("P-Δ"))), btn("pdelta", t("P-Δ"), t("Include the destabilising effect of the gravity loads"), () => { S.inp.pdelta = !S.inp.pdelta; renderRibbon(); commit(); }, { big: true, on: !!S.inp.pdelta })),
        group(t("Regularity"), btn("regular", t("Regularity"), "", () => gotoReport("Structural regularity"), { big: true }), col(tog("regularity", t("Apply to q")))),
        group(t("Storey checks"), btn("drift", t("Storey checks"), "", () => gotoReport("Storey checks"), { big: true }), col(ctl("drift", { width: 150 }))),
      ]],
      ["design", t("Design"), [
        group(t("Options"), btn("design", t("Members"), t("Design members"), () => { S.inp.design = !S.inp.design; renderRibbon(); commit(); }, { big: true, on: !!S.inp.design }),
          col(tog("capacity", t("Capacity design")), tog("slabs", t("Design slabs")), tog("foundations", t("Design foundation")))),
        group(t("Member design"), btn("design", t("Design results"), t("Design results of the selected member (double-click a member)"), openDesignForSel, { big: true, disabled: !S.sel.length || !S.res })),
        group(t("Auto-size"), btn("autosize", t("Auto-size"), t("Enlarge members and adjust options until every Eurocode check passes"), autoSize, { big: true })),
        group(t("Member tables"), btn("table", t("Table"), "", () => setView("table"), { big: true, on: v("table") }),
          btn("selfail", t("Failing members"), "", selectFailing, { big: true }), btn("csv", t("Table CSV"), "", csv, { big: true })),
      ]],
      ["results", t("Results"), [
        group(t("Modes"), (() => {
          const ms = el("select", { on: { change: (e) => { showMode(Number(e.target.value)); } } },
            ...Array.from({ length: nModes }, (_, k) => {
              const md = S.res?.structure?.modes?.[k];
              return el("option", { value: String(k + 1) }, md ? `${k + 1}: T = ${md.T.toFixed(3)} s (${md.type === "RZ" ? t("torsion") : md.type})` : `${t("Mode")} ${k + 1}`);
            }));
          ms.value = String(S.mode || 1);
          ms.style.width = "170px";
          return col(ms, el("label", { class: "rb-ctl", title: t("Speed") }, el("span", {}, t("Speed")),
            el("input", { type: "range", min: "0.3", max: "3", step: "0.1", value: S.animSpeed || 1, style: "width:90px",
              on: { input: (e) => { S.animSpeed = Number(e.target.value); window.dispatchEvent(new CustomEvent("erisma:anim", { detail: { host: "st-3d", on: S.anim, speed: S.animSpeed } })); } } }), el("small", {}, "")));
        })(), btn("mode", t("Show mode"), t("Show / hide in the 3D view"), () => showMode(S.mode || 1, true), { big: true, on: !!S.layers[`mode${S.mode || 1}`] }),
          btn(S.anim ? "pause" : "play", S.anim ? t("Stop") : t("Animate"), t("Animate the mode / deformed shape in the 3D view"), toggleAnim, { big: true, on: S.anim })),
        group(t("Diagrams"), ...[["diagM", "Moments M", "dM"], ["diagV", "Shear V", "dV"], ["diagN", "Axial N", "dN"],
          ["defl", "Deformed", "defl"]].map(([ic, lab, key]) => btn(ic, t(lab), t("Show / hide in the 3D view"), () => layer3d(key), { big: true, on: !!S.layers[key] }))),
        group(t("Colour by"), col(...[["util", t("Utilisation")], ["rho", t("Steel ratio")], ["status", t("Pass / fail")]]
          .map(([k, lab]) => { const r = el("input", { type: "radio", name: "rb-col", on: { change: () => { S.opt.colour = k; saveView(); drawPlan(); } } }); r.checked = S.opt.colour === k; return el("label", { class: "rb-chk" }, r, el("span", {}, lab)); }))),
        group(t("Storey shown"), col((() => {
          const s2 = el("select", { on: { change: (e) => { S.opt.storey = e.target.value; saveView(); drawPlan(); } } },
            el("option", { value: "all" }, t("All storeys")), ...S.inp.storeys.map((_, k) => el("option", { value: String(k + 1) }, `${t("Storey")} ${k + 1}`)),
            el("option", { value: "found" }, t("Foundation")));
          s2.value = S.opt.storey in { all: 1, found: 1 } || +S.opt.storey <= nStorey ? S.opt.storey : "all";
          return s2;
        })(), viewTog("labels", t("Reinforcement")), viewTog("names", t("Names")))),
        group(t("Reports"), btn("modes", t("Modes"), "", () => gotoReport("Masses and modal analysis"), { big: true }),
          btn("qty", t("Quantities"), "", () => gotoReport("Quantities and cost estimate"), { big: true }),
          btn("report", t("Report"), "", () => setView("report"), { big: true })),
      ]],
      ["view", t("View"), [
        group(t("Views"), btn("plan", t("Plan"), "", () => setView("plan"), { big: true, on: v("plan") }),
          btn("cube", "3D", "Ctrl+3", () => setView("3d"), { big: true, on: v("3d") }),
          btn("split", t("Plan + 3D"), "", () => setView("split"), { big: true, on: v("split") }),
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

  // ------------------------------------------------------------ modes, animation, project details
  // while a mode / deformed shape is shown, the solid model is hidden (wireframe + shape)
  function solidFor() {
    const shape = Object.entries(S.layers).some(([k, on]) => on && (k.startsWith("mode") || k === "defl"));
    return { frame: !shape, slabs: !shape, found: !shape, ghost: !shape };
  }
  function showMode(n, toggle = false) {
    const prev = S.mode || 1;
    S.mode = n;
    const key = `mode${n}`;
    const on = toggle ? !S.layers[key] : true;
    const show = {};
    for (let k = 1; k <= 6; k++) { S.layers[`mode${k}`] = false; show[`mode${k}`] = false; }
    S.layers[key] = on; show[key] = on;
    if (on && S.view !== "3d" && S.view !== "split") setView("split");
    window.dispatchEvent(new CustomEvent("erisma:layers", { detail: { host: "st-3d", show: { ...show, ...solidFor() } } }));
    if (prev !== n || toggle) renderRibbon();
  }
  function toggleAnim() {
    S.anim = !S.anim;
    if (S.anim && !Object.entries(S.layers).some(([k, on]) => on && (k.startsWith("mode") || k === "defl"))) showMode(S.mode || 1);
    window.dispatchEvent(new CustomEvent("erisma:anim", { detail: { host: "st-3d", on: S.anim, speed: S.animSpeed || 1 } }));
    renderRibbon();
  }
  function toggleAuto() { S.auto = !S.auto; renderRibbon(); if (S.auto && S.dirty) run(); }
  function projectDialog() {
    const fields = (typeof PROJECT_FIELDS !== "undefined" ? PROJECT_FIELDS : []);
    const dlg = el("dialog", { class: "st-dlg" }, el("h3", {}, t("Project details")),
      ...fields.map(([key, label]) => el("label", { class: "st-f" }, el("span", {}, t(label)),
        el("span", { class: "inp" }, el("input", { type: key === "date" ? "date" : "text", value: state.project[key] || "", "data-k": key })))),
      el("div", { class: "btns" }, el("button", { type: "button", class: "ghost", on: { click: () => dlg.close() } }, t("Cancel")),
        el("button", { type: "button", class: "primary", on: { click: () => {
          dlg.querySelectorAll("input[data-k]").forEach((i) => { state.project[i.dataset.k] = i.value; });
          store.set("erisma.project", state.project);
          if (typeof renderProject === "function") renderProject();
          dlg.close(); changed();
        } } }, t("Save"))));
    document.body.append(dlg);
    dlg.addEventListener("close", () => dlg.remove());
    dlg.showModal();
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
        on: { click: () => { S.tab = id; if (S.opt.ribbonMin) { S.opt.ribbonMin = false; saveView(); } renderRibbon(); drawPlan(); },
          dblclick: () => { S.opt.ribbonMin = !S.opt.ribbonMin; saveView(); renderRibbon(); } } }, label)),
      el("span", { class: "grow" }),
      el("span", { class: "rb-title" }, `Erisma Structure · ${curAnnex()?.label || "EN"}`),
      (() => { const b = el("button", { type: "button", class: "rb-min", title: t("Collapse ribbon"), on: { click: () => { S.opt.ribbonMin = !S.opt.ribbonMin; saveView(); renderRibbon(); } } }); b.innerHTML = icon("min"); return b; })());
    box.append(tabsRow);
    const body = el("div", { class: "rb-body" }, ...all.find(([id]) => id === S.tab)[2]);
    box.append(body);
  }

  // ------------------------------------------------------------ tools, views, selection
  const HINTS = () => ({ select: `${t("Click a column, wall, beam or slab panel in the plan.")} ${t("Shift+click adds to the selection; drag a window to select several.")}`,
    column: t("Click a grid point to place a column."), wallX: t("Click a grid point to place a wall."),
    wallY: t("Click a grid point to place a wall."), beam: t("Click between two grid points to add or remove a beam."),
    opening: t("Click a slab panel to open or close it."),
    aload: t("Click slab panels to add / remove the area load of the current case."),
    lload: t("Click beams to add / remove the line load of the current case."),
    pload: t("Click grid points to add / remove the point load of the current case.") });
  const TOOLN = () => ({ select: t("Select"), column: t("Column"), wallX: t("Wall X"), wallY: t("Wall Y"), beam: t("Beam"), opening: t("Opening"),
    aload: t("Area load"), lload: t("Line load"), pload: t("Point load") });
  function setTool(id) {
    S.tool = id;
    $("#st-hint").textContent = HINTS()[id];
    $("#sb-tool").textContent = `✎ ${TOOLN()[id]}`;
    if (S.view !== "plan" && S.view !== "split" && S.view !== "3d") setView("plan");
    renderRibbon();
  }
  function setView(v) {
    S.view = v;
    const split = v === "split";
    $("#structure .st-center").classList.toggle("split", split);
    document.querySelectorAll(".st-pane").forEach((p) => p.classList.toggle("on",
      p.dataset.pane === v || (split && (p.dataset.pane === "plan" || p.dataset.pane === "3d"))));
    if (v === "3d" || split) setTimeout(() => window.dispatchEvent(new CustomEvent("erisma:show3d", { detail: { host: "st-3d" } })), 30);
    if (v === "plan" || split) drawPlan();
    if (v === "table") renderTable();
    renderRibbon();
  }
  const highlight3d = () => window.dispatchEvent(new CustomEvent("erisma:highlight",
    { detail: { host: "st-3d", picks: S.sel.map((x) => `${x.kind}:${x.id}`) } }));
  function layer3d(key) {
    S.layers[key] = !S.layers[key];
    if (S.view !== "3d" && S.view !== "split") setView("split");
    window.dispatchEvent(new CustomEvent("erisma:layers", { detail: { host: "st-3d", show: { [key]: S.layers[key], ...solidFor() } } }));
    renderRibbon();
  }
  window.addEventListener("erisma:pick", (e) => {
    if (e.detail.host !== "st-3d" || !document.body.classList.contains("in-structure")) return;
    if (!e.detail.pick) { if (S.tool === "select" && !e.detail.shift) setSel([]); return; }
    const [kind, id] = e.detail.pick.split(":");
    const now = Date.now();
    if (S.lastPick && S.lastPick.p === e.detail.pick && now - S.lastPick.t < 400 && S.tool === "select") {
      const key = memberKeyOf(kind, id);     // double-click in 3D → design results
      S.lastPick = null;
      if (key) { designDialog(key); return; }
    }
    S.lastPick = { p: e.detail.pick, t: now };
    act(kind, id, e.detail.shift);
  });
  function setSel(list) {
    S.sel = list;
    highlight3d();
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
      // drift utilisation bars d_r ν / (α h): ν, α from the report → use the EC8 check values
      const checks = (S.res?.summary?.checks || []).filter((c) => /d_r ν ≤ α h/.test(c.description));
      if (checks.length) {
        const chart = el("div", { class: "st-drift" }, el("div", { class: "st-lt" }, t("Drift d_r·ν / (α·h) per storey")));
        for (const c of checks) {
          const u = Math.min(c.utilisation, 1.2);
          chart.append(el("div", { class: "st-dbar", title: c.description },
            el("span", {}, (/(\d+)[^:]*?([XY])\s*:/.exec(c.description) || []).slice(1).join(" ")),
            el("i", { style: `width:${u / 1.2 * 100}%;background:${c.passed ? heat(0.85 * u ** 2) : "#e03b3b"}` }),
            el("b", {}, c.utilisation.toFixed(2))));
        }
        box.append(chart);
      }
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
      if (pc && S.opt.storey !== "found") { r.style.fill = pc; r.style.fillOpacity = "0.13"; }
      sv("title", {}, r).textContent = `${t("Slab panel")} ${id}${open.has(id) ? ` — ${t("Open (no slab)")}` : ""}` +
        (sr.length ? `\n${sr.map((x) => `${t("Storey")} ${x.storey}: ${x.reinforcement} (η = ${x.util.toFixed(2)})`).join("\n")}` : "");
      tag(r, "panel", id);
      if (S.opt.labels && sr.length && S.opt.storey !== "found") sv("text", { x: X((xs[i] + xs[i + 1]) * 500), y: Y((ys[j] + ys[j + 1]) * 500), "font-size": unit * 1.1, class: "st-rlbl", "text-anchor": "middle" }, gTxt)
        .textContent = shortR("panel", sr[sr.length - 1].reinforcement);
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
        const worst = [...r].sort((p, q) => q.util - p.util)[0];
        const tx = horiz ? mx : mx - unit * 1.6, ty = horiz ? my + unit * 2.0 : my;
        const e = sv("text", { x: tx, y: ty, "font-size": unit * 1.25, class: "st-rlbl", "text-anchor": "middle",
          transform: horiz ? "" : `rotate(-90 ${tx} ${ty})` }, gTxt);
        e.textContent = shortR("beam", (S.opt.storey === "all" ? worst : r[0]).reinforcement) + (S.opt.storey === "all" && r.length > 1 ? " *" : "");
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
        if (S.opt.labels && r.length) sv("text", { x: cx + unit * 1.2, y: cy + unit * 2.4, "font-size": unit * 1.25, class: "st-rlbl", "text-anchor": "start" }, gTxt)
          .textContent = shortR("column", [...r].sort((p, q) => q.util - p.util)[0].reinforcement);
      }
      const c = kind === "point" ? null : colourFor(kind, id);
      if (c) node.style.fill = c;
      tag(node, kind, id);
      if (S.opt.names) sv("text", { x: cx + unit * 1.2, y: cy - unit * 1.2, "font-size": unit * 1.7, class: "st-plbl" }, gTxt).textContent = id;
      if (S.opt.names && csz[id] && kind === "column") sv("text", { x: cx + unit * 1.2, y: cy + unit * 1.0, "font-size": unit * 1.2, class: "st-mname" }, gTxt).textContent = `${csz[id][0]}×${csz[id][1]}`;
    }
    // loads of the current user load case
    const c = (S.tab === "loads" || ["aload", "lload", "pload"].includes(S.tool)) ? curCase() : null;
    if (c) {
      const gL = sv("g", { class: "st-loads" }, svg);
      const stTxt = (st) => (st === "all" ? "" : st === "roof" ? ` (${t("Roof")})` : ` (${t("Storey")} ${st.join(",")})`);
      for (const ld of c.loads) {
        if (ld.kind === "area") for (const pid of ld.panels || []) {
          const [i0, j0] = idx(pid);
          if (i0 >= nx - 1 || j0 >= ny - 1) continue;
          const x0 = xs[i0] * 1000, x1 = xs[i0 + 1] * 1000, y0 = ys[j0] * 1000, y1 = ys[j0 + 1] * 1000;
          sv("rect", { x: X(x0) + unit, y: Y(y1) + unit, width: x1 - x0 - 2 * unit, height: y1 - y0 - 2 * unit, class: "st-lrect", "stroke-width": unit * 0.3 }, gL);
          sv("text", { x: (x0 + x1) / 2, y: Y((y0 + y1) / 2), "font-size": unit * 1.8, class: "st-ltxt" }, gL).textContent = `${ld.q} kN/m²${stTxt(ld.storeys)}`;
        }
        if (ld.kind === "line") for (const key of ld.beams || []) {
          const [a, b] = key.split("-").map(idx);
          const x1 = X(xs[a[0]] * 1000), y1 = Y(ys[a[1]] * 1000), x2 = X(xs[b[0]] * 1000), y2 = Y(ys[b[1]] * 1000);
          sv("line", { x1, y1, x2, y2, class: "st-lline", "stroke-width": unit * 0.6 }, gL);
          sv("text", { x: (x1 + x2) / 2, y: (y1 + y2) / 2 - unit * 1.5, "font-size": unit * 1.5, class: "st-ltxt" }, gL).textContent = `${ld.w} kN/m${stTxt(ld.storeys)}`;
        }
        if (ld.kind === "point") for (const g of ld.points || []) {
          const [i0, j0] = idx(g);
          if (i0 >= nx || j0 >= ny) continue;
          const cx = X(xs[i0] * 1000), cy = Y(ys[j0] * 1000);
          sv("circle", { cx, cy, r: unit * 1.8, class: "st-lpt", "stroke-width": unit * 0.4 }, gL);
          sv("text", { x: cx, y: cy - unit * 2.6, "font-size": unit * 1.5, class: "st-ltxt" }, gL).textContent = `↓ ${ld.F} kN${stTxt(ld.storeys)}`;
        }
      }
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
      const pk = `${target.dataset.kind}:${target.dataset.id}`, now = Date.now();
      if (S.tool === "select" && S.lastPlanClick?.p === pk && now - S.lastPlanClick.t < 400) {
        S.lastPlanClick = null;                 // as in Tekla: double-click → design results
        const key = memberKeyOf(target.dataset.kind, target.dataset.id);
        if (key) { designDialog(key); return; }
      }
      S.lastPlanClick = { p: pk, t: now };
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
    const rk = memberKeyOf(kind, id);
    if (rk) item(`🔍 ${t("Design results")}`, () => designDialog(rk));
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
    if (tool === "aload" && kind === "panel") return toggleLoad("area", id);
    if (tool === "lload" && kind === "beam") return toggleLoad("line", id);
    if (tool === "pload" && point) return toggleLoad("point", id);
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
    highlight3d();
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
            el("td", {}, r.util.toFixed(2)), el("td", {}, el("button", { type: "button", class: "mini", title: t("Design results"),
              on: { click: () => designDialog(r.id) } }, "🔍"), el("button", { type: "button", class: "mini", title: t("Open in the member calculation"),
              on: { click: () => openModule(r.module, r.inputs) } }, "↗"))));
        }
        box.append(el("h4", {}, t("Results")), tb);
        const notes = [...new Set(res.flatMap((r) => r.notes))];
        if (notes.length) box.append(el("ul", { class: "st-notes" }, ...notes.map((n) => el("li", {}, n))));
      }
    }
  }

  // ------------------------------------------------------------ design results (Tekla-style)
  // One window per member, as the member design dialogs of Tekla Structural Designer: status,
  // section sketch with the bars, beam elevation with the link zones, every check with its
  // ratio and clause, the design forces, and a check mode in which the engineer sets the bars.
  const BARS = ["10", "12", "14", "16", "18", "20", "22", "25", "28", "32"];
  function memberKeyOf(kind, id) {
    const r = resultsFor(kind, id);
    if (!r.length) return null;
    const st = S.opt.storey;
    return (r.find((x) => String(x.storey) === st) || [...r].sort((a, b) => b.util - a.util)[0]).id;
  }
  function sectionSVG(kind, inp, det) {
    const wide = kind === "wall";
    const W = wide ? 900 : 230, Hm = wide ? 120 : 230;
    const g = sv("svg", { class: wide ? "dr-sec wide" : "dr-sec", viewBox: `0 0 ${W} ${Hm}` });
    let b, h;
    if (kind === "column") { b = inp.b; h = inp.h; } else if (kind === "beam") { b = inp.b; h = inp.h; } else if (kind === "wall") { b = inp.lw * 1000; h = inp.bw; } else return null;
    const k = Math.min((W - 60) / b, (Hm - 60) / h);
    const x0 = (W - b * k) / 2, y0 = (Hm - h * k) / 2;
    sv("rect", { x: x0, y: y0, width: b * k, height: h * k, class: "conc" }, g);
    const cov = inp.cover ?? inp.cnom ?? 30;
    const ld = parseFloat(kind === "column" ? (inp.link || "8") : kind === "beam" ? (det.link_dia || inp.link_dia || "8") : (inp.dh || "10"));
    const inset = (cov + ld / 2) * k;
    sv("rect", { x: x0 + inset, y: y0 + inset, width: b * k - 2 * inset, height: h * k - 2 * inset, rx: 3, class: "link" }, g);
    const bar = (x, y, d) => sv("circle", { cx: x, cy: y, r: Math.max(d * k / 2, 2.2), class: "bar" }, g);
    const off = (d) => (cov + ld + d / 2) * k;
    if (kind === "column") {
      const d = parseFloat(inp.dia), n = +inp.nb, o = off(d);
      for (let i = 0; i < n; i++) {
        const x = x0 + o + (b * k - 2 * o) * i / (n - 1), y = y0 + o + (h * k - 2 * o) * i / (n - 1);
        bar(x, y0 + o, d); bar(x, y0 + h * k - o, d);
        if (i > 0 && i < n - 1) { bar(x0 + o, y, d); bar(x0 + b * k - o, y, d); }
      }
    } else if (kind === "beam") {
      for (const [face, row] of [["top", det.top], ["bottom", det.bottom]]) {
        const d = parseFloat(row.dia), n = row.n_bars, o = off(d);
        const y = face === "top" ? y0 + o : y0 + h * k - o;
        for (let i = 0; i < n; i++) bar(n === 1 ? x0 + b * k / 2 : x0 + o + (b * k - 2 * o) * i / (n - 1), y, d);
      }
    } else if (kind === "wall") {
      const d = parseFloat(inp.dbe), n = +inp.nbe, lc = inp.lc * k, o = off(d);
      for (const xe of [x0, x0 + b * k - lc]) {
        sv("rect", { x: xe + 2, y: y0 + 2, width: lc - 4, height: h * k - 4, class: "zone" }, g);
        const per = Math.ceil(n / 2);
        for (let i = 0; i < per; i++) {
          const x = xe + o + (lc - 2 * o) * (per === 1 ? 0.5 : i / (per - 1));
          bar(x, y0 + o, d); bar(x, y0 + h * k - o, d);
        }
      }
      const dv = parseFloat(inp.dv || "10"), svv = +(inp.sv || 200), ow = off(dv);
      for (let x = inp.lc + svv / 2; x < b - inp.lc; x += svv) {
        sv("circle", { cx: x0 + x * k, cy: y0 + ow, r: Math.max(dv * k / 2, 1.8), class: "bar web" }, g);
        sv("circle", { cx: x0 + x * k, cy: y0 + h * k - ow, r: Math.max(dv * k / 2, 1.8), class: "bar web" }, g);
      }
      const tl = (x, y, s_) => { const e = sv("text", { x, y, "text-anchor": "middle", class: "lbl" }, g); e.textContent = s_; };
      tl(x0 + lc / 2, y0 - 8, `${n}Ø${inp.dbe} · Ø${inp.dh}/${inp.sh}`);
      tl(x0 + b * k - lc / 2, y0 - 8, `${n}Ø${inp.dbe} · Ø${inp.dh}/${inp.sh}`);
      tl(x0 + b * k / 2, y0 - 8, `${t("Web")}: Ø${inp.dv}/${inp.sv} + Ø${inp.dhw}/${inp.shw}`);
    }
    const tx = (x, y, s_, a = "middle") => { const e = sv("text", { x, y, "text-anchor": a, class: "dim" }, g); e.textContent = s_; };
    tx(x0 + b * k / 2, y0 + h * k + 16, `${Math.round(b)}`);
    tx(x0 - 6, y0 + h * k / 2 + 4, `${Math.round(h)}`, "end");
    return g;
  }
  function elevationSVG(inp, det) {
    const W = 900, H = 168, L = det.L || 4000, h = inp.h;
    const g = sv("svg", { class: "dr-elev", viewBox: `0 0 ${W} ${H}` });
    const k = (W - 40) / L, kh = Math.min(56 / h, 0.2);
    const x0 = 20, y0 = 30, hh = h * kh;
    sv("rect", { x: x0, y: y0, width: L * k, height: hh, class: "conc" }, g);
    sv("rect", { x: x0 - 10, y: y0 - 10, width: 10, height: hh + 40, class: "sup" }, g);
    sv("rect", { x: x0 + L * k, y: y0 - 10, width: 10, height: hh + 40, class: "sup" }, g);
    const lcr = det.l_cr || 0, scr = det.s_cr || det.s, s = det.s;
    for (let x = 50; x < L - 25; ) {
      const crit = x < lcr || x > L - lcr;
      sv("line", { x1: x0 + x * k, x2: x0 + x * k, y1: y0 + 3, y2: y0 + hh - 3, class: crit ? "lnk crit" : "lnk" }, g);
      x += crit ? scr : s;
    }
    sv("line", { x1: x0 + 4, x2: x0 + L * k - 4, y1: y0 + 6, y2: y0 + 6, class: "rb" }, g);
    sv("line", { x1: x0 + 4, x2: x0 + L * k - 4, y1: y0 + hh - 6, y2: y0 + hh - 6, class: "rb" }, g);
    const tx = (x, y, s_, cls = "dim", a = "middle") => { const e = sv("text", { x, y, "text-anchor": a, class: cls }, g); e.textContent = s_; };
    tx(x0 + L * k / 2, y0 - 6, `${t("Top")}: ${det.top.n_bars}Ø${det.top.dia}`, "lbl");
    tx(x0 + L * k / 2, y0 + hh + 16, `${t("Bottom")}: ${det.bottom.n_bars}Ø${det.bottom.dia}`, "lbl");
    if (lcr) {
      tx(x0 + lcr * k / 2, y0 + hh + 34, `Ø${det.link_dia}/${scr}`, "lbl crit");
      tx(x0 + (L - lcr / 2) * k, y0 + hh + 34, `Ø${det.link_dia}/${scr}`, "lbl crit");
      tx(x0 + L * k / 2, y0 + hh + 34, `Ø${det.link_dia}/${s}`, "lbl");
      tx(x0 + lcr * k / 2, y0 + hh + 48, `l_cr = ${lcr}`, "dim");
    } else tx(x0 + L * k / 2, y0 + hh + 34, `Ø${det.link_dia}/${s}`, "lbl");
    tx(x0 + L * k / 2, H - 4, `L = ${(L / 1000).toFixed(2)} m`, "dim");
    return g;
  }

  function wallElevationSVG(inp, outs) {
    const W = 230, H = 300, Hw = inp.Hw * 1000, lw = inp.lw * 1000, n = +inp.storeys || 1;
    const g = sv("svg", { class: "dr-sec", viewBox: `0 0 ${W} ${H}` });
    const k = Math.min((W - 70) / lw, (H - 40) / Hw), x0 = (W - lw * k) / 2 + 10, yb = H - 20;
    const hcr = (outs["h_cr"]?.value || 0) * 1000;
    sv("rect", { x: x0, y: yb - Hw * k, width: lw * k, height: Hw * k, class: "conc" }, g);
    if (hcr) sv("rect", { x: x0, y: yb - hcr * k, width: lw * k, height: hcr * k, class: "crit" }, g);
    const lc = inp.lc * k;
    for (const xe of [x0, x0 + lw * k - lc]) sv("rect", { x: xe, y: yb - (hcr || Hw) * k, width: lc, height: (hcr || Hw) * k, class: "zone" }, g);
    for (let i = 1; i < n; i++) sv("line", { x1: x0 - 6, x2: x0 + lw * k + 6, y1: yb - Hw * k * i / n, y2: yb - Hw * k * i / n, class: "fl" }, g);
    sv("line", { x1: x0 - 14, x2: x0 + lw * k + 14, y1: yb, y2: yb, class: "gr" }, g);
    const tx = (x, y, s_, cls = "dim", a = "middle") => { const e = sv("text", { x, y, "text-anchor": a, class: cls }, g); e.textContent = s_; };
    if (hcr) tx(x0 - 4, yb - hcr * k / 2, `h_cr = ${(hcr / 1000).toFixed(2)} m`, "lbl crit", "end");
    tx(x0 + lw * k / 2, yb + 14, `l_w = ${inp.lw} m`);
    tx(x0 + lw * k + 4, yb - Hw * k + 10, `H_w = ${inp.Hw} m`, "dim", "start");
    return g;
  }
  function slabPlanSVG(inp, outs) {
    const W = 230, H = 230, lx = inp.lx * 1000, ly = inp.ly * 1000;
    const g = sv("svg", { class: "dr-sec", viewBox: `0 0 ${W} ${H}` });
    const k = Math.min((W - 60) / lx, (H - 60) / ly), x0 = (W - lx * k) / 2, y0 = (H - ly * k) / 2;
    sv("rect", { x: x0, y: y0, width: lx * k, height: ly * k, class: "conc" }, g);
    const fixed = (e) => String(inp[e]).startsWith("Fixed");
    const edges = { e1: [x0, y0, x0, y0 + ly * k], e2: [x0 + lx * k, y0, x0 + lx * k, y0 + ly * k], e3: [x0, y0 + ly * k, x0 + lx * k, y0 + ly * k], e4: [x0, y0, x0 + lx * k, y0] };
    const band = 0.25;
    for (const [e, [x1, y1, x2, y2]] of Object.entries(edges)) {
      sv("line", { x1, y1, x2, y2, class: fixed(e) ? "edge fix" : "edge ss" }, g);
      if (!fixed(e)) continue;
      // top bars over the continuous edge (extending ~0.25 l into the panel)
      const vert = x1 === x2, L = (vert ? lx : ly) * band * k;
      const inward = vert ? (x1 === x0 ? 1 : -1) : (y1 === y0 ? 1 : -1);
      for (let tpos = 0.1; tpos < 0.95; tpos += 0.1) {
        if (vert) { const y = y1 + (y2 - y1) * tpos; sv("line", { x1, x2: x1 + inward * L, y1: y, y2: y, class: "top" }, g); }
        else { const x = x1 + (x2 - x1) * tpos; sv("line", { x1: x, x2: x, y1, y2: y1 + inward * L, class: "top" }, g); }
      }
    }
    // bottom mesh
    for (let tpos = 0.2; tpos < 0.85; tpos += 0.15) {
      sv("line", { x1: x0 + 6, x2: x0 + lx * k - 6, y1: y0 + ly * k * tpos, y2: y0 + ly * k * tpos, class: "bot" }, g);
      sv("line", { x1: x0 + lx * k * tpos, x2: x0 + lx * k * tpos, y1: y0 + 6, y2: y0 + ly * k - 6, class: "bot" }, g);
    }
    const tx = (x, y, s_, cls = "dim", a = "middle") => { const e = sv("text", { x, y, "text-anchor": a, class: cls }, g); e.textContent = s_; };
    tx(x0 + lx * k / 2, y0 + ly * k + 16, `l_x = ${inp.lx} m`);
    tx(x0 - 6, y0 + ly * k / 2, `l_y = ${inp.ly} m`, "dim", "end");
    const mv = (key) => outs[key] ? outs[key].value.toFixed(1) : null;
    if (mv("m_x,span")) tx(x0 + lx * k / 2, y0 + ly * k / 2 - 4, `m_x = ${mv("m_x,span")}`, "lbl");
    if (mv("m_y,span")) tx(x0 + lx * k / 2, y0 + ly * k / 2 + 12, `m_y = ${mv("m_y,span")}`, "lbl");
    return g;
  }
  function nmSVG(nm, kind) {
    const W = 520, H = 330, padL = 60, padB = 36, padT = 14, padR = 16;
    const g = sv("svg", { class: "dr-nm", viewBox: `0 0 ${W} ${H}` });
    const curves = Object.entries(nm.curves);
    const pts = [];
    for (const p of nm.points) {
      if (kind === "wall") pts.push({ N: p.N, M: p.M, name: p.name, ax: "strong" });
      else { pts.push({ N: p.N, M: p.Mh, name: p.name, ax: "h" }); pts.push({ N: p.N, M: p.Mb, name: p.name, ax: "b" }); }
    }
    const allN = curves.flatMap(([, c]) => c.map((q) => q[0])).concat(pts.map((p) => p.N));
    const allM = curves.flatMap(([, c]) => c.map((q) => q[1])).concat(pts.map((p) => p.M));
    const Nmin = Math.min(...allN), Nmax = Math.max(...allN), Mmax = Math.max(...allM) * 1.08;
    const X = (M) => padL + (M + Mmax) / (2 * Mmax) * (W - padL - padR);
    const Y = (N) => H - padB - (N - Nmin) / (Nmax - Nmin) * (H - padB - padT);
    sv("line", { x1: X(0), x2: X(0), y1: padT, y2: H - padB, class: "ax" }, g);
    sv("line", { x1: padL, x2: W - padR, y1: Y(0), y2: Y(0), class: "ax" }, g);
    const colours = { h: "#1f6fb2", b: "#7c3aed", strong: "#1f6fb2" };
    const cap = {};
    for (const [ax, c] of curves) {
      if (kind === "column" && ax === "b" && nm.curves.b === nm.curves.h) continue;
      const half = c.map((q) => `${X(q[1])},${Y(q[0])}`).join(" ");
      const mirror = [...c].reverse().map((q) => `${X(-q[1])},${Y(q[0])}`).join(" ");
      sv("polygon", { points: `${half} ${mirror}`, class: "curve", stroke: colours[ax] }, g);
      const sorted = [...c].sort((a, b) => a[0] - b[0]);
      cap[ax] = (N) => { for (let i = 1; i < sorted.length; i++) if (N <= sorted[i][0]) { const [n1, m1] = sorted[i - 1], [n2, m2] = sorted[i]; return m1 + (m2 - m1) * (N - n1) / ((n2 - n1) || 1); } return 0; };
    }
    for (const p of pts) {
      const f = cap[p.ax] || cap.h;
      const ok = f && p.N <= Nmax && p.M <= f(p.N) + 1e-9;
      const c = sv("circle", { cx: X(p.M), cy: Y(p.N), r: 3.6, class: ok ? "pt ok" : "pt bad" }, g);
      sv("title", {}, c).textContent = `${p.name} — N = ${p.N.toFixed(0)} kN, M = ${p.M.toFixed(0)} kNm${kind === "column" ? ` (${p.ax})` : ""}`;
    }
    const tx = (x, y, s_, cls = "dim", a = "middle") => { const e = sv("text", { x, y, "text-anchor": a, class: cls }, g); e.textContent = s_; };
    tx(W - padR, Y(0) - 5, "M [kNm]", "dim", "end");
    tx(X(0) + 5, padT + 10, `N [kN] (${t("compression")} +)`, "dim", "start");
    for (const v of [-Mmax / 1.08, Mmax / 1.08]) tx(X(v), H - padB + 14, v.toFixed(0));
    for (const v of [Nmin, Nmax]) tx(padL - 4, Y(v) + 4, v.toFixed(0), "dim", "end");
    if (kind === "column") tx(W - padR, H - 6, t("blue: bending about h · purple: about b (first-order design actions)"), "dim", "end");
    return g;
  }
  function designDialog(key) {
    const m = S.res?.structure?.members?.[key];
    if (!m) return;
    const kind = m.kind, inp = m.inputs || {}, det = m.detail || {};
    const dlg = el("dialog", { class: "st-dlg wide dr" });
    let tab = "checks";
    const sec = { span: t("Span (sagging)"), support: t("Supports (hogging)"), ec8: t("EN 1998-1 detailing (critical regions)"), "": "" };
    const draw = () => {
      dlg.innerHTML = "";
      const size = kind === "wall" ? `${inp.lw} m × ${inp.bw} mm` : kind === "slab" ? `h = ${inp.h} mm` : inp.b ? `${inp.b}×${inp.h}` : "";
      dlg.append(el("div", { class: "dr-head" },
        el("div", {}, el("h3", {}, `${KIND()[kind] || kind} ${key}`),
          el("div", { class: "muted" }, [`${t("Storey")} ${m.storey}`, size, inp.concrete, inp.fyk ? `B${inp.fyk}` : ""].filter(Boolean).join(" · "))),
        el("div", { class: `dr-status ${m.ok ? "pass" : "fail"}` }, m.ok ? t("Pass") : t("Fail"), el("small", {}, `η = ${m.util.toFixed(2)}`)),
        det.override ? el("div", { class: "dr-mode" }, t("Check mode")) : el("div", { class: "dr-mode auto" }, t("Design mode"))));
      const left = el("div", { class: "dr-left" });
      const outs = m.outputs || {};
      const sx = kind === "wall" ? wallElevationSVG(inp, outs) : kind === "slab" ? slabPlanSVG(inp, outs) : sectionSVG(kind, inp, det);
      if (sx) left.append(sx);
      if (kind === "slab") left.append(el("div", { class: "dr-legend" },
        el("span", {}, el("i", { style: "background:#1f6fb2" }), t("bottom bars")), el("span", {}, el("i", { style: "background:#b3261e" }), t("top bars")),
        el("span", {}, el("i", { style: "background:#374151;height:5px" }), t("continuous edge")), el("span", {}, el("i", { style: "background:repeating-linear-gradient(90deg,#6b7280 0 5px,transparent 5px 8px)" }), t("simply supported"))));
      if (kind === "wall") left.append(el("div", { class: "dr-legend" },
        el("span", {}, el("i", { style: "background:#d97706" }), t("critical region h_cr")), el("span", {}, el("i", { style: "background:#1f6fb2" }), t("boundary elements"))));
      left.append(el("div", { class: "dr-reinf" }, m.reinforcement));
      if (m.notes.length) left.append(el("ul", { class: "st-notes" }, ...m.notes.map((n) => el("li", {}, n))));
      const right = el("div", { class: "dr-right" });
      const tabs = [["checks", t("Checks")], ["forces", t("Design forces")]];
      if (m.nm) tabs.push(["nm", "N–M"]);
      if (["beam", "column", "wall", "slab"].includes(kind)) tabs.push(["edit", t("Reinforcement")]);
      right.append(el("div", { class: "dr-tabs" }, ...tabs.map(([k, l]) => el("button", { type: "button", class: tab === k ? "on" : "", on: { click: () => { tab = k; draw(); } } }, l))));
      if (tab === "checks") {
        const tb = el("table", { class: "st-res dr-checks" }, el("tr", {}, el("th", {}, t("Check")), el("th", {}, t("Demand")), el("th", {}, t("Resistance")), el("th", {}, "η"), el("th", {}, ""), el("th", {}, t("Clause"))));
        let last = null;
        for (const c of m.checks || []) {
          if (c.section !== last && c.section) tb.append(el("tr", { class: "grp" }, el("td", { colspan: 6 }, sec[c.section] || c.section)));
          last = c.section;
          const u = Math.min(c.u, 1.5);
          const f = (v) => (v == null ? "" : Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(3));
          tb.append(el("tr", { class: c.ok ? "" : "bad", title: c.hint || "" }, el("td", {}, c.d), el("td", { class: "num" }, `${f(c.demand)} ${c.unit || ""}`), el("td", { class: "num" }, `${f(c.capacity)} ${c.unit || ""}`),
            el("td", { class: "util" }, el("span", { class: "ubar" }, el("i", { style: `width:${(u / 1.5) * 100}%;background:${c.ok ? (c.u > 0.9 ? "#e0a020" : "#2e9b5f") : "#e03b3b"}` })), el("b", {}, c.u.toFixed(2))),
            el("td", {}, c.ok ? "✓" : "✗"), el("td", { class: "muted" }, c.ref)));
        }
        if (!(m.checks || []).length) tb.append(el("tr", {}, el("td", { colspan: 6, class: "muted" }, t("Open the full calculation for the checks."))));
        right.append(tb);
      } else if (tab === "forces") {
        const rows = [];
        if (kind === "beam") {
          rows.push([t("Span (sagging)"), "M_Ed", `${det.M_sag.toFixed(1)} kNm`, det.gov_sag], [t("Supports (hogging)"), "M_Ed", `${det.M_hog.toFixed(1)} kNm`, det.gov_hog],
            [t("Shear"), "V_Ed", `${det.V.toFixed(1)} kN`, det.gov_V]);
        } else if (kind === "column") {
          rows.push(["N", "N_Ed", `${(+inp.NEd).toFixed(1)} kN`, m.governing], ["M (h)", "M_top / M_bot", `${(+inp.Mh_top).toFixed(1)} / ${(+inp.Mh_bot).toFixed(1)} kNm`, m.governing],
            ["M (b)", "M_top / M_bot", `${(+inp.Mb_top).toFixed(1)} / ${(+inp.Mb_bot).toFixed(1)} kNm`, m.governing], [t("Shear"), "V_Ed", `${(+inp.VEd).toFixed(1)} kN`, m.governing]);
        } else if (kind === "slab") {
          const o = m.outputs || {};
          for (const k of ["g_k", "q_k", "p_d", "m_x,span", "m_y,span", "m_x,sup", "m_y,sup"]) if (o[k]) rows.push([o[k].d || k, k, `${o[k].value.toFixed(2)} ${o[k].unit}`, k === "p_d" || k.startsWith("m_") ? "1.35G + 1.5Q" : ""]);
        } else {
          for (const [k, u] of [["NEd", "kN"], ["MEd", "kNm"], ["VEd", "kN"]]) if (inp[k] != null) rows.push([k, k, `${(+inp[k]).toFixed(1)} ${u}`, m.governing]);
        }
        right.append(el("table", { class: "st-res" }, el("tr", {}, el("th", {}, ""), el("th", {}, ""), el("th", {}, t("Value")), el("th", {}, t("Governing"))),
          ...rows.map((r) => el("tr", {}, ...r.map((v) => el("td", {}, v || ""))))));
        if (m.nm?.points?.length) {
          const P = m.nm.points;
          right.append(el("h4", {}, t("Every design combination")), el("table", { class: "st-res" },
            el("tr", {}, el("th", {}, t("Combination")), el("th", {}, "N_Ed [kN]"), ...(kind === "wall" ? [el("th", {}, "M_Ed [kNm]")] : [el("th", {}, "M_h [kNm]"), el("th", {}, "M_b [kNm]")])),
            ...P.map((p) => el("tr", { class: p.name === m.governing ? "gov" : "" }, el("td", {}, p.name), el("td", { class: "num" }, p.N.toFixed(1)),
              ...(kind === "wall" ? [el("td", { class: "num" }, p.M.toFixed(1))] : [el("td", { class: "num" }, p.Mh.toFixed(1)), el("td", { class: "num" }, p.Mb.toFixed(1))])))));
        }
      } else if (tab === "nm") {
        right.append(nmSVG(m.nm, kind), el("p", { class: "muted" }, t("Design interaction curve (EN 1992-1-1 6.1, ε_cu = 3.5 ‰); dots = design actions of every combination — green inside, red outside.")));
      } else if (tab === "edit") {
        const ov = structuredClone(lay().reinf?.[key] || {});
        const selB = (val, on, opts = BARS) => { const s_ = el("select", { on: { change: (e) => on(e.target.value) } }, ...opts.map((o) => el("option", { value: o }, `Ø${o}`))); s_.value = String(val); return s_; };
        const num = (val, on, mn, mx, st = 1) => el("input", { type: "number", min: mn, max: mx, step: st, value: val, style: "width:64px", on: { change: (e) => on(+e.target.value) } });
        const row = (lab, ...c) => el("label", { class: "st-f" }, el("span", {}, lab), el("span", { class: "inp" }, ...c));
        const box = el("div", { class: "dr-edit" });
        if (kind === "beam") {
          const top = { n: ov.top_n ?? det.top.n_bars, d: ov.top_dia ?? det.top.dia }, bot = { n: ov.bottom_n ?? det.bottom.n_bars, d: ov.bottom_dia ?? det.bottom.dia };
          box.append(row(t("Top bars"), num(top.n, (v) => { ov.top_n = v; ov.top_dia ??= top.d; }, 2, 10), selB(top.d, (v) => { ov.top_dia = v; ov.top_n ??= top.n; })),
            row(t("Bottom bars"), num(bot.n, (v) => { ov.bottom_n = v; ov.bottom_dia ??= bot.d; }, 2, 10), selB(bot.d, (v) => { ov.bottom_dia = v; ov.bottom_n ??= bot.n; })),
            row(t("Links (span)"), selB(ov.link_dia ?? det.link_dia, (v) => { ov.link_dia = v; }, ["8", "10", "12"]), num(ov.s ?? det.s, (v) => { ov.s = v; }, 50, 300, 25)));
        } else if (kind === "wall") {
          box.append(row(t("Boundary element bars"), num(ov.nbe ?? inp.nbe, (v) => { ov.nbe = v; }, 4, 30, 2), selB(ov.dbe ?? inp.dbe, (v) => { ov.dbe = v; })),
            row(t("Boundary hoops"), selB(ov.dh ?? inp.dh, (v) => { ov.dh = v; }, ["8", "10", "12"]), num(ov.sh ?? inp.sh, (v) => { ov.sh = v; }, 50, 250, 5)),
            row(t("Web vertical (each face)"), selB(ov.dv ?? inp.dv, (v) => { ov.dv = v; }, ["8", "10", "12", "14", "16"]), num(ov.sv ?? inp.sv, (v) => { ov.sv = v; }, 75, 400, 25)),
            row(t("Web horizontal (each face)"), selB(ov.dhw ?? inp.dhw, (v) => { ov.dhw = v; }, ["8", "10", "12", "14", "16"]), num(ov.shw ?? inp.shw, (v) => { ov.shw = v; }, 75, 400, 25)));
        } else if (kind === "slab") {
          box.append(row(t("Bottom bars (both directions)"), selB(ov.dia_b ?? inp.dia_b, (v) => { ov.dia_b = v; }, ["8", "10", "12", "14", "16"]), num(ov.s_b ?? inp.s_b, (v) => { ov.s_b = v; }, 75, 300, 25)),
            row(t("Top bars over supports"), selB(ov.dia_t ?? inp.dia_t, (v) => { ov.dia_t = v; }, ["8", "10", "12", "14", "16"]), num(ov.s_t ?? inp.s_t, (v) => { ov.s_t = v; }, 75, 300, 25)));
        } else {
          box.append(row(t("Bars per side"), num(ov.nb ?? inp.nb, (v) => { ov.nb = v; }, 2, 6), selB(ov.dia ?? inp.dia, (v) => { ov.dia = v; })),
            row(t("Links"), selB(ov.link ?? inp.link ?? "8", (v) => { ov.link = v; }, ["8", "10", "12"]), num(ov.s ?? inp.s, (v) => { ov.s = v; }, 50, 300, 5)));
        }
        box.append(el("p", { class: "muted" }, t("Check mode: the member is checked with these bars instead of the automatic design; the whole building is re-analysed.")));
        box.append(el("div", { class: "btns" },
          det.override ? el("button", { type: "button", class: "ghost", on: { click: async () => { delete lay().reinf[key]; commit(false); await run(); dlg.close(); designDialog(key); } } }, t("Back to automatic design")) : "",
          el("button", { type: "button", class: "primary", on: { click: async () => { (lay().reinf ||= {})[key] = ov; commit(false); await run(); dlg.close(); designDialog(key); } } }, t("Check"))));
        right.append(box);
      }
      const body = el("div", { class: "dr-body" }, left, right);
      dlg.append(body);
      if (kind === "beam" && det.top) dlg.append(el("h4", {}, t("Elevation")), elevationSVG(inp, det));
      if (kind === "wall") dlg.append(el("h4", {}, t("Section in the critical region")), sectionSVG(kind, inp, det));
      dlg.append(el("div", { class: "btns" }, m.module ? el("button", { type: "button", class: "ghost", on: { click: () => { dlg.close(); openModule(m.module, m.inputs); } } }, `↗ ${t("Full calculation")}`) : "",
        el("button", { type: "button", class: "primary", on: { click: () => dlg.close() } }, t("Close"))));
    };
    draw();
    document.body.append(dlg);
    dlg.addEventListener("close", () => dlg.remove());
    dlg.showModal();
  }
  function openDesignForSel() {
    const s0 = S.sel[0];
    const key = s0 && memberKeyOf(s0.kind, s0.id);
    if (key) designDialog(key);
    else $("#sb-msg").textContent = t("Select a designed member (after the analysis) to see its design results.");
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

  // ------------------------------------------------------------ National Annex (project-wide)
  const curAnnex = () => (state.annexes || []).find((a) => a.code === (state.project.annex || "EN"));
  function annexSelect(bare = false) {
    const sel = el("select", { title: t("National Annex"), on: { change: (e) => {
      state.project.annex = e.target.value;
      store.set("erisma.project", state.project);
      if (typeof renderProject === "function") renderProject();
      renderRibbon(); changed();
    } } }, ...(state.annexes || []).map((a) => el("option", { value: a.code, title: a.reference }, a.label)));
    sel.value = state.project.annex || "EN";
    sel.style.width = bare ? "200px" : "170px";
    if (bare) return el("div", { class: "rb-row" }, sel);
    return el("label", { class: "rb-ctl" }, el("span", {}, t("National Annex")), sel, el("small", {}, ""));
  }

  // ------------------------------------------------------------ load cases
  const L_ = () => (S.inp.loads ||= { cases: [], combos: [] });
  const ucases = () => (L_().cases ||= []);
  const curCase = () => ucases().find((c) => c.name === S.lcase) || null;
  function newCase() {
    const name = prompt(t("Name of the new load case"), `G${ucases().filter((c) => c.type === "G").length + 2}`);
    if (!name || name === "G" || name === "Q" || ucases().some((c) => c.name === name)) return;
    ucases().push({ name, type: "G", category: "A", loads: [] });
    S.lcase = name; renderRibbon(); commit();
  }
  function renameCase() {
    const c = curCase(); if (!c) return;
    const name = prompt(t("New name"), c.name);
    if (!name || name === "G" || name === "Q" || ucases().some((x) => x.name === name)) return;
    for (const cb of L_().combos || []) if (cb.factors?.[c.name] != null) { cb.factors[name] = cb.factors[c.name]; delete cb.factors[c.name]; }
    c.name = name; S.lcase = name; renderRibbon(); commit();
  }
  function deleteCase() {
    const c = curCase(); if (!c) return;
    L_().cases = ucases().filter((x) => x !== c);
    S.lcase = ucases()[0]?.name || null; renderRibbon(); commit();
  }
  const storeySel = () => (S.lstorey === "all" ? "all" : S.lstorey === "roof" ? "roof" : [Number(S.lstorey)]);
  function toggleLoad(kind, id) {
    const c = curCase();
    if (!c) { newCase(); return; }
    const key = { area: "panels", line: "beams", point: "points" }[kind];
    const st = JSON.stringify(storeySel());
    const ld = c.loads.find((l) => l.kind === kind && JSON.stringify(l.storeys) === st && Array.isArray(l[key]) && l[key].includes(id));
    if (ld) {
      ld[key] = ld[key].filter((x) => x !== id);
      if (!ld[key].length) c.loads = c.loads.filter((l) => l !== ld);
    } else {
      const val = S.lval[kind];
      let grp = c.loads.find((l) => l.kind === kind && JSON.stringify(l.storeys) === st && Array.isArray(l[key]) &&
        (l.q ?? l.w ?? l.F) === val);
      if (!grp) { grp = { kind, storeys: storeySel(), [key]: [], [kind === "area" ? "q" : kind === "line" ? "w" : "F"]: val }; c.loads.push(grp); }
      grp[key].push(id);
    }
    commit();
  }
  function combosDialog() {
    const r = S.res?.structure || {};
    const names = (r.cases || [{ name: "G" }, { name: "Q" }]).map((c) => c.name);
    const user = structuredClone(L_().combos || []);
    const dlg = el("dialog", { class: "st-dlg wide" });
    const draw = () => {
      dlg.innerHTML = "";
      dlg.append(el("h3", {}, t("Combinations")), el("h4", {}, t("Generated (EN 1990)")));
      if (r.combos) {
        dlg.append(el("table", { class: "st-res" }, el("tr", {}, el("th", {}, t("Combination")), el("th", {}, t("Kind")), el("th", {}, t("Expression"))),
          ...r.combos.filter((c) => c.kind !== "user").map((c) => el("tr", {}, el("td", {}, c.name), el("td", {}, c.kind), el("td", {}, c.text)))));
      } else dlg.append(el("p", { class: "muted" }, t("Run the analysis to see the generated combinations.")));
      dlg.append(el("h4", {}, t("User combinations")));
      const tb = el("table", { class: "st-res" }, el("tr", {}, el("th", {}, t("Combination")), ...names.map((n) => el("th", {}, n)), el("th", {}, "")));
      user.forEach((cb, k) => {
        cb.factors ||= {};
        tb.append(el("tr", {}, el("td", {}, el("input", { value: cb.name || "", on: { change: (e) => { cb.name = e.target.value; } } })),
          ...names.map((n) => el("td", {}, el("input", { type: "number", step: "0.05", value: cb.factors[n] ?? "", style: "width:64px",
            on: { change: (e) => { const v = parseFloat(e.target.value); if (Number.isFinite(v)) cb.factors[n] = v; else delete cb.factors[n]; } } }))),
          el("td", {}, el("button", { type: "button", class: "mini", on: { click: () => { user.splice(k, 1); draw(); } } }, "×"))));
      });
      dlg.append(tb, el("button", { type: "button", class: "mini add", on: { click: () => { user.push({ name: `User ${user.length + 1}`, factors: { G: 1.35 } }); draw(); } } }, `+ ${t("Add combination")}`),
        el("div", { class: "btns" }, el("button", { type: "button", class: "ghost", on: { click: () => dlg.close() } }, t("Cancel")),
          el("button", { type: "button", class: "primary", on: { click: () => { L_().combos = user; dlg.close(); commit(); } } }, t("Save"))));
    };
    draw();
    document.body.append(dlg);
    dlg.addEventListener("close", () => dlg.remove());
    dlg.showModal();
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
      if (res.model3d) {
        window.dispatchEvent(new CustomEvent("erisma:model3d", { detail: { host: "st-3d", model: res.model3d, summary: res.summary } }));
        const shown = Object.fromEntries(["dM", "dV", "dN", "defl", "mode1", "mode2", "mode3", "mode4", "mode5", "mode6"].map((k) => [k, !!S.layers[k]]));
        window.dispatchEvent(new CustomEvent("erisma:layers", { detail: { host: "st-3d", show: { ...shown, ...solidFor() } } }));
        window.dispatchEvent(new CustomEvent("erisma:anim", { detail: { host: "st-3d", on: S.anim, speed: S.animSpeed || 1 } }));
        highlight3d();
      }
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
    if (r.modes?.length) {
      const kind = { X: "X", Y: "Y", RZ: t("torsion") };
      sm.append(el("h4", {}, t("Modes")), el("table", { class: "st-res" },
        el("tr", {}, el("th", {}, "#"), el("th", {}, "T [s]"), el("th", {}, "m_X"), el("th", {}, "m_Y"), el("th", {}, "m_RZ"), el("th", {}, "")),
        ...r.modes.slice(0, 6).map((md) => el("tr", { class: md.type === "RZ" && md.mode === 1 ? "bad" : "" },
          el("td", {}, String(md.mode)), el("td", {}, md.T.toFixed(3)), el("td", {}, `${(md.mX * 100).toFixed(0)}%`),
          el("td", {}, `${(md.mY * 100).toFixed(0)}%`), el("td", {}, `${((md.mRZ || 0) * 100).toFixed(0)}%`),
          el("td", {}, el("button", { type: "button", class: "mini", title: t("Show / hide in the 3D view"),
            on: { click: () => md.mode <= 3 && layer3d(`mode${md.mode}`) } }, kind[md.type] || ""))))));
    }
    if (r.regularity) {
      const g = r.regularity, yes = (b, a, b2) => el("span", { class: b ? "ok" : "bad" }, b ? a : b2);
      sm.append(el("h4", {}, `${t("Regularity")} (EC8 4.2.3)`), el("table", { class: "st-sum" },
        el("tr", {}, el("td", {}, t("plan")), el("td", {}, yes(g.plan, t("regular"), t("not regular")))),
        el("tr", {}, el("td", {}, t("elevation")), el("td", {}, yes(g.elevation, t("regular"), t("not regular")))),
        el("tr", {}, el("td", {}, "r ≥ l_s"), el("td", {}, yes(!g.torsional, t("torsionally stiff"), t("torsionally flexible")))),
        el("tr", {}, el("td", {}, t("q used")), el("td", {}, g.q_used != null ? g.q_used.toFixed(2) : "—"))));
    }
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
