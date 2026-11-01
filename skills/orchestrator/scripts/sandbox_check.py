"""Is this session fenced well enough to run code-writing instances unattended?

The quarantine flow launches three `tdd-implementation` instances and up to
eighteen reviewers that nobody watches. The sandbox that keeps them off the
machine's keys and off the network is a property of the session they run
in, not of the plugin: a plugin cannot ship `sandbox` or `permissions`
settings, a plugin-shipped agent's `permissionMode` and `hooks` are ignored,
and the sandbox covers only what the Bash tool runs (the Read tool reads
past it). So the orchestrator runs this script inline, from its own Bash
tool, before every step that launches agents, and refuses to launch when it
fails. `--write-settings [FILE]` merges the settings that make it pass into
the session's user settings file (`settings.json` under `CLAUDE_CONFIG_DIR`,
or `~/.claude`; a FILE overrides), keeping everything else in the file; the
orchestrator offers that on a failed check. The README's "Running the
quarantine flow" section shows the block it writes.

Because the script itself runs inside the session's Bash sandbox, the
checks probe the real fence wherever a probe is possible, and read the
settings files only for what no probe can see:

1. platform: the platform has a sandbox backend (Seatbelt on macOS,
   bubblewrap on Linux and WSL2). Native Windows has none and Claude Code
   runs commands unsandboxed there; that failure is not a settings
   problem, so the script exits 2 for it and the orchestrator offers the
   user the choice to continue unsandboxed, logged, or to run the session
   in WSL2. On such a platform `--write-settings` writes the deny rules
   only (check 5's `denyRead` list and check 6's `Read(...)` rules), never
   `sandbox.enabled` or `failIfUnavailable`: with no backend those two
   make the session refuse every command, which is what happened on the
   first real run.
2. write: a write to a fresh file in the home directory fails with the
   sandbox's own error (read-only file system, or permission denied under
   Seatbelt). Any other outcome fails the check: a successful write means
   this command ran unsandboxed; an unrelated error proves nothing. Also,
   `sandbox.filesystem.allowWrite` names nothing outside the project and
   the temp directory.
3. network: a direct TCP connection to each of two public IPv4 addresses
   and one IPv6 address fails with "network unreachable" (or "operation
   not permitted" under Seatbelt): the sandbox leaves no route, and allowed
   domains go through its proxy. A connection that succeeds, times out, is
   refused or fails with "host unreachable" fails the check: a firewall
   blocking an address is not a sandbox. A machine with no IPv6 stack
   skips the IPv6 probe.
4. env: no credential-shaped variable (a name containing SECRET, TOKEN,
   PASSWORD, PASSWD, CREDENTIAL, API_KEY, ACCESS_KEY, PRIVATE_KEY, or
   ending in _KEY) reaches the shell. The sandbox's `credentials.envVars`
   can deny or mask them; a candidate's shell inherits whatever is left.
   Exactly two names are exempt because the session sets them itself and
   the user cannot unset them: `CLAUDE_CODE_MESSAGING_TOKEN` and the
   sandbox proxy's `CLOUDSDK_PROXY_PASSWORD`.
5. shell-secrets: every secret path (`~/.ssh`, `~/.aws`, `~/.gnupg`,
   `~/.kube`, `~/.config/gcloud`, `~/.azure`, `~/.config/gh`, `~/.npmrc`,
   `~/.netrc`, `~/.git-credentials`, `~/.pypirc`, `~/.docker/config.json`,
   `~/.terraform.d/credentials.tfrc.json`, the Claude credentials file
   under `~/.claude` and under `CLAUDE_CONFIG_DIR` if set; `--secret` adds
   more, with a trailing `/` for a directory that may not exist yet) is
   named by `sandbox.filesystem.denyRead` (or a deny entry in
   `sandbox.credentials.files`), present on disk or not, since a login can
   create one later; and each that is present is unreadable from the shell
   now: a directory can be neither listed nor have its usual files opened,
   a file cannot be opened. Only regular files are opened, never a FIFO or
   a device, so the probe cannot hang.
6. read-secrets: every secret path, present or not, is covered by a
   `Read(...)` rule in `permissions.deny` of the merged settings, because
   the Read tool runs outside the sandbox and a candidate holds it. A
   directory needs a recursive rule (`Read(~/.ssh/**)`): in the matcher
   here `*` never crosses a slash, so `Read(~/.ssh/*)` reaches one level
   and does not count, and a rule naming the directory alone does not.
7. settings: `sandbox.enabled` true; `allowUnsandboxedCommands` false (a
   retry with `dangerouslyDisableSandbox` is then ignored);
   `failIfUnavailable` true (no sandbox backend means no session, not an
   unsandboxed one); `excludedCommands` empty (an excluded command runs
   with no sandbox); `autoAllowBashIfSandboxed` not false (an unattended
   agent cannot answer a Bash approval prompt).
8. worktreeinclude: the project's `.worktreeinclude`, if any, matches no
   gitignored file that looks like a credential: by name (`.env*`,
   `.envrc`, `*.pem`, `*.key`, `*.ppk`, `*.p12`, `*.pfx`, `*.jks`,
   `*.keystore`, `*.gpg`, `*.asc`, `*credential*`, `*secret*`, `*token*`,
   `.npmrc`, `.netrc`, `.pypirc`, `.htpasswd`, `id_rsa*`, `id_dsa*`,
   `id_ed25519*`, `id_ecdsa*`, `*kubeconfig*`) or by living under a
   credential directory (`.ssh`, `.aws`, `.kube`, `.gnupg`, `.docker`,
   `.azure`, `gcloud`, `gh`). Patterns are matched with gitignore's rules
   (`**/` at any depth including the root, a slash anchors, no slash
   matches any component). Whatever matches is copied into every
   candidate's worktree.

Under the sandbox runtime (`srt claude`; the runtime sets
`SANDBOX_RUNTIME=1` inside) the whole session is fenced, file tools, hooks
and MCP servers included, by `~/.srt-settings.json` (or the file passed to
`srt --settings`, which this script cannot see unless `--srt-settings FILE`
or `KAD_SRT_SETTINGS`, which the launcher `bin/kad` exports, names it). The probes measure that fence like any other. The settings
checks then read the runtime's file: check 2 scans its
`filesystem.allowWrite` (the project, the temp directories, `~/.claude`
and `~/.claude.json` are expected there, nothing else); checks 5 and 6
accept a secret named in its `filesystem.denyRead`, since the Read tool
runs inside the runtime's boundary; check 7 passes, because Claude's own
sandbox keys are optional inside the runtime and a retry with
`dangerouslyDisableSandbox` cannot leave it (Bash approvals are then the
permission mode's: auto mode or `--dangerously-skip-permissions` inside
the runtime). A missing `denyRead` entry is reported with the list to add;
the runtime reads its file at launch, so the owner adds it outside the
session and restarts, which `--write-settings` cannot do for them.

Settings are merged the way Claude Code merges its files: user, project,
local, then managed on top. A `--settings` flag given on the command line
of the session is not a file and is not visible here; the probes above
still measure the live sandbox, but the escape hatches in check 7 are only
as reliable as the files, so start the session without `--settings`, or
put the block in managed settings where nothing can loosen it. Claude Code
applies the sandbox to each command as it runs, from the settings at that
moment; this script is the preflight that says whether the next launch is
fenced, not the fence itself.

`--write-settings` writes through a symlink to its target, keeps the file's
mode, uses a private temporary name, writes only the two deny lists when
the platform has no sandbox backend (and says so on its first line), and when the sandbox itself refuses
the write (the user settings file is outside the project, so a session
whose sandbox is already on but incomplete cannot write it from Bash)
prints the complete intended content between marker lines, for the
orchestrator to write with its Write tool, which runs outside the sandbox.

One line per check, PASS or FAIL, then information lines (the network
allowlist, which settings files were read), then `sandbox check: PASS` or
`FAIL`. Exit 0 on PASS, 1 on FAIL, 2 when the FAIL is the platform's
(no sandbox backend exists here, whatever the settings say).

Usage: python3 -I ${CLAUDE_SKILL_DIR}/scripts/sandbox_check.py --project DIR
           [--secret ~/.config/private-tool/ ...] [--srt-settings FILE]
       python3 -I .../sandbox_check.py --project DIR --write-settings [FILE] [--secret ...]
           (writes, prints what changed, then runs the checks)
"""
import argparse
import errno
import fnmatch
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import uuid

