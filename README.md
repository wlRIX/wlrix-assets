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
| `images/`     | Pictures for minimized-window icons, one per application.         |
| `avatars/`    | Stock account pictures, square.                                    |
| `maps/`       | The world map in the International panel (NASA Blue Marble).      |

## Installing

```sh
sudo just install    # or `just install-assets` from wlrix-epoch
```

Everything but `palette/` is installed, to three different places:

| Directory     | Installed to                      | Who reads it                                                                 |
|---------------|-----------------------------------|------------------------------------------------------------------------------|
| `wallpapers/` | `$PREFIX/share/wlrix/wallpapers/` | `wlrix-bg`, by absolute path from its system default config.                 |
| `images/`     | `$PREFIX/share/wlrix/images/`     | `wlrix-compositor`, by application id, for minimized-window icons.           |
| `avatars/`    | `$PREFIX/share/wlrix/avatars/`    | User Accounts (`wlrix-settings-users`), as the pictures it offers.           |
| `maps/`       | `$PREFIX/share/wlrix/maps/`       | the International panel (`wlrix-settings-international`), behind its buttons. |
| `cursors/sgi` | `$PREFIX/share/icons/sgi/`        | every XCursor loader, by theme *name*: the compositor, GTK, Qt, XWayland.    |
| `icons/wlrix` | `$PREFIX/share/icons/wlrix/`      | every icon loader, by theme *name*: the file manager, the desktop, the tray. |

A machine without the wallpapers comes up with a plain gray desktop and a line in the session log about the missing
file. Without the cursor theme the pointer falls back to whatever theme the machine already has — usually Adwaita — and
the compositor says so in its log.

The cursor theme goes under `share/icons/` rather than `share/wlrix/` because that is the only place it would be found:
libXcursor, libwayland-cursor and the `xcursor` crate the compositor uses all search `XDG_DATA_DIRS/icons`, `~/.icons`
and a couple of legacy paths, and nothing can point them at a private directory except `XCURSOR_PATH`. **A prefix other
than `/usr` therefore needs `XCURSOR_PATH` to include `$PREFIX/share/icons`**, which `install` says on the way out.

`palette/` is deliberately not installed: it is a *build* input, resolved ahead of time by `tools/palettegen` into
native sources that are checked in to the consuming repos, so that nothing parses it at runtime.

## Minimize pictures

`images/` is the artwork the compositor draws in a minimized window's icon tile, the way 4Dwm did — fixed per
application rather than a snapshot of what the window happened to be showing.

A file is named for the window's **application id**: the Wayland `app_id`, or the X11 `WM_CLASS` for an XWayland
client, plus `.png`. That is why the case is inconsistent here — `Blender.png` and `Lutris.png` are `WM_CLASS` names
and capitalized, while `steam.png` and `microsoft-edge.png` are app ids and are not. The lookup retries
case-insensitively, so either spelling finds either file, and **`default.png` answers for every application without
artwork of its own**.

**An alias is a relative symlink**, not a second copy: `Alacritty.png -> com.wlrix.terminal.png` is how a terminal
emulator with no artwork of its own comes out looking like the wlRIX terminal rather than falling back to the default.
`install` keeps links as links (it would otherwise dereference and write the whole picture out again per alias), and a
link whose target has gone is skipped rather than drawn as a blank tile.

The compositor searches `wlrix/images` on every XDG data directory, user first, so a file in
`~/.local/share/wlrix/images/` overrides the one installed here. `pkill -HUP wlrix-compositor` picks up a change
without a restart.

Artwork is authored at **85×67**, the size of the well in the icon tile. Anything else is scaled to cover that
rectangle and center-cropped — it fills the well rather than sitting letterboxed inside it — so a picture at a
different aspect ratio loses its edges rather than being squashed. PNG only: the compositor builds `wlrix-ui` with its
`png` feature and not its `svg` one.

## World map

`maps/world-map.jpg` is the map across the top of the International panel, where IRIX's ipanel had a satellite map of
its own. It is NASA's **Blue Marble: Next Generation**, July 2004 (`world.200407.3x5400x2700.jpg` from NASA Visible
Earth, by Reto Stöckli, NASA Earth Observatory), scaled from 5400×2700 to 1600×800. NASA imagery is not under
copyright; it is credited here as NASA asks.

The projection is equirectangular — longitude −180° at the left edge, latitude 90° at the top — which is what lets the
panel put a time zone's marker on it from tzdata's coordinates alone. A replacement has to keep that, and the 2:1 shape.

## Icons

`icons/wlrix/` is the IRIX icon set as an XDG icon theme. It is **incomplete on purpose and usable anyway**: its
`index.theme` carries `Inherits=Adwaita,hicolor`, so a name it does not draw resolves to Adwaita's, and an icon added
here simply starts winning over the one it replaces. There is no point at which the theme has to be finished before it
can be switched on.

