#!/usr/bin/env python3
"""Verify the palette JSON against the IRIX scheme sources and the shadow rule.

The failure this guards against is a hand-edited or invented color drifting
into layer 1, which is the exact problem the layered palette exists to prevent.
Re-parses the reference independently of transcribe-reference-palette.py rather than
trusting that script's own output.

    python3 tools/verify-palette.py [path-to-color-reference]

`path-to-color-reference` is the directory holding `Base/` and `Gotham/`; it
defaults to this checkout's sibling `_docs/`, which exists in a development
workspace and nowhere else.

Exits non-zero on any mismatch.
"""
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
DEFAULT_REF = _HERE.parents[2] / "_docs" / "color-reference"
PALETTES = _HERE.parents[1] / "palette"

# Which scheme file each palette's layer 1 must match, and at which gamma. The
# scheme's own BaseColorPalette only -- the shared Imd/Highlight/Base layer under
# it is checked by the cross-file agreement in the transcriber, and re-checking it
# here would just be asserting that three files still equal themselves.
GAMMA_FOR = {
    "classic": ("Base", "GAMMA_1_7"),
    "classic-g10": ("Base", "GAMMA_1_0"),
    "classic-g24": ("Base", "GAMMA_2_4"),
    "gotham": ("Gotham", "GAMMA_1_7"),
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


def toward(hexv: str, factor: float) -> str:
    """Reimplementation of the generator's `toward()`, for cross-checking."""
    ch = [int(hexv[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{max(0, min(255, int(c + (255 - c) * factor))):02x}" for c in ch)


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
    for pid, (scheme, gamma) in GAMMA_FOR.items():
        doc = json.loads((PALETTES / f"{pid}.json").read_text())
        layer1 = doc["palette"]
        expected = gamma_block(ref / scheme / "BaseColorPalette", gamma)

        if not expected:
            print(f"FAIL {pid}: no {gamma} block in {scheme}/BaseColorPalette")
            failures += 1
            continue

        for name, want in expected.items():
            got = layer1.get(name)
            if got != want:
                print(f"FAIL {pid}: {name} is {got}, "
                      f"{scheme}/BaseColorPalette says {want}")
                failures += 1
        print(f"ok   {pid}: {len(expected)} {scheme} values match {gamma}")

        # Every role must resolve to a real layer-1 key, a derivation of one, or a
        # literal. A derivation's factor has to exist in this scheme's own rule --
        # Gotham retunes three of them, and a role naming a factor it dropped would
        # otherwise surface as a C# exception two tools downstream.
        for role, expr in doc["roles"].items():
            if re.match(r"^#[0-9a-fA-F]{6}$", expr):
                continue
            m = re.match(r"^(shadow|shade|toward)\(\s*(\w+)\s*,\s*(\w+)\s*\)$", expr)
            key = m.group(2) if m else expr
            if key not in layer1:
                print(f"FAIL {pid}: role '{role}' references unknown color '{key}'")
                failures += 1
            if m and m.group(1) != "shadow" and m.group(3) not in doc["shadowRule"]:
                print(f"FAIL {pid}: role '{role}' names unknown factor '{m.group(3)}'")
                failures += 1

    # Shadow derivation spot-check, per the plan.
    rule = json.loads((PALETTES / "classic.json").read_text())["shadowRule"]
    top, bottom = shadow("#999999", rule)
    if (top, bottom) != ("#e5e5e5", "#545454"):
        print(f"FAIL shadow(#999999) = {top}/{bottom}, expected #e5e5e5/#545454")
        failures += 1
    else:
        print("ok   shadow(#999999) -> #e5e5e5 / #545454")

    # The 4Dwm frame tones. These were eight literals in the compositor until the
    # `toward`/`frame*` derivation replaced them, so this is the check that the
    # replacement still lands on the colors sampled from the reference.
    for basis, want_top, want_bottom, want_arm in (
        ("#a59f80", "#d9d6c9", "#635f4d", "#847f66"),
        ("#808080", "#c9c9c9", "#4d4d4d", "#666666"),
    ):
        ch = [int(basis[i:i + 2], 16) for i in (1, 3, 5)]
        enc = lambda vals: "#" + "".join(f"{max(0, min(255, int(v))):02x}" for v in vals)
        got = (toward(basis, rule["frameTop"]),
               enc(c * rule["frameBottom"] for c in ch),
               enc(c * rule["frameArm"] for c in ch))
        if got != (want_top, want_bottom, want_arm):
            print(f"FAIL frame({basis}) = {'/'.join(got)}, "
                  f"expected {want_top}/{want_bottom}/{want_arm}")
            failures += 1
        else:
            print(f"ok   frame({basis}) -> {want_top} / {want_bottom} / {want_arm}")

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