# Directories end with "/": a directory that does not exist yet still gets a
# recursive rule.
DEFAULT_SECRETS = [
    "~/.ssh/",
    "~/.aws/",
    "~/.gnupg/",
    "~/.kube/",
    "~/.config/gcloud/",
    "~/.azure/",
    "~/.config/gh/",
    "~/.npmrc",
    "~/.netrc",
    "~/.git-credentials",
    "~/.pypirc",
    "~/.docker/config.json",
    "~/.terraform.d/credentials.tfrc.json",
    "~/.claude/.credentials.json",
]

# Files a secret directory usually holds, opened one by one when the
# directory cannot be listed, since a sandbox that denies listing but not
# traversal would otherwise look closed. GENERIC_FILES are tried in every
# secret directory, the custom ones included.
KNOWN_FILES = {
    "~/.ssh/": ["id_rsa", "id_ed25519", "id_ecdsa", "id_dsa", "config", "known_hosts", "authorized_keys"],
    "~/.aws/": ["credentials", "config", "sso"],
    "~/.gnupg/": ["pubring.kbx", "trustdb.gpg", "private-keys-v1.d", "secring.gpg"],
    "~/.kube/": ["config"],
    "~/.config/gcloud/": ["credentials.db", "application_default_credentials.json", "access_tokens.db", "configurations"],
    "~/.azure/": ["accessTokens.json", "azureProfile.json", "msal_token_cache.json", "msal_token_cache.bin"],
    "~/.config/gh/": ["hosts.yml", "config.yml"],
}
GENERIC_FILES = ["config", "credentials", "credentials.json", "token", "token.json", "key", "key.pem",
                 "id_rsa", "private.key", "secret", "secrets.json", ".env"]

