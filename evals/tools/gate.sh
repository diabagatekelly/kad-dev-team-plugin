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
#   - A `git` shim at $(brew --prefix)/sbin/git that execs Homebrew's git,
#     which you create once by hand (this script prints the command and
#     refuses to write into a system directory itself). Inside the eval's
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
    shim="$brew_prefix/sbin/git"
    [ -x "$git_bin" ] || { echo "gate: no Homebrew git at $git_bin (brew install git)" >&2; exit 2; }
    [ -x "$node_bin/node" ] || { echo "gate: no Homebrew Node 24 at $node_bin (brew install node@24)" >&2; exit 2; }
    if [ ! -x "$shim" ] || ! grep -q "exec \"$git_bin\"" "$shim"; then
      {
        echo "gate: the eval sandbox needs a git shim at $shim (see this script's header). Create it once:"
        echo
        echo "  mkdir -p '$brew_prefix/sbin' && printf '#!/bin/sh\\nexec \"$git_bin\" \"\$@\"\\n' > '$shim' && chmod +x '$shim'"
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
