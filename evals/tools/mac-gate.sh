#!/usr/bin/env bash
# The eval gate on macOS, `wsl-gate.sh`'s counterpart: puts Homebrew's
# Node 24 first on PATH (the fixture's test script passes
# `--experimental-transform-types`, gone in Node 26; nvm's install is under
# the home directory, which the eval's sandbox does not let a run read, so
# its `npm` fails inside a run while `brew install node@24` works) and
# runs `eval_gate.py` with the arguments given. The run inherits PATH.
#
# What this cannot fix, and the reason the loop cases are recorded on WSL:
# inside the eval's sandbox `git` by name is Apple's /usr/bin/git shim,
# which needs /Library/Developer and a cache under /var/folders, both
# denied, and the shell skips Homebrew's git on PATH (its Cellar target
# cannot be stat'ed; only an absolute-path exec works). Nothing documented
# for `claude plugin eval` widens that sandbox (checked 2026-10-31). The
# plugin's scripts fall back to Homebrew's git themselves; the agents
# inside a run mostly find /opt/homebrew/bin/git on their own, at the
# cost of turns, so a case whose agent must commit or diff is not
# measured here.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
brew_prefix="$(brew --prefix 2>/dev/null || echo /opt/homebrew)"
node_bin="$brew_prefix/opt/node@24/bin"
[ -x "$node_bin/node" ] || { echo "mac-gate: no Homebrew Node 24 at $node_bin (brew install node@24)" >&2; exit 1; }
export PATH="$node_bin:$PATH"
exec python3 -I "$root/evals/tools/eval_gate.py" "$@"
