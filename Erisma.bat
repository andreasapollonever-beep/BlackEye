@echo off
rem Erisma - double-click to install (first time) and start the program.
chcp 65001 >nul
title Erisma
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto :nopython

if exist ".venv\Scripts\python.exe" goto :run
echo.
echo   Πρώτη εκκίνηση: εγκατάσταση του Erisma, περιμένετε 1-2 λεπτά...
echo.
%PY% -m venv .venv || goto :fail
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -e . || goto :fail

:run
".venv\Scripts\python.exe" -m erisma.cli serve
if errorlevel 1 goto :fail
goto :eof

:nopython
echo.
echo   Δεν βρέθηκε η Python.
echo   Εγκαταστήστε την από https://www.python.org/downloads/
echo   και τσεκάρετε την επιλογή "Add Python to PATH". Μετά ξανανοίξτε το Erisma.
start "" https://www.python.org/downloads/
pause
exit /b 1

:fail
echo.
echo   Κάτι πήγε στραβά. Στείλτε μια φωτογραφία αυτού του παραθύρου.
pause
exit /b 1
