#!/usr/bin/env python3
"""Copy one slice's audit material into the audit repository's clone, commit, push.

The last step of the orchestrator's chunk loop (its step E) when audit mode
has a repository configured: `KAD_AUDIT=1` with `KAD_AUDIT_REPO` set, which
makes the plugin's SessionStart hook clone that repository into the
project's `audit-docs/` (listed in the project's `.git/info/exclude`, never
in its `.gitignore` or history). This script fills it, under the layout the
first slice established by hand on 2026-10-24:

    audit-docs/<project>-slice-<n>/
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
        transcripts/<session>/       only with --transcripts: the sessions
                                     audit mode kept whose log mentions this
                                     project (a session's transcript is kept
                                     at its end, so the current one is not
                                     there yet)
      sync-log.md                    one line per sync: when, from which
                                     project commit, what was copied

Before copying anything it reads every file it would copy for
credential-shaped strings (cloud and hosting tokens, private keys, Plaid
access tokens, JWTs, `secret=`/`token=`/`password=` assignments) and
refuses on the first hit, listing them with the matched text masked;
`--allow <path fragment>` skips the scan for a file a human has read and
cleared (a test fixture with an invented token, say), and the sync log
records that it was allowed. Files named `.env*` are never copied.

Usage:
  python3 -I audit_sync.py --project <root> --slice <n> [--docs <dir>]
      [--name <project name>] [--audit-dir <dir>] [--transcripts]
      [--allow <fragment>]... [--no-push] [--dry-run]

Exit codes: 0 synced (or nothing had changed); 1 usage or a missing input;
3 a credential-shaped string was found and nothing was copied; 4 git
failed in the clone (the copy stays, the commit or push did not happen).
The last line of output names the audit commit (`audit commit <sha>`), or
`audit commit none` when there was nothing new; the orchestrator's E line
records it.
"""
from __future__ import annotations

import argparse
import datetime as dt
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
    ("secret-like assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|client_secret|access[_-]?token|auth[_-]?token|password|passwd)\b"
        r"\s*[:=]\s*[\"']?(?!<|\$\{|\$[A-Z_]|\*{3}|x{6}|your[-_]|example|placeholder|redacted|changeme)"
        r"[A-Za-z0-9/_+=\-]{16,}[\"']?")),
]


def say(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str, code: int) -> int:
    print(f"audit_sync: {msg}", file=sys.stderr, flush=True)
    return code


def run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=check)


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
    ap.add_argument("--project", required=True, help="the project's root (its git work tree)")
    ap.add_argument("--slice", required=True, type=int, help="the slice number, as in slice-<nnn>")
    ap.add_argument("--docs", help="the orchestrator's target directory; default: the one holding orchestrator-log.md")
    ap.add_argument("--name", help="the project's name in the audit repository; default: the root's basename")
    ap.add_argument("--audit-dir", default=os.environ.get("KAD_AUDIT_DIR") or str(Path.home() / ".claude" / "kad-audit"))
    ap.add_argument("--transcripts", action="store_true", help="also copy the kept session transcripts that mention this project")
    ap.add_argument("--allow", action="append", default=[], metavar="FRAGMENT",
                    help="skip the credential scan for files whose path contains this (a reviewed fixture)")
    ap.add_argument("--no-push", action="store_true", help="commit in the clone but do not push")
    ap.add_argument("--dry-run", action="store_true", help="list what would be copied and scanned; change nothing")
    a = ap.parse_args(argv)

    project = Path(a.project).resolve()
    if not (project / ".git").exists():
        return fail(f"{project} is not a git work tree", 1)
    clone = project / "audit-docs"
    if not (clone / ".git").exists():
        return fail(f"{clone} is not a clone of the audit repository; set KAD_AUDIT_REPO and start a session, or clone it there yourself", 1)
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
    transcripts_taken: list[str] = []
    if a.transcripts:
        sessions = Path(a.audit_dir) / "sessions"
        needle = str(project).replace("\\", "/").lower()
        for log in sorted(sessions.glob("*.jsonl")) if sessions.is_dir() else []:
            try:
                body = log.read_text(encoding="utf-8", errors="replace").replace("\\\\", "/").replace("\\", "/").lower()
            except OSError:
                continue
            if needle not in body:
                continue
            sid = log.stem
            dest = slice_dir / "implementation-docs" / "transcripts" / sid
            plan.append((log, dest / "calls.jsonl"))
            t = Path(a.audit_dir) / "transcripts" / f"{sid}.jsonl"
            if t.exists():
                plan.append((t, dest / f"{sid}.jsonl"))
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
        say("audit commit none")
        return 3

    say(f"audit_sync: {len(kept)} files for {slice_dir.relative_to(clone).as_posix()}/ "
        f"(planning from {docs}, {'map, ' if maps else 'no map, '}"
        f"{'reviews from ' + ', '.join(str(r) for r in review_dirs) if review_dirs else 'no reviews directory'}"
        f"{', transcripts: ' + ', '.join(transcripts_taken) if transcripts_taken else ''})")
    for s in skipped:
        say(f"  skipped {s}")
    for p in allowed:
        say(f"  scan skipped by --allow: {p}")
    if a.dry_run:
        say("audit commit none")
        return 0

    # 3. Copy (the slice folder is rebuilt from the sources so a removed review doesn't linger).
    for sub in ("planning", "implementation-docs"):
        if (slice_dir / sub).exists():
            shutil.rmtree(slice_dir / sub)
    for src, dest in kept:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    head = run_git(project, "rev-parse", "--short", "HEAD", check=False).stdout.strip() or "unknown"
    branch = run_git(project, "rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip() or "unknown"

    # Belt and braces: the clone must never show up in the project's git.
    common = run_git(project, "rev-parse", "--git-common-dir", check=False).stdout.strip()
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
            say("audit_sync: nothing changed since the last sync")
            say("audit commit none")
            return 0
        # Something did change: record the sync in the slice's log, then commit both.
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        line = (f"- {stamp}: {len(kept)} files from `{branch}` at {head}; "
                f"{len(review_dirs)} reviews dir(s), {len(transcripts_taken)} transcript session(s)"
                f"{'; scan skipped by --allow for ' + ', '.join(p.name for p in allowed) if allowed else ''}"
                f"{'; skipped ' + str(len(skipped)) + ' file(s)' if skipped else ''}\n")
        sync_log = slice_dir / "sync-log.md"
        if not sync_log.exists():
            sync_log.write_text(f"# Sync log: {name} slice {a.slice}\n\nWritten by the plugin's `audit_sync.py`, one line per sync.\n\n", encoding="utf-8")
        with sync_log.open("a", encoding="utf-8") as fh:
            fh.write(line)
        run_git(clone, "add", "--", f"{rel}/sync-log.md")
        run_git(clone, "commit", "-q", "-m", f"{name} slice {a.slice}: sync from {branch} at {head}")
        sha = run_git(clone, "rev-parse", "--short", "HEAD").stdout.strip()
        if not a.no_push:
            run_git(clone, "push", "-q")
            say(f"audit_sync: committed and pushed {sha}")
        else:
            say(f"audit_sync: committed {sha}, not pushed (--no-push)")
    except subprocess.CalledProcessError as e:
        say(f"audit_sync: git {' '.join(e.cmd[3:5])} failed in {clone}:")
        say((e.stderr or e.stdout or "").strip())
        say("audit commit none")
        return 4
    say(f"audit commit {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
