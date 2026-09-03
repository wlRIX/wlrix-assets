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
var loaded = new List<Palette>();

foreach (var src in sources)
{
    var palette = Palette.Load(src);
    loaded.Add(palette);
    var schemeName = SchemeName(palette.Id);
    var dest = Path.Combine(schemeDir, schemeName + ".axaml");
    File.WriteAllText(dest, Emit.Scheme(palette, schemeName));
    Console.WriteLine($"  {Rel(root, dest)}  ({palette.Resolved.Count} roles)");

    // The default (gamma 1.7) scheme is the one every other palette is checked against,
    // and the one a component falls back to.
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

// Every scheme must define exactly the same roles.
//
// The Rust side is now one struct with a field per role, so a scheme that is missing one
// cannot be represented -- and a scheme that adds one would have it silently dropped. This
// used to be enforced by nobody: three hand-kept subsets were emitted from the `classic`
// palette alone and the other bakes were never looked at.
foreach (var palette in loaded)
{
    var missing = standard.Resolved.Keys.Except(palette.Resolved.Keys).ToArray();
    var extra = palette.Resolved.Keys.Except(standard.Resolved.Keys).ToArray();
    if (missing.Length == 0 && extra.Length == 0) continue;

    Console.Error.WriteLine($"palettegen: '{palette.Id}' does not define the same roles as 'classic'");
    if (missing.Length > 0) Console.Error.WriteLine($"  missing: {string.Join(", ", missing)}");
    if (extra.Length > 0) Console.Error.WriteLine($"  extra:   {string.Join(", ", extra)}");
    return 1;
}

// The scheme catalog, beside the dictionaries it points at. Emitted after the role check
// above, so a catalog can never list a scheme the theme would fail to load.
var catalog = Path.Combine(schemeDir, "SchemeCatalog.g.cs");
File.WriteAllText(catalog, Emit.SchemeCatalog(loaded, standard, SchemeName));
Console.WriteLine($"  {Rel(root, catalog)}  ({loaded.Count} schemes)");

// One Rust file for every consumer, in `wlrix-ui`. The compositor, the greeter and the
// desktop used to get three different subsets of this in two different color types; they
// share the crate now, so they share the palette.
var uiDir = Path.Combine(root, "wlrix-ui", "src", "palette");
if (Directory.Exists(uiDir))
{
    var generated = Path.Combine(uiDir, "generated.rs");
    File.WriteAllText(generated, Emit.RustUi(loaded, standard));
    Console.WriteLine($"  {Rel(root, generated)}  ({loaded.Count} schemes)");
}
else
{
    Console.Error.WriteLine($"palettegen: {Rel(root, uiDir)} not found; skipped Rust output");
}

return 0;

static string Rel(string root, string path) =>
    Path.GetRelativePath(root, path).Replace('\\', '/');

// classic -> Classic, classic-g10 -> ClassicG10
static string SchemeName(string id) => string.Concat(
    id.Split('-', StringSplitOptions.RemoveEmptyEntries)
      .Select(p => CultureInfo.InvariantCulture.TextInfo.ToTitleCase(p)));
