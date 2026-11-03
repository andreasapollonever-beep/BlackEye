"""User manual (Greek / English), generated from the written chapters below and from the
modules themselves (inputs, units, ranges, help texts and the checks each module performs),
so the reference part can never drift from the program."""

from __future__ import annotations

import html
from functools import lru_cache

from . import __version__
from .core import all_modules
from .design.annex import ANNEXES
from .i18n import tr

E = html.escape

# ------------------------------------------------------------------ chapters
CHAPTERS: list[tuple[str, dict[str, str], dict[str, str]]] = [
    ("intro", {"en": "1. What Erisma is", "el": "1. Τι είναι το Erisma"}, {
        "en": """
<p>Erisma is a suite of structural and geotechnical calculations to the Eurocodes. Every
calculation is written out step by step — <b>input → formula → value → clause → check</b> —
so that the engineer can verify each number by hand and submit the calculation sheet.</p>
<ul>
<li><b>Results while you type:</b> checks, report and 3D model update after every change.</li>
<li><b>Worked examples as defaults:</b> every calculation opens with realistic values that pass,
so you always start from a sensible design and change only what differs.</li>
<li><b>Hints:</b> every failing check says what to change (“increase the base width…”).</li>
<li><b>National Annexes:</b> partial factors and nationally determined parameters are read from
the annex chosen in the project details and listed in every report.</li>
<li><b>Verified:</b> each module is tested against hand calculations and published values.</li>
</ul>
<p class="warn">Erisma is a tool for qualified engineers. The engineer remains responsible for
the model, the input values and the interpretation of the results.</p>""",
        "el": """
<p>Το Erisma είναι σύνολο στατικών και γεωτεχνικών υπολογισμών κατά τους Ευρωκώδικες. Κάθε
υπολογισμός γράφεται βήμα-βήμα — <b>δεδομένο → τύπος → τιμή → άρθρο κανονισμού → έλεγχος</b> —
ώστε ο μηχανικός να μπορεί να επαληθεύσει κάθε αριθμό με το χέρι και να υποβάλει το τεύχος.</p>
<ul>
<li><b>Αποτελέσματα καθώς γράφετε:</b> έλεγχοι, τεύχος και 3D μοντέλο ενημερώνονται σε κάθε
αλλαγή.</li>
<li><b>Ρεαλιστικά παραδείγματα ως προεπιλογές:</b> κάθε υπολογισμός ανοίγει με τιμές που
επαρκούν· αλλάζετε μόνο ό,τι διαφέρει στο έργο σας.</li>
<li><b>Συμβουλές:</b> κάθε έλεγχος που δεν επαρκεί λέει τι να αλλάξετε («αυξήστε το πλάτος
της βάσης…»).</li>
<li><b>Εθνικά Προσαρτήματα:</b> οι συντελεστές ασφαλείας και οι εθνικά καθοριζόμενες
παράμετροι διαβάζονται από το προσάρτημα των στοιχείων έργου και καταγράφονται σε κάθε τεύχος.</li>
<li><b>Επαληθευμένο:</b> κάθε υπολογισμός ελέγχεται με υπολογισμούς στο χέρι και δημοσιευμένες
τιμές.</li>
</ul>
<p class="warn">Το Erisma είναι εργαλείο για διπλωματούχους μηχανικούς. Την ευθύνη για το
προσομοίωμα, τα δεδομένα και την ερμηνεία των αποτελεσμάτων έχει ο μηχανικός.</p>"""}),
    ("start", {"en": "2. Installation and start", "el": "2. Εγκατάσταση και εκκίνηση"}, {
        "en": """
<ol>
<li>Install <a href="https://www.python.org/downloads/">Python 3.10 or newer</a> (on Windows
tick <i>Add Python to PATH</i>).</li>
<li>Unzip <code>Erisma.zip</code> into a folder of your choice.</li>
<li><b>Windows:</b> double-click <code>Erisma.bat</code>. <b>Mac:</b> right-click
<code>Erisma.command</code> → Open.</li>
</ol>
<p>The first start installs the program (1–2 minutes, internet needed once). Erisma then opens
by itself in your browser at <code>http://127.0.0.1:8000</code>. Everything runs on your own
computer and works offline; nothing is sent to the internet. To stop Erisma close the black
window.</p>""",
        "el": """
<ol>
<li>Εγκαταστήστε την <a href="https://www.python.org/downloads/">Python 3.10 ή νεότερη</a>
(στα Windows τσεκάρετε <i>Add Python to PATH</i>).</li>
<li>Αποσυμπιέστε το <code>Erisma.zip</code> σε έναν φάκελο της επιλογής σας.</li>
<li><b>Windows:</b> διπλό κλικ στο <code>Erisma.bat</code>. <b>Mac:</b> δεξί κλικ στο
<code>Erisma.command</code> → Άνοιγμα.</li>
</ol>
<p>Την πρώτη φορά γίνεται αυτόματα η εγκατάσταση (1–2 λεπτά, χρειάζεται internet μόνο τότε).
Μετά το Erisma ανοίγει μόνο του στον browser στη διεύθυνση <code>http://127.0.0.1:8000</code>.
Όλα τρέχουν στον υπολογιστή σας και λειτουργούν χωρίς internet· τίποτα δεν αποστέλλεται.
Για τερματισμό κλείστε το μαύρο παράθυρο.</p>"""}),
    ("ui", {"en": "3. The screen", "el": "3. Η οθόνη"}, {
        "en": """
<ul>
<li><b>Home page:</b> all calculations as cards grouped by category, with search. “Continue”
reopens the last calculation.</li>
<li><b>Left sidebar:</b> search (<kbd>Ctrl</kbd>+<kbd>K</kbd>), ★ favourites, recent
calculations and all categories. « collapses it to icons.</li>
<li><b>Project details</b> (top of the form): company, project, job no., element, engineer,
checker, date, <b>National Annex</b> and <b>project site</b>. They appear in the title block of
every report and are kept for all calculations.</li>
<li><b>Input form</b> (middle): fields grouped in boxes. Above it the <b>status banner</b>:
green when all checks pass, red with the failing checks and what to change.</li>
<li><b>Report / 3D model</b> (right): the full calculation sheet and the interactive model.</li>
<li>Top bar: Home, light/dark theme, language ΕΛ/EN, Open, Save, Export HTML,
Print / PDF, Manual.</li>
</ul>""",
        "el": """
<ul>
<li><b>Αρχική σελίδα:</b> όλοι οι υπολογισμοί σε κάρτες ανά κατηγορία, με αναζήτηση. Το
«Συνέχεια» ανοίγει τον τελευταίο υπολογισμό.</li>
<li><b>Αριστερή μπάρα:</b> αναζήτηση (<kbd>Ctrl</kbd>+<kbd>K</kbd>), ★ αγαπημένα, πρόσφατα
και όλες οι κατηγορίες. Το « τη συμπτύσσει σε εικονίδια.</li>
<li><b>Στοιχεία έργου</b> (πάνω από τη φόρμα): εταιρεία, έργο, αρ. έργου, στοιχείο, συντάκτης,
έλεγχος, ημερομηνία, <b>Εθνικό Προσάρτημα</b> και <b>τοποθεσία έργου</b>. Εμφανίζονται στην
κεφαλίδα κάθε τεύχους και κρατούνται για όλους τους υπολογισμούς.</li>
<li><b>Φόρμα δεδομένων</b> (κέντρο): πεδία σε ομάδες. Από πάνω η <b>μπάρα κατάστασης</b>:
πράσινη όταν όλοι οι έλεγχοι επαρκούν, κόκκινη με τους ελέγχους που δεν επαρκούν και τι
να αλλάξετε.</li>
<li><b>Τεύχος / 3D μοντέλο</b> (δεξιά): το πλήρες τεύχος υπολογισμών και το διαδραστικό
μοντέλο.</li>
<li>Πάνω μπάρα: Αρχική, φωτεινό/σκούρο θέμα, γλώσσα ΕΛ/EN, Άνοιγμα, Αποθήκευση, Εξαγωγή
HTML, Εκτύπωση / PDF, Εγχειρίδιο.</li>
</ul>"""}),
    ("input", {"en": "4. Entering data", "el": "4. Εισαγωγή δεδομένων"}, {
        "en": """
<ul>
<li><b>Decimals:</b> type <code>1,5</code> or <code>1.5</code> — both work.</li>
<li><b>Arithmetic:</b> type <code>2*3,5</code>, <code>(4+2)/2</code> or <code>1,5^2</code>; the
result is shown next to the field and replaces the expression when you leave it.</li>
<li><b>Units</b> are shown next to every field; type the value in that unit.</li>
<li><b>Keyboard:</b> <kbd>Enter</kbd> goes to the next field, <kbd>Shift</kbd>+<kbd>Enter</kbd>
back; <kbd>↑</kbd>/<kbd>↓</kbd> change the value in small steps (with <kbd>Shift</kbd> ×10).</li>
<li><b>Help:</b> the help text of a field appears while the field is selected, or click
<b>ⓘ</b>.</li>
<li><b>Changed fields</b> are marked with a dot; <b>↺</b> returns that field to the example
value. Each group shows how many of its fields you changed. “Reset to defaults” restores the
whole example.</li>
<li><b>Groups</b> can be collapsed by clicking their title — Erisma remembers it.</li>
<li><b>Conditional fields</b> appear only when needed (e.g. jacket data only when “RC jacket”
is chosen).</li>
<li><b>Tables</b> (soil layers, anchors, loads…): “+ Add row” copies the last row, ⧉ duplicates
a row, × deletes it. You can <b>paste a block of cells from Excel</b>: select the first cell
and press <kbd>Ctrl</kbd>+<kbd>V</kbd>.</li>
<li><b>Undo / redo:</b> <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd>.</li>
<li><b>Wrong values</b> turn red immediately; if the calculation cannot run, the banner says why
and the field concerned is highlighted.</li>
</ul>""",
        "el": """
<ul>
<li><b>Δεκαδικά:</b> γράψτε <code>1,5</code> ή <code>1.5</code> — δουλεύουν και τα δύο.</li>
<li><b>Πράξεις:</b> γράψτε <code>2*3,5</code>, <code>(4+2)/2</code> ή <code>1,5^2</code>· το
αποτέλεσμα φαίνεται δίπλα στο πεδίο και αντικαθιστά την παράσταση όταν φύγετε από αυτό.</li>
<li><b>Μονάδες:</b> φαίνονται δίπλα σε κάθε πεδίο· δίνετε την τιμή σε αυτή τη μονάδα.</li>
<li><b>Πληκτρολόγιο:</b> <kbd>Enter</kbd> πάει στο επόμενο πεδίο, <kbd>Shift</kbd>+<kbd>Enter</kbd>
στο προηγούμενο· <kbd>↑</kbd>/<kbd>↓</kbd> αλλάζουν την τιμή σε μικρά βήματα (με
<kbd>Shift</kbd> ×10).</li>
<li><b>Βοήθεια:</b> το κείμενο βοήθειας ενός πεδίου εμφανίζεται όσο το πεδίο είναι
επιλεγμένο, ή με κλικ στο <b>ⓘ</b>.</li>
<li><b>Αλλαγμένα πεδία</b> σημειώνονται με τελεία· το <b>↺</b> επαναφέρει το πεδίο στην τιμή
του παραδείγματος. Κάθε ομάδα δείχνει πόσα πεδία της αλλάξατε. Το «Επαναφορά προεπιλογών»
επαναφέρει όλο το παράδειγμα.</li>
<li><b>Ομάδες:</b> συμπτύσσονται με κλικ στον τίτλο τους — το Erisma το θυμάται.</li>
<li><b>Πεδία υπό συνθήκη:</b> εμφανίζονται μόνο όταν χρειάζονται (π.χ. τα στοιχεία μανδύα μόνο
όταν επιλεγεί «Μανδύας ΟΣ»).</li>
<li><b>Πίνακες</b> (εδαφικές στρώσεις, αγκύρια, φορτία…): «+ Προσθήκη γραμμής» αντιγράφει την
τελευταία γραμμή, ⧉ αντιγράφει μια γραμμή, × τη διαγράφει. Μπορείτε να <b>επικολλήσετε
κελιά από Excel</b>: επιλέξτε το πρώτο κελί και πατήστε <kbd>Ctrl</kbd>+<kbd>V</kbd>.</li>
<li><b>Αναίρεση / επανάληψη:</b> <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd>.</li>
<li><b>Λάθος τιμές</b> γίνονται αμέσως κόκκινες· αν ο υπολογισμός δεν μπορεί να γίνει, η μπάρα
κατάστασης εξηγεί γιατί και το σχετικό πεδίο τονίζεται.</li>
</ul>"""}),
    ("files", {"en": "5. Saving, files and printing", "el": "5. Αποθήκευση, αρχεία και εκτύπωση"}, {
        "en": """
<ul>
<li><b>Autosave:</b> the inputs of every calculation are kept in the browser; when you reopen a
calculation you continue where you left off.</li>
<li><b>Save</b> (<kbd>Ctrl</kbd>+<kbd>S</kbd>) downloads a project file <code>.erisma</code>
with the inputs and the project details; <b>Open</b> (<kbd>Ctrl</kbd>+<kbd>O</kbd>) loads it
again — send it to a colleague or keep it with the project.</li>
<li><b>Print / PDF</b> (<kbd>Ctrl</kbd>+<kbd>P</kbd>) prints the report; choose “Save as PDF”
as the printer to get a PDF. <b>Export HTML</b> saves the report as a web page.</li>
</ul>""",
        "el": """
<ul>
<li><b>Αυτόματη αποθήκευση:</b> τα δεδομένα κάθε υπολογισμού κρατούνται στον browser· όταν
ξανανοίγετε έναν υπολογισμό συνεχίζετε από εκεί που σταματήσατε.</li>
<li><b>Αποθήκευση</b> (<kbd>Ctrl</kbd>+<kbd>S</kbd>) κατεβάζει αρχείο έργου
<code>.erisma</code> με τα δεδομένα και τα στοιχεία έργου· το <b>Άνοιγμα</b>
(<kbd>Ctrl</kbd>+<kbd>O</kbd>) το φορτώνει ξανά — στείλτε το σε συνάδελφο ή κρατήστε το με
τον φάκελο του έργου.</li>
<li><b>Εκτύπωση / PDF</b> (<kbd>Ctrl</kbd>+<kbd>P</kbd>) τυπώνει το τεύχος· επιλέξτε «Αποθήκευση
ως PDF» ως εκτυπωτή για αρχείο PDF. Η <b>Εξαγωγή HTML</b> αποθηκεύει το τεύχος ως ιστοσελίδα.</li>
</ul>"""}),
    ("annex", {"en": "6. National Annex and project site", "el": "6. Εθνικό Προσάρτημα και τοποθεσία"}, {
        "en": """
<p>Choose the <b>National Annex</b> in the project details. All partial factors and nationally
determined parameters (NDPs) come from it, and each report ends with a table of the NDPs used.
Where Erisma has no annex for a part (for example EN 1995-1-1 for Cyprus) the EN recommended
values are used and the report says so.</p>
<p>With the Cyprus annex, <b>📍 Map</b> opens the official seismic zonation map: click on the
site, search a town, use your location or type coordinates. The seismic zone and a<sub>gR</sub>
are filled in automatically (near a boundary the higher zone within 1 km is used), and the
wind and snow calculation reads v<sub>b,0</sub> and s<sub>k</sub> for the same site. Next to
every a<sub>gR</sub> field the zone buttons set the value with one click.</p>""",
        "el": """
<p>Επιλέξτε το <b>Εθνικό Προσάρτημα</b> στα στοιχεία έργου. Όλοι οι επιμέρους συντελεστές και
οι εθνικά καθοριζόμενες παράμετροι (NDP) προέρχονται από αυτό, και κάθε τεύχος τελειώνει με
πίνακα των NDP που χρησιμοποιήθηκαν. Όπου το Erisma δεν έχει προσάρτημα για ένα μέρος (π.χ.
EN 1995-1-1 για την Κύπρο) χρησιμοποιούνται οι συνιστώμενες τιμές EN και το τεύχος το
αναφέρει.</p>
<p>Με το κυπριακό προσάρτημα, το <b>📍 Χάρτης</b> ανοίγει τον επίσημο χάρτη σεισμικών ζωνών:
κάντε κλικ στη θέση, αναζητήστε πόλη, χρησιμοποιήστε τη θέση σας ή δώστε συντεταγμένες. Η
σεισμική ζώνη και το a<sub>gR</sub> συμπληρώνονται αυτόματα (κοντά σε όριο λαμβάνεται η
δυσμενέστερη ζώνη σε ακτίνα 1 km), και ο υπολογισμός ανέμου-χιονιού διαβάζει τα
v<sub>b,0</sub> και s<sub>k</sub> για την ίδια θέση. Δίπλα σε κάθε πεδίο a<sub>gR</sub> τα
κουμπιά ζωνών βάζουν την τιμή με ένα κλικ.</p>"""}),
    ("report", {"en": "7. Reading the report", "el": "7. Το τεύχος υπολογισμών"}, {
        "en": """
<ul>
<li>The <b>title block</b> carries the project details; the summary lists every check with its
utilisation.</li>
<li>Each line shows <b>symbol = expression = value unit</b> with the clause of the standard.</li>
<li>Checks show demand ≤ capacity, the utilisation U and <b>PASS / FAIL</b>; failing checks
carry a hint in the status banner.</li>
<li>Figures (sections, pressure diagrams, spectra) are drawn to scale from the actual values.</li>
<li>The last table lists the National Annex parameters used.</li>
</ul>""",
        "el": """
<ul>
<li>Η <b>κεφαλίδα</b> έχει τα στοιχεία έργου· η σύνοψη δείχνει κάθε έλεγχο με την αξιοποίησή
του.</li>
<li>Κάθε γραμμή δείχνει <b>σύμβολο = τύπος = τιμή μονάδα</b> με το άρθρο του κανονισμού.</li>
<li>Οι έλεγχοι δείχνουν απαίτηση ≤ αντοχή, την αξιοποίηση U και <b>ΕΠΑΡΚΕΙ / ΑΝΕΠΑΡΚΕΙ</b>·
οι ανεπαρκείς έλεγχοι έχουν συμβουλή στη μπάρα κατάστασης.</li>
<li>Τα σχήματα (διατομές, διαγράμματα πιέσεων, φάσματα) σχεδιάζονται υπό κλίμακα από τις
πραγματικές τιμές.</li>
<li>Ο τελευταίος πίνακας δείχνει τις παραμέτρους του Εθνικού Προσαρτήματος.</li>
</ul>"""}),
    ("3d", {"en": "8. The 3D model", "el": "8. Το 3D μοντέλο"}, {
        "en": """
<p>Every calculation has an interactive 3D model (tab “3D model” or <kbd>Ctrl</kbd>+<kbd>3</kbd>).
Drag to rotate, right-drag to pan, scroll to zoom. The <b>Layers</b> panel switches soil, loads,
pressures, reinforcement, deflected shapes and labels on and off; the buttons give 3D, front and
plan views and <b>PNG</b> saves an image for your report. The panel on the right lists the
utilisation of every check; the model updates with every change.</p>""",
        "el": """
<p>Κάθε υπολογισμός έχει διαδραστικό 3D μοντέλο (καρτέλα «3D μοντέλο» ή
<kbd>Ctrl</kbd>+<kbd>3</kbd>). Σύρετε για περιστροφή, δεξί κλικ για μετακίνηση, ροδέλα για
zoom. Το πλαίσιο <b>Επίπεδα</b> ανάβει/σβήνει έδαφος, φορτία, πιέσεις, οπλισμό,
παραμορφωμένους άξονες και ετικέτες· τα κουμπιά δίνουν 3D, όψη και κάτοψη και το <b>PNG</b>
αποθηκεύει εικόνα για το τεύχος σας. Δεξιά φαίνεται η αξιοποίηση κάθε ελέγχου· το μοντέλο
ενημερώνεται σε κάθε αλλαγή.</p>"""}),
]

