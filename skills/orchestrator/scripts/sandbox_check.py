"""Is this session fenced well enough to run code-writing instances unattended?

The quarantine flow launches three `tdd-implementation` instances and up to
eighteen reviewers that nobody watches. The sandbox that keeps them off the
machine's keys and off the network is a property of the session they run
in, not of the plugin: a plugin cannot ship `sandbox` or `permissions`
settings, a plugin-shipped agent's `permissionMode` and `hooks` are ignored,
and the sandbox covers only what the Bash tool runs (the Read tool reads
past it). So the orchestrator runs this script inline, from its own Bash
tool, before every step that launches agents, and refuses to launch when it
fails. `--write-settings FILE` merges the settings that make it pass into a
settings file (the session's user settings, `~/.claude/settings.json`),
keeping everything else in the file; the orchestrator offers that on a
failed check. The README's "Running the quarantine flow" section shows the
block it writes.

Because the script itself runs inside the session's Bash sandbox, the
checks probe the real fence wherever a probe is possible, and read the
settings files only for what no probe can see:

1. platform: not native Windows. Claude Code runs commands unsandboxed
   there; a WSL2 session has the sandbox.
2. write: a write to a fresh file in the home directory fails with the
   sandbox's own error (read-only file system, or permission denied under
   Seatbelt). Any other outcome fails the check: a successful write means
   this command ran unsandboxed; an unrelated error proves nothing. Also,
   `sandbox.filesystem.allowWrite` names nothing outside the project and
   the temp directory.
3. network: a direct TCP connection to each of two public addresses fails
   with "network unreachable" (or "operation not permitted" under
   Seatbelt): the sandbox leaves no route, and allowed domains go through
   its proxy. A connection that succeeds, times out or is refused fails
   the check: a firewall blocking one address is not a sandbox.
4. env: no credential-shaped variable (a name containing SECRET, TOKEN,
   PASSWORD, CREDENTIAL, API_KEY or ending in _KEY) reaches the shell. The
   sandbox's `credentials.envVars` can deny or mask them; a candidate's
   shell inherits whatever is left. Variables the session sets for itself
   (`CLAUDE_CODE_*`) and the sandbox sets for its proxy (`CLOUDSDK_PROXY_*`)
   are listed but do not fail the check: the user cannot unset them.
5. shell-secrets: every secret path (`~/.ssh`, `~/.aws`, `~/.gnupg`,
   `~/.kube`, `~/.config/gcloud`, `~/.azure`, `~/.config/gh`, `~/.npmrc`,
   `~/.netrc`, `~/.git-credentials`, `~/.pypirc`, `~/.docker/config.json`,
   `~/.terraform.d/credentials.tfrc.json`, the Claude credentials file
   under `~/.claude` and under `CLAUDE_CONFIG_DIR` if set; `--secret` adds
   more) is named by `sandbox.filesystem.denyRead` (or a deny entry in
   `sandbox.credentials.files`), present on disk or not, since a login can
   create one later; and each that is present is unreadable from the shell
   now: a directory can be neither listed nor have its usual files opened.
6. read-secrets: every secret path, present or not, is covered by a
   `Read(...)` rule in `permissions.deny` of the merged settings, because
   the Read tool runs outside the sandbox and a candidate holds it. A
   directory needs a rule that reaches its files (`Read(~/.ssh/**)`); a
   rule naming the directory alone does not.
7. settings: `sandbox.enabled` true; `allowUnsandboxedCommands` false (a
   retry with `dangerouslyDisableSandbox` is then ignored);
   `failIfUnavailable` true (no sandbox backend means no session, not an
   unsandboxed one); `excludedCommands` empty (an excluded command runs
   with no sandbox); `autoAllowBashIfSandboxed` not false (an unattended
   agent cannot answer a Bash approval prompt).
8. worktreeinclude: the project's `.worktreeinclude`, if any, matches no
   gitignored file with a credential-shaped name (`.env*`, `*.pem`,
   `*.key`, `*credential*`, `*secret*`, `*token*`, `.npmrc`, `.netrc`, ...),
   since whatever it matches is copied into every candidate's worktree.

Settings are merged the way Claude Code merges its files: user, project,
local, then managed on top. A `--settings` flag given on the command line
of the session is not a file and is not visible here; the probes above
still measure the live sandbox, but the escape hatches in check 7 are only
as reliable as the files, so start the session without `--settings`, or
put the block in managed settings where nothing can loosen it.

One line per check, PASS or FAIL, then information lines (the network
allowlist, which settings files were read), then `sandbox check: PASS` or
`FAIL`. Exit 0 on PASS, 1 on FAIL.

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/sandbox_check.py --project DIR
           [--secret ~/.config/private-tool ...]
       python3 -I .../sandbox_check.py --project DIR --write-settings ~/.claude/settings.json
           [--secret ...]   (writes, prints what changed, then runs the checks)
"""
import argparse
import errno
import fnmatch
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import uuid

