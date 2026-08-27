"""Tests for the deterministic visual hard gate (Issue #26).

Skipped automatically where Pillow is unavailable (ordinary CI); the gate is
host tooling, not part of the stdlib-only package.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

REPO = Path(__file__).resolve().parent.parent


@unittest.skipUnless(HAVE_PIL, "Pillow is not installed")
class VisualGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def _png(self, name, size=(40, 30), color=(10, 20, 30, 255), patch=None):
        image = Image.new("RGBA", size, color)
        if patch:
            x, y, w, h, patch_color = patch
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    image.putpixel((xx, yy), patch_color)
        path = self.dir / name
        image.save(path)
        return path

    def _run(self, *argv):
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "visual_gate.py"), *argv],
            capture_output=True, text=True,
        )
        payload = json.loads(result.stdout) if result.stdout else {}
        return result.returncode, payload

    def test_identical_images_pass(self):
        ref = self._png("ref.png")
        cand = self._png("cand.png")
        code, verdict = self._run(
            "--reference", str(ref), "--candidate", str(cand), "--region", "5,5,10,10"
        )
        self.assertEqual(code, 0)
        self.assertTrue(verdict["hard_gate_passed"])

    def test_inside_region_change_passes_outside_check(self):
        ref = self._png("ref.png")
        cand = self._png("cand.png", patch=(6, 6, 4, 4, (200, 0, 0, 255)))
        code, verdict = self._run(
            "--reference", str(ref), "--candidate", str(cand), "--region", "5,5,10,10"
        )
        self.assertEqual(code, 0, verdict)

    def test_outside_region_change_fails(self):
        ref = self._png("ref.png")
        cand = self._png("cand.png", patch=(0, 0, 2, 2, (200, 0, 0, 255)))
        code, verdict = self._run(
            "--reference", str(ref), "--candidate", str(cand), "--region", "5,5,10,10"
        )
        self.assertEqual(code, 1)
        outside = next(c for c in verdict["checks"] if c["check"].startswith("T43"))
        self.assertEqual(outside["changed_pixels_outside_region"], 4)

    def test_aspect_drift_fails(self):
        ref = self._png("ref.png", size=(40, 30))
        cand = self._png("cand.png", size=(40, 20))
        code, verdict = self._run("--reference", str(ref), "--candidate", str(cand))
        self.assertEqual(code, 1)
        aspect = next(c for c in verdict["checks"] if c["check"].startswith("T21"))
        self.assertFalse(aspect["passed"])

    def test_opaque_rectangle_leak_fails(self):
        ref = self._png("ref.png", color=(10, 20, 30, 0))
        cand = self._png("cand.png", color=(10, 20, 30, 255))
        code, verdict = self._run("--reference", str(ref), "--candidate", str(cand))
        self.assertEqual(code, 1)
        leak = next(c for c in verdict["checks"] if c["check"].startswith("T40"))
        self.assertFalse(leak["passed"])

    def test_transparent_candidate_passes_leak_check(self):
        ref = self._png("ref.png", color=(10, 20, 30, 0))
        cand = self._png("cand.png", color=(10, 20, 30, 0))
        code, verdict = self._run("--reference", str(ref), "--candidate", str(cand))
        self.assertEqual(code, 0, verdict)


if __name__ == "__main__":
    unittest.main()
