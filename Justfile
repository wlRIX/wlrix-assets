#!/usr/bin/env just --justfile
name := 'wlrix-assets'

rootdir := ''
prefix := '/usr'

usrdir := absolute_path(clean(rootdir / prefix))
# `share`, not `lib`: these are architecture-independent data files, and a wallpaper is exactly
# what `share` is for. The subdirectory is named for the desktop rather than dropped into
# `share/backgrounds`, which is a distribution's to arrange and not ours to add to.
sharedir := usrdir / 'share' / 'wlrix'
wallpaperdir := sharedir / 'wallpapers'

# The cursor theme goes under `share/icons/<theme>/`, **not** under `share/wlrix`, because that
# is the only place an XCursor loader looks: libXcursor, libwayland-cursor and the `xcursor`
# crate the compositor uses all walk XDG_DATA_DIRS/icons (plus ~/.icons and a couple of legacy
# paths), and none of them can be told about a private directory without XCURSOR_PATH.
cursorname := 'sgi'
icondir := usrdir / 'share' / 'icons'
cursordir := icondir / cursorname
# Where the theme is looked for at *runtime*, which is not where it is written when DESTDIR is
# set: a staged install is assembled under rootdir and runs from prefix. Only the message at the
# end of `install` uses this -- naming the staging directory there would be telling whoever
# reads it to set XCURSOR_PATH to a path that will not exist on the machine.
runtime-icondir := clean(prefix / 'share' / 'icons')

# List available recipes.
default:
  @just --list

# Nothing to build. This repo is data, and the one thing that *is* generated from it -- the
# palette modules in wlrix-avalonia, wlrix-compositor, wlrix-greeter and wlrix-desktop -- is
# generated into those repos and checked in there. `just palette` in wlrix-epoch does it.
build:
  @echo "nothing to build: {{name}} is data"

# Check the palette against the IRIX reference it was transcribed from.
[doc("Re-verify the palette against the IRIX reference")]
test:
  python3 tools/verify-palette.py

# Install the shared data files.
#
# **`wallpapers/` and `cursors/`.** The other two directories are deliberately not installed,
# for different reasons each:
#
# - `palette/` is a *build* input. `tools/palettegen` resolves it ahead of time into native
#   sources that are checked in to the consuming repos, precisely so nothing parses it at
#   runtime; installing it would put a file on disk that nothing reads and that could drift
#   from the baked values without anyone noticing.
# - `icons/` is still empty. When it is filled it will want the XDG icon-theme layout under
#   `share/icons/<theme>/`, which is where `freedesktop-icons` looks, the same way the cursor
#   theme below does.
#
# Deliberately does not build -- there is nothing to build -- but it is still run as root, and
# the other components' justfiles all say this in the same place:
#
#     sudo just install
[doc("Install the shared data files (run as root)")]
install:
  #!/usr/bin/env bash
  set -euo pipefail
  install -d '{{wallpaperdir}}'
  # `-m0644` and one at a time rather than `cp -r`: the repo directory carries a `.gitkeep`,
  # and a recursive copy would install it.
  for f in wallpapers/*.png wallpapers/*.rgb wallpapers/*.jpg; do
      [ -e "$f" ] || continue
      install -Dm0644 "$f" '{{wallpaperdir}}'/"$(basename "$f")"
      echo "installed {{wallpaperdir}}/$(basename "$f")"
  done

  # The cursor theme, entry by entry rather than `cp -r`, because **the symlinks have to stay
  # symlinks**. 72 of the theme's 121 entries are links -- the legacy X11 names, the MD5-named
  # ones themes use for drag-and-drop, and the modern CSS names -- pointing at 49 real files.
  # `install` dereferences, so a loop of `install -Dm0644` would write 121 separate cursors and
  # more than double the size for nothing.
  install -d '{{cursordir}}/cursors'
  for f in cursors/{{cursorname}}/index.theme cursors/{{cursorname}}/cursor.theme; do
      install -Dm0644 "$f" '{{cursordir}}'/"$(basename "$f")"
  done
  for f in cursors/{{cursorname}}/cursors/*; do
      name="$(basename "$f")"
      if [ -L "$f" ]; then
          # Relative targets, all within this one directory, so the link is correct wherever
          # the theme lands -- including a staged install under DESTDIR.
          ln -sfn "$(readlink "$f")" '{{cursordir}}/cursors/'"$name"
      else
          install -Dm0644 "$f" '{{cursordir}}/cursors/'"$name"
      fi
  done
  echo "installed {{cursordir}} ({{cursorname}} cursor theme)"
  echo
  echo "The compositor's default config names the {{cursorname}} theme. It is found by name"
  echo "under share/icons on any XDG data directory -- so a prefix other than /usr needs"
  echo "XCURSOR_PATH to include {{runtime-icondir}}, or the pointer falls back to"
  echo "whatever theme the machine already has."

# Remove what `install` put down.
[doc("Remove what install put down")]
uninstall:
  #!/usr/bin/env bash
  set -euo pipefail
  rm -rf '{{wallpaperdir}}'
  # Only if this left it empty: `share/wlrix` may hold something else by then.
  rmdir '{{sharedir}}' 2>/dev/null || true
  echo "removed the wlRIX wallpapers"
  # Our own theme directory only. `share/icons` itself belongs to the distribution and holds
  # every other theme on the machine.
  rm -rf '{{cursordir}}'
  echo "removed {{cursordir}}"

clean:
  @echo "nothing to clean: {{name}} is data"