DEFAULT_SECRETS = [
    "~/.ssh",
    "~/.aws",
    "~/.gnupg",
    "~/.kube",
    "~/.config/gcloud",
    "~/.azure",
    "~/.config/gh",
    "~/.npmrc",
    "~/.netrc",
    "~/.git-credentials",
    "~/.pypirc",
    "~/.docker/config.json",
    "~/.terraform.d/credentials.tfrc.json",
    "~/.claude/.credentials.json",
]

# Files a secret directory usually holds: opened one by one when the
# directory cannot be listed, since a sandbox that denies listing but not
# traversal would otherwise look closed.
KNOWN_FILES = {
    "~/.ssh": ["id_rsa", "id_ed25519", "id_ecdsa", "config", "known_hosts"],
    "~/.aws": ["credentials", "config"],
    "~/.gnupg": ["pubring.kbx", "trustdb.gpg", "private-keys-v1.d"],
    "~/.kube": ["config"],
    "~/.config/gcloud": ["credentials.db", "application_default_credentials.json", "access_tokens.db"],
    "~/.azure": ["accessTokens.json", "azureProfile.json", "msal_token_cache.json"],
    "~/.config/gh": ["hosts.yml"],
}

PROBE_HOSTS = [("1.1.1.1", 443), ("8.8.8.8", 443)]

# errno values the sandbox itself produces. Bubblewrap mounts the host
# read-only (EROFS) and has no network route (ENETUNREACH); Seatbelt
# answers EPERM or EACCES to both.
WRITE_DENIED = {errno.EROFS, errno.EACCES, errno.EPERM}
NET_DENIED = {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EPERM, errno.EACCES, errno.EAFNOSUPPORT}

ENV_SECRET = re.compile(r"(SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|API_?KEY|_KEY$)", re.I)
CREDENTIAL_NAMES = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
                    "*credential*", "*secret*", "*token*", ".npmrc", ".netrc", ".pypirc",
                    "id_rsa*", "id_ed25519*", "id_ecdsa*", "*.kubeconfig", "kubeconfig"]

REQUIRED_SETTINGS = {
    "enabled": True,
    "allowUnsandboxedCommands": False,
    "failIfUnavailable": True,
    "excludedCommands": [],
    "autoAllowBashIfSandboxed": True,
}


def home():
    return os.path.realpath(os.path.expanduser("~"))


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def expand(pattern):
    """A settings path to an absolute path: `~/x`, `//abs/x` or a plain one."""
    if pattern.startswith("//"):
        pattern = pattern[1:]
    return os.path.realpath(os.path.expanduser(pattern))


def secret_list(extra):
    paths = list(DEFAULT_SECRETS)
    cfg = os.path.join(config_dir(), ".credentials.json")
    if expand(cfg) != expand("~/.claude/.credentials.json"):
        paths.append(cfg)
    paths += extra
    seen, out = set(), []
    for p in paths:
        if expand(p) not in seen:
            seen.add(expand(p))
            out.append(p)
    return out


# ---- settings ---------------------------------------------------------------

