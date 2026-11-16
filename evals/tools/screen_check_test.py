#!/usr/bin/env python3
"""The screen-change check, without a model and without a browser.

- The PNG reader gives the pixels a writer put in, through each of the
  five row filters and each colour type a browser or an editor writes.
- A pixel on an anti-aliased edge is not counted; a block of flat pixels
  is. Ten changed pixels of ten thousand (0.1%) is not a difference,
  eleven is; two sizes always are.
- C1's "done when", on the loop fixture's desk screen (the images under
  `code-plants/loop/screens/`, captured by Chromium in the plugin's own
  `fixture-screens` workflow): a style change meant for
  `hold-not-cancelled` that also moves `hold-cancelled` is reported, and
  the intended change is not.
- Listed means added on the branch: a line the base already had lists
  nothing.
- `adopt` copies the listed states' images and no other, copies nothing
  while a finding stands, and refuses an artifact made for another commit.
- `states` names the listed states the capture file does not drive;
  `check-section` is what the readiness gate reads.

Usage: python3 -I evals/tools/screen_check_test.py
"""
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "skills", "orchestrator", "scripts", "screen_check.py")
SCREENS = os.path.join(ROOT, "evals", "fixtures", "library-app", "code-plants", "loop", "screens")

spec = importlib.util.spec_from_file_location("screen_check", SCRIPT)
sc = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.dirname(SCRIPT))
spec.loader.exec_module(sc)
import source_scan  # noqa: E402  (beside the script; for a git that runs here)

GIT = source_scan.find_git()


def run(*args, cwd=None):
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True, cwd=cwd)


def git(cwd, *args):
    return subprocess.run([GIT, "-C", cwd, *args], check=True, capture_output=True, text=True).stdout.strip()


def encode(path, width, height, colour, rows, filters, palette=None, trns=None, depth=8):
    """A PNG written row by row with the named filter per row (0 to 4)."""
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colour]
    raw, prev = b"", bytes(width * channels)
    for y, row in enumerate(rows):
        kind = filters[y % len(filters)]
        out = bytearray()
        for i, value in enumerate(row):
            a = row[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if kind == 0:
                pred = 0
            elif kind == 1:
                pred = a
            elif kind == 2:
                pred = b
            elif kind == 3:
                pred = (a + b) >> 1
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else b if pb <= pc else c
            out.append((value - pred) & 255)
        raw += bytes([kind]) + bytes(out)
        prev = row

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, colour, 0, 0, 0))
    if palette:
        data += chunk(b"PLTE", palette)
    if trns:
        data += chunk(b"tRNS", trns)
    data += chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)


def data(path, mode="rb"):
    with open(path, mode) as f:
        return f.read()


def flat(width, height, colour=(255, 255, 255)):
    return bytearray(bytes(colour) * (width * height))


def put(rgb, width, x, y, colour):
    rgb[(y * width + x) * 3:(y * width + x) * 3 + 3] = bytes(colour)


