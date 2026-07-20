// SPDX-License-Identifier: MIT
//
// palettegen — resolves a wlRIX palette JSON into the generated artifacts that
// the C# theme and the Rust compositor consume, so both sides render the same
// colors from one source.
//
//   dotnet run --project tools/palettegen -- <repo-root>
//
// <repo-root> is the directory holding the sibling wlrix-* repos.

using System.Globalization;
using System.Text;
using System.Text.Json;
using Wlrix.PaletteGen;

var root = args.Length > 0
    ? Path.GetFullPath(args[0])
    : Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../../.."));

var paletteDir = Path.Combine(root, "wlrix-assets", "palette");
if (!Directory.Exists(paletteDir))
{
    Console.Error.WriteLine($"palettegen: no palette directory at {paletteDir}");
    return 1;
}

var schemeDir = Path.Combine(root, "wlrix-avalonia", "src", "Wlrix.Avalonia", "Schemes");
Directory.CreateDirectory(schemeDir);

// Real files only: wlrix.palette.json is a symlink re-export of the default.
var sources = Directory.GetFiles(paletteDir, "*.json")
    .Where(p => Path.GetFileName(p) != "wlrix.palette.json")
    .OrderBy(p => p, StringComparer.Ordinal)
    .ToArray();

if (sources.Length == 0)
{
    Console.Error.WriteLine($"palettegen: no palette JSON found in {paletteDir}");
    return 1;
}

Palette? standard = null;

foreach (var src in sources)
{
    var palette = Palette.Load(src);
    var schemeName = SchemeName(palette.Id);
    var dest = Path.Combine(schemeDir, schemeName + ".axaml");
    File.WriteAllText(dest, Emit.Scheme(palette, schemeName));
    Console.WriteLine($"  {Rel(root, dest)}  ({palette.Resolved.Count} roles)");

    // The default (gamma 1.7) scheme is what the compositor matches against.
    if (palette.Id == "classic") standard = palette;
}

// Brush layer is identical across schemes, so it is emitted once and merged by
// the theme rather than duplicated into every scheme dictionary.
var brushes = Path.Combine(schemeDir, "Brushes.axaml");
File.WriteAllText(brushes, Emit.Brushes(Palette.Load(sources[0])));
Console.WriteLine($"  {Rel(root, brushes)}");

if (standard is null)
{
    Console.Error.WriteLine("palettegen: no palette with id 'classic'; skipping Rust output");
    return 1;
}

var rustDir = Path.Combine(root, "wlrix-compositor", "src");
if (Directory.Exists(rustDir))
{
    var rust = Path.Combine(rustDir, "palette.rs");
    File.WriteAllText(rust, Emit.Rust(standard));
    Console.WriteLine($"  {Rel(root, rust)}");
}
else
{
    Console.Error.WriteLine($"palettegen: {Rel(root, rustDir)} not found; skipped Rust output");
}

// The greeter draws a whole Motif dialog, so it needs more roles than the
// compositor and its own color type -- it is not smithay-based.
var greeterSrc = Path.Combine(root, "wlrix-greeter", "src");
if (Directory.Exists(greeterSrc))
{
    var themeDir = Path.Combine(greeterSrc, "theme");
    Directory.CreateDirectory(themeDir);
    var greeter = Path.Combine(themeDir, "palette.rs");
    File.WriteAllText(greeter, Emit.RustGreeter(standard));
    Console.WriteLine($"  {Rel(root, greeter)}");
}
else
{
    Console.Error.WriteLine($"palettegen: {Rel(root, greeterSrc)} not found; skipped greeter output");
}

return 0;

static string Rel(string root, string path) =>
    Path.GetRelativePath(root, path).Replace('\\', '/');

// indigo-magic -> IndigoMagic, indigo-magic-g10 -> IndigoMagicG10
static string SchemeName(string id) => string.Concat(
    id.Split('-', StringSplitOptions.RemoveEmptyEntries)
      .Select(p => CultureInfo.InvariantCulture.TextInfo.ToTitleCase(p)));