def settings_files(project):
    """The settings files Claude Code merges, lowest precedence first."""
    files = [
        os.path.join(config_dir(), "settings.json"),
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


def deny_read_entries(settings):
    """Paths the sandbox denies reads of: `filesystem.denyRead`, plus any
    `credentials.files` entry whose mode is deny."""
    out = [p for p in (get(settings, "sandbox", "filesystem", "denyRead", default=[]) or []) if isinstance(p, str)]
    for entry in get(settings, "sandbox", "credentials", "files", default=[]) or []:
        if isinstance(entry, dict) and entry.get("mode", "deny") == "deny" and isinstance(entry.get("path"), str):
            out.append(entry["path"])
        elif isinstance(entry, str):
            out.append(entry)
    return out


def prefix_covers(entry, secret):
    """A sandbox path entry covers the secret when it names it or a parent."""
    e = expand(entry)
    return secret == e or secret.startswith(e + os.sep)


def read_rule_covers(rule_path, secret, is_dir):
    """Does a `Read(...)` deny pattern reach this secret (and, for a
    directory, the files inside it)?"""
    raw = expand(rule_path)
    if is_dir:
        return fnmatch.fnmatch(os.path.join(secret, "x", "y"), raw)
    return secret == raw or fnmatch.fnmatch(secret, raw)


def read_rules(settings):
    rules = []
    for r in get(settings, "permissions", "deny", default=[]) or []:
        if isinstance(r, str) and r.startswith("Read(") and r.endswith(")"):
            rules.append(r[5:-1].strip())
    return rules


def write_settings(path, secrets):
    """Merge the required block into the settings file at `path`, keeping
    everything else. Returns the lines describing what changed."""
    path = os.path.expanduser(path)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        data = {}
    if not isinstance(data, dict):
        raise SystemExit(f"FAIL  write-settings: {path} does not hold a JSON object\nsandbox check: FAIL")
    changed = []
    sb = data.setdefault("sandbox", {})
    for key, want in REQUIRED_SETTINGS.items():
        if sb.get(key) != want:
            changed.append(f"sandbox.{key}: {json.dumps(sb.get(key))} -> {json.dumps(want)}")
            sb[key] = want
    sb.setdefault("network", {}).setdefault("allowedDomains", [])
    fs = sb.setdefault("filesystem", {})
    deny = [p for p in fs.get("denyRead", []) if isinstance(p, str)]
    for s in secrets:
        if not any(prefix_covers(e, expand(s)) for e in deny):
            deny.append(s)
            changed.append(f"sandbox.filesystem.denyRead += {s}")
    fs["denyRead"] = deny
    perms = data.setdefault("permissions", {})
    rules = [r for r in perms.get("deny", []) if isinstance(r, str)]
    existing = read_rules({"permissions": {"deny": rules}})
    for s in secrets:
        is_dir = s in KNOWN_FILES or os.path.isdir(expand(s))
        if not any(read_rule_covers(r, expand(s), is_dir) for r in existing):
            rule = f"Read({s.rstrip('/')}/**)" if is_dir else f"Read({s})"
            rules.append(rule)
            existing.append(rule[5:-1])
            changed.append(f"permissions.deny += {rule}")
    perms["deny"] = rules
    if changed:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".kad-tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    return changed


# ---- checks -----------------------------------------------------------------

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


def check_write(project, settings):
    h = home()
    if project == h or h.startswith(project + os.sep):
        return False, f"the project ({project}) contains the home directory, so a write there proves nothing; run the flow from a project below it"
    probe = os.path.join(h, f".kad-sandbox-probe-{uuid.uuid4().hex}")
    try:
        with open(probe, "x", encoding="utf-8") as fh:
            fh.write("probe\n")
    except OSError as e:
        if e.errno in WRITE_DENIED:
            denied = f"a write outside the project was refused ({e.strerror})"
        else:
            return False, f"the write probe failed for a reason that is not the sandbox ({e.strerror or e}); cannot tell whether writes are fenced"
    else:
        try:
            os.remove(probe)
        except OSError:
            pass
        return False, f"wrote {probe}: this command ran unsandboxed"
    tmp = os.path.realpath(tempfile.gettempdir())
    outside = []
    for entry in get(settings, "sandbox", "filesystem", "allowWrite", default=[]) or []:
        if not isinstance(entry, str):
            continue
        e = expand(entry)
        inside = any(e == root or e.startswith(root + os.sep) for root in (project, tmp))
        if not inside:
            outside.append(entry)
    if outside:
        return False, denied + "; but sandbox.filesystem.allowWrite opens paths outside the project and temp: " + ", ".join(outside)
    return True, denied


def check_network():
    reasons = []
    for host in PROBE_HOSTS:
        try:
            with socket.create_connection(host, timeout=3):
                pass
        except socket.timeout:
            return False, f"the connection to {host[0]}:{host[1]} timed out: a firewall, not the sandbox, which leaves no route at all"
        except OSError as e:
            if e.errno in NET_DENIED:
                reasons.append(f"{host[0]} {e.strerror}")
                continue
            return False, f"the connection to {host[0]}:{host[1]} failed with {e.strerror or type(e).__name__}, not the sandbox's refusal; cannot tell whether the network is fenced"
        else:
            return False, f"a direct connection to {host[0]}:{host[1]} succeeded: the network is open to commands"
    return True, "no direct route (" + "; ".join(reasons) + ")"


def check_env():
    names = sorted(n for n in os.environ if ENV_SECRET.search(n))
    own = [n for n in names if n.startswith(("CLAUDE_CODE_", "CLOUDSDK_PROXY_"))]
    names = [n for n in names if n not in own]
    note = ("; set by the session or its sandbox, exempt: " + ", ".join(own)) if own else ""
    if names:
        return False, "credential-shaped variables reach the shell: " + ", ".join(names) + " (unset them, or deny them in sandbox.credentials.envVars)" + note
    return True, "no credential-shaped variable in the environment" + note


def readable(path, known):
    """Can the shell read this path? A directory counts as readable when it
    lists, or when any of its usual files opens."""
    try:
        if os.path.isdir(path):
            os.listdir(path)
            return True
        with open(path, "rb") as fh:
            fh.read(1)
        return True
    except OSError:
        pass
    if os.path.isdir(path):
        for name in known:
            try:
                child = os.path.join(path, name)
                if os.path.isdir(child):
                    os.listdir(child)
                else:
                    with open(child, "rb") as fh:
                        fh.read(1)
                return True
            except OSError:
                continue
    return False


def check_shell_secrets(secrets, settings):
    entries = deny_read_entries(settings)
    unlisted = [s for s in secrets if not any(prefix_covers(e, expand(s)) for e in entries)]
    open_ = []
    for s in secrets:
        p = expand(s)
        if os.path.exists(p) and readable(p, KNOWN_FILES.get(s, [])):
            open_.append(s)
    problems = []
    if open_:
        problems.append("readable from the shell now: " + ", ".join(open_))
    if unlisted:
        problems.append("not in sandbox.filesystem.denyRead: " + ", ".join(unlisted))
    if problems:
        return False, "; ".join(problems)
    present = sum(1 for s in secrets if os.path.exists(expand(s)))
    return True, f"{len(secrets)} paths denied in settings, {present} present and unreadable from the shell"


def check_read_rules(secrets, settings):
    rules = read_rules(settings)
    uncovered = []
    for s in secrets:
        is_dir = s in KNOWN_FILES or os.path.isdir(expand(s))
        if not any(read_rule_covers(r, expand(s), is_dir) for r in rules):
            uncovered.append(s + ("/**" if is_dir else ""))
    if uncovered:
        return False, "no Read(...) deny rule reaches: " + ", ".join(uncovered) + " (permissions.deny)"
    return True, f"{len(secrets)} paths each covered by a Read(...) deny rule"


def check_settings(settings):
    wrong = []
    for key, want in REQUIRED_SETTINGS.items():
        have = get(settings, "sandbox", key)
        if key == "autoAllowBashIfSandboxed" and have is None:
            continue  # the default is true
        if have != want:
            wrong.append(f"sandbox.{key} is {json.dumps(have)}, needs {json.dumps(want)}")
    if wrong:
        return False, "; ".join(wrong)
    return True, "enabled, no unsandboxed commands, fails if unavailable, no excluded commands, Bash auto-allowed"


def gitignore_match(pattern, path):
    """Roughly gitignore: a pattern with a slash matches the path from the
    root, one without matches any component or basename; `**` and `*` as
    fnmatch has them."""
    pattern = pattern.strip().rstrip("/")
    if not pattern or pattern.startswith("#"):
        return False
    if pattern.startswith("/"):
        pattern = pattern[1:]
    if "/" in pattern:
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern + "/*")
    parts = path.split("/")
    return any(fnmatch.fnmatch(part, pattern) for part in parts)


