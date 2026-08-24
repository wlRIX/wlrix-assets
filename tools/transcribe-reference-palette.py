#!/usr/bin/env python3
"""Build the layered wlRIX palette JSON files from the IRIX Scheme sources.

Layer 1 is transcribed verbatim from _docs/color-reference; layers 2/3 and the
metrics block are wlRIX's own, shared identically across a scheme's gamma bakes.

Two schemes so far. Classic is Indigo Magic, IRIX's default, and it is merged
from four scheme files. Gotham is IRIX's dark scheme and ships as one file, so
it names none of the Imd*/QuickHelp* colors Classic's roles bind -- which is why
roles are per-scheme and why a role may name a literal #rrggbb.

    ./transcribe-reference-palette.py [<color-reference-dir> [<palette-out-dir>]]

Both default to this checkout's siblings, which is right in a development
workspace and wrong anywhere else: _docs is untracked notes, not a repo, so a
fresh clone of wlrix-assets has to be told where the reference is.
"""
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
REF = _HERE.parents[2] / "_docs" / "color-reference"
OUT = _HERE.parents[1] / "palette"

# The gamma bakes every scheme is transcribed at. The 1.7 bake is the default and
# takes the scheme's bare id; the other two are suffixed.
GAMMAS = {
    "1.0": ("GAMMA_1_0", "-g10"),
    "1.7": ("GAMMA_1_7", ""),
    "2.4": ("GAMMA_2_4", "-g24"),
}

DEFINE = re.compile(r"^#define\s+(\w+)\s+(\S+)\s*$")
HEXCOLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

# Oz* names are byte-identical aliases of the Imd* ones (OzPalette is a verbatim
# copy of ImdPalette). Carrying both would put two keys on one color.
ALIASES = {"ozCltnPanelColor", "ozReadOnlyColor"}

# Layer 3. A value is a layer-1 key, a derivation -- shadow(<key>, top|bottom),
# shade/lighten/darken(<key>, <factor name>) -- or a literal #rrggbb.
# Bindings follow _docs/color-reference/Base/Base unless noted.
CLASSIC_ROLES = {
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

    # --- 4Dwm frame tones (Base/4DWmSpec) ---
    # The border and the titlebar are one Motif surface, so its three tones hang
    # off the same two colors the titles do. 4Dwm computed them itself and not
    # the way Motif computes a widget's, which is what the frame* factors are.
    # These eight reproduce the reference screenshots exactly; before this they
    # were eight literals typed into wlrix-compositor/src/decoration.rs, with
    # `#a59f80` appearing there *and* here under two different names.
    "titleActiveTopShadow":      "toward(wmActiveBackground, frameTop)",
    "titleActiveBottomShadow":   "shade(wmActiveBackground, frameBottom)",
    "titleActiveArmed":          "shade(wmActiveBackground, frameArm)",
    "titleInactiveTopShadow":    "toward(wmBackground, frameTop)",
    "titleInactiveBottomShadow": "shade(wmBackground, frameBottom)",
    "titleInactiveArmed":        "shade(wmBackground, frameArm)",

    # --- minimized-window tiles (4DWmSpec's *icon*) ---
    # Named iconTile* rather than icon*, because the icon* roles above are the
    # *desktop's* icons. These two are the tile a minimized window becomes.
    #
    # The tile face was sampled as #a8a8a8 and is bound to ImdLightGrey, two
    # levels away, so it tracks the gamma bakes instead of standing still.
    "iconTileFace":         "imdLightGrey",
    # The backdrop behind the window thumbnail, and so also the clear color a
    # thumbnail is captured against -- the letterboxing around an off-aspect
    # window has to match the tile. Sampled; no IRIX name is within 30 levels of
    # it, so it is the one literal here, and the one value that does not move
    # with the gamma bakes.
    "iconWell":             "#464a52",
}

# Motif shadow derivation. IRIX stored no shadow colors; the toolkit computed
# them from each widget's background at realize time.
#
# Top shadow is c*1.5 per channel, but that clamps to pure white on the lighter
# surfaces (basicBackground #c1c1c1, imdMenubarBackground #d6d6d6) and flattens
# the bevel exactly where there is the most of it. When any channel would clamp
# we instead move halfway to white, which preserves a visible highlight.
# Integer truncation throughout, matching Motif's C arithmetic.
#
# The frame* factors are 4Dwm's, not Motif's: the window frame was the window
# manager's to draw, and it did not use Motif's rule. `frameTop` moves toward
# white outright rather than multiplying-with-a-fallback, which is why it needs
# toward() and not shadow(). All three were fitted to the tones sampled from
# reference/window_decoration.png, and they reproduce every one of the eight
# active/inactive frame values exactly -- hence 0.603 rather than a round 0.6,
# which truncates one channel of the inactive frame a level too dark.
SHADOW_RULE = {
    "mode": "multiply-with-halfway-fallback",
    "top": 1.5,
    "topFallback": 0.5,
    "bottom": 0.55,
    "arm": 0.85,
    "frameTop": 0.58,
    "frameBottom": 0.603,
    "frameArm": 0.8,
}

