#!/usr/bin/env bash
# The eval gate, one command on every system that has a bash:
#
#   bash evals/tools/gate.sh [eval_gate.py arguments]
#
# Linux and WSL2 (inside the distribution): runs eval_gate.py as is. From
# Windows, use wsl-gate.sh, which mirrors the checkout into the WSL2 clone
# and runs the gate there. macOS: checks the two things the eval's sandbox
# needs, then runs eval_gate.py:
#   - Homebrew's Node 24 first on PATH, which the sandboxed runs inherit:
#     the fixture's test script passes --experimental-transform-types,
#     gone in Node 26, and nvm's install lives under the home directory,
#     which the eval's sandbox does not let a run read (brew install node@24).
#   - Shims at $(brew --prefix)/sbin for git and its push/fetch helpers
#     (git-receive-pack, git-upload-pack, git-upload-archive), each
#     exec'ing Homebrew's, which you create once by hand (this script
#     prints the command and refuses to write into a system directory
#     itself). Inside the eval's
#     sandbox `git` by name is Apple's /usr/bin/git shim, which fails (it
#     needs /Library/Developer and a cache under /var/folders, both denied),
#     and the shell skips Homebrew's own git on PATH because its Cellar
#     target cannot be stat'ed there; sbin is readable and already on PATH
#     after bin, so outside the sandbox nothing changes (bin's git still
#     wins). Verified 2026-10-31 with probe cases; nothing documented for
#     `claude plugin eval` widens its sandbox.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
case "$(uname -s)" in
  Darwin)
    brew_prefix="$(brew --prefix 2>/dev/null || echo /opt/homebrew)"
    git_bin="$brew_prefix/bin/git"
    node_bin="$brew_prefix/opt/node@24/bin"
    [ -x "$git_bin" ] || { echo "gate: no Homebrew git at $git_bin (brew install git)" >&2; exit 2; }
    [ -x "$node_bin/node" ] || { echo "gate: no Homebrew Node 24 at $node_bin (brew install node@24)" >&2; exit 2; }
    # git itself, and the helpers a push, fetch or clone to a local path
    # runs as separate commands: without their shims a push falls back to
    # Apple's /usr/bin/git-receive-pack and fails the same way.
    missing=""
    for name in git git-receive-pack git-upload-pack git-upload-archive; do
      shim="$brew_prefix/sbin/$name"
      [ -x "$shim" ] && grep -q "exec \"$brew_prefix/bin/$name\"" "$shim" || missing="$missing $name"
    done
    if [ -n "$missing" ]; then
      {
        echo "gate: the eval sandbox needs shims in $brew_prefix/sbin for:$missing (see this script's header). Create them once, in a terminal:"
        echo
        echo "  mkdir -p '$brew_prefix/sbin' && for n in git git-receive-pack git-upload-pack git-upload-archive; do printf '#!/bin/sh\\nexec \"$brew_prefix/bin/'\"\$n\"'\" \"\$@\"\\n' > \"$brew_prefix/sbin/\$n\" && chmod +x \"$brew_prefix/sbin/\$n\"; done"
        echo
      } >&2
      exit 2
    fi
    export PATH="$node_bin:$PATH"
    ;;
  Linux) ;;
  *) echo "gate: run from WSL2 (wsl-gate.sh), Linux or macOS; native Windows has no sandbox for the CLI" >&2; exit 2 ;;
esac
exec python3 -I "$root/evals/tools/eval_gate.py" "$@"
