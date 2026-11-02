#!/usr/bin/env bash
# Audit mode for kad-dev-team. Does nothing unless KAD_AUDIT=1, so eval runs
# and everyday sessions are untouched.
#
# With it on, every hook event this plugin registers (a prompt, a Skill or
# Agent call) is appended to $KAD_AUDIT_DIR/sessions/<session-id>.jsonl as
# {"ts": ..., "payload": <the hook's JSON>}. At session end, a session that
# called any kad-dev-team skill or agent gets its transcript and its
# subagents' transcripts copied to $KAD_AUDIT_DIR/transcripts/, since Claude
# Code deletes old transcripts; a session that never used the plugin has its
# log removed. Everything stays on this machine.
#
# A session's end is not the only time the transcript is copied: the
# orchestrator's chunk loop runs `audit.sh --snapshot [<session-id>]` after
# every records commit (the id defaults to CLAUDE_CODE_SESSION_ID), which
# copies the same files there and then. Run 3's loop session ended without
# a SessionEnd and its main transcript was never found; a snapshot per
# chunk does not wait for an end.
#
# With KAD_AUDIT_REPO also set (a clone URL), the audit repository's clone
# lives at $KAD_AUDIT_DIR/repo/, never inside the project tree. The
# launcher (bin/kad) clones it before the sandbox runtime starts, because
# inside the fence git cannot write a .git/config or .git/hooks anywhere
# (the runtime's mandatory deny), so a clone attempted from inside fails
# every time. SessionStart here clones only when nothing is there yet (a
# session not started by the launcher), and records what it found or what
# git said, in the session's log, as
# {"ts": ..., "payload": {"session_id": ..., "kad_audit_clone": "ok" | "failed", "path": ..., "error": ...}}:
# the orchestrator's A step reports it (audit_sync.py --check reads it),
# instead of a sync that silently finds no clone at the end of a slice.
# The orchestrator's audit_sync.py then copies a slice's documents, log,
# report, reviews and kept transcripts into that clone, commits and pushes.
#
# Review the result with evals/tools/audit_report.py and the audit-review
# skill in this repo. KAD_AUDIT_DIR defaults to ~/.claude/kad-audit.
dir="${KAD_AUDIT_DIR:-$HOME/.claude/kad-audit}"