# Gotham inverts the scheme, and three of Motif's factors do not survive that.
#
# `top` at 1.5 on a dark face is a 36-level highlight and the halfway-to-white
# fallback never fires at all, because nothing dark enough to be a Gotham
# surface can clamp; 1.9 puts the highlight back. `bottom` at 0.55 lands the
# dark side *at* the panel behind it -- #494949 shades to #282828 against a
# #2a2a2a panel -- so the bevel dissolves; 0.45 keeps it separate. And `arm`
# must go the other way: darkening an already-dark face by 0.85 is invisible,
# so a pressed Gotham widget lightens instead. Scale() already clamps at 255,
# so a factor above 1 needs no new code.
GOTHAM_SHADOW_RULE = {
    **SHADOW_RULE,
    "top": 1.9,
    "bottom": 0.45,
    "arm": 1.15,
    # How far below the panel the bare desktop sits. Classic names its desktop
    # gray outright (ImdDarkGrey, inherited from Base/ImdPalette); Gotham has to
    # derive one, because that inherited #555555 is *lighter* than its panel.
    "desktopShade": 0.65,
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


# Gotham binds the same roles as Classic; these are the ones where inheriting
# the shared Indigo Magic layer gives a light-scheme answer on a dark scheme.
#
# Everything not listed here is deliberately inherited, including the tooltip
# yellow (a quick-help popup is meant to shout in any scheme) and the icon
# tints, which are greys and white and read correctly on a dark desktop.
GOTHAM_ROLES = {
    **CLASSIC_ROLES,
    # ImdDarkGrey is #555555, which is *lighter* than Gotham's #2a2a2a panel --
    # it would put the desktop in front of the windows. Derived instead.
    "desktop":              "shade(basicBackground, desktopShade)",
    # ImdMenubarBackground is #d6d6d6, a near-white bar on a dark desktop.
    "menubarBackground":    "readOnlyBackground",
    # ImdCltnPanelColor is a mid steel blue; behind a dark login dialog it is
    # the brightest thing on the screen. Gotham's own dark blue instead.
    "loginBackground":      "alternateBackground5",
    # ImdLightGrey would make every minimized window a near-white tile.
    "iconTileFace":         "wmBackground",
    # Classic has to state this one outright; Gotham has a desaturated blue in
    # its own file that is what the literal was reaching for.
    "iconWell":             "drawingAreaBackground",
}


class Scheme:
    """One IRIX scheme: where its colors come from and how wlRIX binds them."""

    def __init__(self, title, own, roles, shadow, gammas=("1.0", "1.7", "2.4")):
        self.title = title
        self.own = own
        self.roles = roles
        self.shadow = shadow
        self.gammas = gammas


# IRIX composed a scheme from its *own* BaseColorPalette over the shared Indigo
# Magic layer, and that is why Gotham/ holds a single file. Transcribing it the
# same way is what lets Gotham bind ImdBlack and QuickHelpBackground at all --
# names its own file never mentions -- and keeps layer 1 verbatim rather than
# hand-filled.
SHARED = ("Base/ImdPalette", "Base/HighlightPalette", "Base/Base")

SCHEMES = {
    "classic": Scheme(
        title="wlRIX Classic",
        own=("Base/BaseColorPalette",),
        roles=CLASSIC_ROLES,
        shadow=SHADOW_RULE,
    ),
    "gotham": Scheme(
        title="wlRIX Gotham",
        own=("Gotham/BaseColorPalette",),
        roles=GOTHAM_ROLES,
        shadow=GOTHAM_SHADOW_RULE,
        # The 1.7 bake only. The other two exist for Classic because the Avalonia
        # theme offers three gammas of it; nobody has looked at Gotham yet, and
        # two more files nothing selects is not worth carrying.
        gammas=("1.7",),
    ),
}

# A role value that is not a plain layer-1 key. Kept in step with
# palettegen/Palette.cs, which resolves the same grammar.
DERIVED = re.compile(r"^(shadow|shade|toward)\(")
LITERAL = re.compile(r"^#[0-9a-fA-F]{6}$")


def lower_camel(name: str) -> str:
    """BasicBackground -> basicBackground; WMBackground -> wmBackground."""
    i = 0
    while i < len(name) and name[i].isupper():
        i += 1
    if i > 1:
        i -= 1 if i < len(name) else 0
    return name[:i].lower() + name[i:]


def parse(path: Path, gamma: str) -> tuple[dict[str, str], bool | None]:
    """Walk the file honoring #ifdef/#ifndef/#else/#endif for `gamma`.

    Returns the colors and the scheme's own IsDarkScheme flag, if it sets one.
    """
    out: dict[str, str] = {}
    dark: bool | None = None
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
        if not m:
            continue
        # Layer 1 is colors, but the scheme also declares whether it is a dark
        # one, and that decides things no color can -- which way a pressed face
        # moves, for one. Carried through rather than restated in Python.
        if m.group(1) == "IsDarkScheme":
            dark = m.group(2).upper() == "TRUE"
            continue
        if not HEXCOLOR.match(m.group(2)):
            continue
        key = lower_camel(m.group(1))
        if key in ALIASES:
            continue
        if key in out and out[key] != m.group(2):
            sys.exit(f"conflict {key} in {path.name}@{gamma}")
        out[key] = m.group(2)
    if stack:
        sys.exit(f"unbalanced conditionals in {path.name}")
    return out, dark


def collect(scheme: Scheme, flag: str) -> tuple[dict[str, str], bool]:
    """Layer 1 for one scheme at one gamma: the shared layer, then its own over it."""
    colors: dict[str, str] = {}
    for src in SHARED:
        found, _ = parse(REF / src, flag)
        for k, v in found.items():
            # The shared files must agree with each other. They are one layer
            # split across three files, so a disagreement is a transcription
            # error, not a scheme making a choice.
            if k in colors and colors[k] != v:
                sys.exit(f"cross-file conflict {k}@{flag}")
            colors[k] = v

    dark = False
    overridden: list[str] = []
    for src in scheme.own:
        found, flagged = parse(REF / src, flag)
        if flagged is not None:
            dark = flagged
        for k, v in found.items():
            # A scheme *is* its overrides of the shared layer, so unlike above
            # this is expected. Reported so the deviation stays reviewable.
            if k in colors and colors[k] != v:
                overridden.append(k)
            colors[k] = v

    if overridden:
        print(f"    {len(overridden)} shared colors overridden: "
              f"{', '.join(sorted(overridden))}", file=sys.stderr)
    return colors, dark


def main() -> None:
    global REF, OUT
    if len(sys.argv) > 1:
        REF = Path(sys.argv[1])
    if len(sys.argv) > 2:
        OUT = Path(sys.argv[2])
    if len(sys.argv) > 3:
        sys.exit(__doc__.strip().splitlines()[-3].strip())
    if not REF.is_dir():
        sys.exit(f"no color reference at {REF}; pass its path as the first argument")

    for scheme_id, scheme in SCHEMES.items():
        for gamma in scheme.gammas:
            flag, suffix = GAMMAS[gamma][0], GAMMAS[gamma][1]
            palette_id = scheme_id + suffix
            print(f"{palette_id} ({flag}):", file=sys.stderr)
            colors, dark = collect(scheme, flag)

            missing = [f"{name} -> {expr}"
                       for name, expr in scheme.roles.items()
                       if not DERIVED.match(expr)
                       and not LITERAL.match(expr)
                       and expr not in colors]
            if missing:
                sys.exit(f"roles reference unknown colors @{flag}: {missing}")

            # Every derivation's basis has to exist too, or the error surfaces
            # three tools downstream as a C# exception with no scheme name in it.
            for name, expr in scheme.roles.items():
                m = re.match(r"^\w+\(\s*(\w+)\s*,\s*(\w+)\s*\)$", expr)
                if not m:
                    continue
                if m.group(1) not in colors:
                    sys.exit(f"role {name} derives from unknown color {m.group(1)}@{flag}")
                if m.group(2) not in scheme.shadow:
                    sys.exit(f"role {name} names unknown factor {m.group(2)}@{flag}")

            doc = {
                "name": f"{scheme.title} (gamma {gamma})",
                "id": palette_id,
                "gamma": gamma,
                "dark": dark,
                "source": "IRIX 6.5 X11 schemes: "
                          + ", ".join(scheme.own + SHARED),
                "$comment": (
                    "GENERATED by tools/transcribe-reference-palette.py. 'palette' is "
                    "transcribed verbatim from the IRIX scheme files and must not "
                    "be hand-edited; 'roles' is wlRIX's own mapping and is the "
                    "layer to change when retuning."
                ),
                "palette": dict(sorted(colors.items())),
                "shadowRule": scheme.shadow,
                "roles": scheme.roles,
                "metrics": METRICS,
            }
            dest = OUT / f"{palette_id}.json"
            dest.write_text(json.dumps(doc, indent=2) + "\n")
            print(f"    {dest}: {len(colors)} colors, {len(scheme.roles)} roles"
                  f"{', dark' if dark else ''}", file=sys.stderr)


if __name__ == "__main__":
    main()
