# wlrix-assets

Shared branding and look-and-feel data for wlRIX, consumed by **both** the Rust system components and the C# apps so
everything renders identically.

- **License:** MIT (freely reusable)

## Layout

| Directory     | Contents                                                          |
|---------------|-------------------------------------------------------------------|
| `palette/`    | Canonical color palette — the single source of truth for theming. |
| `icons/`      | Icon theme (IRIX Indigo Magic icon set).                          |
| `cursors/`    | Cursor theme (`sgi`, the IRIX pointer set).                       |
| `wallpapers/` | Default wallpapers / backgrounds.                                 |

## Installing

```sh
sudo just install    # or `just install-assets` from wlrix-epoch
```

Two directories are installed, to two different places:

| Directory     | Installed to                      | Who reads it                                                              |
|---------------|-----------------------------------|---------------------------------------------------------------------------|
| `wallpapers/` | `$PREFIX/share/wlrix/wallpapers/` | `wlrix-bg`, by absolute path from its system default config.              |
| `cursors/sgi` | `$PREFIX/share/icons/sgi/`        | every XCursor loader, by theme *name*: the compositor, GTK, Qt, XWayland. |

A machine without the wallpapers comes up with a plain gray desktop and a line in the session log about the missing
file. Without the cursor theme the pointer falls back to whatever theme the machine already has — usually Adwaita — and
the compositor says so in its log.

The cursor theme goes under `share/icons/` rather than `share/wlrix/` because that is the only place it would be found:
libXcursor, libwayland-cursor and the `xcursor` crate the compositor uses all search `XDG_DATA_DIRS/icons`, `~/.icons`
and a couple of legacy paths, and nothing can point them at a private directory except `XCURSOR_PATH`. **A prefix other
than `/usr` therefore needs `XCURSOR_PATH` to include `$PREFIX/share/icons`**, which `install` says on the way out.

`palette/` is deliberately not installed: it is a *build* input, resolved ahead of time by `tools/palettegen` into
native sources that are checked in to the consuming repos, so that nothing parses it at runtime. `icons/` is still
empty; when it is filled it will want the XDG icon-theme layout under `share/icons/`, the same way the cursors do.

## Cursors

`cursors/sgi/` is the IRIX pointer set as an XCursor theme: 49 cursors at 32×32, plus 72 symlinked aliases covering the
legacy X11 names (`left_ptr`, `xterm`, `watch`), the MD5-named ones toolkits use for drag-and-drop, and the modern CSS
names (`default`, `ns-resize`, `grabbing`). The install preserves the links as links rather than copying through them.

**The eight resize cursors are directional**, as IRIX drew them: `top_left_corner` points up-left, `bottom_right_corner`
points down-right, and the four sides are an arrow against a bar. So `nw-resize` … `se-resize` and `n-resize` …
`w-resize` each alias the drawing for *that* corner or edge, which is how DMZ — the freedesktop reference theme — maps
them too. As imported, `n-resize` and `e-resize` pointed at the symmetric double-headed arrows (`size_ver`, `size_hor`)
instead; those two names now follow DMZ, and the symmetric drawings keep the `ns-resize`/`ew-resize` names, which is
what an axis with no near end actually means.

`wlrix-compositor`'s system default config names this theme and its size, and the compositor hands both to clients
through the session, so the pointer is the same one over the desktop, over a GTK window and over XWayland. Which shape
is drawn for a given `wl_pointer.set_cursor` or `cursor-shape-v1` request is the compositor's business — see its README.

The theme carries **only 32×32 images**, which is why the default config asks for size 32: a client told 24 would
resample the 32-pixel artwork and lose the hard IRIX edges. On a HiDPI screen the compositor scales it up rather than
picking a larger frame, because there is not one.

## Palette

The palette is the single source of truth for color across wlRIX. Nothing downstream parses it at runtime —
`tools/palettegen` resolves it ahead of time and emits native sources for each consumer, so the compositor and the apps
cannot drift apart.

| File                            | Gamma | Role                                         |
|---------------------------------|-------|----------------------------------------------|
| `palette/indigo-magic.json`     | 1.7   | Default. `wlrix.palette.json` re-exports it. |
| `palette/indigo-magic-g10.json` | 1.0   | Lightest bake.                               |
| `palette/indigo-magic-g24.json` | 2.4   | Darkest bake.                                |

Each file has three layers:

1. **`palette`** — the IRIX names and values, transcribed verbatim from the IRIX 6.5 X11 scheme files. **Never hand-edit
   this.** Regenerate it with
   `tools/transcribe-reference-palette.py`, which reads the reference scheme files.
2. **`shadowRule`** — how bevel shadows are derived. IRIX stored none; Motif computed them per widget from the
   background. Top shadow multiplies by 1.5, falling back to halfway-to-white where that would clamp to pure white.
3. **`roles`** — wlRIX's own semantic names (`face`, `panel`, `viewBackground`,
   `titleActive`, …), each pointing at a layer-1 color or a derivation of one. **This is the layer to edit when
   retuning.**

There is also a `metrics` block carrying the bevel thicknesses and widget sizes from the same specs, since the shadows
only read correctly at the right widths.

### Generating

From `wlrix-epoch`:

```sh
just palette        # regenerate
just check-palette  # fail if the checked-in output is stale
```

This writes `wlrix-avalonia/src/Wlrix.Avalonia/Schemes/*.axaml` (+ `Brushes.axaml`)
and `wlrix-compositor/src/palette.rs`. Those files are checked in, so neither build depends on the generator having been
run; they carry a do-not-edit header.

### Verifying

```sh
python3 tools/verify-palette.py
```

Re-parses the IRIX reference independently and asserts every layer-1 value matches, that every role resolves, and that
the shadow derivation still lands on its expected values. Run it after touching the palette.