def check_worktreeinclude(project):
    path = os.path.join(project, ".worktreeinclude")
    if not os.path.isfile(path):
        return True, "no .worktreeinclude"
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            patterns = [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    except OSError as e:
        return False, f".worktreeinclude unreadable: {e}"
    proc = subprocess.run(["git", "ls-files", "-oi", "--exclude-standard"], cwd=project,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return False, f"cannot list the project's ignored files to see what .worktreeinclude copies: {proc.stderr.strip()}"
    ignored = [l for l in proc.stdout.splitlines() if l]
    copied = [f for f in ignored if any(gitignore_match(p, f) for p in patterns)]
    secret = [f for f in copied if any(fnmatch.fnmatch(os.path.basename(f), n) for n in CREDENTIAL_NAMES)]
    if secret:
        return False, ".worktreeinclude copies credential-shaped files into every worktree: " + ", ".join(secret)
    return True, f".worktreeinclude copies {len(copied)} ignored file(s), none credential-shaped"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="the project root (the real tree, not a worktree)")
    p.add_argument("--secret", action="append", default=[],
                   help="another path that must be unreadable (repeatable; `~` allowed)")
    p.add_argument("--write-settings", metavar="FILE",
                   help="merge the required sandbox and deny settings into this settings file first")
    a = p.parse_args()
    project = os.path.realpath(a.project)
    if not os.path.isdir(project):
        print(f"FAIL  project: {a.project} is not a directory\nsandbox check: FAIL")
        return 1
    secrets = secret_list(a.secret)

    if a.write_settings:
        changed = write_settings(a.write_settings, secrets)
        if changed:
            print(f"settings written: {os.path.expanduser(a.write_settings)}")
            for c in changed:
                print("  " + c)
            print("  (a sandbox setting takes effect in the session's next Bash command; if the probes below still fail, restart the session)")
        else:
            print(f"settings already complete: {os.path.expanduser(a.write_settings)}")

    settings, read, broken = load_settings(project)
    results = [
        ("platform", *check_platform()),
        ("write", *check_write(project, settings)),
        ("network", *check_network()),
        ("env", *check_env()),
        ("shell-secrets", *check_shell_secrets(secrets, settings)),
        ("read-secrets", *check_read_rules(secrets, settings)),
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
