"""Start the app for a smoke run, a criteria walk or a stranger test with every data path inside a scratch folder.

Two of slice 2's smoke agents started the app on the owner's real ledger and
login Keychain (nothing changed, by luck and by checksum). This is the one
way an agent launched by the chunk loop starts the app: the data rule of
`handoff-slice2.md` P2.3, enforced before the first process runs.

    python3 -I scratch_run.py --scratch <dir> [--project <root>]
        [--env NAME=<path>]... [--keep] -- <command> [args...]

- The scratch folder is created (it may already exist; it must be outside
  the project and outside the user's real data). `HOME`, `TMPDIR`,
  `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME` and `XDG_STATE_HOME`
  are pointed inside it, so anything the app resolves from the home
  directory (a Keychain file path, a config directory, a cache) lands
  there. The real `HOME` is kept as `SCRATCH_RUN_REAL_HOME` for the one
  thing that needs it: `PATH` is left alone.
- Each `--env NAME=<path>` sets `NAME` to `<path>` resolved **inside the
  scratch folder**: a relative path is joined to it; an absolute path must
  already be under it. A path that resolves outside, or that is a symlink
  pointing outside, refuses the start: exit 3, the offending variable
  named, no process run. The same check runs over the command's own
  arguments: an argument that is an absolute path under the real home
  directory and not under the scratch folder or the project refuses the
  start, so `--ledger ~/Library/Application Support/…` cannot slip past
  as an argument. Everything the app may write is therefore inside the
  scratch folder.
- The command runs with the scratch environment, replacing this process
  (`exec`), so a background start from Bash keeps one process to stop and
  its exit code is the app's. Nothing is printed before the exec but the
  one line `scratch run: <dir>; HOME inside; <n> path(s) checked`.
- `--hash <dir>` (alone) prints one line, `data <dir>: <sha256> over <n>
  files`, a digest of every regular file under <dir> by relative path, size
  and content, for the orchestrator's before-and-after check around a
  launch (the agent never opens the owner's data directory; the
  orchestrator hashes it before the launch and after, and the C or D line
  carries `data unchanged` or `data CHANGED`). A directory that does not
  exist hashes as `absent`.
- `--clean <dir>` (alone) removes the scratch folder when it is the one
  this script would have created there (it holds the `.scratch-run` marker
  this script writes), and refuses anything else: exit 3.

Exit codes: 0 after `--hash` or `--clean`; the command's own code after a
run; 2 for a usage error; 3 for a refused start or a refused clean.
"""
import argparse
import hashlib
import os
import shutil
import sys

MARKER = ".scratch-run"
SCRATCH_ENV = ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME")


def real(path):
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


def inside(path, root):
    path, root = real(path), real(root)
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def hash_dir(root):
    if not os.path.isdir(root):
        return "absent", 0
    h, n = hashlib.sha256(), 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            h.update(rel.encode("utf-8", "replace") + b"\0")
            h.update(str(os.path.getsize(full)).encode() + b"\0")
            with open(full, "rb") as f:
                for block in iter(lambda: f.read(1 << 16), b""):
                    h.update(block)
            n += 1
    return h.hexdigest()[:16], n


def main(argv=None):
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--scratch", help="the scratch folder every data path must be inside")
    p.add_argument("--project", default=os.getcwd(), help="the project root (its paths are allowed as command arguments)")
    p.add_argument("--env", action="append", default=[], metavar="NAME=PATH", help="a data path variable, resolved inside the scratch folder")
    p.add_argument("--keep", action="store_true", help="(information only) the agent deletes the folder itself after the run")
    p.add_argument("--hash", metavar="DIR", help="print a digest of the files under DIR and exit")
    p.add_argument("--clean", metavar="DIR", help="remove a scratch folder this script created and exit")
    p.add_argument("command", nargs=argparse.REMAINDER, help="-- the command to start")
    a = p.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if a.hash:
        digest, n = hash_dir(a.hash)
        print(f"data {a.hash}: {digest} over {n} files")
        return 0
    if a.clean:
        target = real(a.clean)
        if not os.path.isdir(target) or not os.path.isfile(os.path.join(target, MARKER)):
            print(f"scratch run: refused to remove {a.clean}: not a folder this script created")
            return 3
        shutil.rmtree(target, ignore_errors=True)
        print(f"scratch run: removed {a.clean}")
        return 0

    command = [c for c in a.command if c != "--"] if a.command and a.command[0] == "--" else a.command
    if not a.scratch or not command:
        p.print_usage()
        print("scratch run: --scratch <dir> and a command after -- are required (or --hash / --clean)")
        return 2
    scratch = real(a.scratch)
    real_home = os.path.expanduser("~")
    project = real(a.project)
    if inside(scratch, project):
        print(f"scratch run: refused: the scratch folder {a.scratch} is inside the project")
        return 3
    if scratch == real(real_home):
        print("scratch run: refused: the scratch folder is the home directory itself")
        return 3
    os.makedirs(scratch, exist_ok=True)
    with open(os.path.join(scratch, MARKER), "w", encoding="utf-8") as f:
        f.write("created by scratch_run.py; safe to delete\n")
    env = dict(os.environ)
    env["SCRATCH_RUN_REAL_HOME"] = real_home
    env["HOME"] = scratch
    for name in SCRATCH_ENV[1:]:
        sub = os.path.join(scratch, name.lower().replace("xdg_", "").replace("_home", "") if name != "TMPDIR" else "tmp")
        os.makedirs(sub, exist_ok=True)
        env[name] = sub
    checked = 0
    for spec in a.env:
        name, sep, value = spec.partition("=")
        if not sep or not name:
            print(f"scratch run: --env needs NAME=PATH, got {spec!r}")
            return 2
        resolved = value if os.path.isabs(os.path.expanduser(value)) else os.path.join(scratch, value)
        if not inside(resolved, scratch):
            print(f"scratch run: refused: {name} resolves outside the scratch folder")
            return 3
        env[name] = os.path.abspath(os.path.expanduser(resolved))
        os.makedirs(os.path.dirname(env[name]), exist_ok=True)
        checked += 1
    for arg in command[1:]:
        candidate = arg.split("=", 1)[1] if arg.startswith("--") and "=" in arg else arg
        if os.path.isabs(os.path.expanduser(candidate)) and inside(candidate, real_home) \
                and not inside(candidate, scratch) and not inside(candidate, project):
            print("scratch run: refused: a command argument names a path under the home directory outside the scratch folder")
            return 3
        checked += 1
    print(f"scratch run: {scratch}; HOME inside; {checked} path(s) checked", flush=True)
    program = shutil.which(command[0], path=env.get("PATH")) or command[0]
    try:
        os.execvpe(program, command, env)  # the app replaces this process; the operator's own command
    except OSError as e:
        print(f"scratch run: cannot start {command[0]}: {e.strerror}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
