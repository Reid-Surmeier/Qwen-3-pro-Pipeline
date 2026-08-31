"""Deterministic hard-gate layer of the Issue #26 visual failure gate.

Checks a candidate image against its Reference Screen for the taxonomy's
deterministically decidable classes:

  T21 aspect-ratio-drift      candidate aspect vs reference aspect
  T43 outside-region-change   changed pixels outside a declared edit region
  T40 opaque-rectangle-leak   opaque full-canvas rectangle where the
                              reference carries transparency

It emits a JSON verdict (one line per check plus an overall gate) and exits
non-zero when any hard check fails. It never approves: passing the hard gate
only means the candidate may proceed to advisory critique and human review.

Usage:
    python3.12 scripts/visual_gate.py --reference ref.png --candidate cand.png \
        [--region x,y,w,h] [--aspect-tolerance 0.02]

Requires Pillow (available on the pipeline host; ordinary CI skips its tests).
"""

from __future__ import annotations

import argparse
import json
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - exercised only where Pillow is absent
    Image = None


def check_aspect(reference, candidate, tolerance):
    ref_aspect = reference.width / reference.height
    cand_aspect = candidate.width / candidate.height
    drift = abs(cand_aspect - ref_aspect) / ref_aspect
    return {
        "check": "T21-aspect-ratio-drift",
        "reference_aspect": round(ref_aspect, 4),
        "candidate_aspect": round(cand_aspect, 4),
        "relative_drift": round(drift, 4),
        "tolerance": tolerance,
        "passed": drift <= tolerance,
    }


def check_outside_region(reference, candidate, region):
    if (reference.width, reference.height) != (candidate.width, candidate.height):
        return {
            "check": "T43-outside-region-change",
            "passed": False,
            "error": "candidate dimensions differ from reference; "
            "normalize deterministically before this check",
        }
    x, y, w, h = region
    ref = reference.convert("RGBA")
    cand = candidate.convert("RGBA")
    ref_px, cand_px = ref.load(), cand.load()
    changed = 0
    for yy in range(ref.height):
        inside_row = y <= yy < y + h
        for xx in range(ref.width):
            if inside_row and x <= xx < x + w:
                continue
            if ref_px[xx, yy] != cand_px[xx, yy]:
                changed += 1
    return {
        "check": "T43-outside-region-change",
        "region": {"x": x, "y": y, "width": w, "height": h},
        "changed_pixels_outside_region": changed,
        "passed": changed == 0,
    }


def check_opaque_rectangle(reference, candidate):
    ref = reference.convert("RGBA")
    cand = candidate.convert("RGBA")
    ref_alpha = ref.getchannel("A")
    ref_min_alpha = min(ref_alpha.getdata())
    if ref_min_alpha == 255:
        return {
            "check": "T40-opaque-rectangle-leak",
            "passed": True,
            "note": "reference is fully opaque; check not applicable",
        }
    cand_alpha = cand.getchannel("A")
    cand_min_alpha = min(cand_alpha.getdata())
    return {
        "check": "T40-opaque-rectangle-leak",
        "reference_min_alpha": ref_min_alpha,
        "candidate_min_alpha": cand_min_alpha,
        "passed": cand_min_alpha < 255,
    }


def run_gate(reference_path, candidate_path, region=None, aspect_tolerance=0.02):
    if Image is None:
        raise SystemExit("Pillow is required: pip install Pillow")
    with Image.open(reference_path) as reference, Image.open(candidate_path) as candidate:
        checks = [check_aspect(reference, candidate, aspect_tolerance)]
        if region is not None:
            checks.append(check_outside_region(reference, candidate, region))
        checks.append(check_opaque_rectangle(reference, candidate))
    return {
        "reference": str(reference_path),
        "candidate": str(candidate_path),
        "checks": checks,
        "hard_gate_passed": all(c["passed"] for c in checks),
        "note": "passing means eligible for advisory critique and human "
        "review; it is not an approval",
    }


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--region", help="x,y,w,h edit rectangle on the reference")
    parser.add_argument("--aspect-tolerance", type=float, default=0.02)
    args = parser.parse_args(argv)
    region = None
    if args.region:
        region = tuple(int(v) for v in args.region.split(","))
        if len(region) != 4:
            parser.error("--region must be x,y,w,h")
    verdict = run_gate(args.reference, args.candidate, region, args.aspect_tolerance)
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["hard_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
