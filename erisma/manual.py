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
    ("intro", {"en": "What Erisma is", "el": "Τι είναι το Erisma"}, {
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
    ("start", {"en": "Installation and start", "el": "Εγκατάσταση και εκκίνηση"}, {
        "en": """
<h4>Windows — installer (recommended)</h4>
<ol>
<li>Run <code>Erisma-Setup-<i>version</i>.exe</code>. Python or anything else is not needed.
Choose the language (Greek / English) and, if you wish, a desktop icon. No administrator
rights are required (it installs for the current user; an administrator can choose all
users).</li>
<li>Start <b>Erisma</b> from the Start menu or the desktop. A small window
“Erisma — στατικοί υπολογισμοί” appears and the program opens in your browser. The window
shows the address (normally <code>http://127.0.0.1:8000</code>; if that port is busy the next
free one is used). <b>Άνοιγμα</b> opens the program again in the browser, <b>Τερματισμός</b> or
closing the window stops Erisma.</li>
<li>The Start menu also has <b>Εγχειρίδιο Erisma</b> (this manual as PDF) and the uninstaller.
Updating = running the new Setup; your licence and settings are kept.</li>
</ol>
<h4>Without installer (Windows, Mac, Linux)</h4>
<ol>
<li>Install <a href="https://www.python.org/downloads/">Python 3.10 or newer</a> (on Windows
tick <i>Add Python to PATH</i>).</li>
<li>Unzip <code>Erisma.zip</code> into a folder of your choice.</li>
<li><b>Windows:</b> double-click <code>Erisma.bat</code>. <b>Mac:</b> right-click
<code>Erisma.command</code> → Open.</li>
</ol>
<p>The first start installs the program (1–2 minutes, internet needed once); then Erisma opens
in your browser at <code>http://127.0.0.1:8000</code>. To stop it close the black window.</p>
<p>Either way everything runs on your own computer and works offline; nothing is sent to the
internet. Your projects are ordinary <code>.erisma</code> files that you keep wherever you
like.</p>""",
        "el": """
<h4>Windows — πρόγραμμα εγκατάστασης (συνιστάται)</h4>
<ol>
<li>Τρέξτε το <code>Erisma-Setup-<i>έκδοση</i>.exe</code>. Δεν χρειάζεται Python ή τίποτε άλλο.
Επιλέξτε γλώσσα (Ελληνικά / Αγγλικά) και, αν θέλετε, εικονίδιο στην επιφάνεια εργασίας. Δεν
χρειάζονται δικαιώματα διαχειριστή (εγκαθίσταται για τον τρέχοντα χρήστη· ο διαχειριστής
μπορεί να επιλέξει όλους τους χρήστες).</li>
<li>Ξεκινήστε το <b>Erisma</b> από το μενού Έναρξη ή την επιφάνεια εργασίας. Εμφανίζεται ένα
μικρό παράθυρο «Erisma — στατικοί υπολογισμοί» και το πρόγραμμα ανοίγει στον browser. Το
παράθυρο δείχνει τη διεύθυνση (κανονικά <code>http://127.0.0.1:8000</code>· αν η θύρα είναι
κατειλημμένη χρησιμοποιείται η επόμενη ελεύθερη). Το <b>Άνοιγμα</b> ανοίγει ξανά το πρόγραμμα
στον browser, το <b>Τερματισμός</b> ή το κλείσιμο του παραθύρου σταματά το Erisma.</li>
<li>Στο μενού Έναρξη υπάρχουν επίσης το <b>Εγχειρίδιο Erisma</b> (αυτό το εγχειρίδιο σε PDF)
και η απεγκατάσταση. Ενημέρωση = εκτέλεση του νέου Setup· η άδεια και οι ρυθμίσεις
διατηρούνται.</li>
</ol>
<h4>Χωρίς πρόγραμμα εγκατάστασης (Windows, Mac, Linux)</h4>
<ol>
<li>Εγκαταστήστε την <a href="https://www.python.org/downloads/">Python 3.10 ή νεότερη</a>
(στα Windows τσεκάρετε <i>Add Python to PATH</i>).</li>
<li>Αποσυμπιέστε το <code>Erisma.zip</code> σε έναν φάκελο της επιλογής σας.</li>
<li><b>Windows:</b> διπλό κλικ στο <code>Erisma.bat</code>. <b>Mac:</b> δεξί κλικ στο
<code>Erisma.command</code> → Άνοιγμα.</li>
</ol>
<p>Την πρώτη φορά γίνεται αυτόματα η εγκατάσταση (1–2 λεπτά, χρειάζεται internet μόνο τότε)·
μετά το Erisma ανοίγει στον browser στη διεύθυνση <code>http://127.0.0.1:8000</code>. Για
τερματισμό κλείστε το μαύρο παράθυρο.</p>
<p>Και στους δύο τρόπους όλα τρέχουν στον υπολογιστή σας και λειτουργούν χωρίς internet·
τίποτα δεν αποστέλλεται. Τα έργα σας είναι κανονικά αρχεία <code>.erisma</code> που τα
φυλάτε όπου θέλετε.</p>"""}),
    ("ui", {"en": "The screen", "el": "Η οθόνη"}, {
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
<li><b>Above the form:</b> <b>+ Add to project</b> (see “Projects”), <b>⚖ Alternative</b>
(see “Comparing alternative solutions”), <b>🎯 Most economical</b> (automatic design),
<b>📖 How it works</b> (this manual at that calculation) and <b>↺ Reset</b> (back to the
example values). In the status banner the
<b>💶</b> cost estimate.</li>
<li><b>Top bar:</b> Home, light/dark theme, language ΕΛ/EN, licence state, Manual, Open, Save,
<b>DXF</b> (only for calculations with a drawing), Export HTML, Print / PDF.</li>
<li>At the top of the left sidebar the <b>📁 Project</b> list with the buttons 📄 project report,
⚖ comparison and ✚ new project.</li>
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
<li><b>Πάνω από τη φόρμα:</b> <b>+ Στο έργο</b> (βλ. «Έργα»), <b>⚖ Εναλλακτική λύση</b> (βλ.
«Σύγκριση εναλλακτικών λύσεων»), <b>🎯 Οικονομικότερη λύση</b> (αυτόματη διαστασιολόγηση),
<b>📖 Πώς υπολογίζεται</b> (αυτό το εγχειρίδιο στον συγκεκριμένο υπολογισμό) και
<b>↺ Επαναφορά</b> (πίσω στις τιμές του παραδείγματος). Στη μπάρα κατάστασης
η εκτίμηση κόστους <b>💶</b>.</li>
<li><b>Πάνω μπάρα:</b> Αρχική, φωτεινό/σκούρο θέμα, γλώσσα ΕΛ/EN, κατάσταση άδειας,
Εγχειρίδιο, Άνοιγμα, Αποθήκευση, <b>DXF</b> (μόνο σε υπολογισμούς με σχέδιο), Εξαγωγή HTML,
Εκτύπωση / PDF.</li>
<li>Στην κορυφή της αριστερής μπάρας η λίστα <b>📁 Έργο</b> με τα κουμπιά 📄 τεύχος έργου,
⚖ σύγκριση και ✚ νέο έργο.</li>
</ul>"""}),
    ("input", {"en": "Entering data", "el": "Εισαγωγή δεδομένων"}, {
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
value. Each group shows how many of its fields you changed. “↺ Reset” restores the
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
του παραδείγματος. Κάθε ομάδα δείχνει πόσα πεδία της αλλάξατε. Η «↺ Επαναφορά»
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
    ("files", {"en": "Saving, files and printing", "el": "Αποθήκευση, αρχεία και εκτύπωση"}, {
        "en": """
<ul>
<li><b>Autosave:</b> the inputs of every calculation are kept in the browser; when you reopen a
calculation you continue where you left off.</li>
<li><b>Save</b> (<kbd>Ctrl</kbd>+<kbd>S</kbd>) downloads a file <code>.erisma</code> with the
inputs and the project details — the whole project (all items, links, logo, unit prices) when
the project list is not empty, otherwise the current calculation. <b>Open</b>
(<kbd>Ctrl</kbd>+<kbd>O</kbd>) loads either kind again — send it to a colleague or keep it with
the job.</li>
<li><b>Print / PDF</b> (<kbd>Ctrl</kbd>+<kbd>P</kbd>) prints the report; choose “Save as PDF”
as the printer to get a PDF. <b>Export HTML</b> saves the report as a web page.</li>
</ul>""",
        "el": """
<ul>
<li><b>Αυτόματη αποθήκευση:</b> τα δεδομένα κάθε υπολογισμού κρατούνται στον browser· όταν
ξανανοίγετε έναν υπολογισμό συνεχίζετε από εκεί που σταματήσατε.</li>
<li><b>Αποθήκευση</b> (<kbd>Ctrl</kbd>+<kbd>S</kbd>) κατεβάζει αρχείο <code>.erisma</code> με τα
δεδομένα και τα στοιχεία έργου — ολόκληρο το έργο (όλα τα στοιχεία, συνδέσεις, λογότυπο,
τιμές μονάδας) όταν η λίστα του έργου δεν είναι κενή, αλλιώς τον τρέχοντα υπολογισμό. Το
<b>Άνοιγμα</b> (<kbd>Ctrl</kbd>+<kbd>O</kbd>) φορτώνει και τα δύο — στείλτε το σε συνάδελφο ή
κρατήστε το με τον φάκελο του έργου.</li>
<li><b>Εκτύπωση / PDF</b> (<kbd>Ctrl</kbd>+<kbd>P</kbd>) τυπώνει το τεύχος· επιλέξτε «Αποθήκευση
ως PDF» ως εκτυπωτή για αρχείο PDF. Η <b>Εξαγωγή HTML</b> αποθηκεύει το τεύχος ως ιστοσελίδα.</li>
</ul>"""}),
    ("annex", {"en": "National Annex and project site", "el": "Εθνικό Προσάρτημα και τοποθεσία"}, {
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
    ("report", {"en": "Reading the report", "el": "Το τεύχος υπολογισμών"}, {
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
    ("3d", {"en": "The 3D model", "el": "Το 3D μοντέλο"}, {
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

CHAPTERS += [
    ("verification", {"en": "Verification of Erisma Structure", "el": "Επαλήθευση του Erisma Structure"}, {
        "en": """
<p>As the verification manuals of commercial programs, this table compares Erisma with
independent reference values — closed-form solutions and tabulated results from the
literature. The values are computed now, by the program you are using; the same problems run
in the automatic test suite before every release.</p>
<p>To compare with your own projects, model the same building in Erisma Structure and in your
current program and compare the periods, base shears, member forces and reinforcement — and
please send us any difference you find.</p>""",
        "el": """
<p>Όπως τα εγχειρίδια επαλήθευσης των εμπορικών προγραμμάτων, ο πίνακας συγκρίνει το Erisma με
ανεξάρτητες τιμές αναφοράς — κλειστές λύσεις και πινακοποιημένα αποτελέσματα της βιβλιογραφίας.
Οι τιμές υπολογίζονται τώρα, από το πρόγραμμα που χρησιμοποιείτε· τα ίδια προβλήματα τρέχουν
στα αυτόματα tests πριν από κάθε έκδοση.</p>
<p>Για σύγκριση με δικά σας έργα, προσομοιώστε το ίδιο κτίριο στο Erisma Structure και στο
πρόγραμμα που χρησιμοποιείτε σήμερα και συγκρίνετε ιδιοπεριόδους, τέμνουσες βάσης, εντατικά
μεγέθη και οπλισμούς — και στείλτε μας κάθε διαφορά που βρίσκετε.</p>"""}),
    ("structure", {"en": "Erisma Structure: whole buildings", "el": "Erisma Structure: ολόκληρα κτίρια"}, {
        "en": """
<p><b>Erisma Structure</b> is the second space of the program (button on the home page). It
analyses and designs a whole RC building drawn in plan, with the same calculations, reports,
3D viewer and licence as the member calculations.</p>
<ol>
<li><b>Grid:</b> on the left give the spans along X and Y and the storey heights. The
defaults are a realistic 3-storey building that passes.</li>
<li><b>Draw:</b> pick a tool and click in the plan — <b>Column</b> (C) or <b>Wall X / Y</b>
(W) on a grid point, <b>Beam</b> (B) between two grid points (adds or removes it),
<b>Opening</b> (O) on a slab panel. With <b>Select</b> (V) click any element to change its size;
<b>Del</b> removes it, <b>Ctrl+Z / Ctrl+Y</b> undo and redo.</li>
<li><b>Results:</b> after every change the building is re-analysed (3D frame, modal response
spectrum, drift, θ, capacity design) and every member is designed. In the plan each member is
coloured by its utilisation; red means it fails — the panel on the right says why and what to
change. The table of the selected element lists its reinforcement per storey; ↗ opens that
member, with its design forces, in the member calculation.</li>
<li><b>Report and 3D:</b> the <b>3D</b> and <b>Report</b> buttons (Ctrl+3) show the model
and the full step-by-step report, which prints with Ctrl+P.</li>
</ol>
<p><b>The ribbon</b> follows the workflow of professional structural software — File → Home →
Draw → Define → Foundation → Loads → Analyse → Design → Results → View → Help. In the 3D view the
member under the pointer is highlighted with its name, size, bars and utilisation, a click selects
it; in Results the chosen mode (or the deformed shape) can be animated, with a speed control.
Previously it grouped the commands as:
<b>File</b> (new, open, save, print, HTML report, CSV table) · <b>Home</b> (undo/redo, delete,
select all columns/beams/walls or the failing members, <b>Run</b> F5 and the <b>Auto</b> switch for
large models, views) · <b>Model</b> (element tools, grid wizard, add/remove axes and storeys,
default sections) · <b>Loads</b> · <b>Seismic</b> · <b>Design</b> (materials, options, member
table) · <b>Results</b> (colour by utilisation, steel ratio or pass/fail, the storey shown,
reinforcement labels, jump to modes, storey checks and quantities in the report) · <b>View</b>
(zoom, fit, what is shown, full screen) · <b>Help</b>. Double-click a tab to collapse the ribbon.</p>
<p>In the plan: <b>Shift+click</b> adds to the selection, dragging a window selects several
elements (their sizes can then be changed together), the wheel zooms, the middle button pans and
the right button opens a menu (properties, select all of the type, open in the member
calculation, delete). The status bar shows the cursor coordinates and how many members pass.</p>
<p><b>What is checked.</b> Columns (EC2 bending, biaxial, slenderness, shear; EC8 DCM
detailing), beams (EC2 bending, shear, <b>deflection by span/depth 7.4.2</b>; EC8 detailing),
walls (EC8 ductile walls), <b>slabs</b> (every panel as a two-way slab, continuous over
neighbouring panels), the <b>foundation</b> — a <b>raft</b> (default): MITC4 plate finite
elements on Winkler springs analysed together with the frame, Wood–Armer bending with a basic
mesh and additional bars, shear, punching at every column (EN 1992-1-1 6.4, soil reaction
deducted), EC7 bearing and Annex H settlement; or foundation beams on springs; or isolated pad
footings; seismic actions with the overstrength γ_Rd·Ω of EN 1998-1 4.4.2.6 —, storey drifts, θ, α_cr, effective modal mass
and capacity design (ΣM_Rc ≥ 1.3 ΣM_Rb, capacity shears).</p>
<p><b>Loads and combinations.</b> In the <b>Loads</b> tab create load cases (permanent,
imposed with its use category, snow), pick the Area / Line / Point tool and click slab panels,
beams or grid points (on all floors, the roof or one storey). <b>Combinations…</b> lists the
EN 1990 combinations generated with the factors of the National Annex (ULS 6.10 with each
variable action leading, SLS characteristic / frequent / quasi-permanent, seismic) and lets you
add your own; members are designed for the envelope.</p>
<p><b>Plan + 3D</b> shows both windows at once; elements can be selected in the 3D view too
(empty positions are drawn faintly so that the tools can add columns and beams there). The
<b>Results</b> tab switches the 3D bending-moment, shear, axial-force and deformed-shape
diagrams and the first three mode shapes on and off; the right panel lists the periods with the
character of each mode (X, Y or torsion) and the EC8 regularity, the left panel the storey drifts.
The report contains the full regularity check (centres of mass and stiffness, torsional radii,
compactness, slenderness, storey stiffness) and the resulting q.</p>
<p><b>Auto-size</b> (Home or Design tab) repeats the complete calculation and enlarges what
fails — columns, beams, walls, slab thickness, foundation beams, the number of modes, P-Δ —
until every Eurocode check passes. It lists every change and applies it only when you press
<b>Apply</b> (Ctrl+Z undoes it).</p>
<p>The layout is the same on every storey (typical floor). The work is saved automatically in
the browser; <b>Save</b> writes a project file that <b>Open</b> brings back.</p>""",
        "el": """
<p>Το <b>Erisma Structure</b> είναι ο δεύτερος χώρος του προγράμματος (κουμπί στην αρχική
σελίδα). Αναλύει και διαστασιολογεί ολόκληρο κτίριο Ο/Σ που σχεδιάζεται σε κάτοψη, με τους
ίδιους υπολογισμούς, τεύχη, 3D προβολή και άδεια με τους υπολογισμούς μελών.</p>
<ol>
<li><b>Κάνναβος:</b> αριστερά δίνετε τα ανοίγματα κατά X και Y και τα ύψη ορόφων. Οι
προεπιλογές είναι ένα ρεαλιστικό τριώροφο κτίριο που επαρκεί.</li>
<li><b>Σχεδίαση:</b> διαλέγετε εργαλείο και κάνετε κλικ στην κάτοψη — <b>Υποστύλωμα</b> (C)
ή <b>Τοίχωμα X / Y</b> (W) σε κόμβο του καννάβου, <b>Δοκός</b> (B) ανάμεσα σε δύο κόμβους
(προσθήκη ή αφαίρεση), <b>Άνοιγμα πλάκας</b> (O) σε φάτνωμα. Με την <b>Επιλογή</b> (V)
κάνετε κλικ σε στοιχείο για να αλλάξετε τη διατομή του· το <b>Del</b> το διαγράφει, τα
<b>Ctrl+Z / Ctrl+Y</b> αναιρούν και επαναλαμβάνουν.</li>
<li><b>Αποτελέσματα:</b> μετά από κάθε αλλαγή το κτίριο επιλύεται ξανά (χωρικό πλαίσιο,
φάσμα απόκρισης, σχετικές μετακινήσεις, θ, ικανοτικός σχεδιασμός) και διαστασιολογείται κάθε
μέλος. Στην κάτοψη κάθε μέλος χρωματίζεται ανάλογα με την εκμετάλλευσή του· κόκκινο σημαίνει
ανεπάρκεια — δεξιά φαίνεται γιατί και τι να αλλάξετε. Ο πίνακας του επιλεγμένου στοιχείου
δίνει τον οπλισμό ανά όροφο· το ↗ ανοίγει το μέλος, με τα εντατικά του, στον υπολογισμό
μέλους.</li>
<li><b>Τεύχος και 3D:</b> τα κουμπιά <b>3D</b> και <b>Τεύχος</b> (Ctrl+3) δείχνουν το
μοντέλο και το πλήρες αναλυτικό τεύχος, που εκτυπώνεται με Ctrl+P.</li>
</ol>
<p><b>Το ribbon</b> ακολουθεί τη ροή εργασίας των επαγγελματικών στατικών προγραμμάτων — Αρχείο →
Αρχική → Σχεδίαση → Ορισμοί → Θεμελίωση → Φορτία → Ανάλυση → Σχεδιασμός → Αποτελέσματα → Προβολή →
Βοήθεια. Στο 3D το μέλος κάτω από τον δείκτη φωτίζεται και δείχνει όνομα, διατομή, οπλισμό και
εκμετάλλευση· το κλικ το επιλέγει. Στα Αποτελέσματα η επιλεγμένη ιδιομορφή (ή ο παραμορφωμένος
φορέας) κινείται, με ρύθμιση ταχύτητας. Αναλυτικά οι εντολές:
<b>Αρχείο</b> (νέο, άνοιγμα, αποθήκευση, εκτύπωση, τεύχος HTML, πίνακας CSV) · <b>Αρχική</b>
(αναίρεση/επανάληψη, διαγραφή, επιλογή όλων των υποστυλωμάτων/δοκών/τοιχωμάτων ή των ανεπαρκών
μελών, <b>Επίλυση</b> F5 και διακόπτης <b>Αυτόματα</b> για μεγάλα μοντέλα, προβολές) ·
<b>Μοντέλο</b> (εργαλεία στοιχείων, οδηγός καννάβου, προσθήκη/αφαίρεση αξόνων και ορόφων,
προεπιλεγμένες διατομές) · <b>Φορτία</b> · <b>Σεισμός</b> · <b>Σχεδιασμός</b> (υλικά, επιλογές,
πίνακας μελών) · <b>Αποτελέσματα</b> (χρωματισμός κατά εκμετάλλευση, ποσοστό οπλισμού ή επάρκεια,
όροφος προβολής, ετικέτες οπλισμού, μετάβαση σε ιδιομορφές, ελέγχους ορόφων και ποσότητες του
τεύχους) · <b>Προβολή</b> (zoom, προσαρμογή, τι εμφανίζεται, πλήρης οθόνη) · <b>Βοήθεια</b>.
Διπλό κλικ σε καρτέλα συμπτύσσει το ribbon.</p>
<p>Στην κάτοψη: <b>Shift+κλικ</b> προσθέτει στην επιλογή, το σύρσιμο παραθύρου επιλέγει πολλά
στοιχεία (που αλλάζουν διατομή μαζί), η ροδέλα κάνει zoom, το μεσαίο πλήκτρο μετακινεί και το
δεξί κλικ ανοίγει μενού (ιδιότητες, επιλογή όλων του τύπου, άνοιγμα στον υπολογισμό μέλους,
διαγραφή). Η γραμμή κατάστασης δείχνει τις συντεταγμένες του δείκτη και πόσα μέλη επαρκούν.</p>
<p><b>Τι ελέγχεται.</b> Υποστυλώματα (EC2 κάμψη, διαξονική, λυγηρότητα, διάτμηση· EC8
κατασκευαστικές διατάξεις ΚΠΜ), δοκοί (EC2 κάμψη, διάτμηση, <b>βέλος με λόγο ανοίγματος/ύψους
7.4.2</b>· EC8 διατάξεις), τοιχώματα (EC8 πλάστιμα τοιχώματα), <b>πλάκες</b> (κάθε φάτνωμα ως
διέρειστη πλάκα, συνεχής πάνω από γειτονικά φατνώματα), η <b>θεμελίωση</b> — <b>κοιτόστρωση</b>
(προεπιλογή): πεπερασμένα στοιχεία πλάκας MITC4 σε ελατήρια Winkler, επιλυμένα μαζί με τον
φορέα, κάμψη κατά Wood–Armer με βασικό και πρόσθετο οπλισμό, διάτμηση, διάτρηση σε κάθε
υποστύλωμα (EN 1992-1-1 6.4, με αφαίρεση της αντίδρασης εδάφους), φέρουσα ικανότητα EC7 και
καθιζήσεις Παραρτήματος H· ή πεδιλοδοκοί σε ελατήρια· ή μεμονωμένα πέδιλα· σεισμικές δράσεις με
την υπεραντοχή γ_Rd·Ω του EN 1998-1 4.4.2.6 —, σχετικές μετακινήσεις, θ, α_cr,
δρώσα ιδιομορφική μάζα και ικανοτικός σχεδιασμός (ΣM_Rc ≥ 1.3 ΣM_Rb, ικανοτικές τέμνουσες).</p>
<p><b>Φορτία και συνδυασμοί.</b> Στην καρτέλα <b>Φορτία</b> δημιουργείτε φορτίσεις (μόνιμες,
κινητές με την κατηγορία χρήσης τους, χιόνι), διαλέγετε εργαλείο Επιφανειακό / Γραμμικό /
Σημειακό και κάνετε κλικ σε φατνώματα, δοκούς ή κόμβους (σε όλους τους ορόφους, στο δώμα ή σε
έναν όροφο). Οι <b>Συνδυασμοί…</b> δείχνουν τους συνδυασμούς EN 1990 που δημιουργούνται με τους
συντελεστές του Εθνικού Προσαρτήματος (ΟΚΑ 6.10 με κάθε μεταβλητή δράση ως κύρια, ΟΚΛ
χαρακτηριστικός / συχνός / οιονεί μόνιμος, σεισμικός) και επιτρέπουν δικούς σας· τα μέλη
διαστασιολογούνται για την περιβάλλουσα.</p>
<p>Η <b>Κάτοψη + 3D</b> δείχνει και τα δύο παράθυρα μαζί· τα στοιχεία επιλέγονται και στο 3D (οι
κενές θέσεις εμφανίζονται αχνά ώστε τα εργαλεία να προσθέτουν εκεί υποστυλώματα και δοκούς). Η
καρτέλα <b>Αποτελέσματα</b> ανάβει/σβήνει στο 3D τα διαγράμματα ροπών, τεμνουσών, αξονικών, τον
παραμορφωμένο φορέα και τις τρεις πρώτες ιδιομορφές· το δεξί πάνελ δείχνει τις ιδιοπεριόδους με
τον χαρακτήρα κάθε ιδιομορφής (X, Y ή στρέψη) και την κανονικότητα EC8, το αριστερό τις σχετικές
μετακινήσεις ορόφων. Το τεύχος περιέχει τον πλήρη έλεγχο κανονικότητας (κέντρα μάζας και
δυσκαμψίας, ακτίνες δυστρεψίας, συμπαγή μορφή, λυγηρότητα, δυσκαμψία ορόφων) και το q που
προκύπτει.</p>
<p>Η <b>Αυτόματη διαστασιολόγηση</b> (καρτέλα Αρχική ή Σχεδιασμός) επαναλαμβάνει τον πλήρη
υπολογισμό και μεγαλώνει ό,τι ανεπαρκεί — υποστυλώματα, δοκούς, τοιχώματα, πάχος πλάκας,
πεδιλοδοκούς, αριθμό ιδιομορφών, P-Δ — μέχρι να περάσουν όλοι οι έλεγχοι των Ευρωκωδίκων.
Δείχνει κάθε αλλαγή και την εφαρμόζει μόνο όταν πατήσετε <b>Εφαρμογή</b> (το Ctrl+Z την
αναιρεί).</p>
<p>Η διάταξη είναι ίδια σε όλους τους ορόφους (τυπικός όροφος). Η εργασία αποθηκεύεται
αυτόματα στον browser· η <b>Αποθήκευση</b> γράφει αρχείο έργου που ανοίγει με το
<b>Άνοιγμα</b>.</p>"""}),
    ("project", {"en": "Projects: several calculations together", "el": "Έργα: πολλοί υπολογισμοί μαζί"}, {
        "en": """
<p>A <b>project</b> collects all the calculations of one job (e.g. column C1, footing F1,
retaining wall W1) so that they are saved, linked, priced and printed together.</p>
<ol>
<li>Open a calculation and set its inputs.</li>
<li>Press <b>+ Add to project</b> (above the form) and give the element a name, e.g.
“Footing F1”. The calculation is copied into the project; from now on the inputs you change
are kept in that project item.</li>
<li>Repeat for every element. The same calculation can be added several times (F1, F2, …).</li>
</ol>
<p>The <b>📁 Project</b> section at the top of the left sidebar lists the items. The dot in front
of each name is <span class="ok">green</span> when all checks pass, <span class="ko">red</span>
when a check fails and grey before the first run; hover over it to see the maximum utilisation
U. 🔗<i>n</i> shows how many inputs are linked. Next to each item: <b>↑</b> moves it up (this is
also the order in the project report), <b>✎</b> renames, <b>×</b> removes it (links that used it
are removed too). The buttons under the title are <b>📄 Report</b> (project report),
<b>⚖ Compare</b> and <b>✚ New</b> (new, empty project).</p>
<p>The project is autosaved in the browser. <b>Save</b> (<kbd>Ctrl</kbd>+<kbd>S</kbd>) then
writes <i>one</i> <code>.erisma</code> file with all items, their inputs, links and the project
details (file name from the job no. or project name); <b>Open</b> restores the whole project.
<b>↺ Reset</b> on a project item also removes its links.</p>""",
        "el": """
<p>Ένα <b>έργο</b> συγκεντρώνει όλους τους υπολογισμούς μιας μελέτης (π.χ. υποστύλωμα Κ1, πέδιλο
Π1, τοίχος Τ1) ώστε να αποθηκεύονται, να συνδέονται, να κοστολογούνται και να τυπώνονται
μαζί.</p>
<ol>
<li>Ανοίξτε έναν υπολογισμό και δώστε τα δεδομένα του.</li>
<li>Πατήστε <b>+ Στο έργο</b> (πάνω από τη φόρμα) και δώστε όνομα στοιχείου, π.χ. «Πέδιλο Π1».
Ο υπολογισμός αντιγράφεται στο έργο· από εκεί και πέρα οι αλλαγές σας κρατούνται σε αυτό το
στοιχείο του έργου.</li>
<li>Επαναλάβετε για κάθε στοιχείο. Ο ίδιος υπολογισμός μπορεί να μπει πολλές φορές (Π1, Π2, …).</li>
</ol>
<p>Η ενότητα <b>📁 Έργο</b> στην κορυφή της αριστερής μπάρας δείχνει τα στοιχεία. Η τελεία μπροστά
από κάθε όνομα είναι <span class="ok">πράσινη</span> όταν όλοι οι έλεγχοι επαρκούν,
<span class="ko">κόκκινη</span> όταν κάποιος δεν επαρκεί και γκρι πριν τον πρώτο υπολογισμό·
με το ποντίκι πάνω της φαίνεται η μέγιστη αξιοποίηση U. Το 🔗<i>n</i> δείχνει πόσα δεδομένα
είναι συνδεδεμένα. Δίπλα σε κάθε στοιχείο: <b>↑</b> μετακίνηση πάνω (αυτή είναι και η σειρά στο
τεύχος έργου), <b>✎</b> μετονομασία, <b>×</b> αφαίρεση (αφαιρούνται και οι συνδέσεις που το
χρησιμοποιούσαν). Τα κουμπιά κάτω από τον τίτλο: <b>📄 Τεύχος</b> (τεύχος έργου),
<b>⚖ Σύγκριση</b> και <b>✚ Νέο</b> (νέο, κενό έργο).</p>
<p>Το έργο αποθηκεύεται αυτόματα στον browser. Η <b>Αποθήκευση</b> (<kbd>Ctrl</kbd>+<kbd>S</kbd>)
γράφει <i>ένα</i> αρχείο <code>.erisma</code> με όλα τα στοιχεία, τα δεδομένα τους, τις
συνδέσεις και τα στοιχεία έργου (όνομα αρχείου από τον αρ. έργου ή το όνομα του έργου)· το
<b>Άνοιγμα</b> επαναφέρει ολόκληρο το έργο. Η <b>↺ Επαναφορά</b> σε στοιχείο έργου
καταργεί και τις συνδέσεις του.</p>"""}),
    ("chain", {"en": "Linking calculations (calculation chain)", "el": "Σύνδεση υπολογισμών (αλυσίδα)"}, {
        "en": """
<p>An input of one project item can take its value from a <b>result</b> of another item, so a
change travels down the chain by itself — e.g. the axial force of the column becomes the load
on the footing.</p>
<ol>
<li>Open the receiving item (e.g. “Footing F1”) from the project list. Every numeric input now
has a <b>🔗</b> button next to its label.</li>
<li>Click 🔗. Choose the <b>source calculation</b>; the list shows only its results whose unit
is of the <b>same kind</b> as the input (force with force, moment with moment, …), with symbol,
description and current value. Units are converted automatically (e.g. kN → MN).</li>
<li>Optionally type a <b>factor</b> — e.g. <code>1/1,35</code> to turn a design value N<sub>Ed</sub>
into a characteristic permanent load G — and tick <b>Use absolute value</b> for results that may
be negative (e.g. hogging moments).</li>
<li>Press <b>Link</b>. The field becomes read-only and shows
“🔗 from Column C1: N_Ed × 0,741”; <b>×</b> in that line removes the link.</li>
</ol>
<p>Value used = factor × (|source result| if “absolute” is ticked, else source result).
Before each run Erisma recalculates the whole project in dependency order (sources first), so
the value is always current. If the source item is deleted or its result no longer exists, the
field is marked red (“Link broken”) and the last value is kept. Links that form a loop
(A → B → A) are refused with the message “Circular link between calculations” naming the items.
Linked values are visible in the report as ordinary inputs, so the sheet remains checkable by
hand.</p>""",
        "el": """
<p>Ένα δεδομένο ενός στοιχείου του έργου μπορεί να παίρνει την τιμή του από ένα
<b>αποτέλεσμα</b> άλλου στοιχείου, ώστε κάθε αλλαγή να περνά μόνη της στην αλυσίδα — π.χ. η
αξονική δύναμη του υποστυλώματος γίνεται φορτίο του πεδίλου.</p>
<ol>
<li>Ανοίξτε από τη λίστα του έργου το στοιχείο που δέχεται την τιμή (π.χ. «Πέδιλο Π1»). Κάθε
αριθμητικό δεδομένο έχει τώρα κουμπί <b>🔗</b> δίπλα στην ετικέτα του.</li>
<li>Πατήστε 🔗. Επιλέξτε τον <b>υπολογισμό προέλευσης</b>· η λίστα δείχνει μόνο τα αποτελέσματά
του με μονάδα <b>ίδιου είδους</b> με το δεδομένο (δύναμη με δύναμη, ροπή με ροπή, …), με
σύμβολο, περιγραφή και τρέχουσα τιμή. Οι μονάδες μετατρέπονται αυτόματα (π.χ. kN → MN).</li>
<li>Προαιρετικά δώστε <b>συντελεστή</b> — π.χ. <code>1/1,35</code> για μετατροπή της τιμής
σχεδιασμού N<sub>Ed</sub> σε χαρακτηριστικό μόνιμο φορτίο G — και τσεκάρετε <b>Απόλυτη τιμή</b>
για αποτελέσματα που μπορεί να είναι αρνητικά (π.χ. αρνητικές ροπές).</li>
<li>Πατήστε <b>Σύνδεση</b>. Το πεδίο γίνεται μόνο για ανάγνωση και δείχνει
«🔗 από Υποστύλωμα Κ1: N_Ed × 0,741»· το <b>×</b> σε αυτή τη γραμμή καταργεί τη σύνδεση.</li>
</ol>
<p>Τιμή που χρησιμοποιείται = συντελεστής × (|αποτέλεσμα| αν έχει τσεκαριστεί η «Απόλυτη τιμή»,
αλλιώς αποτέλεσμα). Πριν από κάθε υπολογισμό το Erisma ξαναϋπολογίζει όλο το έργο με τη σειρά
των εξαρτήσεων (πρώτα οι πηγές), οπότε η τιμή είναι πάντα τρέχουσα. Αν το στοιχείο προέλευσης
διαγραφεί ή το αποτέλεσμα δεν υπάρχει πια, το πεδίο γίνεται κόκκινο («Η σύνδεση δεν ισχύει»)
και κρατιέται η τελευταία τιμή. Συνδέσεις που κλείνουν κύκλο (Α → Β → Α) απορρίπτονται με το
μήνυμα «Κυκλική σύνδεση μεταξύ υπολογισμών» και τα ονόματα των στοιχείων. Οι συνδεδεμένες
τιμές εμφανίζονται στο τεύχος ως κανονικά δεδομένα, ώστε ο έλεγχος με το χέρι να είναι
δυνατός.</p>"""}),
    ("preport", {"en": "Project report and company logo", "el": "Τεύχος έργου και λογότυπο"}, {
        "en": """
<p><b>📄</b> in the project header produces the whole project as one printable document:</p>
<ul>
<li><b>Cover page</b> with your company logo, project name and the project details (company,
job no., engineer, checker, date, National Annex).</li>
<li><b>Contents</b>: every item with its calculation, result (PASS / FAIL) and maximum
utilisation.</li>
<li>Every calculation sheet in full, in the order of the project list.</li>
</ul>
<p>It opens in a new tab; print it with <kbd>Ctrl</kbd>+<kbd>P</kbd> or save it as PDF.
<b>Logo:</b> in the project details press <b>🖼 …</b> next to “Company logo” and choose an
image (PNG, JPG, SVG…). It is reduced to at most 360 px to keep project files small, stored in
the project file and printed on the cover and in the title block. “Remove logo” deletes it.</p>""",
        "el": """
<p>Το <b>📄</b> στην κεφαλίδα του έργου παράγει όλο το έργο ως ένα τεύχος για εκτύπωση:</p>
<ul>
<li><b>Εξώφυλλο</b> με το λογότυπο της εταιρείας σας, το όνομα του έργου και τα στοιχεία έργου
(εταιρεία, αρ. έργου, συντάκτης, έλεγχος, ημερομηνία, Εθνικό Προσάρτημα).</li>
<li><b>Περιεχόμενα</b>: κάθε στοιχείο με τον υπολογισμό του, το αποτέλεσμα (ΕΠΑΡΚΕΙ /
ΑΝΕΠΑΡΚΕΙ) και τη μέγιστη αξιοποίηση.</li>
<li>Κάθε φύλλο υπολογισμών πλήρες, με τη σειρά της λίστας του έργου.</li>
</ul>
<p>Ανοίγει σε νέα καρτέλα· τυπώστε το με <kbd>Ctrl</kbd>+<kbd>P</kbd> ή αποθηκεύστε το ως PDF.
<b>Λογότυπο:</b> στα στοιχεία έργου πατήστε <b>🖼 …</b> δίπλα στο «Λογότυπο εταιρείας» και
επιλέξτε εικόνα (PNG, JPG, SVG…). Μικραίνει σε έως 360 px ώστε τα αρχεία να μένουν μικρά,
αποθηκεύεται στο αρχείο έργου και τυπώνεται στο εξώφυλλο και στην κεφαλίδα. Το «Αφαίρεση
λογοτύπου» το διαγράφει.</p>"""}),
    ("cost", {"en": "Quantities and cost estimate", "el": "Ποσότητες και εκτίμηση κόστους"}, {
        "en": """
<p>Calculations of members that are built (footings, walls, beams, columns, slabs, piles, steel
and timber members, strengthening…) end with a table <b>Quantities and cost estimate</b>:
concrete, reinforcement, structural steel, timber, masonry, gabions, formwork, excavation, pile
boring, ground anchors or FRP, each with quantity, unit price and cost. The total also appears
in the status banner (<b>💶 ≈ … €</b>; hover for the quantities). Section “Calculation
reference” states for each calculation whether it has quantities.</p>
<ul>
<li>Quantities come from the actual geometry and the reinforcement chosen in the calculation
(steel at 7850 kg/m³). Where the bar layout is not modelled in detail (e.g. walls, tanks) a
typical reinforcement ratio is used and stated under the table.</li>
<li><b>Unit prices</b>: press <b>💶 Unit prices</b> in the project details or <b>✎</b> on the
cost chip. Defaults (€, supply and placing): concrete 130/m³, reinforcement 1,30/kg, structural
steel 3,20/kg, timber 950/m³, masonry 160/m³, gabions 95/m³, formwork 25/m², excavation 12/m³,
pile boring 70/m, anchors 90/m, FRP 120/m² per layer. Your prices are kept with the project and
the project file; “Reset prices” returns to the defaults.</li>
</ul>
<p class="warn">The estimate is for comparing alternatives and preliminary budgets; it is not
a bill of quantities (no laps, wastage, site overheads or VAT).</p>""",
        "el": """
<p>Οι υπολογισμοί στοιχείων που κατασκευάζονται (πέδιλα, τοίχοι, δοκοί, υποστυλώματα, πλάκες,
πάσσαλοι, μεταλλικά και ξύλινα μέλη, ενισχύσεις…) τελειώνουν με πίνακα <b>Ποσότητες και
εκτίμηση κόστους</b>: σκυρόδεμα, οπλισμός, δομικός χάλυβας, ξυλεία, τοιχοποιία,
συρματοκιβώτια, ξυλότυποι, εκσκαφή, διάτρηση πασσάλων, αγκύρια ή ΙΟΠ, το καθένα με ποσότητα,
τιμή μονάδας και κόστος. Το σύνολο φαίνεται και στη μπάρα κατάστασης (<b>💶 ≈ … €</b>· με το
ποντίκι φαίνονται οι ποσότητες). Ο «Οδηγός υπολογισμών» αναφέρει για κάθε υπολογισμό αν έχει
ποσότητες.</p>
<ul>
<li>Οι ποσότητες προκύπτουν από την πραγματική γεωμετρία και τον οπλισμό του υπολογισμού
(χάλυβας 7850 kg/m³). Όπου η διάταξη ράβδων δεν προσομοιώνεται αναλυτικά (π.χ. τοίχοι,
δεξαμενές) λαμβάνεται τυπικό ποσοστό οπλισμού, που αναγράφεται κάτω από τον πίνακα.</li>
<li><b>Τιμές μονάδας</b>: πατήστε <b>💶 Τιμές μονάδας</b> στα στοιχεία έργου ή το <b>✎</b> στην
ένδειξη κόστους. Προεπιλογές (€, προμήθεια και τοποθέτηση): σκυρόδεμα 130/m³, οπλισμός
1,30/kg, δομικός χάλυβας 3,20/kg, ξυλεία 950/m³, τοιχοποιία 160/m³, συρματοκιβώτια 95/m³,
ξυλότυποι 25/m², εκσκαφή 12/m³, διάτρηση πασσάλων 70/m, αγκύρια 90/m, ΙΟΠ 120/m² ανά στρώση.
Οι τιμές σας κρατούνται με το έργο και το αρχείο έργου· το «Προεπιλεγμένες τιμές» επαναφέρει
τις αρχικές.</li>
</ul>
<p class="warn">Η εκτίμηση προορίζεται για σύγκριση λύσεων και προϋπολογισμό προμελέτης· δεν
είναι προμέτρηση (δεν περιλαμβάνει υπερκαλύψεις, φύρα, γενικά έξοδα ή ΦΠΑ).</p>"""}),
    ("optimise", {"en": "Automatic design — most economical solution", "el": "Αυτόματη διαστασιολόγηση — οικονομικότερη λύση"}, {
        "en": """
<p><b>🎯 Most economical</b> (above the form) searches for the <b>cheapest design that passes every check</b>.
It is available for the calculations listed with “Automatic design” in the calculation
reference, together with the variables it may change.</p>
<ol>
<li>The dialog lists the design variables (e.g. footing B<sub>x</sub>, B<sub>y</sub>, h; beam
depth, number and diameter of bars; steel section). Untick the ones that must stay as they are
(e.g. a width fixed by the architect) and adjust <b>From / To / Step</b> (in the field's unit).
Choice variables (sections, bar diameters) try all options.</li>
<li>Press <b>Search</b>. Every candidate is calculated in full with your other inputs, loads
and National Annex. Ranking: first designs where all checks pass, then lowest cost (from the
quantities and your unit prices), then lowest utilisation.</li>
<li>The result shows current and optimum values side by side (changed rows highlighted), cost
and utilisation of both, number of trials, method and time. <b>Apply</b> puts the optimum into
the form (<kbd>Ctrl</kbd>+<kbd>Z</kbd> undoes it).</li>
</ol>
<p><b>Method:</b> if the combinations are at most 2500 every one is tried (<i>exhaustive</i>,
the true optimum on the grid). Otherwise <i>coordinate descent</i>: starting from your design,
each variable in turn is run over its whole range and the best value kept, repeated (up to 5
rounds) until nothing improves — this gives a very good but not always the global optimum, so
it is worth starting from a sensible design. A search stops after 40 s and returns the best
found. If nothing passes in the ranges: “No passing design found — widen the ranges”. The
optimum is an ordinary design: check it and round it to practical dimensions if necessary.</p>""",
        "el": """
<p>Το <b>🎯 Οικονομικότερη λύση</b> (πάνω από τη φόρμα) αναζητά τη <b>φθηνότερη λύση που επαρκεί σε όλους τους
ελέγχους</b>. Υπάρχει στους υπολογισμούς που στον «Οδηγό υπολογισμών» έχουν «Αυτόματη
διαστασιολόγηση», μαζί με τις μεταβλητές που μπορεί να αλλάξει.</p>
<ol>
<li>Το παράθυρο δείχνει τις μεταβλητές σχεδιασμού (π.χ. πέδιλο B<sub>x</sub>, B<sub>y</sub>, h·
δοκός ύψος, πλήθος και διάμετρος ράβδων· μεταλλική διατομή). Ξετσεκάρετε όσες πρέπει να
μείνουν ως έχουν (π.χ. πλάτος που ορίζει ο αρχιτέκτονας) και ρυθμίστε τα <b>Από / Έως / Βήμα</b>
(στη μονάδα του πεδίου). Οι μεταβλητές επιλογής (διατομές, διάμετροι) δοκιμάζουν όλες τις
επιλογές.</li>
<li>Πατήστε <b>Αναζήτηση</b>. Κάθε υποψήφια λύση υπολογίζεται πλήρως με τα υπόλοιπα δεδομένα,
τα φορτία και το Εθνικό Προσάρτημα. Κατάταξη: πρώτα οι λύσεις που επαρκούν σε όλους τους
ελέγχους, μετά το μικρότερο κόστος (από τις ποσότητες και τις τιμές σας), μετά η μικρότερη
αξιοποίηση.</li>
<li>Το αποτέλεσμα δείχνει την τρέχουσα και τη βέλτιστη λύση δίπλα-δίπλα (οι αλλαγμένες γραμμές
τονίζονται), το κόστος και την αξιοποίηση και των δύο, πλήθος δοκιμών, μέθοδο και χρόνο. Η
<b>Εφαρμογή</b> περνά τη βέλτιστη λύση στη φόρμα (το <kbd>Ctrl</kbd>+<kbd>Z</kbd> την
αναιρεί).</li>
</ol>
<p><b>Μέθοδος:</b> αν οι συνδυασμοί είναι έως 2500 δοκιμάζονται όλοι (<i>πλήρης αναζήτηση</i>,
το πραγματικό βέλτιστο στον κάνναβο). Αλλιώς <i>αναζήτηση ανά μεταβλητή</i>: ξεκινώντας από τη
δική σας λύση, κάθε μεταβλητή με τη σειρά διατρέχει όλο το εύρος της και κρατιέται η καλύτερη
τιμή, επαναληπτικά (έως 5 κύκλοι) μέχρι να μη βελτιώνεται τίποτα — δίνει πολύ καλή αλλά όχι
πάντα την ολικά βέλτιστη λύση, γι' αυτό αξίζει να ξεκινάτε από λογική λύση. Η αναζήτηση
σταματά μετά από 40 s και δίνει την καλύτερη που βρήκε. Αν καμία δεν επαρκεί στα εύρη:
«Δεν βρέθηκε λύση που επαρκεί — διευρύνετε τα όρια». Η βέλτιστη λύση είναι κανονική λύση:
ελέγξτε τη και στρογγυλέψτε τη σε πρακτικές διαστάσεις αν χρειάζεται.</p>"""}),
    ("compare", {"en": "Comparing alternative solutions", "el": "Σύγκριση εναλλακτικών λύσεων"}, {
        "en": """
<p>Erisma compares different solutions for the same element — e.g. footing 2,0 × 2,0 m against
2,4 × 2,4 m, or a cantilever RC wall against a gravity wall — by checks and by cost.</p>
<ol>
<li>Open the calculation and enter the first solution.</li>
<li>Press <b>⚖ Alternative</b> above the form. The current solution is kept in the project
(“… – Solution A”) and a copy opens with the name you give (default “… – Solution B”).</li>
<li>Change the copy — other dimensions, other reinforcement, or open another calculation (e.g.
a gravity wall) and add it with <b>+ Add to project</b>. Press ⚖ Alternative again for more
solutions; a note above the form confirms each one.</li>
<li>Press <b>⚖ Compare</b> in the project list on the left.</li>
</ol>
<p>The table groups the project items by kind of calculation. In each group the solutions are
sorted by cost and show result (PASS / FAIL), maximum utilisation U, quantities, cost and the
<b>difference</b> from the cheapest solution that passes (e.g. “+230 € (+38%)”). The cheapest
solution that passes all checks is marked <b>★</b>; solutions that fail a check are greyed out
and marked “not eligible”. Costs come from the quantities and the unit prices
(💶 in the project details), so set your own prices for a meaningful comparison. With fewer
than two solutions in the project ⚖ Compare shows these steps instead of a table.</p>
<p>To compare <i>wall types</i>, give the items clear names (“Wall W1 – cantilever”, “Wall W1 –
gravity”): different calculation types are listed in separate groups, so read the costs of the
groups side by side.</p>""",
        "el": """
<p>Το Erisma συγκρίνει διαφορετικές λύσεις για το ίδιο στοιχείο — π.χ. πέδιλο 2,0 × 2,0 m με
2,4 × 2,4 m, ή τοίχο ΟΣ προβόλου με τοίχο βαρύτητας — ως προς τους ελέγχους και το κόστος.</p>
<ol>
<li>Ανοίξτε τον υπολογισμό και δώστε την πρώτη λύση.</li>
<li>Πατήστε <b>⚖ Εναλλακτική λύση</b> πάνω από τη φόρμα. Η τρέχουσα λύση κρατιέται στο έργο
(«… – Λύση Α») και ανοίγει αντίγραφο με το όνομα που δίνετε (προεπιλογή «… – Λύση Β»).</li>
<li>Αλλάξτε το αντίγραφο — άλλες διαστάσεις, άλλος οπλισμός — ή ανοίξτε άλλο υπολογισμό (π.χ.
τοίχο βαρύτητας) και προσθέστε τον με <b>+ Στο έργο</b>. Πατήστε ξανά ⚖ Εναλλακτική λύση για
περισσότερες λύσεις· ένα μήνυμα πάνω από τη φόρμα επιβεβαιώνει την καθεμία.</li>
<li>Πατήστε <b>⚖ Σύγκριση</b> στη λίστα του έργου αριστερά.</li>
</ol>
<p>Ο πίνακας ομαδοποιεί τα στοιχεία του έργου ανά είδος υπολογισμού. Σε κάθε ομάδα οι λύσεις
ταξινομούνται κατά κόστος και δείχνουν αποτέλεσμα (ΕΠΑΡΚΕΙ / ΑΝΕΠΑΡΚΕΙ), μέγιστη αξιοποίηση U,
ποσότητες, κόστος και τη <b>διαφορά</b> από τη φθηνότερη λύση που επαρκεί (π.χ. «+230 €
(+38%)»). Η φθηνότερη λύση που επαρκεί σε όλους τους ελέγχους σημειώνεται με <b>★</b>· οι λύσεις
που δεν επαρκούν εμφανίζονται αχνές με την ένδειξη «δεν επαρκεί». Το κόστος προκύπτει από τις
ποσότητες και τις τιμές μονάδας (💶 στα στοιχεία έργου), οπότε βάλτε τις δικές σας τιμές για
ουσιαστική σύγκριση. Με λιγότερες από δύο λύσεις στο έργο, η ⚖ Σύγκριση δείχνει αυτά τα βήματα
αντί για πίνακα.</p>
<p>Για σύγκριση <i>ειδών τοίχου</i>, δώστε σαφή ονόματα («Τοίχος Τ1 – πρόβολος», «Τοίχος Τ1 –
βαρύτητας»): διαφορετικά είδη υπολογισμού εμφανίζονται σε χωριστές ομάδες, οπότε συγκρίνετε τα
κόστη των ομάδων μεταξύ τους.</p>"""}),
    ("dxf", {"en": "DXF drawings for CAD", "el": "Σχέδια DXF για CAD"}, {
        "en": """
<p>For the calculations marked “DXF drawing” in the calculation reference the <b>DXF</b> button
in the top bar downloads a drawing of the current design: plan and/or section with outline,
reinforcement (bars and diameters, e.g. 5Ø16/200), soil line, dimensions
and a title with element and project. It opens in AutoCAD and compatible CAD programs
(BricsCAD, ZWCAD, progeCAD…) (format DXF R12, Greek code page, so Greek text is correct).</p>
<ul>
<li><b>Units:</b> drawing units are millimetres at true size (1 unit = 1 mm); scale it at
plotting.</li>
<li><b>Layers</b> (with colours): CONCRETE (7), REBAR (1 red), SOIL (34), DIM (3 green), TEXT
(2 yellow), AXIS (8), STEEL (5 blue), HATCH (9) — so you can freeze or re-colour them to your
office standard.</li>
<li>The drawing is a starting point for the construction drawing; detailing (laps, anchorage
lengths, bar schedules) is the designer's responsibility.</li>
</ul>""",
        "el": """
<p>Στους υπολογισμούς με «Σχέδιο DXF» στον «Οδηγό υπολογισμών» το κουμπί <b>DXF</b> στην πάνω
μπάρα κατεβάζει σχέδιο της τρέχουσας λύσης: κάτοψη ή/και τομή με περίγραμμα, οπλισμό (ράβδοι
και διάμετροι, π.χ. 5Ø16/200), γραμμή εδάφους, διαστάσεις και τίτλο με στοιχείο και έργο.
Ανοίγει σε AutoCAD και συμβατά προγράμματα CAD (BricsCAD, ZWCAD, progeCAD…) (μορφή DXF R12 με ελληνική
κωδικοσελίδα, ώστε τα ελληνικά να εμφανίζονται σωστά).</p>
<ul>
<li><b>Μονάδες:</b> το σχέδιο είναι σε χιλιοστά σε φυσικό μέγεθος (1 μονάδα = 1 mm)· η κλίμακα
ορίζεται στην εκτύπωση.</li>
<li><b>Layers</b> (με χρώματα): CONCRETE (7), REBAR (1 κόκκινο), SOIL (34), DIM (3 πράσινο), TEXT
(2 κίτρινο), AXIS (8), STEEL (5 μπλε), HATCH (9) — ώστε να τα παγώνετε ή να τα προσαρμόζετε στο
πρότυπο του γραφείου σας.</li>
<li>Το σχέδιο είναι βάση για το κατασκευαστικό σχέδιο· η όπλιση σε λεπτομέρεια (υπερκαλύψεις,
μήκη αγκύρωσης, πίνακες οπλισμού) είναι ευθύνη του μελετητή.</li>
</ul>"""}),
    ("licence", {"en": "Trial and licence", "el": "Δοκιμαστική περίοδος και άδεια χρήσης"}, {
        "en": """
<p>Erisma can be used free of charge with all functions for <b>30 days</b> from the first
start on a computer. The button in the top bar shows the state: “⏳ Trial: <i>n</i> days left”,
“✓ Licensed to <i>name</i>” or “⚠ Trial ended”.</p>
<ul>
<li><b>Activating:</b> click that button, paste the licence key you received
(<code>ERISMA-…</code>; spaces and line breaks are ignored) and press <b>Activate</b>. The key
is checked on your computer (no internet needed) and kept in your user profile
(<code>%APPDATA%\\Erisma</code> on Windows, <code>~/.config/erisma</code> on Mac/Linux), so it
survives updates of the program.</li>
<li><b>After the trial</b> without a key, calculations, reports, project reports, comparison,
automatic design and DXF are blocked and the licence window opens; your inputs and project
files are kept and everything works again as soon as a key is entered. The manual stays
available.</li>
<li>A key carries the licensee's name, the plan and possibly an expiry date. A key that is not
accepted gets a clear reply (“not an Erisma licence key”, “damaged — copy it again”, “not
valid”, “expired on …”). When a key with an expiry date runs out the program falls back to the
trial state. Keys are digitally signed (Ed25519) and cannot be altered or made up.</li>
</ul>""",
        "el": """
<p>Το Erisma χρησιμοποιείται δωρεάν με όλες τις λειτουργίες για <b>30 ημέρες</b> από την πρώτη
εκκίνηση σε έναν υπολογιστή. Το κουμπί στην πάνω μπάρα δείχνει την κατάσταση: «⏳ Δοκιμαστική:
<i>n</i> ημέρες», «✓ Άδεια: <i>όνομα</i>» ή «⚠ Η δοκιμή έληξε».</p>
<ul>
<li><b>Ενεργοποίηση:</b> πατήστε αυτό το κουμπί, επικολλήστε το κλειδί άδειας που λάβατε
(<code>ERISMA-…</code>· κενά και αλλαγές γραμμής αγνοούνται) και πατήστε <b>Ενεργοποίηση</b>. Το
κλειδί ελέγχεται στον υπολογιστή σας (χωρίς internet) και φυλάσσεται στο προφίλ χρήστη
(<code>%APPDATA%\\Erisma</code> στα Windows, <code>~/.config/erisma</code> σε Mac/Linux), οπότε
παραμένει και μετά από ενημέρωση του προγράμματος.</li>
<li><b>Μετά τη δοκιμαστική περίοδο</b> χωρίς κλειδί, μπλοκάρονται οι υπολογισμοί, τα τεύχη,
το τεύχος έργου, η σύγκριση, η αυτόματη διαστασιολόγηση και τα DXF και ανοίγει το παράθυρο
άδειας· τα δεδομένα και τα αρχεία έργου σας διατηρούνται και όλα λειτουργούν ξανά μόλις
δοθεί κλειδί. Το εγχειρίδιο μένει διαθέσιμο.</li>
<li>Το κλειδί περιέχει το όνομα του κατόχου, το πακέτο και ενδεχομένως ημερομηνία λήξης. Αν ένα
κλειδί δεν γίνει δεκτό, το μήνυμα λέει γιατί («δεν είναι κλειδί άδειας Erisma», «κατεστραμμένο
— αντιγράψτε το ξανά», «δεν είναι έγκυρο», «έληξε στις …»). Όταν λήξει κλειδί με ημερομηνία
λήξης, το πρόγραμμα επιστρέφει σε κατάσταση δοκιμής. Τα κλειδιά έχουν ψηφιακή υπογραφή
(Ed25519) και δεν αλλοιώνονται ούτε κατασκευάζονται.</li>
</ul>"""}),
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
               "pseudo-static seismic action (EN 1998-5 4.1.3.3); optional soil nails / anchors "
               "adding T·r about the centre."],
        "el": ["Απλοποιημένη μέθοδος Bishop με αυτόματη αναζήτηση του κρίσιμου κύκλου· "
               "ψευδοστατική σεισμική δράση (EN 1998-5 4.1.3.3)· προαιρετικά ήλοι / αγκύρια "
               "με ροπή T·r ως προς το κέντρο."]},
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
    "ec1_imposed_loads": {
        "en": ["Self-weight g_k = Σ γ t of the build-up with the nominal densities of EN 1991-1-1 "
               "Annex A (upper value of a range); imposed q_k, Q_k by category (Tables 6.2, 6.4, "
               "6.8, 6.10, National Annex value or the recommended one).",
               "α_A = 5/7 ψ0 + A0/A ≤ 1.0 (≥ 0.6 for C, D; Eq. 6.1) for floors, α_n = "
               "(2 + (n − 2) ψ0)/n for columns (Eq. 6.2); movable partitions 0.5 / 0.8 / "
               "1.2 kN/m² (6.3.1.2(8)) added unreduced; parapets Table 6.12, car-park barriers "
               "Annex B."],
        "el": ["Ίδιο βάρος g_k = Σ γ t της διαστρωμάτωσης με τις ονομαστικές πυκνότητες του "
               "Παραρτήματος A του EN 1991-1-1 (άνω τιμή εύρους)· επιβαλλόμενα q_k, Q_k ανά "
               "κατηγορία (Πίνακες 6.2, 6.4, 6.8, 6.10, τιμή Εθνικού Προσαρτήματος ή η "
               "προτεινόμενη).",
               "α_A = 5/7 ψ0 + A0/A ≤ 1,0 (≥ 0,6 για C, D· Εξ. 6.1) για δάπεδα, α_n = "
               "(2 + (n − 2) ψ0)/n για υποστυλώματα (Εξ. 6.2)· μετακινούμενα χωρίσματα 0,5 / 0,8 / "
               "1,2 kN/m² (6.3.1.2(8)) προστίθενται χωρίς μείωση· στηθαία Πίνακας 6.12, "
               "κιγκλιδώματα χώρων στάθμευσης Παράρτημα B."]},
    "ec1_wind_pressures": {
        "en": ["q_p(z_e) as in 'Wind and snow loads at the site' with z_e = h (h + h_p for "
               "parapets); zones with e = min(b, 2h) for θ = 0°, 90° (and 180° for monopitch).",
               "c_pe from Tables 7.1–7.5 (interpolation in h/d, pitch and h_p/h, r/h; same-sign "
               "only), c_pe,1 → c_pe,10 by log10 A (Figure 7.2); net w = q_p (c_pe − c_pi) with "
               "the more onerous c_pi; canopies c_f and c_p,net of Tables 7.6/7.7 linear in φ.",
               "Multispan roofs by Figure 7.10 (span 1 full zones, following spans H/I × 0.8, 0.6 "
               "or −0.4); vaulted roofs by Figure 7.11 (A, B, C = ¼, ½, ¼ of the arc); dominant "
               "openings c_pi = 0.75 … 0.90 c_pe at the opening (Eq. 7.2/7.3); friction "
               "c_fr q_p A_fr beyond min(2b, 4h) (7.5).",
               "Free-standing walls and parapets c_p,net of Table 7.9 (l/h, φ, return corners) "
               "with shelter ψ_s (Figure 7.20); signboards c_f = 1.8 at z_g + h/2, e = ±0.25 b.",
               "PROVISIONAL: coefficients entered from prEN 1991-1-4:2004; to be verified "
               "against EN 1991-1-4:2005 + A1:2010."],
        "el": ["q_p(z_e) όπως στον υπολογισμό «Άνεμος και χιόνι» με z_e = h (h + h_p με "
               "στηθαίο)· ζώνες με e = min(b, 2h) για θ = 0°, 90° (και 180° για μονόριχτη).",
               "c_pe από τους Πίνακες 7.1–7.5 (παρεμβολή σε h/d, κλίση, h_p/h, r/h· μόνο μεταξύ "
               "τιμών ίδιου προσήμου), c_pe,1 → c_pe,10 με log10 A (Σχήμα 7.2)· καθαρή w = q_p "
               "(c_pe − c_pi) με το δυσμενέστερο c_pi· στέγαστρα c_f και c_p,net των Πινάκων "
               "7.6/7.7 γραμμικά ως προς φ.",
               "Πολλαπλές στέγες κατά Σχήμα 7.10 (1ο άνοιγμα όλες οι ζώνες, επόμενα H/I × 0,8, "
               "0,6 ή −0,4)· θολωτές κατά Σχήμα 7.11 (A, B, C = ¼, ½, ¼ του τόξου)· κυρίαρχα "
               "ανοίγματα c_pi = 0,75 … 0,90 c_pe στο άνοιγμα (Εξ. 7.2/7.3)· τριβή c_fr q_p A_fr "
               "πέρα από min(2b, 4h) (7.5).",
               "Ελεύθεροι τοίχοι και στηθαία c_p,net του Πίνακα 7.9 (l/h, φ, γωνιακές επιστροφές) "
               "με συντελεστή προφύλαξης ψ_s (Σχήμα 7.20)· πινακίδες c_f = 1,8 σε z_g + h/2, "
               "e = ±0,25 b.",
               "ΠΡΟΣΩΡΙΝΟ: οι συντελεστές προέρχονται από το prEN 1991-1-4:2004· να επαληθευτούν "
               "με το EN 1991-1-4:2005 + A1:2010."]},
    "ec1_wind_snow": {
        "en": ["q_p(z) by Eq. 4.8 with c_dir = c_season = 1; walls by Table 7.1; roof snow "
               "μ_1 C_e C_t s_k."],
        "el": ["q_p(z) κατά Εξ. 4.8 με c_dir = c_season = 1· τοίχοι κατά Πίνακα 7.1· χιόνι στη "
               "στέγη μ_1 C_e C_t s_k."]},
    "building_frame": {
        "en": ["3D frame of Timoshenko beam elements with a rigid diaphragm per floor; slab loads "
               "to the beams by the 45° rule (exact fixed-end forces for trapezoids).",
               "Modal response spectrum analysis (CQC) in X and Y, accidental torsion ±0.05 L, "
               "E_X + 0.3 E_Y, drift d_r ν ≤ α h and θ (EN 1998-1 4.4.2.2) per storey.",
               "Every beam and column is designed by the EC2/EC8 modules with the lightest "
               "passing bars; the critical members are printed in full.",
               "Slabs per panel (EC2, two-way), beam deflection by span/depth (EC2 7.4.2) and "
               "the foundation: beams on Winkler springs (EC2 + EC7 bearing, EN 1998-1 4.4.2.6 "
               "overstrength) or pad footings (EC7)."],
        "el": ["Χωρικό πλαίσιο με στοιχεία Timoshenko και άκαμπτο διάφραγμα ανά όροφο· φορτία "
               "πλακών στις δοκούς με τον κανόνα των 45° (ακριβείς δυνάμεις πάκτωσης για "
               "τραπεζοειδή φορτία).",
               "Ιδιομορφική ανάλυση φάσματος απόκρισης (CQC) κατά X και Y, τυχηματική στρέψη "
               "±0.05 L, E_X + 0.3 E_Y, σχετικές μετακινήσεις d_r ν ≤ α h και θ (EN 1998-1 "
               "4.4.2.2) ανά όροφο.",
               "Κάθε δοκός και υποστύλωμα διαστασιολογείται με τα modules EC2/EC8 με τον "
               "ελαφρύτερο επαρκή οπλισμό· τα κρίσιμα μέλη τυπώνονται αναλυτικά.",
               "Πλάκες ανά φάτνωμα (EC2, διέρειστες), βέλος δοκών με λόγο ανοίγματος/ύψους "
               "(EC2 7.4.2) και θεμελίωση: πεδιλοδοκοί σε ελατήρια Winkler (EC2 + φέρουσα "
               "ικανότητα EC7, υπεραντοχή EN 1998-1 4.4.2.6) ή μεμονωμένα πέδιλα (EC7)."]},
    "en1990_combinations": {
        "en": ["All ULS (6.10), seismic (6.12b) and SLS combinations with ψ of the annex; each "
               "variable action in turn as leading action."],
        "el": ["Όλοι οι συνδυασμοί ΟΚΑ (6.10), σεισμικοί (6.12b) και ΟΚΛ με τα ψ του "
               "προσαρτήματος· κάθε μεταβλητή δράση διαδοχικά ως κύρια."]},
    "ec3_weld": {
        "en": ["Elastic stresses on the throat area unfolded into the joint plane; σ⊥ = τ⊥ = σ_w/√2, "
               "τ∥ from the shear on the vertical welds; Eq. 4.1 and the simplified method 4.5.3.3."],
        "el": ["Ελαστικές τάσεις στο ξεδιπλωμένο εμβαδόν λαιμού· σ⊥ = τ⊥ = σ_w/√2, τ∥ από την "
               "τέμνουσα στις κατακόρυφες ραφές· Εξ. 4.1 και απλοποιημένη μέθοδος 4.5.3.3."]},
    "ec2_rc_stair": {
        "en": ["Waist slab as a one-way slab on the horizontal span; self weight of waist and steps "
               "on plan; comfort rule 2R + G."],
        "el": ["Η πλάκα της σκάλας ως πλάκα μίας διεύθυνσης στο οριζόντιο άνοιγμα· ίδιο βάρος "
               "πλάκας και βαθμίδων σε κάτοψη· κανόνας άνεσης 2R + G."]},
    "ec2_pile_cap": {
        "en": ["Rigid cap: pile loads from N and M; strut-and-tie with z = 0.9d, ties along the "
               "pile lines; node stresses by Eq. 6.60/6.61."],
        "el": ["Δύσκαμπτος κεφαλόδεσμος: φορτία πασσάλων από N και M· θλιπτήρες-ελκυστήρες με "
               "z = 0.9d, ελκυστήρες στις γραμμές πασσάλων· τάσεις κόμβων κατά Εξ. 6.60/6.61."]},
    "ec8_rc_wall": {
        "en": ["DCM wall: ν_d ≤ 0.4, h_cr (Eq. 5.19), M_Rd by strain compatibility with web bars, "
               "V_Ed = 1.5 V'_Ed, confinement of boundary elements by Eq. 5.20 with μ_φ = 2q_0 − 1."],
        "el": ["Τοίχωμα ΚΠΜ: ν_d ≤ 0.4, h_cr (Εξ. 5.19), M_Rd με συμβιβαστό παραμορφώσεων και τον "
               "οπλισμό κορμού, V_Ed = 1.5 V'_Ed, περίσφιγξη άκρων κατά Εξ. 5.20 με μ_φ = 2q_0 − 1."]},
    "ec7_raft": {
        "en": ["Strip method: each column line as a beam on Winkler springs carrying the full "
               "column loads in both directions (conservative); E_c = 0.5 E_cm."],
        "el": ["Μέθοδος λωρίδων: κάθε γραμμή υποστυλωμάτων ως δοκός σε ελατήρια Winkler με όλα τα "
               "φορτία και στις δύο διευθύνσεις (συντηρητικά)· E_c = 0.5 E_cm."]},
    "ec8_5_liquefaction": {
        "en": ["τ_e = 0.65 α S σ_v0; (N1)60 with C_N and fines correction; CRR of Youd et al. "
               "(2001) × C_M (Table B.1); FS ≥ λ of the National Annex."],
        "el": ["τ_e = 0.65 α S σ_v0· (N1)60 με C_N και διόρθωση λεπτόκοκκων· CRR κατά Youd κ.ά. "
               "(2001) × C_M (Πίνακας B.1)· FS ≥ λ του Εθνικού Προσαρτήματος."]},
    "ec3_fire": {
        "en": ["Critical temperature Eq. 4.22; heating to ISO 834 by Eq. 4.25 (unprotected, k_sh) "
               "or Eq. 4.27 (protected, product data λ_p, d_p, c_p, ρ_p)."],
        "el": ["Κρίσιμη θερμοκρασία Εξ. 4.22· θέρμανση κατά ISO 834 με Εξ. 4.25 (απροστάτευτο, "
               "k_sh) ή Εξ. 4.27 (προστατευμένο, στοιχεία προϊόντος λ_p, d_p, c_p, ρ_p)."]},
    "ec5_fire": {
        "en": ["Reduced cross-section: d_ef = β_n t + 7 mm; f_d,fi = k_fi f_k (k_mod,fi = γ_M,fi = 1)."],
        "el": ["Μειωμένη διατομή: d_ef = β_n t + 7 mm· f_d,fi = k_fi f_k (k_mod,fi = γ_M,fi = 1)."]},
    "ec2_fire": {
        "en": ["Tabulated data: Table 5.5 (simply supported beams, interpolated in b, corner bars "
               "+10 mm) and Table 5.8 (slabs)."],
        "el": ["Πίνακες: Πίνακας 5.5 (αμφιέρειστες δοκοί, παρεμβολή ως προς b, γωνιακές ράβδοι "
               "+10 mm) και Πίνακας 5.8 (πλάκες)."]},
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
    "shortcuts": {"en": "Keyboard shortcuts", "el": "Συντομεύσεις πληκτρολογίου"},
    "annexes": {"en": "National Annexes in Erisma", "el": "Εθνικά Προσαρτήματα στο Erisma"},
    "ref": {"en": "Calculation reference", "el": "Οδηγός υπολογισμών"},
    "tools": {"en": "Available tools", "el": "Διαθέσιμα εργαλεία"},
    "t3d": {"en": "3D model", "el": "3D μοντέλο"},
    "tq": {"en": "quantities and cost", "el": "ποσότητες και κόστος"},
    "tdxf": {"en": "DXF drawing", "el": "σχέδιο DXF"},
    "topt": {"en": "automatic design", "el": "αυτόματη διαστασιολόγηση"},
    "tlink": {"en": "Results that can be linked", "el": "Αποτελέσματα για σύνδεση"},
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


def _tools(m, lang: str) -> str:
    """Which tools this calculation offers — read from the registries, so always true."""
    from . import drawings, optimize, quantities
    try:
        calc = m.calculate({}, {"annex": "CY"}, lang)
    except Exception:  # noqa: BLE001
        calc = None
    have = []
    if calc is not None and getattr(calc, "model3d", None):
        have.append(T["t3d"][lang])
    if m.id in quantities._FN:
        have.append(T["tq"][lang])
    if drawings.supported(m.id):
        have.append(T["tdxf"][lang])
    opt = optimize.spec(m.id)
    if opt:
        names = ", ".join(tr(v["label"], lang) for v in opt)
        have.append(f"{T['topt'][lang]} ({E(names)})")
    txt = f"<p class='std'><b>{T['tools'][lang]}:</b> {' · '.join(have)}</p>"
    outs = getattr(calc, "outputs", None) or {}
    if outs:
        syms = ", ".join(E(k) for k in list(outs)[:14]) + (" …" if len(outs) > 14 else "")
        txt += f"<p class='std'><b>{T['tlink'][lang]}:</b> {syms}</p>"
    return txt


def _module_card(m, lang: str) -> str:
    sch = m.schema(lang)
    out = [f'<div class="card" id="{m.id}"><h3>{E(sch["title"])}</h3>',
           f'<div class="std">{E(T["standard"][lang])}: {E(sch["standard"])}</div>',
           f"<p>{E(sch['description'])}</p>"]
    out.append(_tools(m, lang))
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
def _verification_table(lang: str) -> str:
    from .structure.verification import run

    head = {"en": ("No.", "Problem", "Reference (source)", "Reference", "Erisma", "Difference"),
            "el": ("Α/Α", "Πρόβλημα", "Αναφορά (πηγή)", "Τιμή αναφοράς", "Erisma", "Διαφορά")}[lang]
    rows = "".join(
        f"<tr><td>{r['id']}</td><td>{E(r['title'][lang])}</td><td>{E(r['source'])}</td>"
        f"<td>{r['reference']:.4g} {E(r['unit'])}</td><td>{r['erisma']:.4g} {E(r['unit'])}</td>"
        f"<td>{r['diff'] * 100:+.2f} %</td></tr>" for r in run())
    return "<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>" + rows + "</table>"


def build_manual(lang: str = "el") -> str:
    lang = "el" if lang == "el" else "en"
    LANG_NOW["lang"] = lang
    n = len(CHAPTERS)
    num = {"shortcuts": f"{n + 1}. {T['shortcuts'][lang]}", "annexes": f"{n + 2}. {T['annexes'][lang]}",
           "reference": f"{n + 3}. {T['ref'][lang]}"}
    toc = [(cid, f"{k}. {title[lang]}") for k, (cid, title, _) in enumerate(CHAPTERS, 1)]
    toc += list(num.items())
    body = []
    for (cid, title, text), (_, numbered) in zip(CHAPTERS, toc):
        extra = _verification_table(lang) if cid == "verification" else ""
        body.append(f'<h2 id="{cid}">{E(numbered)}</h2>{text[lang]}{extra}')
    body.append(f'<h2 id="shortcuts">{num["shortcuts"]}</h2><table><tr><th>{T["key"][lang]}'
                f'</th><th>{T["action"][lang]}</th></tr>' +
                "".join(f"<tr><td><kbd>{E(k)}</kbd></td><td>{E(en if lang == 'en' else el)}</td>"
                        f"</tr>" for k, en, el in SHORTCUTS) + "</table>")
    ann = []
    for a in ANNEXES.values():
        notes = "".join(f"<li>{E(tr(n, lang))}</li>" for n in a.notes)
        ann.append(f"<h4>{E(tr(a.label, lang))}</h4><p class='std'>{E(a.reference)}</p>"
                   + (f"<ul>{notes}</ul>" if notes else ""))
    body.append(f'<h2 id="annexes">{num["annexes"]}</h2>' + "".join(ann))
    body.append(f'<h2 id="reference">{num["reference"]}</h2>')
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
