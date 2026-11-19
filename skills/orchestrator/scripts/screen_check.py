"""Did a screen change that the slice did not say it would change?

The screen-change check (C1, kad 0.16.0). Every state of the built app
that a scripted browser drives is captured as a PNG, on made-up data, in
one fixed environment (the project's CI); each capture is compared with
the baseline image committed beside the screen designs. A difference in a
state the slice's screen design lists as changed is expected and its
baseline is owed; a difference anywhere else is a finding. No model reads
a pixel.

This file is copied into a project by `ci-pipeline` (as
`tools/screen_check.py`) so the project's CI depends on nothing outside
its own repository; the plugin's own copy is the one the loop runs
locally. Python standard library only.

Where things are, under the planning directory (`--planning`):

  visual-ux/<state>.html                 a mockup; its file stem is the
                                         state's one name everywhere
  visual-ux/screen-*.md                  a screen design, with a section
                                         `## States this slice changes`
  visual-ux/baselines/<state>.png        the committed baseline
  visual-ux/baselines/screen-check.json  {"max_changed_percent": 0.1}, the
                                         owner's number; 0.1 when absent

The section holds one line per state, by name:

  - `hold-not-cancelled`: changed, the heading is larger
  - `queue-failure`: new
  - `hold-expired`: removed

**Listed** means a line the branch added: a state line of a screen design
at `HEAD` that the same file does not hold at the merge base with `--base`
(a file the base does not have lists all of its lines). So a later fix on
the same slice does not inherit the slice's list. Without `--base` every
line of every screen design is listed.

A pixel differs when its colour distance (YIQ, as pixelmatch computes it,
at pixelmatch's threshold 0.1) is over the limit and it is not an
anti-aliased pixel in either image (pixelmatch's test: a pixel on an edge
whose neighbours in both images are flat on one side). A state differs
when more than `max_changed_percent` of its pixels do, or the two images
are not the same size. Two sizes are compared over the part they share
(from the top-left corner); the pixels only one image has count as
changed, the state's line ends `; size <w>x<h> -> <w>x<h>`, and its
difference image is drawn at the size that holds both, those pixels in
blue.

    compare --planning DIR --captures DIR --out DIR [--base REF] [--head SHA]
        One line per state, then the verdict as the last line:
          screens: PASS (<n> states)                              exit 0
          screens: BASELINES OWED <c> changed, <n> new, <r> removed   exit 3
          screens: FAIL <k> not listed: <state>, ...              exit 1
          screens: FAIL <k> not captured: <state>, ...            exit 1
          screens: FAIL <k>: <i> not captured: <state>, ...; <j> not listed: <state>, ...
        (`not listed` for STRAY and UNLISTED states, `not captured` for
        MISSING ones, which may well be listed: the third form when the
        run has both)
        A state's line is one of
          same        within the threshold of its baseline
          changed     differs, and listed (as changed, or as new with a
                      first baseline already adopted): its baseline is owed
          new         captured, no baseline, and listed as new (or the
                      project has no baseline at all yet: first baselines)
          removed     listed as removed and not captured: its baseline goes
          STRAY       differs and is not listed            (a finding)
          UNLISTED    captured, no baseline, not listed    (a finding)
          MISSING     a baseline, a listed state, a state the capture
                      reported as failed (`capture-errors.json` in the
                      captures) or a state of the capture's own list
                      (`states.txt` beside the captures, one name a
                      line) with no capture                (a finding)
        A state that threw is MISSING whether or not it has a baseline:
        on a first run, with no baseline and no list in the screen
        design, it was simply absent, and the verdict was BASELINES
        OWED for the states that did capture.
        Writes `screen-check.txt` (the same lines), `screen-check.json`
        and `diff/<state>.png` for every state that differs (changed
        pixels red, anti-aliased ones yellow, the rest the baseline
        faded) into `--out`. FAIL outranks OWED: findings are fixed
        first, baselines adopted after.
    adopt --planning DIR --artifact DIR [--base REF]
        `DIR` is a downloaded CI artifact (its `captures/` and its
        `screen-check.json`). Compares again, here, with this checkout's
        list and baselines; on any finding copies nothing (exit 1).
        Otherwise copies the capture of every `changed` and `new` state
        over its baseline, deletes each `removed` one, prints each path
        and `adopted: <c> changed, <n> new, <r> removed` (exit 0). An
        artifact made for another commit than `HEAD` is refused (exit 2),
        unless `HEAD` only adds commits inside the planning directory to
        it (records, the log, a handoff: nothing a browser renders).
        It never copies a state that is not listed.
    states --planning DIR --capture FILE [--base REF]
        Which listed `changed` and `new` states the project's capture
        file does not drive (a state is driven when its name is a quoted
        key in the file: `'hold-cancelled': async (page) => { ... }`).
        `missing: <state>` per state, then `states: <n> listed, <m> not
        driven`; exit 1 when any is missing.
    check-section --planning DIR --screen FILE
        For the readiness gate: the section exists, each line names a
        state with a mockup, and a state listed as new has no baseline
        yet. One `problem: ...` line each; exit 1 on any.

Exit 2 on a usage or environment error (no planning directory, a base
that is not a commit, a PNG this reader does not support: 16-bit or
interlaced).

Usage: python3 -I screen_check.py compare --planning docs/x --captures out/captures --out out --base origin/main
"""
import argparse
import glob
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

