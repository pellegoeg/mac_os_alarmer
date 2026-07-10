#!/bin/bash

# Bestem absolut sti til dette projekt
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PLIST_LABEL="com.user.mac_os_alarmer"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

echo "=== Konfigurerer macOS LaunchAgent for mac_os_alarmer ==="
echo "Projektmappe: $PROJECT_DIR"

# 1. Opret virtuelt miljø hvis det ikke findes
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Opretter virtuelt Python miljø (.venv)..."
    python3 -m venv "$PROJECT_DIR/.venv"
fi

# 2. Installer afhængigheder
echo "Installerer afhængigheder fra requirements.txt..."
"$PROJECT_DIR/.venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 3. Opret config.json hvis den ikke findes
if [ ! -f "$PROJECT_DIR/config.json" ]; then
    echo "Opretter standard config.json ud fra skabelonen..."
    cp "$PROJECT_DIR/config.json.example" "$PROJECT_DIR/config.json"
fi

# 4. Generer .plist-filen med dynamiske stier
echo "Genererer LaunchAgent plist fil..."
cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PROJECT_DIR}/.venv/bin/python</string>
        <string>${PROJECT_DIR}/main.py</string>
    </array>
    <key>StartInterval</key>
    <!-- Kør hvert 30. minut (1800 sekunder) -->
    <key>RunAtLoad</key>
    <true/>
    <integer>1800</integer>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/${PLIST_LABEL}.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/${PLIST_LABEL}.stderr.log</string>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
</dict>
</plist>
EOF

# 5. Sæt korrekte rettigheder på plist filen
chmod 644 "$PLIST_PATH"

# 6. Hent og genindlæs LaunchAgenten
echo "Indlæser LaunchAgent i launchctl..."
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo "=== Færdig! ==="
echo "Programmet vil nu køre automatisk ved login og derefter hvert 30. minut."
echo "Du kan ændre intervallet i: $PLIST_PATH"
echo "Logfiler findes i: ~/Library/Logs/"
echo "Brug 'launchctl unload $PLIST_PATH' for at deaktivere agenten."
EOF
