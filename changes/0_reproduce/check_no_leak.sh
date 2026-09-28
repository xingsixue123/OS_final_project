#!/bin/bash
# List files modified since the marker OUTSIDE changes/0_reproduce (home dir + /tmp),
# ignoring editor/agent state that is not produced by the reproduction.
#   touch .cache/leak_marker   # before running jobs
#   bash check_no_leak.sh      # after
R="$(cd "$(dirname "$0")" && pwd)"
M="$R/.cache/leak_marker"
[ -f "$M" ] || { echo "no marker: touch $M before running"; exit 2; }
hits=$(find /home/sxing /tmp /var/tmp /dev/shm -xdev -newer "$M" -type f 2>/dev/null \
  | grep -v "^$R/" \
  | grep -vE "^/home/sxing/\.(claude|vscode-server|cursor-server|codex|bash_history|lesshst|viminfo|cache/tracker3)" \
  | grep -vE "^/tmp/(claude-|vscode|python-languageserver-cancellation/|tmp\.|\.X|systemd)" \
  | grep -vE "/\.claude/" )
if [ -n "$hits" ]; then echo "LEAK: files modified outside $R:"; echo "$hits"; exit 1; fi
echo "no-leak OK (nothing modified outside $R since $(date -r "$M" +%F\ %T))"