PROBE_HOSTS = [("1.1.1.1", 443), ("8.8.8.8", 443), ("2606:4700:4700::1111", 443)]

# errno values the sandbox itself produces. Bubblewrap mounts the host
# read-only (EROFS) and has no network route (ENETUNREACH); Seatbelt
# answers EPERM or EACCES to both. "Host unreachable" is a firewall or a
# routing fault and does not count.
WRITE_DENIED = {errno.EROFS, errno.EACCES, errno.EPERM}
NET_DENIED = {errno.ENETUNREACH, errno.EPERM, errno.EACCES}

ENV_SECRET = re.compile(r"(SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|_KEY$)", re.I)
ENV_EXEMPT = {"CLAUDE_CODE_MESSAGING_TOKEN", "CLOUDSDK_PROXY_PASSWORD"}

CREDENTIAL_NAMES = [".env", ".env.*", ".envrc", "*.pem", "*.key", "*.ppk", "*.p12", "*.pfx", "*.jks",
                    "*.keystore", "*.gpg", "*.asc", "*credential*", "*secret*", "*token*", ".npmrc",
                    ".netrc", ".pypirc", ".htpasswd", "id_rsa*", "id_dsa*", "id_ed25519*", "id_ecdsa*",
                    "*kubeconfig*", ".git-credentials"]
CREDENTIAL_DIRS = {".ssh", ".aws", ".kube", ".gnupg", ".docker", ".azure", "gcloud", "gh"}

REQUIRED_SETTINGS = {
    "enabled": True,
    "allowUnsandboxedCommands": False,
    "failIfUnavailable": True,
    "excludedCommands": [],
    "autoAllowBashIfSandboxed": True,
}


_GIT = None