DEFAULT_PERCENT = 0.1
PIXEL_THRESHOLD = 0.1  # pixelmatch's default
MAX_DELTA = 35215 * PIXEL_THRESHOLD * PIXEL_THRESHOLD
SECTION = re.compile(r"^#{2,3}\s+States this slice changes\s*$", re.I)
STATE_LINE = re.compile(r"^\s*[-*]\s+`?([a-z0-9][a-z0-9._-]*)`?\s*(?::|—|–|-)\s*\**(changed|new|removed)\b", re.I)
NONE_LINE = re.compile(r"^\s*(?:[-*]\s+)?none\b", re.I)


class Unsupported(Exception):
    pass


# ---------- PNG ----------

def read_png(path):
    """(width, height, RGBA bytes) of an 8-bit, non-interlaced PNG."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise Unsupported(f"{path}: not a PNG")
    pos, idat, palette, trns, header = 8, [], None, None, None
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
    if header is None:
        raise Unsupported(f"{path}: no IHDR")
    width, height, depth, colour, _, _, interlace = header
    if depth != 8 or interlace != 0 or colour not in (0, 2, 3, 4, 6):
        raise Unsupported(f"{path}: only 8-bit, non-interlaced PNGs are read (bit depth {depth}, colour type {colour}, interlace {interlace})")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colour]
    stride = width * channels
    raw = zlib.decompress(b"".join(idat))
    if len(raw) < height * (stride + 1):
        raise Unsupported(f"{path}: image data is short")
    rows, prev = [], bytes(stride)
    for y in range(height):
        start = y * (stride + 1)
        row = _unfilter(raw[start], raw[start + 1:start + 1 + stride], prev, channels)
        rows.append(row)
        prev = row
    flat = b"".join(rows)
    if colour == 6:
        return width, height, flat
    out = bytearray(width * height * 4)
    if colour == 2:
        out[0::4], out[1::4], out[2::4] = flat[0::3], flat[1::3], flat[2::3]
        out[3::4] = b"\xff" * (width * height)
    elif colour == 0:
        out[0::4] = out[1::4] = out[2::4] = flat
        out[3::4] = b"\xff" * (width * height)
    elif colour == 4:
        out[0::4] = out[1::4] = out[2::4] = flat[0::2]
        out[3::4] = flat[1::2]
    else:
        if palette is None:
            raise Unsupported(f"{path}: a palette image with no palette")
        alpha = (trns or b"") + b"\xff" * 256
        table = [bytes(palette[i * 3:i * 3 + 3]) + alpha[i:i + 1] for i in range(len(palette) // 3)]
        try:
            out = bytearray(b"".join(table[i] for i in flat))
        except IndexError:
            raise Unsupported(f"{path}: a palette index outside the palette")
    return width, height, bytes(out)


def _unfilter(kind, row, prev, bpp):
    if kind == 0:
        return bytes(row)
    if kind == 2:
        return bytes((a + b) & 255 for a, b in zip(row, prev))
    out = bytearray(row)
    n = len(out)
    if kind == 1:
        for i in range(bpp, n):
            out[i] = (out[i] + out[i - bpp]) & 255
    elif kind == 3:
        for i in range(n):
            left = out[i - bpp] if i >= bpp else 0
            out[i] = (out[i] + ((left + prev[i]) >> 1)) & 255
    elif kind == 4:
        for i in range(n):
            a = out[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            out[i] = (out[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
    else:
        raise Unsupported(f"PNG filter type {kind}")
    return bytes(out)


def write_png(path, width, height, rgb):
    """An 8-bit RGB PNG from `rgb` (3 bytes a pixel)."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    stride = width * 3
    raw = b"".join(b"\x00" + bytes(rgb[y * stride:(y + 1) * stride]) for y in range(height))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


