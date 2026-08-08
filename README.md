# wlrix-assets

Shared branding and look-and-feel data for wlRIX, consumed by **both** the Rust system components and the C# apps so
everything renders identically.

- **License:** MIT (freely reusable)

## Layout

| Directory     | Contents                                                          |
|---------------|-------------------------------------------------------------------|
| `palette/`    | Canonical color palette — the single source of truth for theming. |
| `icons/`      | Icon theme (IRIX Indigo Magic icon set).                          |
| `cursors/`    | Cursor theme.                                                     |
| `wallpapers/` | Default wallpapers / backgrounds.                                 |

## Installing

```sh
sudo just install    # or `just install-assets` from wlrix-epoch
```

Only `wallpapers/` is installed, to `$PREFIX/share/wlrix/wallpapers/`. `wlrix-bg`'s system default config names
`scatter.png` there by absolute path, so a machine without this installed comes up with a plain gray desktop and a line
in the session log about the missing file.

`palette/` is deliberately not installed: it is a *build* input, resolved ahead of time by `tools/palettegen` into
native sources that are checked in to the consuming repos, so that nothing parses it at runtime. `icons/` and
`cursors/` are empty; when they are filled they will want the XDG icon-theme and XCursor layouts under `share/icons/`,
which is where the loaders actually look, rather than this directory.

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