SHORTCUTS = [
    ("Ctrl+K", "Search calculations", "Αναζήτηση υπολογισμών"),
    ("Ctrl+S", "Save project file", "Αποθήκευση αρχείου έργου"),
    ("Ctrl+O", "Open project file", "Άνοιγμα αρχείου έργου"),
    ("Ctrl+P", "Print / PDF", "Εκτύπωση / PDF"),
    ("Ctrl+3", "Report ↔ 3D model", "Τεύχος ↔ 3D μοντέλο"),
    ("Ctrl+Z / Ctrl+Y", "Undo / redo inputs", "Αναίρεση / επανάληψη"),
    ("Enter / Shift+Enter", "Next / previous field", "Επόμενο / προηγούμενο πεδίο"),
    ("↑ / ↓ (Shift)", "Change the value (×10)", "Αλλαγή τιμής (×10)"),
    ("F1", "This manual", "Αυτό το εγχειρίδιο"),
]

# ---------------------------------------------------- method notes per module
NOTES: dict[str, dict[str, list[str]]] = {
    "beam_analysis": {
        "en": ["Linear elastic stiffness (finite element) method, Euler–Bernoulli beam.",
               "Supports pinned or fixed at any position; loads downward positive."],
        "el": ["Γραμμική ελαστική μέθοδος δυσκαμψίας (πεπερασμένα στοιχεία), δοκός Euler–Bernoulli.",
               "Στηρίξεις αρθρωτές ή πακτώσεις σε οποιαδήποτε θέση· φορτία θετικά προς τα κάτω."]},
    "ec2_rc_beam": {
        "en": ["Rectangular stress block (λ = 0.8, η = 1.0), ε_cu3 = 3.5 ‰, x/d ≤ 0.45 for ductility.",
               "Shear with variable strut inclination 1 ≤ cot θ ≤ 2.5 (6.2.3)."],
        "el": ["Ορθογωνικό διάγραμμα τάσεων (λ = 0.8, η = 1.0), ε_cu3 = 3.5 ‰, x/d ≤ 0.45 για πλαστιμότητα.",
               "Διάτμηση με μεταβλητή κλίση θλιπτήρα 1 ≤ cot θ ≤ 2.5 (6.2.3)."]},
    "ec2_rc_column": {
        "en": ["Second-order effects by the nominal curvature method (5.8.8); biaxial by Eq. 5.39.",
               "M_Rd by strain compatibility for the actual axial force; EC8 DCM rules optional."],
        "el": ["Φαινόμενα 2ας τάξης με τη μέθοδο ονομαστικής καμπυλότητας (5.8.8)· διαξονική κατά Εξ. 5.39.",
               "M_Rd με συμβιβαστό παραμορφώσεων για την πραγματική αξονική· προαιρετικά κανόνες ΚΠΜ."]},
    "ec2_rc_slab": {
        "en": ["Two-way panels: Kirchhoff plate by finite differences with any edge conditions "
               "(verified against Timoshenko's tables).",
               "One-way continuous slabs: pattern loading (all / odd / even spans)."],
        "el": ["Διασταυρούμενες πλάκες: πλάκα Kirchhoff με πεπερασμένες διαφορές, οποιεσδήποτε "
               "στηρίξεις (επαληθευμένο με τους πίνακες Timoshenko).",
               "Συνεχείς πλάκες μίας διεύθυνσης: δυσμενείς φορτίσεις (όλα / μονά / ζυγά ανοίγματα)."]},
    "ec2_tank": {
        "en": ["Long walls as vertical strips fixed into the base, free or pinned at the top.",
               "Crack width by EN 1992-1-1 7.3.4 (quasi-permanent) against w_k1 of tightness class 1.",
               "Thermal/early-age restraint cracking is not included."],
        "el": ["Τα μακριά τοιχώματα ως κατακόρυφες λωρίδες πακτωμένες στη βάση, ελεύθερες ή "
               "αρθρωτές στην κορυφή.",
               "Εύρος ρωγμών κατά EN 1992-1-1 7.3.4 (οιονεί μόνιμος) έναντι w_k1 κατηγορίας στεγανότητας 1.",
               "Δεν περιλαμβάνεται η ρηγμάτωση από θερμοκρασία / συστολή νεαρής ηλικίας."]},
    "ec3_steel_beam": {
        "en": ["Simply supported rolled I-beam; LTB with M_cr (NCCI SN003) and 6.3.2.3."],
        "el": ["Αμφιέρειστη έλατη δοκός I· πλευρικός λυγισμός με M_cr (NCCI SN003) και 6.3.2.3."]},
    "ec3_steel_column": {
        "en": ["Buckling curves of Table 6.2; interaction factors of Annex B (Method 2).",
               "Class 4 webs by the effective width of EN 1993-1-5."],
        "el": ["Καμπύλες λυγισμού Πίνακα 6.2· συντελεστές αλληλεπίδρασης Παραρτήματος B (Μέθοδος 2).",
               "Κορμοί Κατηγορίας 4 με ενεργό πλάτος κατά EN 1993-1-5."]},
    "ec3_bolted_connection": {
        "en": ["Elastic distribution of eccentric shear in the bolt group; bearing checked for "
               "the governing bolt with the end/inner values of Table 3.4."],
        "el": ["Ελαστική κατανομή της έκκεντρης τέμνουσας στην ομάδα κοχλιών· η σύνθλιψη άντυγας "
               "ελέγχεται για τον κρίσιμο κοχλία με τις τιμές Πίνακα 3.4."]},
    "ec3_base_plate": {
        "en": ["Component method: compression T-stubs on the foundation, tension T-stub with "
               "anchor bolts (no prying), M–N from statics about the compressed flange.",
               "Anchorage of the bolts in concrete (EN 1992-4) and welds are not checked."],
        "el": ["Μέθοδος συνιστωσών: θλιβόμενα ισοδύναμα T στο θεμέλιο, εφελκυόμενο T με αγκύρια "
               "(χωρίς μοχλοδράση), M–N από ισορροπία ως προς το θλιβόμενο πέλμα.",
               "Δεν ελέγχονται η αγκύρωση στο σκυρόδεμα (EN 1992-4) και οι συγκολλήσεις."]},
    "ec5_timber_beam": {
        "en": ["Governing combination by the largest w_d / k_mod; deflection includes shear "
               "deformation and creep (k_def)."],
        "el": ["Κρίσιμος συνδυασμός με το μεγαλύτερο w_d / k_mod· το βέλος περιλαμβάνει "
               "διατμητική παραμόρφωση και ερπυσμό (k_def)."]},
    "ec6_masonry_wall": {
        "en": ["Vertical resistance with the reduction factors Φ at top, bottom and mid-height "
               "(Annex G, E = K_E f_k); in-plane shear by Eq. 6.13."],
        "el": ["Κατακόρυφη αντοχή με μειωτικούς συντελεστές Φ σε κορυφή, βάση και μέσο ύψος "
               "(Παράρτημα G, E = K_E f_k)· διάτμηση εντός επιπέδου κατά Εξ. 6.13."]},
    "ec7_retaining_wall": {
        "en": ["Coulomb active pressure on the virtual back through the heel; Mononobe-Okabe in "
               "the seismic case (±k_v); bearing by Annex D with inclination factors.",
               "Passive resistance in front is ignored except at a shear key."],
        "el": ["Ενεργητική ώθηση Coulomb στη νοητή πίσω παρειά από την πτέρνα· Mononobe-Okabe στη "
               "σεισμική κατάσταση (±k_v)· φέρουσα ικανότητα κατά Παράρτημα D με συντελεστές κλίσης.",
               "Η παθητική αντίσταση μπροστά αγνοείται, εκτός από το δόντι."]},
    "ec7_gravity_wall": {
        "en": ["Same stability engine as the cantilever wall; plain-concrete body sections to "
               "EN 1992-1-1 §12."],
        "el": ["Ίδιος υπολογισμός ευστάθειας με τον πρόβολο· διατομές κορμού από άοπλο "
               "σκυρόδεμα κατά EN 1992-1-1 §12."]},
    "ec7_gabion_wall": {
        "en": ["Global stability as a gravity wall (γ_g = γ_s(1 − n)) plus sliding and "
               "eccentricity at every joint between courses."],
        "el": ["Γενική ευστάθεια ως τοίχος βαρύτητας (γ_g = γ_s(1 − n)) και ολίσθηση και "
               "εκκεντρότητα σε κάθε αρμό μεταξύ στρώσεων."]},
    "ec7_pad_footing": {
        "en": ["Effective area B'×L' for biaxial eccentricity (Annex D); punching with the "
               "critical perimeter search between 0 and 2d (6.4.4)."],
        "el": ["Ενεργό εμβαδόν B'×L' για διαξονική εκκεντρότητα (Παράρτημα D)· διάτρηση με "
               "αναζήτηση της κρίσιμης περιμέτρου μεταξύ 0 και 2d (6.4.4)."]},
    "ec7_strip_footing": {
        "en": ["Strip bearing per metre run with load inclination; tie-beam force ±k α S N "
               "(EN 1998-5 5.4.1.2) with the minimum sections of EN 1998-1 5.8.2."],
        "el": ["Φέρουσα ικανότητα λωριδωτού ανά μέτρο με κλίση φορτίου· δύναμη συνδετήριου δοκού "
               "±k α S N (EN 1998-5 5.4.1.2) με τις ελάχιστες διατομές του EN 1998-1 5.8.2."]},
    "ec7_pile": {
        "en": ["Shaft: α-method (clay) and β-method K tan δ σ'_v (sand); base: 9c_u or Meyerhof "
               "N_q* with base efficiency η_b (0.5 bored/CFA, 1.0 driven).",
               "Characteristic value by model factor (7.6.2.3(8)) or ξ3/ξ4; lateral by Broms "
               "(free head, top layer)."],
        "el": ["Πλευρική: μέθοδος α (άργιλος) και β, K tan δ σ'_v (άμμος)· αιχμή: 9c_u ή Meyerhof "
               "N_q* με συντελεστή η_b (0.5 διάτρησης/CFA, 1.0 εμπηγνύμενοι).",
               "Χαρακτηριστική τιμή με συντελεστή προσομοίωσης (7.6.2.3(8)) ή ξ3/ξ4· πλευρικά "
               "κατά Broms (ελεύθερη κεφαλή, ανώτερη στρώση)."]},
    "ec7_settlement": {
        "en": ["Boussinesq stresses below the centre (Newmark), sub-layers of 0.25 m down to "
               "Δσ = 0.2 σ'_v0; granular by E_oed, clays by C_c/C_r/OCR."],
        "el": ["Τάσεις Boussinesq κάτω από το κέντρο (Newmark), υποστρώσεις 0.25 m έως "
               "Δσ = 0.2 σ'_v0· κοκκώδη με E_oed, άργιλοι με C_c/C_r/OCR."]},
    "ec7_slope_stability": {
        "en": ["Bishop simplified method with automatic search of the critical circle; "
               "pseudo-static seismic action (EN 1998-5 4.1.3.3)."],
        "el": ["Απλοποιημένη μέθοδος Bishop με αυτόματη αναζήτηση του κρίσιμου κύκλου· "
               "ψευδοστατική σεισμική δράση (EN 1998-5 4.1.3.3)."]},
    "ec7_berlin_wall": {
        "en": ["Blum (cantilever) or free earth support (one anchor row); spatial passive "
               "resistance below the excavation (f·b ≤ a)."],
        "el": ["Blum (πρόβολος) ή ελεύθερη στήριξη (μία σειρά αγκυρίων)· χωρική παθητική "
               "αντίσταση κάτω από την εκσκαφή (f·b ≤ a)."]},
    "ec7_embedded_wall": {
        "en": ["Beam on elastic–plastic Winkler springs: at-rest pressure ± k_h u bounded by "
               "active and passive; anchors as springs locked off at P_0.",
               "Factored effects (DA2: characteristic soil, effects × γ_G) or factored strength "
               "(DA1-C2, DA3)."],
        "el": ["Δοκός σε ελαστοπλαστικά ελατήρια Winkler: πίεση ηρεμίας ± k_h u μεταξύ "
               "ενεργητικής και παθητικής· αγκύρια ως ελατήρια με προένταση P_0.",
               "Συντελεστές στα αποτελέσματα (DA2: χαρακτηριστικό έδαφος, × γ_G) ή στις αντοχές "
               "(DA1-C2, DA3)."]},
    "ec1_wind_snow": {
        "en": ["q_p(z) by Eq. 4.8 with c_dir = c_season = 1; walls by Table 7.1; roof snow "
               "μ_1 C_e C_t s_k."],
        "el": ["q_p(z) κατά Εξ. 4.8 με c_dir = c_season = 1· τοίχοι κατά Πίνακα 7.1· χιόνι στη "
               "στέγη μ_1 C_e C_t s_k."]},
    "ec8_lateral_force": {
        "en": ["Type 1 design spectrum, T1 = C_t H^¾, λ = 0.85 when applicable, storey forces "
               "with a linear mode shape (Eq. 4.11)."],
        "el": ["Φάσμα σχεδιασμού Τύπου 1, T1 = C_t H^¾, λ = 0.85 όπου ισχύει, δυνάμεις ορόφων με "
               "γραμμική ιδιομορφή (Εξ. 4.11)."]},
    "en1990_combinations": {
        "en": ["All ULS (6.10), seismic (6.12b) and SLS combinations with ψ of the annex; each "
               "variable action in turn as leading action."],
        "el": ["Όλοι οι συνδυασμοί ΟΚΑ (6.10), σεισμικοί (6.12b) και ΟΚΛ με τα ψ του "
               "προσαρτήματος· κάθε μεταβλητή δράση διαδοχικά ως κύρια."]},
    "ec8_3_assessment": {
        "en": ["EN 1998-3 Annex A: θ_y (A.10a), θ_um (A.1), V_R (A.12); mean strengths ÷ CF, "
               "brittle shear also ÷ γ (Cyprus NA 2.3).",
               "NC: θ_E ≤ θ_um, SD: θ_E ≤ ¾θ_um, DL: θ_E ≤ θ_y. RC jacket by the monolithic "
               "factors of A.4.2.2, FRP by A.4.4. The Greek KANEPE is not implemented."],
        "el": ["EN 1998-3 Παράρτημα A: θ_y (A.10a), θ_um (A.1), V_R (A.12)· μέσες αντοχές ÷ CF, "
               "η ψαθυρή διάτμηση και ÷ γ (Κυπριακό ΕΠ 2.3).",
               "NC: θ_E ≤ θ_um, SD: θ_E ≤ ¾θ_um, DL: θ_E ≤ θ_y. Μανδύας ΟΣ με τους συντελεστές "
               "μονολιθικού μέλους A.4.2.2, ΙΟΠ κατά A.4.4. Ο ΚΑΝΕΠΕ δεν έχει υλοποιηθεί."]},
}