# ---------- the comparison (pixelmatch's rules) ----------

def _blend(c, a):
    return 255 + (c - 255) * a


def _delta(a, i, b, j, y_only=False):
    r1, g1, b1, a1 = a[i], a[i + 1], a[i + 2], a[i + 3]
    r2, g2, b2, a2 = b[j], b[j + 1], b[j + 2], b[j + 3]
    if r1 == r2 and g1 == g2 and b1 == b2 and a1 == a2:
        return 0
    if a1 < 255:
        a1 /= 255
        r1, g1, b1 = _blend(r1, a1), _blend(g1, a1), _blend(b1, a1)
    if a2 < 255:
        a2 /= 255
        r2, g2, b2 = _blend(r2, a2), _blend(g2, a2), _blend(b2, a2)
    y1 = r1 * 0.29889531 + g1 * 0.58662247 + b1 * 0.11448223
    y2 = r2 * 0.29889531 + g2 * 0.58662247 + b2 * 0.11448223
    y = y1 - y2
    if y_only:
        return y
    i_ = (r1 * 0.59597799 - g1 * 0.27417610 - b1 * 0.32180189) - (r2 * 0.59597799 - g2 * 0.27417610 - b2 * 0.32180189)
    q = (r1 * 0.21147017 - g1 * 0.52261711 + b1 * 0.31114694) - (r2 * 0.21147017 - g2 * 0.52261711 + b2 * 0.31114694)
    d = 0.5053 * y * y + 0.299 * i_ * i_ + 0.1957 * q * q
    return -d if y1 > y2 else d


def _siblings(img, x1, y1, w, h):
    x0, y0, x2, y2 = max(x1 - 1, 0), max(y1 - 1, 0), min(x1 + 1, w - 1), min(y1 + 1, h - 1)
    pos = (y1 * w + x1) * 4
    centre = img[pos:pos + 4]
    zeroes = 1 if (x1 == x0 or x1 == x2 or y1 == y0 or y1 == y2) else 0
    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue
            p = (y * w + x) * 4
            if img[p:p + 4] == centre:
                zeroes += 1
            if zeroes > 2:
                return True
    return False