def find_git():
    """The first git that answers `--version`: whatever PATH holds, then the
    Homebrew and MacPorts paths. macOS's /usr/bin/git is Apple's xcrun
    shim, which fails inside a sandbox that cannot read the developer
    directory; the candidates are tried by running them, not by stat,
    since such a sandbox may deny the stat and still allow the exec."""
    global _GIT
    if _GIT is None:
        for c in (shutil.which("git") or "git", "/opt/homebrew/bin/git", "/usr/local/bin/git", "/opt/local/bin/git"):
            try:
                if subprocess.run([c, "--version"], capture_output=True, timeout=15).returncode == 0:
                    _GIT = c
                    break
            except (OSError, subprocess.TimeoutExpired):
                continue
        _GIT = _GIT or "git"
    return _GIT

def home():
    return os.path.realpath(os.path.expanduser("~"))


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def user_settings_path():
    return os.path.join(config_dir(), "settings.json")


def expand(path):
    """A settings path to an absolute path: `~/x`, `//abs/x` or a plain one."""
    if path.startswith("//"):
        path = path[1:]
    return os.path.realpath(os.path.expanduser(path.rstrip("/") or path))


def is_dir_secret(spec):
    """Directory intent: a trailing slash, a known directory, or an
    existing directory on disk."""
    return spec.endswith("/") or spec in KNOWN_FILES or os.path.isdir(expand(spec))


def secret_list(extra):
    specs = list(DEFAULT_SECRETS)
    cfg = os.path.join(config_dir(), ".credentials.json")
    if expand(cfg) != expand("~/.claude/.credentials.json"):
        specs.append(cfg)
    specs += extra
    seen, out = set(), []
    for s in specs:
        if expand(s) not in seen:
            seen.add(expand(s))
            out.append(s)
    return out


# ---- settings ---------------------------------------------------------------