It is the default everywhere wlRIX looks an icon up: the file manager and the file picker through
`files.appearance.icon_theme` in `files.toml`, `wlrix-desktop` and `wlrix-tray` through their own `icon_theme`
settings. Each of those can name another theme, or `""` for hicolor alone.

The layout is the spec's: `<theme>/<subdir>/<icon>.svg`, with every subdir declared in `index.theme`. A directory
listed in `Directories=` with no group of its own below is skipped **silently** by every implementation, wlRIX's own
included, so adding one means adding both. Today that is `scalable/places`, `scalable/mimetypes`,
`scalable/devices` and `scalable/apps`, all `Type=Scalable` over 8–512px, because the art is SVG and one drawing serves a 16px listing row and a 48px desktop
icon. A hand-tuned raster at a particular size would go in a sibling `48x48/` with `Type=Fixed`; the resolvers try
`.png` before `.svg`, so it wins at that size without anything else changing.

`scalable/devices` draws hardware under the freedesktop device names. A drive and the medium in it are two names, the
way GVfs asks for them: the empty drive is `drive-optical` or `drive-removable-media-floppy`, and the drive with a disc
or floppy loaded is `media-optical` or `media-floppy`. A hard disk has no medium to load, so its two IRIX states are
mounted (`drive-harddisk`) and unmounted (`drive-harddisk-unmounted`, a wlRIX name that falls back to `drive-harddisk`
in any other theme by the spec's dash rule). The floptical drive stands in for every other removable drive, a USB
stick included, as `drive-removable-media` with `media-removable` linked to it. `camera-web` is the IndyCam, and
`audio-input-microphone` the microphone, linked as `microphone`, Adwaita's name for it. `input-mouse` and
`input-keyboard` are the two drawings shared with an application. Those
same drawings are the Mouse and Keyboard settings panels' own icons, which those applications install into hicolor
under their application ids (`com.wlrix.settings.mouse`) so they show whichever theme is chosen. The copies are kept in
step by hand. `scalable/apps` does the same for applications under their generic role names: the Writer's closed
drawing is `accessories-text-editor` here and `com.wlrix.writer` in its own install. Another application's icon can be
drawn here too, under the name its own entry asks for: `firefox`, with `org.mozilla.firefox` (the Flatpak's) and
`firefox-esr` as links to it. The wlrix theme is searched before hicolor, where an application installs its own, so the
drawing here wins.

An application symbol drawn in the IRIX export frame -- a 50pt square over a `0 0 50 50` view box, as every drawing
here is -- is laid over its magic carpet 1:1 by the desktop and the icon catalog, in register, the way IRIX composed
them; that is how the Writer's closed symbol erases lines written on the carpet's paper. An ordinary theme icon is
shrunk and stood on the carpet instead. Like every drawing here, they carry the SVG namespace, which the IRIX-era exports lacked and the resvg
behind the C# loaders requires.

**An icon whose name nothing asks for is invisible, and nothing reports it.** That is the one failure mode worth
guarding against here: the file is present, it renders, and no type ever resolves to it. Three of the names below are
another theme's vocabulary rather than this machine's -- `unknown`, `image-x-pixmap` and `image-jpeg2000` are Breeze's
-- so each is kept as the drawing and given a link under the name shared-mime-info actually produces
(`application-x-generic`, `image-x-xpixmap`, and `image-jp2`/`jpx`/`jpm`). To check a new one, resolve every type in
`/usr/share/mime/types` through the same list and see whether the filename appears; add the `inode/*` types by hand,
because the stat-derived ones are not in that file. `inode/x-empty` is the example: wlRIX Files names empty files that,
where gio says `application/x-zerosize`, and nothing in the system list mentions either.

**Which name to draw is decided by shared-mime-info, not guessed.** A type resolves to a list of candidate names,
most specific first: an explicit override from `/usr/share/mime/icons`, then the type with its slash turned into a
dash, then the generic hint from `/usr/share/mime/generic-icons`, then `<media>-x-generic`. So a directory asks for
`inode-directory` and then `folder` — both are provided here, the second as the real file and the first as a symlink
to it, which saves a full failed search through Adwaita and hicolor on every miss. Aliases are kept as links and the
install preserves them as links, the same way the cursor theme's are.

A generic drawing loses to any theme's specific one, because every lookup tries a type's first name in every theme
before its next name. So the disk image is drawn under the specific names, not under `media-optical`, the hint
shared-mime-info gives ISO images: `application-vnd.efi.iso` is the drawing, linked as the old ISO aliases, the other
CD images and the raw and virtual machine disk images (`vnd.efi.img`, qcow2, VDI, VHD, VMDK, Apple's). The executable
is `application-x-executable`, the magic carpet itself; AppImages reach it through their hint, and are linked by name
too. The spreadsheet is `x-office-spreadsheet`, the hint every spreadsheet type carries, from `.ods` and the Excel
formats to CSV, since no installed theme draws a specific one.

`folder` is IRIX's plain white folder. Its body is all white, so the desktop's state tint (stippled, white, yellow,
the blue of a drop target) colors the whole folder evenly; a manila folder kept its tan back panel through every
state, because only the light body is tinted. `folder-open` is IRIX's open state, the spec's name for a folder being
browsed. Nothing asks for it yet. It is here for a file manager that marks the directories it has open, the way the
magic carpet marks a running application.

Every drop shadow is IRIX's: black at 75% opacity (`fill:#000000;fill-opacity:75%`), so the background shows through
it. Drawings redrawn in Inkscape and some from other sources came with an opaque gray (`#808080`, `#999999`) instead,
which reads as a flat gray slab on a dark desktop. A new drawing's shadow is brought to the same style when it is added.

`user-trash` and `user-trash-full` are IRIX's dumpster, empty and full, for `wlrix-desktop`'s Dumpster. They sit in
`places` with the folder rather than splitting `-full` into a `status` directory of its own: every lookup is by name, so
the context directory changes nothing but the size of `index.theme`. Their lids and garbage come from IRIX's dumpster
icon, which was only those overlay layers. The body under them, and the empty icon's left lid, are drawn to match.
`wlrix-dumpster-open` is the third state, the lid flung open with an icon going in, which the desktop shows while icons
are dragged over the Dumpster. The spec has no name for that, hence the `wlrix-` prefix; the desktop asks for it ahead
of the other two, so a theme without it shows the Dumpster as it was, tinted blue.

## File types

`mime/wlrix.xml` is a shared-mime-info package for file types the system database does not know. A file whose name
matches nothing there is `application/octet-stream`, which draws as the blank unknown-file page, and no icon can fix
that: there is no type for an icon name to come from. Each type here exists because a file showed that page, and
today they are C# work: `text/x-msbuild-project+xml` for `*.csproj`, `*.fsproj` and `*.vbproj`, and
`text/x-dotnet-solution+xml` for `*.slnx`.

They are XML underneath, so each is a subclass of `application/xml` and names `application-xml` as its generic icon
in the package itself rather than through a link in the icon theme. That way the icon follows whichever theme is
chosen, as long as it draws XML.

`just install` puts the package under `share/mime/packages/` and runs `update-mime-database`, because nothing reads
the XML directly: every reader, wlRIX Files included, loads the compiled `globs2` and `generic-icons`. A staged
install skips that step and leaves it to the distribution's package hook.

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

| Path                                                   | Written by                                                                                       |
|--------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `gtk-3.0/wlrix.css`, `gtk-4.0/wlrix.css`               | by hand. Structure: sizes, resets, which nodes to reach.                                         |
| `gtk-3.0/schemes/<id>.css`, `gtk-4.0/schemes/<id>.css` | generated. Colors, and which asset goes on which button.                                         |
| `assets/<id>/*.svg`                                    | generated. Twenty per scheme: four states each of menu, minimize, maximize, maximized and close. |
| `assets/check.svg`, `assets/check-disabled.svg`        | by hand. The check box's red check, the same shapes as Wlrix.Avalonia's; shared by every scheme. |

The generated half comes from **`wlrix-compositor --dump-gtk-theme`**, not from `palettegen`. Only
the compositor knows what a titlebar button looks like, and `decoration_quads()` hands back the
whole frame as a list of colored rectangles -- so an asset is that list written out as SVG, one
`<rect>` per quad. Lossless, because the source really is rectangles, and it scales to any HiDPI
factor in a way no screen capture would. Regenerate with `just gtk-theme` from `wlrix-epoch`;
`just check-gtk-theme` fails if the checked-in output is stale.

The bar itself has no asset. A Motif bevel is not a CSS border -- its top and bottom shadows run
the full width and the left and right pair is inset between them, while a CSS border miters its
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

| File                       | Id            | Gamma | Role                                                                 |
|----------------------------|---------------|-------|----------------------------------------------------------------------|
| `palette/classic.json`     | `classic`     | 1.7   | Default — Indigo Magic. `wlrix.palette.json` re-exports it.          |
| `palette/classic-g10.json` | `classic-g10` | 1.0   | Lightest bake.                                                       |
| `palette/classic-g24.json` | `classic-g24` | 2.4   | Darkest bake.                                                        |
| `palette/gotham.json`      | `gotham`      | 1.7   | IRIX's dark scheme. 1.7 only — it was never baked for the other two. |

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

| Output                                        | Consumer                                                                  |
|-----------------------------------------------|---------------------------------------------------------------------------|
| `wlrix-avalonia/…/Schemes/<Scheme>.axaml`     | one `ResourceDictionary` per scheme, merged by `WlrixTheme`.              |
| `wlrix-avalonia/…/Schemes/Brushes.axaml`      | one brush per color key, scheme-independent.                              |
| `wlrix-avalonia/…/Schemes/SchemeCatalog.g.cs` | `WlrixSchemes.All` — id, name, gamma, dark flag, resource URI.            |
| `wlrix-ui/src/palette/generated.rs`           | the `Palette` struct and one static per scheme, for every Rust component. |

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