T = {
    "title": {"en": "Erisma — User manual", "el": "Erisma — Εγχειρίδιο χρήσης"},
    "toc": {"en": "Contents", "el": "Περιεχόμενα"},
    "shortcuts": {"en": "9. Keyboard shortcuts", "el": "9. Συντομεύσεις πληκτρολογίου"},
    "annexes": {"en": "10. National Annexes in Erisma", "el": "10. Εθνικά Προσαρτήματα στο Erisma"},
    "ref": {"en": "11. Calculation reference", "el": "11. Οδηγός υπολογισμών"},
    "inputs": {"en": "Inputs", "el": "Δεδομένα"},
    "checks": {"en": "Checks performed (worked example)", "el": "Έλεγχοι (παράδειγμα προεπιλογών)"},
    "method": {"en": "Method and assumptions", "el": "Μέθοδος και παραδοχές"},
    "field": {"en": "Input", "el": "Δεδομένο"}, "unit": {"en": "Unit", "el": "Μονάδα"},
    "default": {"en": "Example", "el": "Παράδειγμα"}, "range": {"en": "Range", "el": "Εύρος"},
    "help": {"en": "Notes", "el": "Σημειώσεις"}, "check": {"en": "Check", "el": "Έλεγχος"},
    "clause": {"en": "Clause", "el": "Άρθρο"}, "util": {"en": "U (example)", "el": "U (παράδειγμα)"},
    "key": {"en": "Keys", "el": "Πλήκτρα"}, "action": {"en": "Action", "el": "Ενέργεια"},
    "table": {"en": "table", "el": "πίνακας"}, "yes": {"en": "yes", "el": "ναι"},
    "no": {"en": "no", "el": "όχι"}, "open": {"en": "Open this calculation", "el": "Άνοιγμα υπολογισμού"},
    "print": {"en": "Print / PDF", "el": "Εκτύπωση / PDF"},
    "version": {"en": "Version", "el": "Έκδοση"},
    "standard": {"en": "Standard", "el": "Κανονισμός"},
}

