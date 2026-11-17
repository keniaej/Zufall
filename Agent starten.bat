@echo off
rem ==========================================================================
rem  Agent Oeffentliche Ausschreibungen (ZUFALL) - Start unter Windows
rem
rem  Doppelklick auf diese Datei startet den Agenten.
rem  Beim ersten Start wird alles Noetige eingerichtet (dauert 1-3 Minuten).
rem
rem  Ergebnis:   output\ausschreibungen.xlsx
rem  Protokoll:  output\log.txt
rem
rem  Fuer die Aufgabenplanung (ohne Rueckfragen):  "Agent starten.bat" /auto
rem ==========================================================================
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

rem In den Ordner wechseln, in dem diese Datei liegt (auch bei Leerzeichen im Pfad)
cd /d "%~dp0"

set "AUTO="
if /i "%~1"=="/auto" set "AUTO=1"

set "VENV_PY=.venv\Scripts\python.exe"

rem ---------------------------------------------------------------- Einrichtung
if exist "%VENV_PY%" goto pakete_pruefen

echo Erster Start: Python-Umgebung wird eingerichtet ...
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
    python --version >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo.
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python 3.11 oder neuer installieren: https://www.python.org/downloads/
    echo Beim Installieren "Add python.exe to PATH" ankreuzen. Danach diese Datei erneut starten.
    goto fehler
)
%PY% -m venv .venv
if errorlevel 1 (
    echo FEHLER: Die Python-Umgebung .venv konnte nicht angelegt werden.
    goto fehler
)

:pakete_pruefen
"%VENV_PY%" -c "import pandas, openpyxl, requests" >nul 2>&1
if not errorlevel 1 goto starten
echo Pakete werden installiert ...
"%VENV_PY%" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
    echo FEHLER: Die Pakete konnten nicht installiert werden. Besteht eine Internetverbindung?
    goto fehler
)

rem ---------------------------------------------------------------- Lauf
:starten
echo.
echo Agent laeuft. Das dauert einige Minuten, bitte das Fenster offen lassen ...
echo.
"%VENV_PY%" -m agent.main --protokoll output\log.txt
if errorlevel 1 goto fehler

echo.
echo Fertig. Ergebnis: %CD%\output\ausschreibungen.xlsx
if defined AUTO goto ende
choice /c JN /m "Excel-Datei jetzt oeffnen"
if errorlevel 2 goto ende_pause
start "" "output\ausschreibungen.xlsx"
goto ende

:fehler
echo.
echo Der Agent wurde NICHT erfolgreich beendet. Details stehen oben und in output\log.txt.
if not defined AUTO pause
endlocal
exit /b 1

:ende_pause
pause
:ende
endlocal
exit /b 0
