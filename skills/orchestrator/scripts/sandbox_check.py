"""Is this session fenced well enough to run code-writing instances unattended?

The quarantine flow launches three `tdd-implementation` instances and up to
eighteen reviewers that nobody watches. The sandbox that keeps them off the
machine's keys and off the network is a property of the session they run
in, not of the plugin: a plugin cannot ship `sandbox` or `permissions`
settings, a plugin-shipped agent's `permissionMode` and `hooks` are ignored,
and the sandbox covers only what the Bash tool runs (the Read tool reads
past it). So the orchestrator runs this script inline, from its own Bash
tool, before the flow launches anything, and refuses to start when it
fails. The README's "Running the quarantine flow" section has the settings
block that makes it pass.

Because the script itself runs inside the session's Bash sandbox, most
checks are probes of the real fence rather than readings of a settings
file:

1. platform: not native Windows. Claude Code runs commands unsandboxed
   there; a WSL2 session has the sandbox.
2. write: a write outside the project, in the home directory, is refused.
   This is the proof that the command running this script was sandboxed.
3. network: a direct TCP connection out fails. The sandbox routes allowed
   domains through its own proxy and leaves no direct route; an open route
   means an unsandboxed command (or an escape hatch) is in play.
4. shell-secrets: each secret path that exists on this machine (`~/.ssh`,
   `~/.aws`, `~/.gnupg`, `~/.config/gh`, `~/.npmrc`, `~/.netrc`,
   `~/.git-credentials`, `~/.docker/config.json`,
   `~/.claude/.credentials.json`; `--secret` adds more) cannot be read from
   the shell. The sandbox lets a command read the whole machine unless
   `sandbox.filesystem.denyRead` names the path.
5. read-secrets: each of those paths is covered by a `Read(...)` rule in
   `permissions.deny` of the merged settings, because the Read tool runs
   outside the sandbox and a candidate holds it.
6. settings: `sandbox.enabled` is true, `sandbox.allowUnsandboxedCommands`
   is false (a retry with `dangerouslyDisableSandbox` is then ignored),
   `sandbox.failIfUnavailable` is true (a session with no sandbox backend
   refuses to start instead of running unsandboxed) and
   `sandbox.excludedCommands` is empty (an excluded command runs with no
   sandbox at all). These are read from the settings files, merged the way
   Claude Code merges them (user, then project, then local, then managed on
   top; `--settings` on the command line is not visible here), since no
   probe can see an escape hatch that has not been used yet.
7. worktreeinclude: the project's `.worktreeinclude`, if any, copies no
   `.env` file into the candidates' worktrees.

One line per check, PASS or FAIL, then information lines (the network
allowlist, which settings files were read), then `sandbox check: PASS` or
`FAIL`. Exit 0 on PASS, 1 on FAIL.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/sandbox_check.py --project DIR
           [--secret ~/.config/private-tool ...]
"""
import argparse
import fnmatch
import json
import os
import socket
import sys

DEFAULT_SECRETS = [
    "~/.ssh",
    "~/.aws",
    "~/.gnupg",
    "~/.config/gh",
    "~/.npmrc",
    "~/.netrc",
    "~/.git-credentials",
    "~/.docker/config.json",
    "~/.claude/.credentials.json",
]

# The probe target: a well-known address that answers on 443. The sandbox
# leaves no direct route, so the connection fails whatever the address.
PROBE_HOST = ("1.1.1.1", 443)


def home():
    return os.path.realpath(os.path.expanduser("~"))


def settings_files(project):
    """The settings files Claude Code merges, lowest precedence first."""
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    files = [
        os.path.join(config_dir, "settings.json"),
        os.path.join(project, ".claude", "settings.json"),
        os.path.join(project, ".claude", "settings.local.json"),
        "/etc/claude-code/managed-settings.json",
        "/Library/Application Support/ClaudeCode/managed-settings.json",
    ]
    return [f for f in files if os.path.isfile(f)]


def merge(base, over):
    """Deep merge: dicts recurse, lists concatenate, scalars override."""
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = out[k] + v
        else:
            out[k] = v
    return out


def load_settings(project):
    merged, read, broken = {}, [], []
    for f in settings_files(project):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as e:
            broken.append(f"{f}: {e}")
            continue
        if isinstance(data, dict):
            merged = merge(merged, data)
            read.append(f)
    return merged, read, broken


def get(settings, *path, default=None):
    cur = settings
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def expand(pattern):
    """A settings path to an absolute path: `~/x`, `//abs/x` or a plain one."""
    if pattern.startswith("//"):
        pattern = pattern[1:]
    return os.path.realpath(os.path.expanduser(pattern))