def rgba(rgb):
    out = bytearray(len(rgb) // 3 * 4)
    out[0::4], out[1::4], out[2::4] = rgb[0::3], rgb[1::3], rgb[2::3]
    out[3::4] = b"\xff" * (len(rgb) // 3)
    return bytes(out)


class Planning:
    """A planning directory with a screen design, baselines and captures."""

    def __init__(self, tmp, section="- `one`: changed\n- `three`: new\n", percent=None):
        self.root = tmp
        self.planning = os.path.join(tmp, "docs", "x")
        self.ux = os.path.join(self.planning, "visual-ux")
        self.baselines = os.path.join(self.ux, "baselines")
        self.captures = os.path.join(tmp, "out", "captures")
        self.out = os.path.join(tmp, "out")
        os.makedirs(self.baselines)
        os.makedirs(self.captures)
        self.design = os.path.join(self.ux, "screen-design-001.md")
        self.write_design(section)
        if percent is not None:
            with open(os.path.join(self.baselines, "screen-check.json"), "w") as f:
                json.dump({"max_changed_percent": percent}, f)

    def write_design(self, section):
        with open(self.design, "w") as f:
            f.write("# Screen design\n\n## Layout\nText.\n" + ("\n## States this slice changes\n\n" + section if section is not None else "")
                    + "\n## Open questions\nNone.\n")

    def image(self, where, name, changed=0, size=(100, 100)):
        """A white image with `changed` black pixels in one row."""
        w, h = size
        rgb = flat(w, h)
        for x in range(changed):
            put(rgb, w, 10 + x, 50, (0, 0, 0))
        sc.write_png(os.path.join(self.baselines if where == "baseline" else self.captures, name + ".png"), w, h, bytes(rgb))

    def compare(self, *extra):
        return run("compare", "--planning", self.planning, "--captures", self.captures, "--out", self.out, *extra)


class Png(unittest.TestCase):
    def test_every_row_filter_gives_the_pixels_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            w, h = 7, 6
            rows = [bytes((x * 37 + y * 91 + c * 53) & 255 for x in range(w) for c in range(4)) for y in range(h)]
            for filters in ([0], [1], [2], [3], [4], [4, 3, 1, 2, 0]):
                path = os.path.join(tmp, "f.png")
                encode(path, w, h, 6, rows, filters)
                self.assertEqual(sc.read_png(path), (w, h, b"".join(rows)), filters)

    def test_rgb_grey_and_palette_images_become_rgba(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "p.png")
            encode(path, 2, 1, 2, [bytes([1, 2, 3, 4, 5, 6])], [1])
            self.assertEqual(sc.read_png(path)[2], bytes([1, 2, 3, 255, 4, 5, 6, 255]))
            encode(path, 2, 1, 0, [bytes([9, 200])], [0])
            self.assertEqual(sc.read_png(path)[2], bytes([9, 9, 9, 255, 200, 200, 200, 255]))
            encode(path, 2, 1, 4, [bytes([9, 128, 200, 255])], [0])
            self.assertEqual(sc.read_png(path)[2], bytes([9, 9, 9, 128, 200, 200, 200, 255]))
            encode(path, 2, 1, 3, [bytes([1, 0])], [0], palette=bytes([10, 20, 30, 40, 50, 60]), trns=bytes([7]))
            self.assertEqual(sc.read_png(path)[2], bytes([40, 50, 60, 255, 10, 20, 30, 7]))

    def test_the_writer_and_the_reader_agree(self):
        with tempfile.TemporaryDirectory() as tmp:
            rgb = bytes(range(256)) * 3
            path = os.path.join(tmp, "w.png")
            sc.write_png(path, 16, 16, rgb)
            self.assertEqual(sc.read_png(path), (16, 16, rgba(rgb)))

    def test_a_sixteen_bit_image_is_refused_not_misread(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp)
            encode(os.path.join(p.baselines, "one.png"), 2, 1, 2, [bytes(6)], [0], depth=16)
            p.image("capture", "one")
            r = p.compare()
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertIn("cannot run", r.stdout)


class Pixels(unittest.TestCase):
    def test_identical_images_differ_nowhere(self):
        img = (4, 4, rgba(flat(4, 4, (10, 20, 30))))
        self.assertEqual(sc.diff_images(img, img)[:3], (0, 0, 16))

    def test_a_flat_block_counts_and_an_antialiased_edge_does_not(self):
        w, h = 20, 20
        a, b = flat(w, h), flat(w, h)
        for y in range(h):  # black on the left, white on the right, one grey column between
            for x in range(10):
                put(a, w, x, y, (0, 0, 0))
                put(b, w, x, y, (0, 0, 0))
            put(a, w, 10, y, (100, 100, 100))
            put(b, w, 10, y, (160, 160, 160))
        changed, ignored, total, _ = sc.diff_images((w, h, rgba(a)), (w, h, rgba(b)))
        self.assertEqual((changed, total), (0, 400))
        self.assertEqual(ignored, 20)
        for x in range(14, 18):  # a block in the flat white: no edge to be the smoothing of
            for y in range(4, 8):
                put(b, w, x, y, (200, 0, 0))
        changed, ignored, _, image = sc.diff_images((w, h, rgba(a)), (w, h, rgba(b)))
        self.assertEqual(changed, 16)
        self.assertEqual(image[(4 * w + 14) * 3:(4 * w + 14) * 3 + 3], b"\xe0\x20\x20")

    def test_a_colour_shift_under_the_pixel_threshold_is_not_a_change(self):
        a, b = flat(8, 8, (120, 120, 120)), flat(8, 8, (124, 124, 124))
        self.assertEqual(sc.diff_images((8, 8, rgba(a)), (8, 8, rgba(b)))[0], 0)

    def test_two_sizes_differ_in_full(self):
        a, b = (4, 4, rgba(flat(4, 4))), (4, 5, rgba(flat(4, 5)))
        self.assertEqual(sc.diff_images(a, b)[:3], (20, 0, 20))


class Compare(unittest.TestCase):
    def test_a_tenth_of_a_percent_is_not_a_difference_and_one_pixel_more_is(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section="- none\n")
            p.image("baseline", "one")
            p.image("capture", "one", changed=10)
            r = p.compare()
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("screens: PASS (1 states)", r.stdout)
            p.image("capture", "one", changed=11)
            r = p.compare()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("screens: FAIL 1 not listed: one", r.stdout)

    def test_the_owners_number_is_read_and_a_bad_one_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section="- none\n", percent=0.5)
            p.image("baseline", "one")
            p.image("capture", "one", changed=40)
            self.assertEqual(p.compare().returncode, 0)
            with open(os.path.join(p.baselines, "screen-check.json"), "w") as f:
                f.write('{"max_changed_percent": "lots"}')
            r = p.compare()
            self.assertEqual(r.returncode, 2, r.stdout)

    def test_each_status_and_the_three_verdicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section="- `one`: changed, wider\n- `three`: new\n- `gone`: removed\n")
            for name in ("one", "two", "gone"):
                p.image("baseline", name)
            p.image("capture", "one", changed=200)
            p.image("capture", "two")
            p.image("capture", "three")
            r = p.compare()
            self.assertEqual(r.returncode, 3, r.stdout)
            self.assertEqual(r.stdout.strip().splitlines()[-1], "screens: BASELINES OWED 1 changed, 1 new, 1 removed")
            self.assertRegex(r.stdout, r"(?m)^changed\s+one:")
            self.assertRegex(r.stdout, r"(?m)^same\s+two:")
            self.assertRegex(r.stdout, r"(?m)^new\s+three:")
            self.assertRegex(r.stdout, r"(?m)^removed\s+gone:")
            self.assertTrue(os.path.isfile(os.path.join(p.out, "diff", "one.png")))
            report = json.loads(data(os.path.join(p.out, "screen-check.json"), "r"))
            self.assertEqual(report["exit"], 3)
            # A finding outranks what is owed: two moved, a fourth appeared, a baseline has no capture.
            p.image("capture", "two", changed=200)
            p.image("capture", "four")
            p.image("baseline", "five")
            r = p.compare()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertEqual(r.stdout.strip().splitlines()[-1], "screens: FAIL 3 not listed: five, four, two")
            self.assertRegex(r.stdout, r"(?m)^STRAY\s+two:")
            self.assertRegex(r.stdout, r"(?m)^UNLISTED\s+four:")
            self.assertRegex(r.stdout, r"(?m)^MISSING\s+five:")
            self.assertEqual(data(os.path.join(p.out, "screen-check.txt"), "r"), r.stdout)

    def test_a_listed_state_the_capture_did_not_produce_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section="- `three`: new\n")
            p.image("baseline", "one")
            p.image("capture", "one")
            r = p.compare()
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertRegex(r.stdout, r"(?m)^MISSING\s+three:")

    def test_a_project_with_no_baseline_yet_takes_every_capture_as_its_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section=None)
            p.image("capture", "one")
            p.image("capture", "two")
            r = p.compare()
            self.assertEqual(r.returncode, 3, r.stdout)
            self.assertIn("screens: BASELINES OWED 0 changed, 2 new, 0 removed", r.stdout)

    def test_a_state_listed_as_new_may_still_move_after_its_first_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section="- `three`: new\n")
            p.image("baseline", "three")
            p.image("capture", "three", changed=200)
            r = p.compare()
            self.assertEqual(r.returncode, 3, r.stdout)
            self.assertRegex(r.stdout, r"(?m)^changed\s+three:")


