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
# With KAD_AUDIT_REPO also set (a clone URL), SessionStart clones that
# repository into <project>/audit-docs/ when it isn't there yet and lists
# audit-docs/ in the project's .git/info/exclude, so the project's own
# .gitignore and history never mention it (not a submodule: a gitlink in
# the parent is exactly what must not appear). The orchestrator's
# audit_sync.py then copies a slice's documents, log, report and reviews
# into that clone, commits and pushes.
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

if [ "$(field hook_event_name)" = "SessionStart" ] && [ -n "${KAD_AUDIT_REPO:-}" ]; then
  # The payload's cwd is JSON-escaped; on Windows that is C:\\Users\\..., which
  # Git Bash reads once the doubled backslashes become forward slashes.
  cwd=$(field cwd | sed 's#\\\\#/#g')
  if [ -n "$cwd" ] && [ -d "$cwd" ] && [ ! -e "$cwd/audit-docs" ]; then
    gitdir=$(git -C "$cwd" rev-parse --git-common-dir 2>/dev/null)
    case "$gitdir" in
      '') ;;
      /*|?:/*) ;;
      *) gitdir="$cwd/$gitdir" ;;
    esac
    if [ -n "$gitdir" ] && git clone -q -- "$KAD_AUDIT_REPO" "$cwd/audit-docs" >/dev/null 2>&1; then
      mkdir -p "$gitdir/info" 2>/dev/null
      grep -qx 'audit-docs/' "$gitdir/info/exclude" 2>/dev/null || printf 'audit-docs/\n' >> "$gitdir/info/exclude"
    fi
  fi
fi

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
