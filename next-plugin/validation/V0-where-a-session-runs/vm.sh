#!/usr/bin/env bash
# The launcher's first backend: Docker Sandboxes (sbx) on macOS.
#
#   vm.sh check     say what is present and what is missing; changes nothing
#   vm.sh install   install the VM tool (asks first unless --yes is given)
#
# Later commands (create, allow, run, copy-out, destroy) are added as the
# trial reaches them; each is one verb of the contract in ../../../TODO.md, V0.
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

case "${1:-}" in
  check) check ;;
  install) shift; install "$@" ;;
  *) say "usage: vm.sh check | install [--yes]"; exit 2 ;;
esac