CSS = """
:root{--ink:#1d2433;--muted:#5b6575;--line:#d6dbe3;--accent:#123a6b;--soft:#eef3f9}
body{font:14px/1.55 system-ui,"Segoe UI",Roboto,sans-serif;color:var(--ink);margin:0;background:#fff}
.wrap{max-width:980px;margin:0 auto;padding:24px 28px 80px}
h1{color:var(--accent);margin:0 0 4px;font-size:28px}
h2{color:var(--accent);border-bottom:2px solid var(--accent);padding-bottom:4px;margin-top:36px}
h3{color:var(--accent);margin:28px 0 4px}
h4{margin:14px 0 4px;font-size:13.5px;color:#334}
.muted{color:var(--muted)}
.bar{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.bar a,.bar button{font:inherit;font-size:13px;color:var(--accent);border:1px solid var(--line);
background:var(--soft);border-radius:6px;padding:4px 10px;text-decoration:none;cursor:pointer}
nav.toc{background:var(--soft);border-radius:8px;padding:10px 18px;margin:18px 0;columns:2}
nav.toc a{color:var(--accent);text-decoration:none}nav.toc li{break-inside:avoid}
nav.toc ul.ch{list-style:none;padding-left:0;font-weight:600}
td.num{width:11%}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin:6px 0}
th,td{border:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
th{background:var(--soft)}
td.num{text-align:right;white-space:nowrap}
.card{border:1px solid var(--line);border-radius:10px;padding:4px 16px 12px;margin:18px 0;break-inside:avoid-page}
.std{color:var(--muted);font-size:12.5px}
.warn{background:#fff6e5;border-left:4px solid #e3a008;padding:8px 12px;border-radius:4px}
kbd{border:1px solid #b9c0cb;border-bottom-width:2px;border-radius:4px;padding:0 5px;font-size:12px;
background:#f7f8fa}
code{background:var(--soft);padding:0 4px;border-radius:3px}
.cat{margin-top:34px;color:#334;font-size:15px;text-transform:uppercase;letter-spacing:.04em}
.ok{color:#1d7a46}.ko{color:#b42318}
@media print{.bar{display:none}.wrap{padding:0}h2{break-after:avoid}h2#reference,h2#shortcuts{break-before:page}.card{break-inside:auto}h3,h4{break-after:avoid}
a{color:inherit;text-decoration:none}nav.toc{columns:2}}
"""


