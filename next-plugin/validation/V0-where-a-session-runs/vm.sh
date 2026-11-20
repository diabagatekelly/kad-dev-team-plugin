#!/usr/bin/env bash
# The launcher's first backend: Docker Sandboxes (sbx) on macOS.
#
#   vm.sh check                    what is present and missing; changes nothing
#   vm.sh install [--yes]          install the VM tool (asks first without --yes)
#   vm.sh policy                   deny everything, then allow the default hosts
#   vm.sh create NAME DIR          a VM holding a private clone of the repository in DIR
#   vm.sh allow NAME HOST[,HOST]   allow more hosts, for that VM only
#   vm.sh exec NAME COMMAND        run a shell command in the VM, in the clone
#   vm.sh run NAME PROMPT          run a session in the VM on PROMPT, prompts skipped
#   vm.sh out NAME DEST            copy the VM's transcripts to DEST on the host
#   vm.sh destroy NAME             remove the VM and everything in it
#
# Each verb is one line of the contract in ../../../TODO.md, V0. The hand steps
# no verb can do: `sbx login`, and signing the model in once inside a VM.
set -euo pipefail

say() { printf '%s\n' "$*"; }

need_macos_arm() {
  [ "$(uname -s)" = "Darwin" ] || { say "not macOS: this backend is for macOS only"; return 1; }
  [ "$(uname -m)" = "arm64" ] || { say "not Apple silicon: Docker Sandboxes needs it on macOS"; return 1; }
}

check() {
  local missing=0
  need_macos_arm || missing=1
  if command -v sbx >/dev/null 2>&1; then
    say "sbx: present ($(sbx version 2>/dev/null | head -1 || echo 'version unknown'))"
  else
    say "sbx: missing"; missing=1
  fi
  if command -v brew >/dev/null 2>&1; then say "brew: present"; else say "brew: missing (needed to install sbx)"; fi
  return "$missing"
}

install() {
  need_macos_arm
  if command -v sbx >/dev/null 2>&1; then say "sbx is already installed"; return 0; fi
  command -v brew >/dev/null 2>&1 || { say "Homebrew is needed to install sbx: https://brew.sh"; return 1; }
  if [ "${1:-}" != "--yes" ]; then
    printf 'Install Docker Sandboxes (brew install docker/tap/sbx)? [y/N] '
    read -r answer
    [ "$answer" = "y" ] || { say "not installed"; return 1; }
  fi
  brew trust docker/tap
  brew install docker/tap/sbx
  say "installed. One step is yours: run 'sbx login' (it opens a browser)."
}

DEFAULT_HOSTS="api.anthropic.com,claude.ai,platform.claude.com,github.com,registry.npmjs.org"

policy() {
  sbx policy ls >/dev/null 2>&1 || sbx policy init deny-all
  sbx policy allow network "$DEFAULT_HOSTS"
}

# The clone sits in the VM at the same path the repository has on the host.
workdir() { sbx inspect "$1" --json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d.get("workspace") or d.get("Workspace") or "")' 2>/dev/null; }

create() { ( cd "$2" && sbx --no-input create --clone --name "$1" claude . ); }
allow() { sbx policy allow network --sandbox "$1" "$2"; }
in_vm() { local name="$1"; shift; sbx exec -w "$(workdir "$name")" "$name" "$@"; }
run() { in_vm "$1" claude -p --dangerously-skip-permissions "$2"; }
out() { mkdir -p "$2" && sbx cp "$1:/home/agent/.claude/projects" "$2"; }
destroy() { sbx rm --force "$1"; }

case "${1:-}" in
  check) check ;;
  install) shift; install "$@" ;;
  policy) policy ;;
  create) create "$2" "$3" ;;
  allow) allow "$2" "$3" ;;
  exec) name="$2"; shift 2; in_vm "$name" bash -lc "$*" ;;
  run) run "$2" "$3" ;;
  out) out "$2" "$3" ;;
  destroy) destroy "$2" ;;
  *) sed -n '4,12p' "$0" | sed 's/^# \{0,3\}//'; exit 2 ;;
esac