def rule_covers(rule_path, secret):
    """Does a `Read(...)` deny pattern cover this secret path?"""
    raw = expand(rule_path)
    stem = raw
    for suffix in ("/**", "/*", "**", "*"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    stem = stem.rstrip("/") or stem
    return (secret == stem or secret.startswith(stem + os.sep)
            or fnmatch.fnmatch(secret, raw) or fnmatch.fnmatch(secret, raw.rstrip("*")))


def check_platform():
    if sys.platform == "win32":
        return False, "native Windows: Claude Code runs commands unsandboxed here; run the session in WSL2"
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/version", encoding="utf-8", errors="replace") as fh:
                if "microsoft" in fh.read().lower():
                    return True, "WSL2"
        except OSError:
            pass
        return True, "Linux"
    if sys.platform == "darwin":
        return True, "macOS"
    return True, sys.platform


def check_write(project):
    h = home()
    if project == h or h.startswith(project + os.sep):
        return False, f"the project ({project}) contains the home directory, so a write there proves nothing; run the flow from a project below it"
    probe = os.path.join(h, f".kad-sandbox-probe-{os.getpid()}")
    try:
        with open(probe, "x", encoding="utf-8") as fh:
            fh.write("probe\n")
    except OSError as e:
        return True, f"a write outside the project was refused ({e.strerror or e})"
    try:
        os.remove(probe)
    except OSError:
        pass
    return False, f"wrote {probe}: this command ran unsandboxed"


def check_network():
    try:
        with socket.create_connection(PROBE_HOST, timeout=3):
            pass
    except OSError as e:
        return True, f"no direct route to {PROBE_HOST[0]}:{PROBE_HOST[1]} ({e.strerror or type(e).__name__}); the same holds offline"
    return False, f"a direct connection to {PROBE_HOST[0]}:{PROBE_HOST[1]} succeeded: the network is open to commands"


def readable(path):
    try:
        if os.path.isdir(path):
            os.listdir(path)
        else:
            with open(path, "rb") as fh:
                fh.read(1)
    except PermissionError:
        return False
    except OSError:
        # Unreadable for another reason (a broken link, a socket): not a
        # secret a command can read either way.
        return False
    return True


def check_shell_secrets(secrets):
    present = [s for s in secrets if os.path.exists(s)]
    if not present:
        return True, "none of the secret paths exists on this machine"
    open_ = [s for s in present if readable(s)]
    if open_:
        return False, "readable from the shell: " + ", ".join(open_) + " (sandbox.filesystem.denyRead)"
    return True, f"{len(present)} present, none readable from the shell"


def check_read_rules(settings, secrets):
    present = [s for s in secrets if os.path.exists(s)]
    if not present:
        return True, "none of the secret paths exists on this machine"
    deny = get(settings, "permissions", "deny", default=[]) or []
    rules = []
    for r in deny:
        if isinstance(r, str) and r.startswith("Read(") and r.endswith(")"):
            rules.append(r[5:-1].strip())
    uncovered = [s for s in present if not any(rule_covers(r, s) for r in rules)]
    if uncovered:
        return False, "no Read(...) deny rule covers: " + ", ".join(uncovered) + " (permissions.deny)"
    return True, f"{len(present)} present, each covered by a Read(...) deny rule"


def check_settings(settings):
    wanted = [
        (("sandbox", "enabled"), True),
        (("sandbox", "allowUnsandboxedCommands"), False),
        (("sandbox", "failIfUnavailable"), True),
        (("sandbox", "excludedCommands"), []),
    ]
    wrong = []
    for path, want in wanted:
        have = get(settings, *path)
        if have != want:
            wrong.append(f"{'.'.join(path)} is {json.dumps(have)}, needs {json.dumps(want)}")
    if wrong:
        return False, "; ".join(wrong)
    return True, "enabled, no unsandboxed commands, fails if unavailable, no excluded commands"


def check_worktreeinclude(project):
    path = os.path.join(project, ".worktreeinclude")
    if not os.path.isfile(path):
        return True, "no .worktreeinclude"
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    except OSError as e:
        return False, f".worktreeinclude unreadable: {e}"
    env = [l for l in lines if ".env" in l]
    if env:
        return False, ".worktreeinclude copies into every worktree: " + ", ".join(env)
    return True, f".worktreeinclude copies {len(lines)} pattern(s), none an .env file"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="the project root (the real tree, not a worktree)")
    p.add_argument("--secret", action="append", default=[],
                   help="another path that must be unreadable (repeatable; `~` allowed)")
    a = p.parse_args()
    project = os.path.realpath(a.project)
    if not os.path.isdir(project):
        print(f"FAIL  project: {a.project} is not a directory\nsandbox check: FAIL")
        return 1
    secrets = [expand(s) for s in DEFAULT_SECRETS + a.secret]
    settings, read, broken = load_settings(project)

    results = [
        ("platform", *check_platform()),
        ("write", *check_write(project)),
        ("network", *check_network()),
        ("shell-secrets", *check_shell_secrets(secrets)),
        ("read-secrets", *check_read_rules(settings, secrets)),
        ("settings", *check_settings(settings)),
        ("worktreeinclude", *check_worktreeinclude(project)),
    ]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    allowed = get(settings, "sandbox", "network", "allowedDomains", default=[]) or []
    print("network allowlist:", ", ".join(map(str, allowed)) if allowed else "none")
    print("settings read:", ", ".join(read) if read else "none found")
    for b in broken:
        print("settings skipped:", b)
    passed = all(ok for _, ok, _ in results)
    print("sandbox check:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
