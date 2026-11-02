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
# One form for a repository URL, so two spellings of one repository compare
# equal: no userinfo, no .git, no trailing slash, the ssh form as https.
norm_url() { printf '%s' "$1" | sed -E -e 's#(://)[^/@[:space:]]+@#\1#' -e 's#^git@([^:]+):#https://\1/#' -e 's#\.git$##' -e 's#/$##' | tr 'A-Z' 'a-z'; }
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
# into $dir/transcripts/, replacing an earlier copy only once both copied
# whole (a copy that stops halfway leaves the earlier copy in place, never a
# truncated one that a cost run would total). One line on stdout.
snapshot() {
  local sid="$1" transcript="$2" sdir n=0 tmpf tmpd
  [ -f "$transcript" ] || { echo "snapshot FAILED: transcript missing at $transcript"; return 1; }
  tmpf="$dir/transcripts/.$sid.jsonl.part"; tmpd="$dir/transcripts/.$sid.part"
  rm -rf "$tmpf" "$tmpd"
  cp "$transcript" "$tmpf" 2>/dev/null || { rm -f "$tmpf"; echo "snapshot FAILED: could not copy $transcript into $dir/transcripts"; return 1; }
  sdir="${transcript%.jsonl}/subagents"
  if [ -d "$sdir" ]; then
    mkdir -p "$tmpd" && cp -R "$sdir" "$tmpd/" 2>/dev/null \
      || { rm -rf "$tmpf" "$tmpd"; echo "snapshot FAILED: could not copy $sdir into $dir/transcripts/$sid"; return 1; }
    n=$(ls "$sdir"/agent-*.jsonl 2>/dev/null | wc -l | tr -d ' ')
  fi
  mv -f "$tmpf" "$dir/transcripts/$sid.jsonl" || { rm -rf "$tmpf" "$tmpd"; echo "snapshot FAILED: could not place $dir/transcripts/$sid.jsonl"; return 1; }
  if [ -d "$tmpd" ]; then
    rm -rf "$dir/transcripts/$sid" && mv -f "$tmpd" "$dir/transcripts/$sid" || { echo "snapshot FAILED: could not place $dir/transcripts/$sid"; return 1; }
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

record_clone() {  # record_clone ok|failed <path> [<error>]
  if [ "$1" = ok ]; then
    printf '{"ts":"%s","payload":{"session_id":"%s","kad_audit_clone":"ok","path":"%s"}}\n' "$(now)" "$sid" "$(json_str "$2")" >> "$log"
  else
    printf '{"ts":"%s","payload":{"session_id":"%s","kad_audit_clone":"failed","path":"%s","error":"%s"}}\n' "$(now)" "$sid" "$(json_str "$2")" "$(json_str "$3")" >> "$log"
  fi
}

if [ "$event" = "SessionStart" ] && [ -n "${KAD_AUDIT_REPO:-}" ]; then
  clone="$dir/repo"
  git=$(find_git)
  cwd=$(unjson_path "$(field cwd)")
  project_origin=$("$git" -C "$cwd" remote get-url origin 2>/dev/null || true)
  if [ -n "$project_origin" ] && [ "$(norm_url "$project_origin")" = "$(norm_url "$KAD_AUDIT_REPO")" ]; then
    # The sync would push audit documents onto the project's own default branch.
    record_clone failed "$clone" "KAD_AUDIT_REPO is this project's own origin; refused (use a separate repository)"
  elif [ -d "$clone/.git" ]; then
    have=$("$git" -C "$clone" remote get-url origin 2>/dev/null || true)
    if [ "$(norm_url "$have")" = "$(norm_url "$KAD_AUDIT_REPO")" ]; then
      record_clone ok "$clone"
    else
      record_clone failed "$clone" "the clone there points at $(printf '%s' "$have" | redact), not KAD_AUDIT_REPO ($(printf '%s' "$KAD_AUDIT_REPO" | redact)); remove it, or point KAD_AUDIT_REPO back"
    fi
  else
    if out=$("$git" clone -q -- "$KAD_AUDIT_REPO" "$clone" 2>&1); then
      # The clone commits under the project's identity (a noreply address,
      # where the project uses one), never the machine's global one.
      for k in user.name user.email; do
        v=$("$git" -C "$cwd" config --get "$k" 2>/dev/null || true)
        [ -n "$v" ] && "$git" -C "$clone" config "$k" "$v" 2>/dev/null
      done
      record_clone ok "$clone"
    else
      err=$(printf '%s\n' "$out" | redact | grep -v '^$' | tail -1)
      record_clone failed "$clone" "${err:-git clone failed with no message}"
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
