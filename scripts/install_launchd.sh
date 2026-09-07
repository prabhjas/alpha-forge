#!/bin/zsh
# Install (or reinstall) the three launchd agents. Times are LOCAL (this Mac is on IST).
#   india  16:00 IST Mon-Fri   (NSE closes 15:30)
#   us     03:00 IST Tue-Sat   (NYSE closes 16:00 ET = 01:30/02:30 IST)
#   brief  08:30 IST daily
# The Mac must be awake. Either keep it plugged in with 'pmset -c sleep 0', schedule wakes with
# 'sudo pmset repeat wakeorpoweron MTWRFSU 02:55:00', or move this to a Mumbai VPS (SEBI static-IP rule).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS="$HOME/Library/LaunchAgents"; mkdir -p "$AGENTS"
UID_=$(id -u)

write_plist() {  # label, program args (array as string), calendar entries (xml)
  local label="$1" args="$2" cal="$3"
  cat > "$AGENTS/$label.plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>$args</array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>StartCalendarInterval</key><array>$cal</array>
  <key>StandardOutPath</key><string>$ROOT/data_cache/logs/launchd_$label.out</string>
  <key>StandardErrorPath</key><string>$ROOT/data_cache/logs/launchd_$label.err</string>
  <key>EnvironmentVariables</key><dict><key>PATH</key><string>/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string></dict>
</dict></plist>
PL
  launchctl bootout "gui/$UID_/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$UID_" "$AGENTS/$label.plist"
  echo "installed $label"
}

mkdir -p "$ROOT/data_cache/logs"
cal_weekdays() { local h=$1 m=$2; local out=""; for d in "$@[3,-1]"; do out+="<dict><key>Weekday</key><integer>$d</integer><key>Hour</key><integer>$h</integer><key>Minute</key><integer>$m</integer></dict>"; done; echo "$out"; }

write_plist com.alphaforge.india "<string>/bin/zsh</string><string>$ROOT/scripts/daily.sh</string><string>india</string>" "$(cal_weekdays 16 0 1 2 3 4 5)"
write_plist com.alphaforge.us    "<string>/bin/zsh</string><string>$ROOT/scripts/daily.sh</string><string>us</string>"    "$(cal_weekdays 3 0 2 3 4 5 6)"
write_plist com.alphaforge.brief "<string>$ROOT/.venv313/bin/python</string><string>$ROOT/scripts/morning_brief.py</string>" "<dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>"
write_plist com.alphaforge.weekly "<string>$ROOT/.venv313/bin/python</string><string>$ROOT/scripts/weekly_report.py</string>" "<dict><key>Weekday</key><integer>0</integer><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>"
write_plist com.alphaforge.news "<string>$ROOT/.venv313/bin/python</string><string>$ROOT/scripts/news_digest.py</string>" "<dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>15</integer></dict>"
echo; launchctl list | grep alphaforge
