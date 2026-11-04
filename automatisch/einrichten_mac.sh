#!/bin/bash
# Richtet auf einem Mac ein, dass der Agent automatisch läuft.
#
# Starten aus dem Hauptordner "Zufall":
#     bash automatisch/einrichten_mac.sh
#
# Wieder ausschalten:
#     bash automatisch/ausschalten_mac.sh

# ---- Wann soll der Agent laufen? (hier ändern) ----
TAG=1        # Tag im Monat (1 = am Ersten)
STUNDE=8     # Uhrzeit, Stunde
MINUTE=0     # Uhrzeit, Minute
# ---------------------------------------------------

NAME="de.zufall.ausschreibungsagent"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$REPO/.venv/bin/python"
PLIST="$HOME/Library/LaunchAgents/$NAME.plist"

if [ ! -x "$PYTHON" ]; then
    echo "FEHLER: $PYTHON gibt es nicht."
    echo "Bitte zuerst im Ordner Zufall einrichten: python3 -m venv .venv und pip install -r requirements.txt"
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$REPO/output"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$NAME</string>
    <key>WorkingDirectory</key>
    <string>$REPO</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>-m</string>
        <string>agent.main</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Day</key>
        <integer>$TAG</integer>
        <key>Hour</key>
        <integer>$STUNDE</integer>
        <key>Minute</key>
        <integer>$MINUTE</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$REPO/output/log.txt</string>
    <key>StandardErrorPath</key>
    <string>$REPO/output/log.txt</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST"

echo "Fertig. Der Agent läuft ab jetzt am $TAG. jedes Monats um $STUNDE:$(printf '%02d' $MINUTE) Uhr."
echo "Ergebnis: $REPO/output/ausschreibungen.xlsx"
echo "Protokoll: $REPO/output/log.txt"
echo
echo "Sofort einmal testen:  launchctl start $NAME"