def _antialiased(img, x1, y1, w, h, other):
    x0, y0, x2, y2 = max(x1 - 1, 0), max(y1 - 1, 0), min(x1 + 1, w - 1), min(y1 + 1, h - 1)
    pos = (y1 * w + x1) * 4
    zeroes = 1 if (x1 == x0 or x1 == x2 or y1 == y0 or y1 == y2) else 0
    low = high = 0
    low_at = high_at = (0, 0)
    for x in range(x0, x2 + 1):
        for y in range(y0, y2 + 1):
            if x == x1 and y == y1:
                continue
            d = _delta(img, pos, img, (y * w + x) * 4, True)
            if d == 0:
                zeroes += 1
                if zeroes > 2:
                    return False
            elif d < low:
                low, low_at = d, (x, y)
            elif d > high:
                high, high_at = d, (x, y)
    if low == 0 or high == 0:
        return False
    return ((_siblings(img, low_at[0], low_at[1], w, h) and _siblings(other, low_at[0], low_at[1], w, h))
            or (_siblings(img, high_at[0], high_at[1], w, h) and _siblings(other, high_at[0], high_at[1], w, h)))


OUTSIDE = b"\x30\x60\xe0"  # a pixel only one of the two images has


def _crop(img, w, cw, ch):
    """The top-left `cw` by `ch` of an RGBA buffer `w` wide."""
    if cw == w:
        return img[:cw * ch * 4]
    return b"".join(img[y * w * 4:y * w * 4 + cw * 4] for y in range(ch))


def diff_images(base, shot, want_image=True):
    """(pixels that differ, anti-aliased pixels ignored, total pixels, RGB
    difference image or None). Two images of different sizes are compared
    over the part they share, from the top-left corner; every pixel only
    one of them has differs, the total is the size that holds both, and
    the difference image is drawn at that size with those pixels in blue.
    They used to "differ in full" with no image: a page one row taller
    read 100% in 27 of 28 states, and the check said nothing about what
    had changed in them."""
    w, h, a = base
    w2, h2, b = shot
    if (w, h) != (w2, h2):
        cw, ch, uw, uh = min(w, w2), min(h, h2), max(w, w2), max(h, h2)
        changed, ignored, _, shared = diff_images((cw, ch, _crop(a, w, cw, ch)), (cw, ch, _crop(b, w2, cw, ch)), want_image)
        image = None
        if want_image:
            if shared is None:  # nothing differs in the shared part: the baseline, faded
                faded = bytearray(cw * ch * 3)
                crop = _crop(a, w, cw, ch)
                for c in range(3):
                    faded[c::3] = bytes(255 - ((255 - v) >> 2) for v in crop[c::4])
                shared = bytes(faded)
            out = bytearray(OUTSIDE * (uw * uh))
            for y in range(ch):
                out[y * uw * 3:y * uw * 3 + cw * 3] = shared[y * cw * 3:(y + 1) * cw * 3]
            image = bytes(out)
        return changed + uw * uh - cw * ch, ignored, uw * uh, image
    changed = ignored = 0
    marks = {}
    if a != b:
        stride = w * 4
        for y in range(h):
            start = y * stride
            if a[start:start + stride] == b[start:start + stride]:
                continue
            for x in range(w):
                pos = start + x * 4
                if a[pos:pos + 4] == b[pos:pos + 4]:
                    continue
                if abs(_delta(a, pos, b, pos)) > MAX_DELTA:
                    if _antialiased(a, x, y, w, h, b) or _antialiased(b, x, y, w, h, a):
                        ignored += 1
                        marks[y * w + x] = b"\xf0\xc0\x30"
                    else:
                        changed += 1
                        marks[y * w + x] = b"\xe0\x20\x20"
    image = None
    if want_image and marks:
        out = bytearray(w * h * 3)
        # The baseline, faded towards white, so the marks stand out.
        for c in range(3):
            out[c::3] = bytes(255 - ((255 - v) >> 2) for v in a[c::4])
        for index, colour in marks.items():
            out[index * 3:index * 3 + 3] = colour
        image = bytes(out)
    return changed, ignored, w * h, image


# ---------- the project's files ----------

