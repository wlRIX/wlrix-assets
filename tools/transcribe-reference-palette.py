#!/usr/bin/env python3
"""Build the layered wlRIX palette JSON files from the IRIX Scheme sources.

Layer 1 is transcribed verbatim from _docs/color-reference; layers 2/3 and the
metrics block are wlRIX's own, shared identically across the three gamma bakes.
"""
import json
import re
import sys
from pathlib import Path

REF = Path("/mnt/Dev/wlRIX/_docs/color-reference/Base")
OUT = Path("/mnt/Dev/wlRIX/wlrix-assets/palette")

SOURCES = ("BaseColorPalette", "ImdPalette", "HighlightPalette", "Base")
GAMMAS = {
    "1.0": ("GAMMA_1_0", "classic-g10.json"),
    "1.7": ("GAMMA_1_7", "classic.json"),
    "2.4": ("GAMMA_2_4", "classic-g24.json"),
}

DEFINE = re.compile(r"^#define\s+(\w+)\s+(\S+)\s*$")
HEXCOLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

# Oz* names are byte-identical aliases of the Imd* ones (OzPalette is a verbatim
# copy of ImdPalette). Carrying both would put two keys on one color.
ALIASES = {"ozCltnPanelColor", "ozReadOnlyColor"}

# Layer 3. Values are either a layer-1 key, or shadow(<key>, top|bottom).
# Bindings follow _docs/color-reference/Base/Base unless noted.
ROLES = {
    # --- structural, with no direct IRIX counterpart ---
    # The hard 1px outline around every chiselled widget. Motif drew this with
    # the widget's foreground; IRIX never gave it a palette name of its own.
    "outerLine":            "imdBlack",
    # Armed/pressed face. Motif's XmNarmColor, computed by darkening the
    # background rather than stored in the scheme.
    "armed":                "shade(buttonBackground, arm)",
    # Attention color: default-button outline and the checkbox check itself.
    # IRIX used CheckColor for both.
    "accent":               "checkColor",

    # --- surfaces ---
    "panel":                "basicBackground",           # *background
    "face":                 "buttonBackground",          # *XmPushButton.background
    "readOnly":             "readOnlyBackground",
    "listBackground":       "scrolledListBackground",    # *XmList.background
    "textBackground":       "textBackground",            # multi-line XmText
    "textFieldBackground":  "textFieldBackground",       # single-line XmTextField
    "viewBackground":       "drawingAreaBackground",     # *XmDrawingArea.background
    "menubarBackground":    "imdMenubarBackground",
    "tooltipBackground":    "quickHelpBackground",       # *VkQuickHelpPopup*background
    "tooltipForeground":    "quickHelpForeground",
    "indicatorBackground":  "indicatorBackground",

    # --- text ---
    "foreground":           "textForeground",
    "disabledForeground":   "disabledTextForeground",
    "selectionBackground":  "textSelectedBackground",    # *selectionBackground
    "selectionForeground":  "textSelectedForeground",

    # --- bevels: Motif derived these per-widget from the background (see 1.2) ---
    "panelTopShadow":       "shadow(basicBackground, top)",
    "panelBottomShadow":    "shadow(basicBackground, bottom)",
    "faceTopShadow":        "shadow(buttonBackground, top)",
    "faceBottomShadow":     "shadow(buttonBackground, bottom)",
    "troughTopShadow":      "shadow(scrollBarTroughColor, top)",
    "troughBottomShadow":   "shadow(scrollBarTroughColor, bottom)",
    "textTopShadow":        "shadow(textFieldBackground, top)",
    "textBottomShadow":     "shadow(textFieldBackground, bottom)",
    # IRIX inverts the pixmap-button bevel deliberately; these are explicit,
    # never derived.
    "pixmapButtonFill":         "pixmapButtonFillColor",
    "pixmapButtonTopShadow":    "pixmapButtonTopShadowColor",
    "pixmapButtonBottomShadow": "pixmapButtonBottomShadowColor",

    # --- scrollbars / sliders ---
    "trough":               "scrollBarTroughColor",
    "scrollBarControl":     "scrollBarControlBackground",

    # --- indicators ---
    "checkColor":           "checkColor",                # *selectColor, *checkColor
    "radioColor":           "radioColor",
    "lightRadioFill":       "lightRadioFillColor",
    "disabledCheck":        "disabledCheckColor",
    "selectFill":           "selectFillColor",           # *lampColor
    "indicatorLight":       "indicatorLightColor",

    # --- window manager / desktop (Base/4DWmSpec) ---
    "titleActive":          "wmActiveBackground",        # *client*activeBackground
    "titleActiveText":      "wmActiveForeground",
    "titleInactive":        "wmBackground",              # *client*background
    "titleInactiveText":    "wmForeground",
    "desktop":              "imdDarkGrey",               # *newBackground0
    # The greeter's steel-blue backdrop, as IRIX's clogin had.
    "loginBackground":      "imdCltnPanelColor",
    # Lock screen. Deliberately black rather than the desktop color, so a
    # locked output never resembles a live session.
    "locked":               "imdBlack",

    # --- desktop icons (wlrix-desktop) ---
    # An icon is drawn as a coverage mask and tinted by its state, the way the
    # Indigo Magic desktop did: resting icons are knocked back so the desktop
    # reads as a whole, the one under the pointer comes up to full white, and
    # the selected one takes the same yellow IRIX used for a lit indicator.
    "iconTint":             "imdLightGrey",
    "iconTintHover":        "imdWhite",
    "iconTintSelected":     "selectFillColor",           # *lampColor
    # The filename under the icon. Selected labels invert onto the tint.
    "iconLabel":            "imdWhite",
    "iconLabelSelected":    "imdBlack",

    # --- window chrome ---
    # The wireframe drawn while a window is moved or resized non-opaquely: a
    # red outline of where the frame would land. IRIX drew it in plain red on
    # the root window, which is what `redColor` is.
    "dragOutline":          "redColor",

    # --- status / links ---
    "error":                "errorColor",
    "warning":              "warningColor",
    "information":          "informationColor",
    "link":                 "linkForegroundColor",
    "linkVisited":          "visitedLinkForegroundColor",
    "linkActive":           "activeLinkForegroundColor",

    # --- alternate panels; convention documented in Base/SaSpec ---
    "readOnlyPanel":        "alternateBackground6",
    "readWritePanel":       "alternateBackground5",
}