LANG_NOW = {"lang": "en"}


def _num(v) -> str:
    if v is None:
        return ""
    txt = f"{v:g}" if isinstance(v, float) else str(v)
    return txt.replace(".", ",") if LANG_NOW["lang"] == "el" else txt


def _module_card(m, lang: str) -> str:
    sch = m.schema(lang)
    out = [f'<div class="card" id="{m.id}"><h3>{E(sch["title"])}</h3>',
           f'<div class="std">{E(T["standard"][lang])}: {E(sch["standard"])}</div>',
           f"<p>{E(sch['description'])}</p>"]
    notes = NOTES.get(m.id, {}).get(lang)
    if notes:
        out.append(f"<h4>{T['method'][lang]}</h4><ul>" +
                   "".join(f"<li>{E(n)}</li>" for n in notes) + "</ul>")
    rows = []
    for f in sch["fields"]:
        if f["kind"] == "table":
            cols = ", ".join(f"{c['label']}{' [' + c['unit'] + ']' if c.get('unit') else ''}"
                             for c in f["columns"])
            rows.append(f"<tr><td>{E(f['label'])}</td><td>{T['table'][lang]}</td><td></td>"
                        f"<td></td><td>{E(cols)}{(' — ' + E(f['help'])) if f.get('help') else ''}"
                        f"</td></tr>")
            continue
        if f["kind"] == "choice":
            labels = f.get("choice_labels") or f["choices"]
            dv = labels[f["choices"].index(f["default"])] if f["default"] in f["choices"] else ""
            rng = " / ".join(labels) if len(labels) <= 6 else f"{len(labels)} …"
        elif f["kind"] == "bool":
            dv = T["yes"][lang] if f["default"] else T["no"][lang]
            rng = ""
        else:
            dv = _num(f["default"])
            lo, hi = f.get("min"), f.get("max")
            rng = " – ".join(x for x in (_num(lo) if lo is not None else "…",
                                         _num(hi) if hi is not None else "…")) \
                if (lo is not None or hi is not None) else ""
        rows.append(f"<tr><td>{E(f['label'])}</td><td>{E(f.get('unit') or '')}</td>"
                    f"<td class='num'>{E(str(dv))}</td><td>{E(rng)}</td>"
                    f"<td>{E(f.get('help') or '')}</td></tr>")
    out.append(f"<h4>{T['inputs'][lang]}</h4><table><tr><th>{T['field'][lang]}</th>"
               f"<th>{T['unit'][lang]}</th><th>{T['default'][lang]}</th><th>{T['range'][lang]}"
               f"</th><th>{T['help'][lang]}</th></tr>{''.join(rows)}</table>")
    try:
        calc = m.calculate({}, {"annex": "CY"}, lang)
        crow = "".join(
            f"<tr><td>{E(c.description)}</td><td>{E(c.ref or '')}</td>"
            f"<td class='num {'ok' if c.passed else 'ko'}'>{_num(round(c.utilisation, 2))}</td></tr>"
            for c in calc.checks)
        if crow:
            out.append(f"<h4>{T['checks'][lang]}</h4><table><tr><th>{T['check'][lang]}</th>"
                       f"<th>{T['clause'][lang]}</th><th>{T['util'][lang]}</th></tr>{crow}"
                       "</table>")
    except Exception:  # noqa: BLE001 — the manual must render even if a module errors
        pass
    out.append(f'<p class="bar"><a href="/#{m.id}">▶ {T["open"][lang]}</a></p></div>')
    return "".join(out)