class Fixture(unittest.TestCase):
    """C1's "done when" on the loop fixture's desk screen."""

    def planning(self, tmp):
        planning = os.path.join(tmp, "docs", "cancel-hold")
        shutil.copytree(os.path.join(SCREENS, "base-planning"), planning)
        shutil.copytree(os.path.join(SCREENS, "slice-planning"), planning, dirs_exist_ok=True)
        return planning

    def test_the_intended_change_is_owed_and_not_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("compare", "--planning", self.planning(tmp), "--captures", os.path.join(SCREENS, "captures", "intended"),
                    "--out", os.path.join(tmp, "out"))
            self.assertEqual(r.returncode, 3, r.stdout)
            self.assertEqual(r.stdout.strip().splitlines()[-1], "screens: BASELINES OWED 1 changed, 1 new, 0 removed")
            self.assertRegex(r.stdout, r"(?m)^same\s+hold-cancelled:")
            self.assertRegex(r.stdout, r"(?m)^changed\s+hold-not-cancelled:")
            self.assertRegex(r.stdout, r"(?m)^new\s+queue-failure:")

    def test_a_change_that_moves_another_state_is_reported_and_the_intended_one_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("compare", "--planning", self.planning(tmp), "--captures", os.path.join(SCREENS, "captures", "planted"),
                    "--out", os.path.join(tmp, "out"))
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertEqual(r.stdout.strip().splitlines()[-1], "screens: FAIL 1 not listed: hold-cancelled")
            self.assertRegex(r.stdout, r"(?m)^STRAY\s+hold-cancelled:")
            self.assertRegex(r.stdout, r"(?m)^changed\s+hold-not-cancelled:")
            self.assertTrue(os.path.isfile(os.path.join(tmp, "out", "diff", "hold-cancelled.png")))

    def test_the_fixtures_capture_file_drives_what_its_screen_design_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            planning = self.planning(tmp)
            r = run("states", "--planning", planning, "--capture", os.path.join(SCREENS, "base", "screens", "states.mjs"))
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertEqual(r.stdout.strip().splitlines(), ["missing: queue-failure", "states: 2 listed, 1 not driven"])
            r = run("states", "--planning", planning, "--capture", os.path.join(SCREENS, "slice", "screens", "states.mjs"))
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(run("check-section", "--planning", planning, "--screen",
                                 os.path.join(planning, "visual-ux", "screen-design-001.md")).returncode, 0)


