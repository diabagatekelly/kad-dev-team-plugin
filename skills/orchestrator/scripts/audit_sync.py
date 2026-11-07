#!/usr/bin/env python3
"""Copy one slice's audit material into the audit repository's clone, commit, push.

Run by the orchestrator's chunk loop after every records commit (each
chunk's, the slice review's, the delivery's) when audit mode has a
repository configured: `KAD_AUDIT=1` with `KAD_AUDIT_REPO` set. The clone
lives at `$KAD_AUDIT_DIR/repo/` (the launcher clones it there before the
sandbox runtime starts, since inside the fence git cannot write a
`.git/config` anywhere; the SessionStart hook clones there for a session
the launcher did not start). `--clone <dir>` names another one; without
it, the project's own `audit-docs/` is still accepted when it holds a
clone (the location before 2026-11-02). Each sync copies the whole slice
folder, so a sync that a crash skipped is covered by the next one. This
script fills the clone under the layout the first slice established by
hand on 2026-10-24:

    <clone>/<project>-slice-<n>/
      planning/                      every file in the orchestrator's target
                                     directory (the planning documents, the
                                     orchestrator log, the implementation
                                     report, visual-ux/ if any)
      implementation-docs/
        architecture-map.md          the project's docs/architecture-map.md
        reviews-slice-<nnn>/         the reviewer reports and the fix-round
                                     sidecar rounds-slice-<nnn>.jsonl, from
                                     $KAD_AUDIT_DIR/reviews/slice-<nnn>/ or
                                     <project>/.git/kad-audit/reviews/slice-<nnn>/
        transcripts/<session>/       only with --transcripts: every session
                                     whose audit log ran in this project,
                                     its log as calls.jsonl, and its
                                     transcript and subagents' when audit
                                     mode kept them (snapshotted by
                                     `hooks/audit.sh --snapshot` at A, after
                                     each records commit and at session end);
                                     the sync-log line counts the two apart
      sync-log.md                    one line per sync: when, from which
                                     project commit, what was copied

Before copying anything it reads every file it would copy for
credential-shaped strings (cloud and hosting tokens, private keys, Plaid
access tokens, JWTs, `secret=`/`token=`/`password=` assignments) and
refuses on the first hit, listing them with the matched text masked;
`--allow <path fragment>` skips the scan for a file a human has read and
cleared (a test fixture with an invented token, say), and the sync log
records that it was allowed. Files named `.env*` are never copied.

The clone commits under the project's `user.name` and `user.email` when
the project sets them (a noreply address, where GitHub's email privacy
would otherwise refuse the push), and fast-forwards from its remote before
copying, so a clone another machine pushed to is not left behind.

Usage:
  python3 -I audit_sync.py --project <root> --slice <n> [--docs <dir>]
      [--name <project name>] [--audit-dir <dir>] [--clone <dir>] [--transcripts]
      [--allow <fragment>]... [--no-push] [--dry-run]
  python3 -I audit_sync.py --check [--audit-dir <dir>] [--clone <dir>] [--session <id>]

`--check` (the orchestrator's A step) prints one line and changes nothing:
`audit: not configured` when `KAD_AUDIT_REPO` is unset (exit 0);
`audit clone: <dir>` when a usable clone is there whose origin is that
repository (exit 0); otherwise `audit clone FAILED: <why>` (exit 1): a
clone pointing at another repository (the configured one changed since),
or none, with git's own message when the session's audit log
(`$KAD_AUDIT_DIR/sessions/<id>.jsonl`, the id from `--session` or
`CLAUDE_CODE_SESSION_ID`) recorded a failed clone. The sync applies the
same two refusals, and a third: a clone whose origin is the project's own
repository is never pushed to.

`--snapshot` first runs `hooks/audit.sh --snapshot` (this session's
transcript and its subagents' into the audit directory, so `--transcripts`
carries them), prints its line, and goes on to the sync whatever it said;
a failed snapshot is appended to the last line (`…; snapshot FAILED:
<why>`), so the log line carries both.

Exit codes: 0 synced (or nothing had changed); 1 usage or a missing input;
3 a credential-shaped string was found and nothing was copied; 4 git
failed in the clone (a fast-forward refused before anything was copied,
or the commit or push after; the copy stays).
The last line of output names the audit commit (`audit commit <sha>`),
`audit commit none` when there was nothing new, or `audit sync FAILED:
<reason>` on any failure; the orchestrator's line records it as it is.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "audit-docs", "dist", "build", ".next", "coverage", "__pycache__", ".venv", "venv"}
MAX_FILE_BYTES = 50 * 1024 * 1024  # GitHub refuses files over 100 MB; stop well short

# Each pattern names what it catches, for the refusal message.
CREDENTIAL_PATTERNS = [
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("Anthropic or OpenAI-style key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b")),
    ("Stripe key", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Plaid access or public token", re.compile(r"\b(?:access|public)-(?:sandbox|development|production)-[0-9a-f-]{36}\b")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("bearer token", re.compile(r"(?i)\bauthorization\b\s*[:=]\s*[\"']?bearer\s+(?!\$|<|\{|\*{3}|x{6}|your[-_]|example|placeholder|redacted)[A-Za-z0-9._~+/=-]{20,}")),
    ("secret-like assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|client_secret|access[_-]?token|auth[_-]?token|password|passwd)\b"
        r"\s*[:=]\s*[\"']?(?!<|\$\{|\$[A-Z_]|\*{3}|x{6}|your[-_]|example|placeholder|redacted|changeme)"
        r"[A-Za-z0-9/_+=\-]{16,}[\"']?")),
]


def say(msg: str) -> None:
    print(msg, flush=True)


SNAPSHOT_NOTE = ""  # "; snapshot FAILED: <why>" once a --snapshot has failed, appended to the last line


def last(msg: str) -> None:
    say(msg + SNAPSHOT_NOTE)


def fail(msg: str, code: int) -> int:
    print(f"audit_sync: {msg}", file=sys.stderr, flush=True)
    last(f"audit sync FAILED: {msg}")
    return code


def norm_url(url: str) -> str:
    """One form for a repository URL, so two spellings of one repository compare
    equal: no userinfo, no .git, no trailing slash, the ssh form as https."""
    u = re.sub(r"(://)[^/@\s]+@", r"\1", url.strip())
    u = re.sub(r"^git@([^:]+):", r"https://\1/", u)
    u = re.sub(r"\.git$", "", u).rstrip("/")
    return u.lower()


def origin_of(repo: Path) -> str:
    return run_git(repo, "remote", "get-url", "origin", check=False).stdout.strip()


def run_snapshot() -> str:
    """hooks/audit.sh --snapshot, from the plugin this script ships in; its one line."""
    hook = Path(__file__).resolve().parents[3] / "hooks" / "audit.sh"
    if not hook.is_file():
        return f"snapshot FAILED: {hook} is not there"
    try:
        r = subprocess.run(["bash", str(hook), "--snapshot"], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"snapshot FAILED: {e}"
    line = (r.stdout.strip().splitlines() or [""])[-1]
    return line or f"snapshot FAILED: no output (exit {r.returncode})"


def default_clone(audit_dir: str, project: Path | None) -> Path:
    """The clone's location: under the audit directory, else the project's
    own audit-docs/ when that still holds one (the location before 2026-11-02)."""
    primary = Path(audit_dir) / "repo"
    if (primary / ".git").exists() or project is None:
        return primary
    legacy = project / "audit-docs"
    return legacy if (legacy / ".git").exists() else primary


def clone_failure_recorded(audit_dir: str, session: str | None) -> str | None:
    """What the SessionStart hook recorded about its clone attempt, if anything."""
    if not session:
        return None
    log = Path(audit_dir) / "sessions" / f"{session}.jsonl"
    try:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        if '"kad_audit_clone"' not in line:
            continue
        try:
            p = json.loads(line).get("payload", {})
        except ValueError:
            continue
        if p.get("kad_audit_clone") == "failed":
            return p.get("error") or "git clone failed with no message"
        return None
    return None


def check(a) -> int:
    if not os.environ.get("KAD_AUDIT_REPO"):
        say("audit: not configured")
        return 0
    project = Path(a.project).resolve() if a.project else None
    clone = Path(a.clone).resolve() if a.clone else default_clone(a.audit_dir, project)
    if (clone / ".git").exists():
        origin = origin_of(clone)
        if norm_url(origin) != norm_url(os.environ["KAD_AUDIT_REPO"]):
            say(f"audit clone FAILED: the clone at {clone} points at {redact(origin) or 'no origin'}, not KAD_AUDIT_REPO ({redact(os.environ['KAD_AUDIT_REPO'])}); remove it, or point KAD_AUDIT_REPO back")
            return 1
        say(f"audit clone: {clone}" + (f" (origin {redact(origin)})" if origin else ""))
        return 0
    recorded = clone_failure_recorded(a.audit_dir, a.session or os.environ.get("CLAUDE_CODE_SESSION_ID"))
    why = f"git said: {recorded}" if recorded else "no clone and no record of an attempt (was the session started by bin/kad?)"
    say(f"audit clone FAILED: nothing at {clone}; {why}")
    return 1


def redact(url: str) -> str:
    return re.sub(r"(://)[^/@\s]+@", r"\1<redacted>@", url)


def identity(project: Path) -> list[str]:
    """`-c user.name=… -c user.email=…` from the project's git config, when set:
    the clone's commits carry the project's identity, never the machine's."""
    out: list[str] = []
    for key in ("user.name", "user.email"):
        v = run_git(project, "config", "--get", key, check=False).stdout.strip()
        if v:
            out += ["-c", f"{key}={v}"]
    return out


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


