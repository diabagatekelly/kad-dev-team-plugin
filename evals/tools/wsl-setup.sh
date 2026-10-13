#!/usr/bin/env bash
# One-time setup of a fresh WSL2 Ubuntu 22.04 so the eval gate can run
# locally on a Claude subscription. Windows itself cannot run the gate:
# it grants Bash to every case and the CLI refuses a shell grant without
# a sandbox backend. Ubuntu 22.04 rather than 24.04 because 24.04's
# AppArmor restriction on unprivileged user namespaces stops bubblewrap
# from bringing up loopback.
#
# From an elevated PowerShell on Windows, once:
#   wsl --install -d Ubuntu-22.04
# reboot, let Ubuntu create its user, then inside Ubuntu:
#   bash /mnt/c/Users/<you>/Documents/Development/Portfolio/kad-dev-team-plugin/evals/tools/wsl-setup.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y bubblewrap socat git python3 curl ca-certificates

# Node 24, the version the GitHub workflow uses; Ubuntu 22.04's own
# package is far too old for the fixtures' test runner flags.
if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 24 ]; then
  curl -fsSL https://deb.nodesource.com/setup_24.x -o /tmp/nodesource-setup.sh
  sudo -E bash /tmp/nodesource-setup.sh
  sudo apt-get install -y nodejs
fi

# Pinned to the version the recorded bars came from; move it together
# with a re-recorded thresholds.json (see .github/workflows/eval-gate.yml).
sudo npm install -g @anthropic-ai/claude-code@2.1.296

# Prove the sandbox starts before anything else is attempted.
bwrap --ro-bind / / --dev /dev --unshare-all --die-with-parent -- /bin/true
echo "sandbox ok: $(bwrap --version)"

# Line endings: the repo is edited from Windows with autocrlf; inside WSL
# everything must stay LF or the fixtures' shell scripts break.
git config --global core.autocrlf input

cat <<'EOF'

Next, inside Ubuntu:
  1. claude            # log in once with the subscription, then /exit
  2. git clone /mnt/c/Users/<you>/Documents/Development/Portfolio/kad-dev-team-plugin ~/kad-dev-team-plugin
     cd ~/kad-dev-team-plugin
     git remote set-url origin https://github.com/diabagatekelly/kad-dev-team-plugin.git
     git config --global credential.helper "/mnt/c/Program Files/Git/mingw64/bin/git-credential-manager.exe"
     (clone from the Windows checkout, not from GitHub: the repo is
     private and a clone over HTTPS inside WSL hangs on a credential
     prompt it can never show. Clone into the Linux filesystem, not
     /mnt/c: bubblewrap and the scaffold are many times slower on the
     Windows mount. The credential helper line lets later pushes from
     WSL reuse Windows' stored GitHub login.)
  3. Done. From then on, from the repository root on Windows:
       wsl -d Ubuntu -- bash evals/tools/wsl-gate.sh [--cases <case ...> | --all]
     mirrors the checkout into the clone, runs the gate, and copies the
     results, evals/evidence.json and evals/thresholds.json back, ready
     to commit. (Inside Ubuntu by hand: python3 -I evals/tools/eval_gate.py)
EOF