@lru_cache(maxsize=4)
def build_manual(lang: str = "el") -> str:
    lang = "el" if lang == "el" else "en"
    LANG_NOW["lang"] = lang
    toc = [(cid, title[lang]) for cid, title, _ in CHAPTERS]
    toc += [("shortcuts", T["shortcuts"][lang]), ("annexes", T["annexes"][lang]),
            ("reference", T["ref"][lang])]
    body = []
    for cid, title, text in CHAPTERS:
        body.append(f'<h2 id="{cid}">{E(title[lang])}</h2>{text[lang]}')
    body.append(f'<h2 id="shortcuts">{T["shortcuts"][lang]}</h2><table><tr><th>{T["key"][lang]}'
                f'</th><th>{T["action"][lang]}</th></tr>' +
                "".join(f"<tr><td><kbd>{E(k)}</kbd></td><td>{E(en if lang == 'en' else el)}</td>"
                        f"</tr>" for k, en, el in SHORTCUTS) + "</table>")
    ann = []
    for a in ANNEXES.values():
        notes = "".join(f"<li>{E(tr(n, lang))}</li>" for n in a.notes)
        ann.append(f"<h4>{E(tr(a.label, lang))}</h4><p class='std'>{E(a.reference)}</p>"
                   + (f"<ul>{notes}</ul>" if notes else ""))
    body.append(f'<h2 id="annexes">{T["annexes"][lang]}</h2>' + "".join(ann))
    body.append(f'<h2 id="reference">{T["ref"][lang]}</h2>')
    cats: dict[str, list] = {}
    for m in all_modules():
        cats.setdefault(tr(m.category, lang), []).append(m)
    sub = []
    for cat, mods in cats.items():
        body.append(f'<div class="cat">{E(cat)}</div>')
        for m in mods:
            body.append(_module_card(m, lang))
            sub.append(f'<li><a href="#{m.id}">{E(tr(m.title, lang))}</a></li>')
    toc_html = "".join(f'<li><a href="#{cid}">{E(t_)}</a></li>' for cid, t_ in toc)
    other = "en" if lang == "el" else "el"
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{T['title'][lang]}</title><style>{CSS}</style></head><body><div class="wrap">
<div class="bar"><a href="/">← Erisma</a><span><a href="/manual?lang={other}">{'English' if lang == 'el' else 'Ελληνικά'}</a>
<button onclick="print()">{T['print'][lang]}</button></span></div>
<h1>{T['title'][lang]}</h1><div class="muted">{T['version'][lang]} {__version__}</div>
<nav class="toc"><b>{T['toc'][lang]}</b><ul class="ch">{toc_html}</ul><ul>{''.join(sub)}</ul></nav>
{''.join(body)}
</div></body></html>"""
