# wlrix-assets

Shared branding and look-and-feel data for wlRIX, consumed by **both** the Rust
system components and the C# apps so everything renders identically.

- **License:** MIT (freely reusable)

## Layout

| Directory      | Contents                                                              |
|----------------|----------------------------------------------------------------------|
| `palette/`     | Canonical colour palette — the single source of truth for theming.   |
| `icons/`       | Icon theme (IRIX Indigo Magic icon set).                             |
| `cursors/`     | Cursor theme.                                                        |
| `wallpapers/`  | Default wallpapers / backgrounds.                                    |

## Palette

`palette/wlrix.palette.json` holds the named colours. It is intended to be
consumed two ways:

- **Rust** (compositor, greeter): parse the JSON at build/run time.
- **C#** (`wlrix-avalonia`): generate/import an Avalonia resource dictionary from
  the same JSON so app colours match the compositor exactly.

Keep this file the source of truth; do not hard-code colours in the theme.