def git(cwd, *args):
    for exe in ("git", "/opt/homebrew/bin/git", "/usr/local/bin/git", "/usr/bin/git"):
        try:
            r = subprocess.run([exe, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        except OSError:
            continue
        if r.returncode == 0:
            return r.stdout
        if "xcrun" in r.stderr or "xcode" in r.stderr.lower():
            continue
        return None
    return None


def section_entries(text):
    """(has section, [(state, kind)], says none): the lines of `## States
    this slice changes`."""
    found, inside, entries, none = False, False, [], False
    for line in text.splitlines():
        if SECTION.match(line):
            found = inside = True
            continue
        if inside and re.match(r"^#{1,3}\s", line):
            inside = False
        if not inside:
            continue
        m = STATE_LINE.match(line)
        if m:
            entries.append((m.group(1).lower(), m.group(2).lower()))
        elif NONE_LINE.match(line):
            none = True
    return found, entries, none


def screen_designs(planning):
    pats = ("screen-*.md", os.path.join("visual-ux", "screen-*.md"))
    return sorted({p for pat in pats for p in glob.glob(os.path.join(glob.escape(planning), pat))})


def listed(planning, base):
    """{state: kind} for the lines the branch added, or an error string."""
    out = {}
    root = merge_base = None
    if base:
        top = git(planning, "rev-parse", "--show-toplevel")
        if top is None:
            return f"{planning} is not inside a git repository (needed for --base)"
        root = top.strip()
        mb = git(root, "merge-base", base, "HEAD")
        if mb is None:
            return f"--base {base} is not a commit this checkout has"
        merge_base = mb.strip()
    for path in screen_designs(planning):
        with open(path, encoding="utf-8", errors="replace") as f:
            _, entries, _ = section_entries(f.read())
        before = set()
        if merge_base:
            rel = os.path.relpath(os.path.realpath(path), os.path.realpath(root)).replace(os.sep, "/")
            old = git(root, "show", f"{merge_base}:{rel}")
            if old is not None:
                before = set(section_entries(old)[1])
        for name, kind in entries:
            if (name, kind) not in before:
                out[name] = kind
    return out


def threshold(planning):
    path = os.path.join(planning, "visual-ux", "baselines", "screen-check.json")
    if not os.path.isfile(path):
        return DEFAULT_PERCENT, f"no {os.path.relpath(path, planning)}: the default"
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f)["max_changed_percent"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 100:
            raise ValueError(value)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        raise Unsupported(f"{path}: needs {{\"max_changed_percent\": <a number from 0 to 100>}} ({e})")
    return float(value), "screen-check.json"


def _bytes(path):
    with open(path, "rb") as f:
        return f.read()


def pngs(directory):
    return {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(glob.escape(directory), "*.png"))}


def capture_errors(captures_dir):
    """{state: the first line of its error} from the `capture-errors.json`
    the capture writes when a state throws; {} when there is none. A file
    that cannot be read names no state and is said as one finding."""
    path = os.path.join(captures_dir, "capture-errors.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {str(k): (str(v).strip().splitlines() or [""])[0] for k, v in data.items()}
    except (OSError, ValueError, AttributeError):
        return {"capture-errors.json": "the capture's errors file could not be read"}


def expected_states(captures_dir):
    """The capture's own list of states (`node screens/capture.mjs --list`,
    written by the workflow to `states.txt` beside the captures or in
    them), or an empty set when there is none."""
    for path in (os.path.join(os.path.dirname(os.path.abspath(captures_dir)), "states.txt"),
                 os.path.join(captures_dir, "states.txt")):
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return {line.strip() for line in f if line.strip()}
            except OSError:
                # a list that is there and cannot be read is not "no list":
                # one row that no capture can meet, so the set is not judged whole
                return {"states.txt (not readable)"}
    return set()


def judge(planning, captures_dir, base, diff_dir=None, sizes=None):
    """([(state, status, percent, changed pixels, ignored pixels)], limit,
    where the limit came from), or an error string. `sizes`, when given,
    is filled with {state: ((w, h) of the baseline, (w, h) of the
    capture)} for every state whose two images are not the same size."""
    names = listed(planning, base)
    if isinstance(names, str):
        return names
    limit, source = threshold(planning)
    baselines = pngs(os.path.join(planning, "visual-ux", "baselines"))
    captures = pngs(captures_dir)
    first = not baselines
    # What the capture said it would produce or failed to: owed a capture
    # whatever the baselines and the screen design say.
    failed = set(capture_errors(captures_dir))
    owed = failed | expected_states(captures_dir)
    rows = []
    for state in sorted(set(baselines) | set(captures) | set(names) | owed):
        kind = names.get(state)
        has_base, has_shot = state in baselines, state in captures
        if state in failed or (state in owed and not has_shot):
            # a state the capture reported as failed is missing even with an
            # image under its name: the image is an earlier run's
            rows.append((state, "MISSING", 100.0, 0, 0))
        elif has_base and has_shot:
            if _bytes(baselines[state]) == _bytes(captures[state]):
                rows.append((state, "same", 0.0, 0, 0))
                continue
            before, after = read_png(baselines[state]), read_png(captures[state])
            changed, ignored, total, image = diff_images(before, after, diff_dir is not None)
            percent = 100.0 * changed / total if total else 0.0
            resized = before[:2] != after[:2]
            if resized and sizes is not None:
                sizes[state] = (before[:2], after[:2])
            if percent <= limit and not resized:  # another size is a difference whatever the share of pixels
                rows.append((state, "same", percent, changed, ignored))
                continue
            if diff_dir and image:
                write_png(os.path.join(diff_dir, state + ".png"), max(before[0], after[0]), max(before[1], after[1]), image)
            # A state the slice lists as new has a baseline once its first
            # one is adopted; a later fix on the branch may still move it.
            rows.append((state, "changed" if kind in ("changed", "new") else "STRAY", percent, changed, ignored))
        elif has_shot:
            rows.append((state, "new" if kind in ("new", "changed") or first else "UNLISTED", 100.0, 0, 0))
        elif kind == "removed":
            if has_base:
                rows.append((state, "removed", 100.0, 0, 0))
        else:
            rows.append((state, "MISSING", 100.0, 0, 0))
    return rows, limit, source


FINDINGS = ("STRAY", "UNLISTED", "MISSING")
WHY = {
    "same": "within the threshold of its baseline",
    "changed": "differs, listed as changed: its baseline is owed",
    "new": "no baseline yet: its first baseline is owed",
    "removed": "listed as removed and not captured: its baseline goes",
    "STRAY": "differs and the slice's screen design does not list it",
    "UNLISTED": "captured with no baseline and not listed as new",
    "MISSING": "no capture (a baseline or a listed state the capture did not produce)",
}


def verdict(rows):
    bad = [s for s, status, *_ in rows if status in FINDINGS]
    count = {k: sum(1 for _, status, *_ in rows if status == k) for k in ("changed", "new", "removed")}
    if bad:
        # A state with no capture is not "not listed": it may be on the
        # list and have thrown. Named apart, so the reader looks at the
        # capture and not at the screen design.
        missing = [s for s, status, *_ in rows if status == "MISSING"]
        stray = [s for s in bad if s not in missing]
        if not missing:
            return 1, f"screens: FAIL {len(bad)} not listed: {', '.join(bad)}"
        if not stray:
            return 1, f"screens: FAIL {len(bad)} not captured: {', '.join(bad)}"
        return 1, (f"screens: FAIL {len(bad)}: {len(missing)} not captured: {', '.join(missing)}; "
                   f"{len(stray)} not listed: {', '.join(stray)}")
    if any(count.values()):
        return 3, f"screens: BASELINES OWED {count['changed']} changed, {count['new']} new, {count['removed']} removed"
    return 0, f"screens: PASS ({len(rows)} states)"


def lines_for(rows, limit, source, failed=None, sizes=None):
    out = [f"threshold: more than {limit:g}% of a state's pixels, anti-aliasing ignored ({source})"]
    for state, status, percent, changed, ignored in rows:
        size = ""
        if sizes and state in sizes:
            (bw, bh), (cw, ch) = sizes[state]
            size = f"; size {bw}x{bh} -> {cw}x{ch}"
        detail = f" ({percent:.3f}% of pixels, {changed} changed, {ignored} anti-aliased ignored{size})" if changed or ignored or size else ""
        why = f"the capture failed: {failed[state]}" if status == "MISSING" and failed and state in failed else WHY[status]
        out.append(f"{status:<8} {state}: {why}{detail}")
    return out


def cmd_compare(a):
    os.makedirs(a.out, exist_ok=True)
    sizes = {}
    result = judge(a.planning, a.captures, a.base, os.path.join(a.out, "diff"), sizes)
    if isinstance(result, str):
        print(f"screens: cannot run: {result}")
        return 2
    rows, limit, source = result
    code, last = verdict(rows)
    text = lines_for(rows, limit, source, capture_errors(a.captures), sizes) + [last]
    print("\n".join(text))
    with open(os.path.join(a.out, "screen-check.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(text) + "\n")
    with open(os.path.join(a.out, "screen-check.json"), "w", encoding="utf-8") as f:
        json.dump({"head": a.head, "max_changed_percent": limit, "verdict": last, "exit": code,
                   "states": [{"state": s, "status": st, "percent": round(p, 4), "changed_pixels": c, "antialiased_ignored": i,
                               **({"size": {"baseline": list(sizes[s][0]), "capture": list(sizes[s][1])}} if s in sizes else {})}
                              for s, st, p, c, i in rows]}, f, indent=2)
    return code


def cmd_adopt(a):
    captures = os.path.join(a.artifact, "captures")
    if not os.path.isdir(captures):
        print(f"adopt: no captures/ in {a.artifact}")
        return 2
    report = os.path.join(a.artifact, "screen-check.json")
    made_for = None
    if os.path.isfile(report):
        try:
            with open(report, encoding="utf-8") as f:
                made_for = json.load(f).get("head")
        except (json.JSONDecodeError, AttributeError):
            made_for = None
    here = (git(a.planning, "rev-parse", "HEAD") or "").strip()
    if made_for and here and not (here.startswith(made_for) or made_for.startswith(here)):
        # A commit of records on top of the captured one (a handoff, the
        # log) changes no pixel; a commit that touches anything outside
        # the planning directory may have.
        top = (git(a.planning, "rev-parse", "--show-toplevel") or "").strip()
        since = git(top, "diff", "--name-only", made_for, "HEAD") if top and git(top, "merge-base", "--is-ancestor", made_for, "HEAD") is not None else None
        inside = os.path.relpath(os.path.realpath(a.planning), os.path.realpath(top)).replace(os.sep, "/") + "/" if top else ""
        if since is None or any(not name.startswith(inside) for name in since.split("\n") if name):
            print(f"adopt: the artifact was made for {made_for[:12]} and HEAD is {here[:12]}, with changes outside the planning directory since: nothing adopted")
            return 2
    result = judge(a.planning, captures, a.base)
    if isinstance(result, str):
        print(f"adopt: cannot run: {result}")
        return 2
    rows, _, _ = result
    bad = [s for s, status, *_ in rows if status in FINDINGS]
    if bad:
        gone = [st for st, status, *_ in rows if status == "MISSING"]
        print(f"adopt: nothing adopted: {len(bad)} state(s) not listed or with no capture ({', '.join(bad)}); those are findings, not baselines"
              + (f"; no capture for {', '.join(gone)}: a baseline set that leaves a driven state out is not a first baseline" if gone else ""))
        return 1
    baselines = os.path.join(a.planning, "visual-ux", "baselines")
    os.makedirs(baselines, exist_ok=True)
    # Paths are printed from the repository's root, for the commit.
    top = os.path.realpath((git(a.planning, "rev-parse", "--show-toplevel") or a.planning).strip())
    baselines = os.path.realpath(baselines)
    count = {"changed": 0, "new": 0, "removed": 0}
    for state, status, *_ in rows:
        target = os.path.join(baselines, state + ".png")
        if status in ("changed", "new"):
            shutil.copyfile(os.path.join(captures, state + ".png"), target)
        elif status == "removed":
            os.remove(target)
        else:
            continue
        count[status] += 1
        print(f"{status}: {os.path.relpath(target, top)}")
    print(f"adopted: {count['changed']} changed, {count['new']} new, {count['removed']} removed")
    return 0


def cmd_states(a):
    names = listed(a.planning, a.base)
    if isinstance(names, str):
        print(f"states: cannot run: {names}")
        return 2
    want = sorted(s for s, kind in names.items() if kind in ("changed", "new"))
    driven = set()
    if os.path.isfile(a.capture):
        with open(a.capture, encoding="utf-8", errors="replace") as f:
            driven = set(re.findall(r"""['"]([a-z0-9][a-z0-9._-]*)['"]\s*:""", f.read()))
    else:
        print(f"no capture file at {a.capture}")
    missing = [s for s in want if s not in driven]
    for s in missing:
        print(f"missing: {s}")
    print(f"states: {len(want)} listed, {len(missing)} not driven")
    return 1 if missing else 0


def section_problems(planning, screen):
    """What the readiness gate reads: [(key, display)]."""
    with open(screen, encoding="utf-8", errors="replace") as f:
        found, entries, none = section_entries(f.read())
    name = os.path.basename(screen)
    if not found:
        return [("no section", f"{name} has no `## States this slice changes` section")]
    if not entries:
        return [] if none else [("empty section", f"{name}: the section names no state (one line per state: `<name>`: changed, new or removed; or `none`)")]
    ux = os.path.join(glob.escape(planning), "visual-ux")
    stems = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ux, "**", "*.html"), recursive=True)}
    baselines = pngs(os.path.join(planning, "visual-ux", "baselines"))
    out = []
    for state, kind in entries:
        if kind != "removed" and state not in stems:
            out.append((f"no mockup: {state}", f"`{state}` ({kind}) has no mockup named {state}.html under visual-ux/"))
        if kind == "new" and state in baselines:
            out.append((f"new with a baseline: {state}", f"`{state}` is listed as new and visual-ux/baselines/{state}.png exists: another state has the name, or it is changed"))
    return out


def cmd_check_section(a):
    problems = section_problems(a.planning, a.screen)
    for _, shown in problems:
        print(f"problem: {shown}")
    print(f"section: {'FAIL' if problems else 'PASS'}")
    return 1 if problems else 0


def main():
    p = argparse.ArgumentParser(description="The screen-change check.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--planning", required=True)
    c.add_argument("--captures", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--base")
    c.add_argument("--head", help="the commit the captures were made from, recorded in the report")
    c.set_defaults(fn=cmd_compare)
    d = sub.add_parser("adopt")
    d.add_argument("--planning", required=True)
    d.add_argument("--artifact", required=True)
    d.add_argument("--base")
    d.set_defaults(fn=cmd_adopt)
    s = sub.add_parser("states")
    s.add_argument("--planning", required=True)
    s.add_argument("--capture", required=True)
    s.add_argument("--base")
    s.set_defaults(fn=cmd_states)
    k = sub.add_parser("check-section")
    k.add_argument("--planning", required=True)
    k.add_argument("--screen", required=True)
    k.set_defaults(fn=cmd_check_section)
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a.planning = os.path.abspath(a.planning)
    if not os.path.isdir(a.planning):
        print(f"screens: cannot run: {a.planning} is not a directory")
        return 2
    try:
        return a.fn(a)
    except Unsupported as e:
        print(f"screens: cannot run: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