def settings_files(project):
    """The settings files Claude Code merges, lowest precedence first."""
    files = [
        user_settings_path(),
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


def under_srt():
    """True inside the sandbox runtime, which sets SANDBOX_RUNTIME=1 for every process it fences."""
    return os.environ.get("SANDBOX_RUNTIME") == "1"


def srt_settings_path(override):
    """--srt-settings, else KAD_SRT_SETTINGS (the launcher `bin/kad` exports the
    file it passed to `srt --settings`), else the runtime's default path."""
    return os.path.expanduser(override or os.environ.get("KAD_SRT_SETTINGS") or "~/.srt-settings.json")


def load_srt_settings(path):
    """(settings, note): the runtime's file, or {} with a note when there is none or it is unreadable."""
    if not os.path.isfile(path):
        return {}, f"none at {path} (runtime defaults: no network, writes to the runtime's own paths only, every read allowed)"
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        return {}, f"{path} unreadable or invalid ({e}); the runtime refuses to start on such a file, so this session is not under it"
    return (data if isinstance(data, dict) else {}), path


def srt_deny_read_entries(srt):
    return [expand(e) for e in (get(srt, "filesystem", "denyRead", default=[]) or []) if isinstance(e, str)]


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


def glob_regex(pattern):
    """A path glob as a regex: `**` crosses slashes, `*` and `?` do not."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


def rule_path(rule):
    """A `Read(...)` rule's path made absolute, the glob part untouched."""
    if rule.startswith("//"):
        rule = rule[1:]
    rule = os.path.expanduser(rule)
    m = re.search(r"[*?\[]", rule)
    head, tail = (rule[:m.start()], rule[m.start():]) if m else (rule, "")
    head_dir, head_base = os.path.split(head) if tail else (head, "")
    base = os.path.realpath(head_dir) if head_dir else ""
    return (os.path.join(base, head_base) if head_base else base) + tail


def read_rule_covers(rule, secret, is_dir):
    """Does a `Read(...)` deny pattern reach this secret and, for a
    directory, every file below it?"""
    rx = glob_regex(rule_path(rule))
    if is_dir:
        return bool(rx.match(secret + "/x") and rx.match(secret + "/x/y/z"))
    return bool(rx.match(secret))


def read_rules(settings):
    rules = []
    for r in get(settings, "permissions", "deny", default=[]) or []:
        if isinstance(r, str) and r.startswith("Read(") and r.endswith(")"):
            rules.append(r[5:-1].strip())
    return rules


def rule_for(spec):
    return f"Read({spec.rstrip('/')}/**)" if is_dir_secret(spec) else f"Read({spec})"


def write_settings(path, secrets, deny_only=False):
    """Merge the required block into the settings file at `path`, keeping
    everything else. With `deny_only` (a platform with no sandbox backend)
    only `sandbox.filesystem.denyRead` and the `Read(...)` rules in
    `permissions.deny` are written: `sandbox.enabled` and
    `failIfUnavailable` would make such a session refuse every command.
    Returns (changed lines, error, intended content):
    on an error nothing was written and the intended content is printed by
    the caller for the orchestrator to write another way."""
    path = os.path.realpath(os.path.expanduser(path))
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        mode = stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        data, mode = {}, 0o600
    except (OSError, ValueError) as e:
        return [], f"{path} could not be read as JSON ({e}); fix the file by hand", None
    if not isinstance(data, dict):
        return [], f"{path} does not hold a JSON object; fix the file by hand", None
    for key in ("sandbox", "permissions"):
        if key in data and not isinstance(data[key], dict):
            return [], f"{path}: {key} is not an object; fix the file by hand", None
    changed = []
    sb = data.setdefault("sandbox", {})
    if not deny_only:
        for key, want in REQUIRED_SETTINGS.items():
            if sb.get(key) != want:
                changed.append(f"sandbox.{key}: {json.dumps(sb.get(key))} -> {json.dumps(want)}")
                sb[key] = want
        net = sb.get("network")
        if not isinstance(net, dict):
            sb["network"] = net = {}
        net.setdefault("allowedDomains", [])
    fs = sb.get("filesystem")
    if not isinstance(fs, dict):
        sb["filesystem"] = fs = {}
    deny = [p for p in (fs.get("denyRead") or []) if isinstance(p, str)]
    for s in secrets:
        if not any(prefix_covers(e, expand(s)) for e in deny):
            deny.append(s.rstrip("/"))
            changed.append(f"sandbox.filesystem.denyRead += {s.rstrip('/')}")
    fs["denyRead"] = deny
    perms = data.setdefault("permissions", {})
    rules = [r for r in (perms.get("deny") or []) if isinstance(r, str)]
    existing = read_rules({"permissions": {"deny": rules}})
    for s in secrets:
        if not any(read_rule_covers(r, expand(s), is_dir_secret(s)) for r in existing):
            rule = rule_for(s)
            rules.append(rule)
            existing.append(rule[5:-1])
            changed.append(f"permissions.deny += {rule}")
    perms["deny"] = rules
    content = json.dumps(data, indent=2) + "\n"
    if not changed:
        return [], None, content
    tmp = os.path.join(os.path.dirname(path) or ".", f".settings-{uuid.uuid4().hex}.kad-tmp")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return changed, f"the write to {path} was refused ({e.strerror or e})", content
    return changed, None, content


# ---- checks -----------------------------------------------------------------

NO_SANDBOX = 2  # exit code: this platform has no sandbox backend; not a settings problem


def check_platform():
    """Which sandbox this platform has. Native Windows has none: Claude Code runs every
    command unsandboxed there, and no settings file changes that; the orchestrator then
    offers to continue unsandboxed and logs the choice, or the user runs the session in WSL2."""
    if sys.platform == "win32":
        return False, "native Windows has no sandbox backend (bubblewrap and Seatbelt are Linux, WSL2 and macOS); commands run unsandboxed"
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/version", encoding="utf-8", errors="replace") as fh:
                if "microsoft" in fh.read().lower():
                    return True, "WSL2 (bubblewrap)"
        except OSError:
            pass
        return True, "Linux (bubblewrap)"
    if sys.platform == "darwin":
        return True, "macOS (Seatbelt)"
    return True, sys.platform


def platform_line():
    ok, detail = check_platform()
    if ok and under_srt():
        detail += " under the sandbox runtime: the whole session is fenced, file tools, hooks and MCP servers included"
    return ok, detail


def check_write(project, settings, srt):
    h = home()
    if project == h or h.startswith(project + os.sep):
        return False, f"the project ({project}) contains the home directory, so a write there proves nothing; run the flow from a project below it"
    probe = os.path.join(h, f".kad-sandbox-probe-{uuid.uuid4().hex}")
    try:
        fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as e:
        if e.errno in WRITE_DENIED:
            denied = f"a write outside the project was refused ({e.strerror})"
        else:
            return False, f"the write probe failed for a reason that is not the sandbox ({e.strerror or e}); cannot tell whether writes are fenced"
    else:
        os.close(fd)
        try:
            os.remove(probe)
        except OSError:
            pass
        return False, f"wrote {probe}: this command ran unsandboxed"
    try:
        tmp = os.path.realpath(tempfile.gettempdir())
    except OSError:
        tmp = None  # a fence that leaves no writable temp directory at all
    roots = [r for r in (project, tmp) if r]
    key = "sandbox.filesystem.allowWrite"
    entries = get(settings, "sandbox", "filesystem", "allowWrite", default=[]) or []
    if under_srt():
        # The runtime's own grants: Claude Code needs its config and temp
        # directories writable to run at all, so those are expected.
        key = "the runtime's filesystem.allowWrite"
        entries = get(srt, "filesystem", "allowWrite", default=[]) or []
        # ~/.npm is npm's cache, which an install inside the project writes;
        # the credential file ~/.npmrc is a separate path and stays denied.
        roots += [os.path.realpath(expand(r)) for r in ("~/.claude", "~/.claude.json", "/tmp", "/private/tmp", "~/.npm")]
        if os.environ.get("CLAUDE_CODE_TMPDIR"):
            roots.append(os.path.realpath(os.environ["CLAUDE_CODE_TMPDIR"]))
    outside = []
    for entry in entries:
        if not isinstance(entry, str):
            continue
        e = os.path.realpath(expand(entry)) if entry not in (".", "./") else project
        if not any(e == root or e.startswith(root + os.sep) for root in roots):
            outside.append(entry)
    if outside:
        return False, denied + f"; but {key} opens paths outside the project and temp: " + ", ".join(outside)
    return True, denied


def check_network():
    reasons = []
    for host, port in PROBE_HOSTS:
        v6 = ":" in host
        try:
            with socket.create_connection((host, port), timeout=3):
                pass
        except socket.timeout:
            return False, f"the connection to {host}:{port} timed out: a firewall, not the sandbox, which leaves no route at all"
        except OSError as e:
            if e.errno in NET_DENIED:
                reasons.append(f"{host} {e.strerror}")
                continue
            if v6 and e.errno in (errno.EAFNOSUPPORT, errno.EADDRNOTAVAIL):
                reasons.append(f"{host} no IPv6 stack, skipped")
                continue
            return False, f"the connection to {host}:{port} failed with {e.strerror or type(e).__name__}, not the sandbox's refusal; cannot tell whether the network is fenced"
        else:
            return False, f"a direct connection to {host}:{port} succeeded: the network is open to commands"
    return True, "no direct route (" + "; ".join(reasons) + ")"


def check_env():
    names = sorted(n for n in os.environ if ENV_SECRET.search(n))
    exempt = [n for n in names if n in ENV_EXEMPT]
    names = [n for n in names if n not in ENV_EXEMPT]
    note = ("; set by the session or its sandbox, exempt: " + ", ".join(exempt)) if exempt else ""
    if names:
        return False, "credential-shaped variables reach the shell: " + ", ".join(names) + " (unset them, or deny them in sandbox.credentials.envVars)" + note
    return True, "no credential-shaped variable in the environment" + note


def opens(path):
    """Can a regular file be opened and read? Never blocks: FIFOs, sockets
    and devices are not opened."""
    try:
        st = os.stat(path)
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode):
        return False
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return False
    try:
        os.read(fd, 1)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def readable(path, known):
    """Can the shell read this path? A directory counts as readable when it
    lists, or when any of its usual files opens."""
    if os.path.isdir(path):
        try:
            os.listdir(path)
            return True
        except OSError:
            pass
        for name in known:
            child = os.path.join(path, name)
            if os.path.isdir(child):
                try:
                    os.listdir(child)
                    return True
                except OSError:
                    continue
            if opens(child):
                return True
        return False
    return opens(path)


