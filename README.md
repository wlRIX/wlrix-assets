# wlrix-assets

Shared branding and look-and-feel data for wlRIX, consumed by **both** the Rust system components and the C# apps so
everything renders identically.

- **License:** MIT (freely reusable)

## Layout

| Directory     | Contents                                                          |
|---------------|-------------------------------------------------------------------|
| `palette/`    | Canonical color palette — the single source of truth for theming. |
| `themes/`     | The wlRIX GTK stylesheets and their titlebar assets.              |
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

## GTK theme

`themes/wlRIX/` makes a GTK application's own headerbar look like the titlebar row
`wlrix-compositor` draws around it. GTK never negotiates `xdg-decoration`, so the compositor gives
it the IRIX border and no titlebar and the client draws its own bar inside that frame; without
this the bar is an Adwaita slab in an IRIX border.

| Path | Written by |
|------|------------|
| `gtk-3.0/wlrix.css`, `gtk-4.0/wlrix.css` | by hand. Structure: sizes, resets, which nodes to reach. |
| `gtk-3.0/schemes/<id>.css`, `gtk-4.0/schemes/<id>.css` | generated. Colors, and which asset goes on which button. |
| `assets/<id>/*.svg` | generated. Twenty per scheme: four states each of menu, minimize, maximize, maximized and close. |

The generated half comes from **`wlrix-compositor --dump-gtk-theme`**, not from `palettegen`. Only
the compositor knows what a titlebar button looks like, and `decoration_quads()` hands back the
whole frame as a list of colored rectangles -- so an asset is that list written out as SVG, one
`<rect>` per quad. Lossless, because the source really is rectangles, and it scales to any HiDPI
factor in a way no screen capture would. Regenerate with `just gtk-theme` from `wlrix-epoch`;
`just check-gtk-theme` fails if the checked-in output is stale.

The bar itself has no asset. A Motif bevel is not a CSS border -- its top and bottom shadows run
the full width and the left and right pair is inset between them, while a CSS border mitres its
corners -- but four inset `box-shadow`s draw it exactly, and then it takes its colors from
`@define-color` instead of an image. A `border-image` nine-slice would have been the obvious
answer and does not work: GTK 3 parses `border-image-slice: 2 fill` and ignores the `fill`,
leaving the middle unpainted.

### How it reaches a window

`wlrix-settings-daemon` writes two `@import` lines into `~/.config/gtk-{3,4}.0/gtk.css` naming the
structural sheet and the current scheme's, inside a marked block that leaves the rest of the file
alone. There is no `index.theme` and `gtk-theme-name` is never set to `wlRIX`: this is a pair of
stylesheets rather than a complete GTK theme, and libadwaita ignores `gtk-theme-name` regardless.

Two things it cannot do, both measured rather than assumed:

- **A running GTK application does not pick up a scheme change.** GTK does not reload `gtk.css`
  when it changes, so the new scheme reaches applications started afterwards. KDE closes this gap
  with a GTK 3 module (`colorreload-gtk-module` in the reference config under
  `_docs/kde-config-ref`); GTK 4 dropped modules, so its half is the settings portal.
- **The button layout comes from the Settings portal.** On Wayland GTK reads
  `gtk-decoration-layout` from `org.freedesktop.impl.portal.Settings` and ignores `settings.ini`
  for it; `xdg-desktop-portal-wlrix` reports `menu:minimize,maximize`. GTK 3 asks a portal only
  when `GTK_USE_PORTAL=1`, which `start-wlrix.sh` exports; GTK 4 asks unconditionally. The
  stylesheets still style the close button rather than hiding it, because the layout is only ours
  where that portal is reached. Where it is, there is no close button — as on IRIX, where a
  right-click on the compositor's border opens the window menu and Close is in it.

  GTK will not draw the *menu* button: GTK 3 does so only for an application with an app menu,
  and GTK 4 not at all. The layout asks for it anyway, since it costs nothing and says what is
  meant.

## Palette

The palette is the single source of truth for color across wlRIX. Nothing downstream parses it at runtime —
`tools/palettegen` resolves it ahead of time and emits native sources for each consumer, so the compositor and the apps
cannot drift apart.

| File                         | Id            | Gamma | Role                                                                 |
|------------------------------|---------------|-------|----------------------------------------------------------------------|
| `palette/classic.json`       | `classic`     | 1.7   | Default — Indigo Magic. `wlrix.palette.json` re-exports it.          |
| `palette/classic-g10.json`   | `classic-g10` | 1.0   | Lightest bake.                                                       |
| `palette/classic-g24.json`   | `classic-g24` | 2.4   | Darkest bake.                                                        |
| `palette/gotham.json`        | `gotham`      | 1.7   | IRIX's dark scheme. 1.7 only — it was never baked for the other two. |

The **id** is what a config file names (`[appearance] palette = "gotham"`) and what the settings daemon writes; a
component given an id it does not ship falls back to `classic` and says so in its log.

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

This writes:

| Output                                                     | Consumer                                                        |
|------------------------------------------------------------|-----------------------------------------------------------------|
| `wlrix-avalonia/…/Schemes/<Scheme>.axaml`                   | one `ResourceDictionary` per scheme, merged by `WlrixTheme`.    |
| `wlrix-avalonia/…/Schemes/Brushes.axaml`                    | one brush per color key, scheme-independent.                    |
| `wlrix-avalonia/…/Schemes/SchemeCatalog.g.cs`               | `WlrixSchemes.All` — id, name, gamma, dark flag, resource URI.  |
| `wlrix-ui/src/palette/generated.rs`                         | the `Palette` struct and one static per scheme, for every Rust component. |

Those files are checked in, so neither build depends on the generator having been run; they carry a do-not-edit header.

The catalog is why a new palette JSON is one edit: `wlrix-ui` gets a new `Palette` and the theme gets a new dictionary
*and* a new entry in every scheme picker, from the same run. Nothing has a hand-kept list of scheme names — not the
theme, not the settings daemon, and not the Color Schemes panel.

### Verifying

```sh
python3 tools/verify-palette.py
```

Re-parses the IRIX reference independently and asserts every layer-1 value matches, that every role resolves, and that
the shadow derivation still lands on its expected values. Run it after touching the palette.
