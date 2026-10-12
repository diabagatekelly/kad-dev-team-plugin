#!/usr/bin/env bash
# Audit mode for kad-dev-team. Does nothing unless KAD_AUDIT=1, so eval runs
# and everyday sessions are untouched.
#
# With it on, every hook event this plugin registers (a prompt, a Skill or
# Agent call) is appended to $KAD_AUDIT_DIR/sessions/<session-id>.jsonl as
# {"ts": ..., "payload": <the hook's JSON>}. At session end, a session that
# called any kad-dev-team skill or agent gets its transcript (and its
# subagents' transcripts) copied to $KAD_AUDIT_DIR/transcripts/, since Claude
# Code deletes old transcripts; a session that never used the plugin has its
# log removed. Everything stays on this machine.
#
# Review the result with evals/tools/audit_report.py and the audit-review
# skill in this repo. KAD_AUDIT_DIR defaults to ~/.claude/kad-audit.
[ "${KAD_AUDIT:-}" = "1" ] || exit 0
dir="${KAD_AUDIT_DIR:-$HOME/.claude/kad-audit}"
mkdir -p "$dir/sessions" "$dir/transcripts" 2>/dev/null || exit 0

# JSON strings never hold a raw newline, so dropping them keeps it one line.
payload=$(tr -d '\n')
field() { printf '%s' "$payload" | grep -o "\"$1\" *: *\"[^\"]*\"" | head -1 | sed 's/.*: *"\(.*\)"/\1/'; }
sid=$(field session_id)
case "$sid" in ''|*/*) exit 0 ;; esac
log="$dir/sessions/$sid.jsonl"
printf '{"ts":"%s","payload":%s}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$payload" >> "$log"

if [ "$(field hook_event_name)" = "SessionEnd" ]; then
  if grep -q 'kad-dev-team:' "$log" 2>/dev/null; then
    transcript=$(field transcript_path)
    if [ -f "$transcript" ]; then
      cp "$transcript" "$dir/transcripts/$sid.jsonl"
      [ -d "${transcript%.jsonl}" ] && cp -R "${transcript%.jsonl}" "$dir/transcripts/$sid"
    fi
  else
    rm -f "$log"
  fi
fi
exit 0