def check_shell_secrets(secrets, settings, srt):
    entries = deny_read_entries(settings)
    if under_srt():
        entries = entries + srt_deny_read_entries(srt)
    unlisted = [s for s in secrets if not any(prefix_covers(e, expand(s)) for e in entries)]
    open_ = []
    for s in secrets:
        p = expand(s)
        if os.path.exists(p) and readable(p, KNOWN_FILES.get(s, []) + GENERIC_FILES):
            open_.append(s)
    problems = []
    if open_:
        problems.append("readable from the shell now: " + ", ".join(open_))
    if unlisted:
        where = ("the runtime's filesystem.denyRead (add them to its settings file outside the session and restart it)"
                 if under_srt() else "sandbox.filesystem.denyRead")
        problems.append(f"not in {where}: " + ", ".join(unlisted))
    if problems:
        return False, "; ".join(problems)
    present = sum(1 for s in secrets if os.path.exists(expand(s)))
    return True, f"{len(secrets)} paths denied in settings, {present} present and unreadable from the shell"


def check_read_rules(secrets, settings, srt):
    rules = read_rules(settings)
    srt_entries = srt_deny_read_entries(srt) if under_srt() else []
    uncovered, by_runtime = [], 0
    for s in secrets:
        is_dir = is_dir_secret(s)
        if any(read_rule_covers(r, expand(s), is_dir) for r in rules):
            continue
        if any(prefix_covers(e, expand(s)) for e in srt_entries):
            by_runtime += 1  # the Read tool runs inside the runtime's boundary
            continue
        uncovered.append(rule_for(s))
    if uncovered:
        hint = (" (permissions.deny, or the runtime's filesystem.denyRead, which fences the Read tool too)" if under_srt()
                else " (permissions.deny; a directory needs the /** form)")
        return False, "no Read(...) deny rule reaches: " + ", ".join(uncovered) + hint
    if by_runtime:
        return True, f"{len(secrets)} paths covered: {len(secrets) - by_runtime} by a Read(...) deny rule, {by_runtime} by the runtime's denyRead"
    return True, f"{len(secrets)} paths each covered by a Read(...) deny rule"