class Repo(Planning):
    """A planning directory committed on `main`, then a branch."""

    def __init__(self, tmp, section):
        super().__init__(tmp, section)
        for name in ("one", "two"):
            self.image("baseline", name)
        git(tmp, "init", "-q", "-b", "main")
        git(tmp, "config", "user.name", "t")
        git(tmp, "config", "user.email", "t@example.test")
        git(tmp, "config", "commit.gpgsign", "false")
        with open(os.path.join(tmp, ".gitignore"), "w") as f:
            f.write("out/\n")
        git(tmp, "add", "-A")
        git(tmp, "commit", "-qm", "main")
        git(tmp, "checkout", "-q", "-b", "slice")

    def commit(self, message):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", message)
        return git(self.root, "rev-parse", "HEAD")


class Listed(unittest.TestCase):
    def test_a_line_the_base_already_had_lists_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, "- `one`: changed\n")
            p.image("capture", "one", changed=200)
            p.image("capture", "two")
            # On the branch nothing was added to the section: `one` was an earlier slice's.
            r = p.compare("--base", "main")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertRegex(r.stdout, r"(?m)^STRAY\s+one:")
            # The branch adds a line for `two`; `one` is still not its own.
            p.write_design("- `one`: changed\n- `two`: changed\n")
            p.commit("the fix's screen design")
            p.image("capture", "two", changed=200)
            r = p.compare("--base", "main")
            self.assertEqual(r.stdout.strip().splitlines()[-1], "screens: FAIL 1 not listed: one")
            self.assertRegex(r.stdout, r"(?m)^changed\s+two:")
            # Without a base every line is listed.
            self.assertEqual(p.compare().returncode, 3)

    def test_a_screen_design_the_base_does_not_have_lists_all_of_its_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, None)
            os.remove(p.design)
            p.commit("no design on the branch point")
            git(tmp, "branch", "-f", "main", "HEAD")
            p.write_design("- `one`: changed\n")
            p.commit("the slice's screen design")
            p.image("capture", "one", changed=200)
            p.image("capture", "two")
            r = p.compare("--base", "main")
            self.assertEqual(r.returncode, 3, r.stdout)

    def test_a_base_that_is_no_commit_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, "- `one`: changed\n")
            r = p.compare("--base", "origin/nowhere")
            self.assertEqual(r.returncode, 2, r.stdout)


