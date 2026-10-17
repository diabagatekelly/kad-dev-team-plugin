#!/usr/bin/env bash
# Run the eval gate in the WSL2 clone from the Windows checkout, one command:
#
#   wsl -d Ubuntu-22.04 -- bash evals/tools/wsl-gate.sh [eval_gate.py arguments]
#
# from the repository root on Windows. It mirrors this checkout (committed
# or not) into ~/kad-dev-team-plugin, strips the CRLF the mount brings in,
# runs eval_gate.py there, and copies the new results, evals/evidence.json
# and evals/thresholds.json back here, so the next step on Windows is just
# to commit. Exit code is the gate's. Set KAD_WSL_CLONE to use another
# clone path. wsl-setup.sh has the one-time setup.
set -euo pipefail

win="$(cd "$(dirname "$0")/../.." && pwd)"
clone="${KAD_WSL_CLONE:-$HOME/kad-dev-team-plugin}"
[ -d "$clone/.git" ] || { echo "no clone at $clone; see evals/tools/wsl-setup.sh" >&2; exit 2; }
cd "$clone"

# Same commit as Windows, so "what changed against main" agrees; and a
# current origin/main, fetched through the Windows checkout (no login).
branch="$(git -C "$win" rev-parse --abbrev-ref HEAD)"
git fetch -q "$win" "refs/heads/$branch"
git checkout -q -f --detach FETCH_HEAD
git fetch -q "$win" "refs/remotes/origin/main:refs/remotes/origin/main" 2>/dev/null || true

# Working tree, uncommitted work included; results stay local to each side.
rsync -a --delete --exclude .git --exclude /evals/results --exclude __pycache__ --exclude node_modules \
  "$win/" "$clone/"
git config core.fileMode false
# `-m` also lists a file deleted or moved since the mirrored commit, which
# sed cannot open; skip anything that is not a file here.
git ls-files -mo --exclude-standard -z \
  | grep -z -v -E '\.(png|jpe?g|gif|ico|woff2?|pdf)$' \
  | xargs -0 -r sh -c 'for f; do if [ -f "$f" ]; then sed -i "s/\r$//" -- "$f"; fi; done' _
find . -name '*.sh' -not -path './.git/*' -exec chmod +x {} +

mkdir -p evals/results "$win/evals/results"
# WSL's /tmp is a tmpfs, and WSL stops the VM a few seconds after the last
# `wsl` command exits, so a run directory the gate keeps there
# (--keep-scaffold, for freeze-history.sh) is gone before the next command
# can read it. Keep the CLI's temp directories on the Linux disk instead,
# whatever TMPDIR the environment arrived with (KAD_EVAL_TMP overrides).
export TMPDIR="${KAD_EVAL_TMP:-$HOME/.cache/kad-eval-tmp}"
mkdir -p "$TMPDIR"
marker="$(mktemp)"
rc=0
python3 -I evals/tools/eval_gate.py "$@" || rc=$?

# Back to Windows: every result this run wrote, plus the two committed tables.
find evals/results -type f -newer "$marker" -exec cp -p {} "$win/evals/results/" \;
cp -p evals/evidence.json "$win/evals/evidence.json" 2>/dev/null || true
cp -p evals/thresholds.json "$win/evals/thresholds.json"
rm -f "$marker"
echo "copied new results, evidence.json and thresholds.json back to $win"
exit $rc