def check_settings(settings):
    if under_srt():
        return True, "the sandbox runtime fences the whole session; Claude's own sandbox keys are optional inside it, and an unsandboxed retry cannot leave it (Bash approvals are the permission mode's)"
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
    """Gitignore's matching, as far as include patterns need it: `**/x`
    matches x at any depth including the root; `x/**` everything under x;
    a pattern with a slash is anchored at the root; one without matches
    any single component; `*` and `?` stay inside a component."""
    pattern = pattern.strip()
    if not pattern or pattern.startswith("#") or pattern.startswith("!"):
        return False  # a comment, or an exclusion, copies nothing
    pattern = pattern.rstrip("/")
    anchored = "/" in pattern
    if pattern.startswith("/"):
        pattern = pattern[1:]
    if pattern.startswith("**/"):
        tail = pattern[3:]
        candidates = [path] + [path.split("/", i)[-1] for i in range(1, path.count("/") + 1)]
        return any(gitignore_match(tail, c) for c in candidates)
    if anchored:
        return bool(glob_regex(pattern).match(path)) or bool(glob_regex(pattern + "/**").match(path))
    rx = glob_regex(pattern)
    return any(rx.match(part) for part in path.split("/"))


def looks_like_credential(path):
    parts = path.split("/")
    if any(p in CREDENTIAL_DIRS for p in parts[:-1]):
        return True
    return any(fnmatch.fnmatch(parts[-1], n) for n in CREDENTIAL_NAMES)