def run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([find_git(), "-C", str(cwd), *args], capture_output=True, text=True, check=check)


def find_one(root: Path, name: str) -> list[Path]:
    hits: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if name in filenames:
            hits.append(Path(dirpath) / name)
    return hits


def files_under(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for f in sorted(filenames):
            out.append(Path(dirpath) / f)
    return out


def mask(s: str) -> str:
    return s[:6] + "..." + s[-3:] if len(s) > 12 else "..."


def scan(path: Path) -> list[str]:
    """Credential-shaped strings in one text file, as 'line: kind: masked' entries."""
    try:
        data = path.read_bytes()
    except OSError as e:
        return [f"unreadable: {e}"]
    if b"\x00" in data[:8192]:
        return []  # binary: nothing to read as text, and no token survives being read as one
    text = data.decode("utf-8", errors="replace")
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, rx in CREDENTIAL_PATTERNS:
            m = rx.search(line)
            if m:
                hits.append(f"{lineno}: {kind}: {mask(m.group(0))}")
                break
    return hits


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", help="the project's root (its git work tree)")
    ap.add_argument("--slice", type=int, help="the slice number, as in slice-<nnn>")
    ap.add_argument("--clone", help="the audit repository's clone; default: $KAD_AUDIT_DIR/repo, else the project's audit-docs/ when it holds one")
    ap.add_argument("--check", action="store_true", help="report whether a usable clone exists and change nothing")
    ap.add_argument("--session", help="with --check: the session whose audit log may hold the clone's failure (default: CLAUDE_CODE_SESSION_ID)")
    ap.add_argument("--snapshot", action="store_true", help="first run hooks/audit.sh --snapshot for this session; a failure is appended to the last line")
    ap.add_argument("--docs", help="the orchestrator's target directory; default: the one holding orchestrator-log.md")
    ap.add_argument("--name", help="the project's name in the audit repository; default: the root's basename")
    ap.add_argument("--audit-dir", default=os.environ.get("KAD_AUDIT_DIR") or str(Path.home() / ".claude" / "kad-audit"))
    ap.add_argument("--transcripts", action="store_true", help="also copy the kept session transcripts that mention this project")
    ap.add_argument("--allow", action="append", default=[], metavar="FRAGMENT",
                    help="skip the credential scan for files whose path contains this (a reviewed fixture)")
    ap.add_argument("--no-push", action="store_true", help="commit in the clone but do not push")
    ap.add_argument("--dry-run", action="store_true", help="list what would be copied and scanned; change nothing")
    a = ap.parse_args(argv)
    global SNAPSHOT_NOTE
    if a.check:
        return check(a)
    if not a.project or a.slice is None:
        return fail("--project and --slice are required (or --check)", 1)
    if a.snapshot:
        line = run_snapshot()
        say(line)
        if not line.startswith("snapshot:"):
            SNAPSHOT_NOTE = f"; {line}"

    project = Path(a.project).resolve()
    if not (project / ".git").exists():
        return fail(f"{project} is not a git work tree", 1)
    clone = Path(a.clone).resolve() if a.clone else default_clone(a.audit_dir, project)
    if not (clone / ".git").exists():
        return fail(f"no clone of the audit repository at {clone}; start the session with bin/kad (it clones before the fence), or clone it there yourself", 1)
    inside_project = clone == project / "audit-docs"
    clone_origin = origin_of(clone)
    configured = os.environ.get("KAD_AUDIT_REPO", "")
    if configured and norm_url(clone_origin) != norm_url(configured):
        return fail(f"the clone at {clone} points at {redact(clone_origin) or 'no origin'}, not KAD_AUDIT_REPO ({redact(configured)}); remove it, or point KAD_AUDIT_REPO back", 1)
    project_origin = origin_of(project)
    if project_origin and norm_url(clone_origin) == norm_url(project_origin):
        return fail(f"the clone's origin is this project's own repository ({redact(project_origin)}); the sync would push audit documents onto the project's default branch", 1)
    name = a.name or project.name
    slice_dir = clone / f"{name}-slice-{a.slice}"
    nnn = f"{a.slice:03d}"

    # 1. Sources.
    if a.docs:
        docs = Path(a.docs).resolve()
        if not docs.is_dir():
            return fail(f"--docs {docs} is not a directory", 1)
    else:
        logs = find_one(project, "orchestrator-log.md")
        if len(logs) != 1:
            where = ", ".join(str(p) for p in logs) or "none"
            return fail(f"expected exactly one orchestrator-log.md under {project}, found: {where}; pass --docs", 1)
        docs = logs[0].parent
    maps = [p for p in find_one(project, "architecture-map.md") if p.parent != docs]
    maps += [docs / "architecture-map.md"] if (docs / "architecture-map.md").exists() else []
    review_roots = [Path(a.audit_dir) / "reviews", project / ".git" / "kad-audit" / "reviews"]
    review_dirs = [r / d for r in review_roots for d in (f"slice-{nnn}", f"slice-{a.slice}") if (r / d).is_dir()]

    plan: list[tuple[Path, Path]] = []  # (source, destination)
    for src in files_under(docs):
        plan.append((src, slice_dir / "planning" / src.relative_to(docs)))
    for m in maps[:1]:
        plan.append((m, slice_dir / "implementation-docs" / "architecture-map.md"))
    for rd in review_dirs:
        for src in files_under(rd):
            plan.append((src, slice_dir / "implementation-docs" / f"reviews-slice-{nnn}" / src.relative_to(rd)))
    transcripts_taken: list[str] = []   # every session log copied (calls.jsonl)
    with_transcript: list[str] = []     # those whose transcript audit mode kept
    if a.transcripts:
        sessions = Path(a.audit_dir) / "sessions"
        # A session is this project's when a hook payload's cwd is the project
        # root or below it: the whole path, never a prefix of a sibling's
        # (`/x/app` is not `/x/app-2`) and never a mention in a prompt.
        root = str(project).replace("\\", "/").rstrip("/").lower()
        cwd_here = re.compile(r'"cwd"\s*:\s*"' + re.escape(root) + r'(?:/|")')
        for log in sorted(sessions.glob("*.jsonl")) if sessions.is_dir() else []:
            try:
                body = log.read_text(encoding="utf-8", errors="replace").replace("\\\\", "/").replace("\\", "/").lower()
            except OSError:
                continue
            if not cwd_here.search(body):
                continue
            sid = log.stem
            dest = slice_dir / "implementation-docs" / "transcripts" / sid
            plan.append((log, dest / "calls.jsonl"))
            t = Path(a.audit_dir) / "transcripts" / f"{sid}.jsonl"
            if t.exists():
                plan.append((t, dest / f"{sid}.jsonl"))
                with_transcript.append(sid)
            tdir = Path(a.audit_dir) / "transcripts" / sid
            if tdir.is_dir():
                for src in files_under(tdir):
                    plan.append((src, dest / sid / src.relative_to(tdir)))
            transcripts_taken.append(sid)

    skipped: list[str] = []
    kept: list[tuple[Path, Path]] = []
    for src, dest in plan:
        if src.name.startswith(".env"):
            skipped.append(f"{src} (an environment file is never copied)")
            continue
        try:
            size = src.stat().st_size
        except OSError as e:
            skipped.append(f"{src} ({e})")
            continue
        if size > MAX_FILE_BYTES:
            skipped.append(f"{src} ({size // (1024 * 1024)} MB, over the {MAX_FILE_BYTES // (1024 * 1024)} MB limit)")
            continue
        kept.append((src, dest))
    if not kept:
        return fail("nothing to copy: the target directory, map and reviews directory are all empty or missing", 1)

    # 2. The credential scan, over everything, before any copy.
    allowed: list[Path] = []
    findings: list[str] = []
    for src, _ in kept:
        posix = src.as_posix()
        if any(frag and frag in posix for frag in a.allow):
            allowed.append(src)
            continue
        for h in scan(src):
            findings.append(f"  {src}:{h}")
    if findings:
        say("audit_sync: refused, credential-shaped strings in what would be copied:")
        for f in findings[:50]:
            say(f)
        if len(findings) > 50:
            say(f"  … and {len(findings) - 50} more")
        say("Nothing was copied. Remove or redact them, or pass --allow <path fragment> for a file you have read and cleared.")
        last(f"audit sync FAILED: {len(findings)} credential-shaped string(s) in what would be copied; nothing copied")
        return 3

    say(f"audit_sync: {len(kept)} files for {slice_dir.relative_to(clone).as_posix()}/ "
        f"(planning from {docs}, {'map, ' if maps else 'no map, '}"
        f"{'reviews from ' + ', '.join(str(r) for r in review_dirs) if review_dirs else 'no reviews directory'}"
        f"{', sessions: ' + ', '.join(s if s in with_transcript else s + ' (calls only, no transcript kept)' for s in transcripts_taken) if transcripts_taken else ''})")
    for s in skipped:
        say(f"  skipped {s}")
    for p in allowed:
        say(f"  scan skipped by --allow: {p}")
    if a.dry_run:
        last("audit commit none")
        return 0

    # 3. Fast-forward the clone first (a sync from another machine, or a
    #    clone the launcher made days ago), then copy (the slice folder is
    #    rebuilt from the sources so a removed review doesn't linger).
    fetched = run_git(clone, "fetch", "-q", check=False)
    if fetched.returncode != 0:
        detail = redact((fetched.stderr or fetched.stdout).strip())
        return fail(f"the clone at {clone} could not fetch from its remote ({detail.splitlines()[-1] if detail else 'no message'}); nothing copied", 4)
    # A brand-new audit repository has no branch yet: nothing to fast-forward to.
    if run_git(clone, "rev-parse", "--verify", "-q", "@{u}", check=False).returncode == 0:
        ff = run_git(clone, "merge", "-q", "--ff-only", "@{u}", check=False)
        if ff.returncode != 0:
            detail = redact((ff.stderr or ff.stdout).strip())
            return fail(f"the clone at {clone} did not fast-forward from its remote ({detail.splitlines()[-1] if detail else 'no message'}); nothing copied", 4)
    for sub in ("planning", "implementation-docs"):
        if (slice_dir / sub).exists():
            shutil.rmtree(slice_dir / sub)
    for src, dest in kept:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    head = run_git(project, "rev-parse", "--short", "HEAD", check=False).stdout.strip() or "unknown"
    branch = run_git(project, "rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip() or "unknown"

    # Belt and braces, for a clone still inside the project: it must never
    # show up in the project's git.
    common = run_git(project, "rev-parse", "--git-common-dir", check=False).stdout.strip() if inside_project else ""
    if common:
        exclude = (project / common if not Path(common).is_absolute() else Path(common)) / "info" / "exclude"
        try:
            exclude.parent.mkdir(parents=True, exist_ok=True)
            if "audit-docs/" not in (exclude.read_text(encoding="utf-8") if exclude.exists() else "").splitlines():
                with exclude.open("a", encoding="utf-8") as fh:
                    fh.write("audit-docs/\n")
        except OSError:
            pass

    # 4. Commit and push in the clone.
    rel = slice_dir.relative_to(clone).as_posix()
    try:
        run_git(clone, "add", "-A", "--", rel)
        if not run_git(clone, "status", "--porcelain", "--", rel).stdout.strip():
            # An earlier sync may have committed and then failed to push: push it now.
            ahead = run_git(clone, "rev-list", "--count", "@{u}..HEAD", check=False).stdout.strip()
            if ahead.isdigit() and int(ahead) > 0 and not a.no_push:
                run_git(clone, "push", "-q")
                sha = run_git(clone, "rev-parse", "--short", "HEAD").stdout.strip()
                say(f"audit_sync: nothing changed since the last sync; pushed {ahead} earlier commit(s) that had not reached the remote")
                last(f"audit commit {sha}")
                return 0
            say("audit_sync: nothing changed since the last sync")
            last("audit commit none")
            return 0
        # Something did change: record the sync in the slice's log, then commit both.
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        line = (f"- {stamp}: {len(kept)} files from `{branch}` at {head}; "
                f"{len(review_dirs)} reviews dir(s), {len(transcripts_taken)} session log(s), {len(with_transcript)} with a transcript"
                f"{'; scan skipped by --allow for ' + ', '.join(p.name for p in allowed) if allowed else ''}"
                f"{'; skipped ' + str(len(skipped)) + ' file(s)' if skipped else ''}\n")
        sync_log = slice_dir / "sync-log.md"
        if not sync_log.exists():
            sync_log.write_text(f"# Sync log: {name} slice {a.slice}\n\nWritten by the plugin's `audit_sync.py`, one line per sync.\n\n", encoding="utf-8")
        with sync_log.open("a", encoding="utf-8") as fh:
            fh.write(line)
        run_git(clone, "add", "--", f"{rel}/sync-log.md")
        run_git(clone, *identity(project), "commit", "-q", "-m", f"{name} slice {a.slice}: sync from {branch} at {head}")
        sha = run_git(clone, "rev-parse", "--short", "HEAD").stdout.strip()
        if not a.no_push:
            run_git(clone, "push", "-q")
            say(f"audit_sync: committed and pushed {sha}")
        else:
            say(f"audit_sync: committed {sha}, not pushed (--no-push)")
    except subprocess.CalledProcessError as e:
        verb = next((w for w in e.cmd[3:] if not w.startswith("-") and "=" not in w), "command")
        detail = redact((e.stderr or e.stdout or "").strip())
        say(f"audit_sync: git {verb} failed in {clone}:")
        say(detail)
        tail = detail.splitlines()[-1] if detail else "no message"
        last(f"audit sync FAILED: git {verb} in {clone}: {tail}")
        return 4
    last(f"audit commit {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
