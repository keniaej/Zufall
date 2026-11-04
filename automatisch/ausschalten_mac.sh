#!/bin/bash
# Schaltet den automatischen Lauf auf dem Mac wieder aus.
#     bash automatisch/ausschalten_mac.sh

PLIST="$HOME/Library/LaunchAgents/de.zufall.ausschreibungsagent.plist"
launchctl unload "$PLIST" 2>/dev/null
rm -f "$PLIST"
echo "Automatischer Lauf ist ausgeschaltet."
