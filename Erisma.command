#!/bin/bash
# Erisma - double-click (macOS) or run ./Erisma.command to install (first time) and start.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Δεν βρέθηκε η Python. Εγκαταστήστε την από https://www.python.org/downloads/"
  open https://www.python.org/downloads/ 2>/dev/null || xdg-open https://www.python.org/downloads/ 2>/dev/null
  read -r -p "Πατήστε Enter για έξοδο..."
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "Πρώτη εκκίνηση: εγκατάσταση του Erisma, περιμένετε 1-2 λεπτά..."
  python3 -m venv .venv && .venv/bin/python -m pip install --quiet --upgrade pip \
    && .venv/bin/python -m pip install --quiet -e . || {
      echo "Κάτι πήγε στραβά. Στείλτε ένα στιγμιότυπο αυτού του παραθύρου."
      read -r -p "Πατήστε Enter για έξοδο..."; exit 1; }
fi
exec .venv/bin/python -m erisma.cli serve