def check_worktreeinclude(project):
    path = os.path.join(project, ".worktreeinclude")
    if not os.path.isfile(path):
        return True, "no .worktreeinclude"
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            patterns = [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    except OSError as e:
        return False, f".worktreeinclude unreadable: {e}"
    proc = subprocess.run([find_git(), "ls-files", "-oi", "--exclude-standard"], cwd=project,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return False, f"cannot list the project's ignored files to see what .worktreeinclude copies: {proc.stderr.strip()}"
    ignored = [l for l in proc.stdout.splitlines() if l]
    copied = [f for f in ignored if any(gitignore_match(p, f) for p in patterns)]
    secret = [f for f in copied if looks_like_credential(f)]
    if secret:
        return False, ".worktreeinclude copies credential-shaped files into every worktree: " + ", ".join(secret)
    return True, f".worktreeinclude copies {len(copied)} ignored file(s), none credential-shaped"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="the project root (the real tree, not a worktree)")
    p.add_argument("--secret", action="append", default=[],
                   help="another path that must be unreadable (repeatable; `~` allowed; end a directory with `/`)")
    p.add_argument("--write-settings", nargs="?", const="", metavar="FILE",
                   help="merge the required sandbox and deny settings into the session's user settings file first (FILE overrides the path)")
    p.add_argument("--srt-settings", metavar="FILE",
                   help="the sandbox runtime's settings file when the session was launched with `srt --settings FILE` (default ~/.srt-settings.json)")
    a = p.parse_args()
    project = os.path.realpath(a.project)
    if not os.path.isdir(project):
        print(f"FAIL  project: {a.project} is not a directory\nsandbox check: FAIL")
        return 1
    secrets = secret_list(a.secret)

    if a.write_settings is not None:
        target = a.write_settings or user_settings_path()
        has_sandbox = check_platform()[0]
        changed, error, content = write_settings(target, secrets, deny_only=not has_sandbox)
        shown = os.path.realpath(os.path.expanduser(target))
        scope = ("" if has_sandbox else
                 " (deny rules only: this platform has no sandbox backend, so sandbox.enabled and failIfUnavailable are left alone)")
        if error and content is None:
            print(f"settings not written: {error}")
        elif error:
            print(f"settings not written{scope}: {error}")
            print(f"--- intended content of {shown}, for the Write tool (it runs outside the sandbox) ---")
            print(content, end="")
            print("--- end of intended content ---")
        elif changed:
            print(f"settings written{scope}: {shown}")
            for c in changed:
                print("  " + c)
            if has_sandbox:
                print("  (a sandbox setting takes effect in the session's next Bash command; if the probes below still fail, restart the session)")
        else:
            print(f"settings already complete{scope}: {shown}")

    settings, read, broken = load_settings(project)
    srt, srt_note = (load_srt_settings(srt_settings_path(a.srt_settings)) if under_srt() else ({}, None))
    results = [
        ("platform", *platform_line()),
        ("write", *check_write(project, settings, srt)),
        ("network", *check_network()),
        ("env", *check_env()),
        ("shell-secrets", *check_shell_secrets(secrets, settings, srt)),
        ("read-secrets", *check_read_rules(secrets, settings, srt)),
        ("settings", *check_settings(settings)),
        ("worktreeinclude", *check_worktreeinclude(project)),
    ]
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    allowed = get(settings, "sandbox", "network", "allowedDomains", default=[]) or []
    if under_srt():
        allowed = allowed + [f"{d} (runtime)" for d in (get(srt, "network", "allowedDomains", default=[]) or [])]
    print("network allowlist:", ", ".join(map(str, allowed)) if allowed else "none")
    print("settings read:", ", ".join(read) if read else "none found")
    if srt_note is not None:
        print("sandbox runtime settings:", srt_note)
    for b in broken:
        print("settings skipped:", b)
    passed = all(ok for _, ok, _ in results)
    print("sandbox check:", "PASS" if passed else "FAIL")
    if passed:
        return 0
    return NO_SANDBOX if not results[0][1] else 1


if __name__ == "__main__":
    sys.exit(main())