class Adopt(unittest.TestCase):
    def artifact(self, p, head=None):
        with open(os.path.join(p.out, "screen-check.json"), "w") as f:
            json.dump({"head": head}, f)
        return p.out

    def test_only_the_listed_states_are_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, None)
            p.write_design("- `one`: changed\n- `three`: new\n")
            head = p.commit("the slice")
            p.image("capture", "one", changed=200)
            p.image("capture", "two", changed=5)  # under the threshold: same, and not copied
            p.image("capture", "three")
            before = data(os.path.join(p.baselines, "two.png"))
            r = run("adopt", "--planning", p.planning, "--artifact", self.artifact(p, head), "--base", "main")
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(r.stdout.strip().splitlines(), [
                "changed: docs/x/visual-ux/baselines/one.png", "new: docs/x/visual-ux/baselines/three.png",
                "adopted: 1 changed, 1 new, 0 removed"])
            self.assertEqual(data(os.path.join(p.baselines, "one.png")), data(os.path.join(p.captures, "one.png")))
            self.assertEqual(data(os.path.join(p.baselines, "two.png")), before)
            self.assertEqual(git(tmp, "status", "--porcelain").split(), ["M", "docs/x/visual-ux/baselines/one.png", "??", "docs/x/visual-ux/baselines/three.png"])
            self.assertEqual(p.compare("--base", "main").returncode, 0)

    def test_nothing_is_copied_while_a_finding_stands(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, None)
            p.write_design("- `one`: changed\n")
            head = p.commit("the slice")
            p.image("capture", "one", changed=200)
            p.image("capture", "two", changed=200)
            r = run("adopt", "--planning", p.planning, "--artifact", self.artifact(p, head), "--base", "main")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("nothing adopted", r.stdout)
            self.assertEqual(git(tmp, "status", "--porcelain"), "")

    def test_an_artifact_made_for_another_commit_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, None)
            p.write_design("- `one`: changed\n")
            p.commit("the slice")
            p.image("capture", "one", changed=200)
            p.image("capture", "two")
            r = run("adopt", "--planning", p.planning, "--artifact", self.artifact(p, "0123456789abcdef0123456789abcdef01234567"), "--base", "main")
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertEqual(git(tmp, "status", "--porcelain"), "")

    def test_a_records_commit_on_top_is_accepted_and_a_code_commit_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, None)
            p.write_design("- `one`: changed\n")
            head = p.commit("the slice")
            p.image("capture", "one", changed=200)
            p.image("capture", "two")
            artifact = self.artifact(p, head)
            with open(os.path.join(tmp, "app.css"), "w") as f:
                f.write("body { margin: 0 }\n")
            p.commit("a style change after the capture")
            r = run("adopt", "--planning", p.planning, "--artifact", artifact, "--base", "main")
            self.assertEqual(r.returncode, 2, r.stdout)
            git(tmp, "reset", "-q", "--hard", head)
            os.makedirs(os.path.join(p.planning, "implementation"))
            with open(os.path.join(p.planning, "implementation", "handoff.md"), "w") as f:
                f.write("records\n")
            p.commit("Records: handoff")
            r = run("adopt", "--planning", p.planning, "--artifact", artifact, "--base", "main")
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_removed_states_baseline_goes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Repo(tmp, None)
            p.write_design("- `two`: removed\n")
            head = p.commit("the slice")
            p.image("capture", "one")
            r = run("adopt", "--planning", p.planning, "--artifact", self.artifact(p, head), "--base", "main")
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertFalse(os.path.exists(os.path.join(p.baselines, "two.png")))


class Section(unittest.TestCase):
    def check(self, p):
        return run("check-section", "--planning", p.planning, "--screen", p.design)

    def test_no_section_an_empty_one_and_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp, section=None)
            r = self.check(p)
            self.assertEqual(r.returncode, 1)
            self.assertIn("no `## States this slice changes` section", r.stdout)
            p.write_design("Some words, no state.\n")
            self.assertEqual(self.check(p).returncode, 1)
            p.write_design("- none: the slice restyles nothing a person sees\n")
            self.assertEqual(self.check(p).returncode, 0)

    def test_a_listed_state_needs_a_mockup_of_its_name_and_a_new_one_no_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Planning(tmp)
            r = self.check(p)
            self.assertIn("`one` (changed) has no mockup named one.html", r.stdout)
            os.makedirs(os.path.join(p.ux, "screen-slice-001"))
            for name in ("one", "three"):  # a mockup in a folder of its slice counts
                open(os.path.join(p.ux, "screen-slice-001", name + ".html"), "w").close()
            self.assertEqual(self.check(p).returncode, 0)
            p.image("baseline", "three")
            r = self.check(p)
            self.assertEqual(r.returncode, 1)
            self.assertIn("`three` is listed as new and visual-ux/baselines/three.png exists", r.stdout)


if __name__ == "__main__":
    unittest.main()
