#!/usr/bin/env python3
"""Verify the palette JSON against the IRIX scheme sources and the shadow rule.

The failure this guards against is a hand-edited or invented color drifting
into layer 1, which is the exact problem the layered palette exists to prevent.
Re-parses the reference independently of transcribe-reference-palette.py rather than
trusting that script's own output.

    python3 tools/verify-palette.py [path-to-color-reference]

Exits non-zero on any mismatch.
"""
import json
import re
import sys
from pathlib import Path

DEFAULT_REF = Path("/mnt/Dev/wlRIX/_docs/color-reference/Base")
PALETTES = Path(__file__).resolve().parent.parent / "palette"

GAMMA_FOR = {
    "classic": "GAMMA_1_7",
    "classic-g10": "GAMMA_1_0",
    "classic-g24": "GAMMA_2_4",
}

DEFINE = re.compile(r"^#define\s+(\w+)\s+(#[0-9a-fA-F]{6})\s*$")


def lower_camel(name: str) -> str:
    i = 0
    while i < len(name) and name[i].isupper():
        i += 1
    if i > 1:
        i -= 1 if i < len(name) else 0
    return name[:i].lower() + name[i:]


def gamma_block(path: Path, gamma: str) -> dict[str, str]:
    """Pull just the `#ifdef <gamma>` ... `#endif` region's color defines."""
    out, inside = {}, False
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line == f"#ifdef {gamma}":
            inside = True
            continue
        if inside and line == "#endif":
            inside = False
            continue
        if not inside:
            continue
        m = DEFINE.match(line)
        if m:
            out[lower_camel(m.group(1))] = m.group(2).lower()
    return out


def shadow(hexv: str, rule: dict) -> tuple[str, str]:
    """Reimplementation of the generator's derivation, for cross-checking."""
    ch = [int(hexv[i:i + 2], 16) for i in (1, 3, 5)]
    def enc(vals):
        return "#" + "".join(f"{max(0, min(255, int(v))):02x}" for v in vals)
    if any(c * rule["top"] > 255 for c in ch):
        top = enc(c + (255 - c) * rule["topFallback"] for c in ch)
    else:
        top = enc(c * rule["top"] for c in ch)
    return top, enc(c * rule["bottom"] for c in ch)


def main() -> int:
    ref = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REF
    if not ref.is_dir():
        print(f"SKIP: reference not available at {ref}", file=sys.stderr)
        return 0

    failures = 0
    for pid, gamma in GAMMA_FOR.items():
        doc = json.loads((PALETTES / f"{pid}.json").read_text())
        layer1 = doc["palette"]
        expected = gamma_block(ref / "BaseColorPalette", gamma)

        if not expected:
            print(f"FAIL {pid}: no {gamma} block found in BaseColorPalette")
            failures += 1
            continue

        for name, want in expected.items():
            got = layer1.get(name)
            if got != want:
                print(f"FAIL {pid}: {name} is {got}, BaseColorPalette says {want}")
                failures += 1
        print(f"ok   {pid}: {len(expected)} BaseColorPalette values match {gamma}")

        # Every role must resolve to a real layer-1 key or a derivation of one.
        for role, expr in doc["roles"].items():
            m = re.match(r"^(shadow|shade)\(\s*(\w+)\s*,", expr)
            key = m.group(2) if m else expr
            if key not in layer1:
                print(f"FAIL {pid}: role '{role}' references unknown color '{key}'")
                failures += 1

    # Shadow derivation spot-check, per the plan.
    rule = json.loads((PALETTES / "classic.json").read_text())["shadowRule"]
    top, bottom = shadow("#999999", rule)
    if (top, bottom) != ("#e5e5e5", "#545454"):
        print(f"FAIL shadow(#999999) = {top}/{bottom}, expected #e5e5e5/#545454")
        failures += 1
    else:
        print("ok   shadow(#999999) -> #e5e5e5 / #545454")

    # The light surfaces must not blow out to pure white.
    for surface in ("#c1c1c1", "#d6d6d6"):
        top, _ = shadow(surface, rule)
        if top == "#ffffff":
            print(f"FAIL topShadow({surface}) clamped to pure white")
            failures += 1
        else:
            print(f"ok   topShadow({surface}) -> {top}")

    print(f"\n{'FAILED' if failures else 'PASSED'} ({failures} problem(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
