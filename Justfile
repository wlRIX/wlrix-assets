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
# **Only `wallpapers/`.** The other three directories are deliberately not installed, for
# different reasons each:
#
# - `palette/` is a *build* input. `tools/palettegen` resolves it ahead of time into native
#   sources that are checked in to the consuming repos, precisely so nothing parses it at
#   runtime; installing it would put a file on disk that nothing reads and that could drift
#   from the baked values without anyone noticing.
# - `icons/` and `cursors/` are empty. When they are filled they will want the XDG icon-theme
#   and XCursor layouts (`share/icons/<theme>/...`), not this directory, because that is where
#   `freedesktop-icons` and the compositor's XCursor loader look. Adding them here now would be
#   guessing at a layout twice.
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

# Remove what `install` put down.
[doc("Remove what install put down")]
uninstall:
  #!/usr/bin/env bash
  set -euo pipefail
  rm -rf '{{wallpaperdir}}'
  # Only if this left it empty: `share/wlrix` may hold something else by then.
  rmdir '{{sharedir}}' 2>/dev/null || true
  echo "removed the wlRIX wallpapers"

clean:
  @echo "nothing to clean: {{name}} is data"