now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
# A string as a JSON value: backslash and quote escaped, control characters dropped.
json_str() { printf '%s' "$1" | tr -d '\000-\037' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
# git repeats the clone URL in its diagnostics; a URL's userinfo may be a token.
redact() { sed -E 's#(://)[^/@[:space:]]+@#\1<redacted>@#g'; }
# A path out of a JSON string: on Windows that is C:\\Users\\..., which Git
# Bash reads once the doubled backslashes become forward slashes.
unjson_path() { printf '%s' "$1" | sed 's#\\\\#/#g'; }
# git by name inside a macOS sandbox is Apple's xcrun shim, which fails there;
# the candidates are tried by running them (the same rule as audit_sync.py).
find_git() {
  local c
  for c in git /opt/homebrew/bin/git /usr/local/bin/git /opt/local/bin/git; do
    "$c" --version >/dev/null 2>&1 && { printf '%s' "$c"; return; }
  done
  printf 'git'
}

# snapshot <session-id> <transcript path>: the transcript and its subagents'
# into $dir/transcripts/, overwriting an earlier copy. One line on stdout.
snapshot() {
  local sid="$1" transcript="$2" sdir n=0
  [ -f "$transcript" ] || { echo "snapshot FAILED: transcript missing at $transcript"; return 1; }
  cp "$transcript" "$dir/transcripts/$sid.jsonl" 2>/dev/null || { echo "snapshot FAILED: could not copy $transcript into $dir/transcripts"; return 1; }
  sdir="${transcript%.jsonl}/subagents"
  if [ -d "$sdir" ]; then
    mkdir -p "$dir/transcripts/$sid" && cp -R "$sdir" "$dir/transcripts/$sid/" 2>/dev/null \
      || { echo "snapshot FAILED: could not copy $sdir into $dir/transcripts/$sid"; return 1; }
    n=$(ls "$sdir"/agent-*.jsonl 2>/dev/null | wc -l | tr -d ' ')
  fi
  echo "snapshot: $sid at $(now), $n subagent transcripts, in $dir/transcripts"
}

if [ "${1:-}" = "--snapshot" ]; then
  [ "${KAD_AUDIT:-}" = "1" ] || { echo "snapshot: audit mode off, nothing kept"; exit 0; }
  sid="${2:-${CLAUDE_CODE_SESSION_ID:-}}"
  case "$sid" in ''|*/*) echo "snapshot FAILED: no session id (pass one, or run inside the session)"; exit 1 ;; esac
  mkdir -p "$dir/transcripts" 2>/dev/null || { echo "snapshot FAILED: cannot write $dir"; exit 1; }
  log="$dir/sessions/$sid.jsonl"
  [ -f "$log" ] || { echo "snapshot FAILED: no audit log for session $sid under $dir/sessions"; exit 1; }
  # Every hook payload names the transcript; the first one is the session's own.
  transcript=$(grep -o '"transcript_path" *: *"[^"]*"' "$log" | head -1 | sed 's/.*: *"\(.*\)"/\1/')
  [ -n "$transcript" ] || { echo "snapshot FAILED: the audit log for $sid names no transcript"; exit 1; }
  snapshot "$sid" "$(unjson_path "$transcript")"; exit $?
fi

[ "${KAD_AUDIT:-}" = "1" ] || exit 0
mkdir -p "$dir/sessions" "$dir/transcripts" 2>/dev/null || exit 0

# JSON strings never hold a raw newline, so dropping them keeps it one line.
payload=$(tr -d '\n')
field() { printf '%s' "$payload" | grep -o "\"$1\" *: *\"[^\"]*\"" | head -1 | sed 's/.*: *"\(.*\)"/\1/'; }
sid=$(field session_id)
case "$sid" in ''|*/*) exit 0 ;; esac
log="$dir/sessions/$sid.jsonl"
printf '{"ts":"%s","payload":%s}\n' "$(now)" "$payload" >> "$log"
event=$(field hook_event_name)

if [ "$event" = "SessionStart" ] && [ -n "${KAD_AUDIT_REPO:-}" ]; then
  clone="$dir/repo"
  git=$(find_git)
  if [ -d "$clone/.git" ]; then
    printf '{"ts":"%s","payload":{"session_id":"%s","kad_audit_clone":"ok","path":"%s"}}\n' "$(now)" "$sid" "$(json_str "$clone")" >> "$log"
  else
    if out=$("$git" clone -q -- "$KAD_AUDIT_REPO" "$clone" 2>&1); then
      # The clone commits under the project's identity (a noreply address,
      # where the project uses one), never the machine's global one.
      cwd=$(unjson_path "$(field cwd)")
      for k in user.name user.email; do
        v=$("$git" -C "$cwd" config --get "$k" 2>/dev/null || true)
        [ -n "$v" ] && "$git" -C "$clone" config "$k" "$v" 2>/dev/null
      done
      printf '{"ts":"%s","payload":{"session_id":"%s","kad_audit_clone":"ok","path":"%s"}}\n' "$(now)" "$sid" "$(json_str "$clone")" >> "$log"
    else
      err=$(printf '%s\n' "$out" | redact | grep -v '^$' | tail -1)
      printf '{"ts":"%s","payload":{"session_id":"%s","kad_audit_clone":"failed","path":"%s","error":"%s"}}\n' \
        "$(now)" "$sid" "$(json_str "$clone")" "$(json_str "${err:-git clone failed with no message}")" >> "$log"
    fi
  fi
fi

if [ "$event" = "SessionEnd" ]; then
  if grep -q 'kad-dev-team:' "$log" 2>/dev/null; then
    snapshot "$sid" "$(unjson_path "$(field transcript_path)")" >/dev/null 2>&1
  else
    rm -f "$log"
  fi
fi
exit 0