# Motif shadow derivation. IRIX stored no shadow colors; the toolkit computed
# them from each widget's background at realize time.
#
# Top shadow is c*1.5 per channel, but that clamps to pure white on the lighter
# surfaces (basicBackground #c1c1c1, imdMenubarBackground #d6d6d6) and flattens
# the bevel exactly where there is the most of it. When any channel would clamp
# we instead move halfway to white, which preserves a visible highlight.
# Integer truncation throughout, matching Motif's C arithmetic.
SHADOW_RULE = {
    "mode": "multiply-with-halfway-fallback",
    "top": 1.5,
    "topFallback": 0.5,
    "bottom": 0.55,
    "arm": 0.85,
}

# Geometry from Base/Base and Base/SgiSpec. Not colors, but the bevel widths are
# what make the shadows read correctly, so they travel with the palette.
METRICS = {
    "shadowThickness": {
        "default": 2,
        "scrollBar": 3,       # *XmScrollBar.shadowThickness
        "scrolledWindow": 3,  # *XmScrolledWindow.shadowThickness
        "list": 3,            # *XmList*shadowThickness
        "scale": 3,           # *XmScale*shadowThickness
        "text": 4,            # *XmText.shadowThickness / *XmTextField
    },
    "scrollBarSize": 18,      # *XmScrollBar*width / *height
    "indicatorSize": 15,      # *XmMenuShell*XmToggleButton.indicatorSize
    "textMargin": {"height": 4, "width": 5},
    "lightThreshold": 87,     # .lightThreshold
}


def lower_camel(name: str) -> str:
    """BasicBackground -> basicBackground; WMBackground -> wmBackground."""
    i = 0
    while i < len(name) and name[i].isupper():
        i += 1
    if i > 1:
        i -= 1 if i < len(name) else 0
    return name[:i].lower() + name[i:]


def parse(path: Path, gamma: str) -> dict[str, str]:
    """Walk the file honoring #ifdef/#ifndef/#else/#endif for `gamma`."""
    out: dict[str, str] = {}
    stack: list[bool] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("#ifdef "):
            stack.append(line.split(None, 1)[1].strip() == gamma)
            continue
        if line.startswith("#ifndef "):
            stack.append(line.split(None, 1)[1].strip() != gamma)
            continue
        if line == "#else":
            stack[-1] = not stack[-1]
            continue
        if line == "#endif":
            stack.pop()
            continue
        if not all(stack):
            continue
        m = DEFINE.match(line)
        if not m or not HEXCOLOR.match(m.group(2)):
            continue
        key = lower_camel(m.group(1))
        if key in ALIASES:
            continue
        if key in out and out[key] != m.group(2):
            sys.exit(f"conflict {key} in {path.name}@{gamma}")
        out[key] = m.group(2)
    if stack:
        sys.exit(f"unbalanced conditionals in {path.name}")
    return out


def main() -> None:
    for gamma, (flag, filename) in GAMMAS.items():
        colors: dict[str, str] = {}
        for src in SOURCES:
            for k, v in parse(REF / src, flag).items():
                if k in colors and colors[k] != v:
                    sys.exit(f"cross-file conflict {k}@{flag}")
                colors[k] = v

        missing = [r for r in ROLES.values()
                   if not re.match(r"^(shadow|shade)\(", r) and r not in colors]
        if missing:
            sys.exit(f"roles reference unknown colors @{flag}: {missing}")

        doc = {
            "name": f"wlRIX Classic (gamma {gamma})",
            "id": Path(filename).stem,
            "gamma": gamma,
            "source": (
                "IRIX 6.5 X11 schemes: Base/BaseColorPalette, Base/ImdPalette, "
                "Base/HighlightPalette, Base/Base"
            ),
            "$comment": (
                "GENERATED by tools/transcribe-reference-palette.py. 'palette' is "
                "transcribed verbatim from the IRIX scheme files and must not "
                "be hand-edited; 'roles' is wlRIX's own mapping and is the "
                "layer to change when retuning."
            ),
            "palette": dict(sorted(colors.items())),
            "shadowRule": SHADOW_RULE,
            "roles": ROLES,
            "metrics": METRICS,
        }
        dest = OUT / filename
        dest.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"{dest}: {len(colors)} colors, {len(ROLES)} roles",
              file=sys.stderr)


if __name__ == "__main__":
    main()
