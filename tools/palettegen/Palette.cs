// SPDX-License-Identifier: MIT
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Wlrix.PaletteGen;

/// <summary>An RGB color, kept as bytes so the arithmetic matches Motif's.</summary>
public readonly record struct Rgb(byte R, byte G, byte B)
{
    public static Rgb Parse(string hex)
    {
        if (hex.Length != 7 || hex[0] != '#')
            throw new FormatException($"expected #rrggbb, got '{hex}'");
        return new Rgb(
            Convert.ToByte(hex.Substring(1, 2), 16),
            Convert.ToByte(hex.Substring(3, 2), 16),
            Convert.ToByte(hex.Substring(5, 2), 16));
    }

    public string Hex => $"#{R:x2}{G:x2}{B:x2}";

    /// <summary>Per-channel multiply, truncating like Motif's integer maths.</summary>
    public Rgb Scale(double f) => new(Clamp(R * f), Clamp(G * f), Clamp(B * f));

    /// <summary>Move each channel a fraction of the way to white.</summary>
    public Rgb TowardWhite(double f) =>
        new(Clamp(R + (255 - R) * f), Clamp(G + (255 - G) * f), Clamp(B + (255 - B) * f));

    public bool WouldClamp(double f) => R * f > 255 || G * f > 255 || B * f > 255;

    private static byte Clamp(double v) => (byte)Math.Clamp((int)v, 0, 255);
}

/// <summary>
/// A palette file with its role layer resolved down to concrete colors.
/// </summary>
public sealed class Palette
{
    private static readonly Regex Call =
        new(@"^(?<fn>shadow|shade|toward)\(\s*(?<key>\w+)\s*,\s*(?<arg>\w+)\s*\)$",
            RegexOptions.Compiled);

    /// <summary>
    /// A role may state a color outright. Needed because a scheme's roles are its own:
    /// Gotham binds five of them differently from Classic, and one wlRIX surface -- the
    /// backdrop behind a minimized window's thumbnail -- was sampled from a screenshot and
    /// has no IRIX name within thirty levels to point at. The prohibition on hand-editing
    /// is on layer 1, the transcribed <c>palette</c> block; <c>roles</c> is wlRIX's own.
    /// </summary>
    private static readonly Regex Literal =
        new(@"^#[0-9a-fA-F]{6}$", RegexOptions.Compiled);

    public required string Id { get; init; }
    public required string Name { get; init; }
    public required string Gamma { get; init; }
    public required string Source { get; init; }

    /// <summary>
    /// The scheme's own <c>IsDarkScheme</c>. Carried rather than inferred: it decides
    /// things no single color can, and a consumer that wants to know should not have to
    /// guess by measuring the panel.
    /// </summary>
    public required bool Dark { get; init; }

    /// <summary>Role name -> resolved color, in the file's declaration order.</summary>
    public required IReadOnlyDictionary<string, Rgb> Resolved { get; init; }

    /// <summary>
    /// Motif geometry: shadow thicknesses and widget sizes. Carried through with the
    /// colors because a consumer drawing a bevel needs both, and hand-copying these
    /// is the drift `check-palette` exists to catch.
    /// </summary>
    public required IReadOnlyDictionary<string, int> Metrics { get; init; }

    public static Palette Load(string path)
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        var r = doc.RootElement;

        var palette = r.GetProperty("palette").EnumerateObject()
            .ToDictionary(p => p.Name, p => Rgb.Parse(p.Value.GetString()!));

        var rule = r.GetProperty("shadowRule");
        double Factor(string n) => rule.GetProperty(n).GetDouble();

        var metrics = new Dictionary<string, int>();
        if (r.TryGetProperty("metrics", out var metricsElement))
        {
            foreach (var entry in metricsElement.EnumerateObject())
            {
                if (entry.Value.ValueKind == JsonValueKind.Object)
                {
                    // One level of nesting, flattened as "shadowThickness.default".
                    foreach (var inner in entry.Value.EnumerateObject())
                        metrics[$"{entry.Name}.{inner.Name}"] = inner.Value.GetInt32();
                }
                else
                {
                    metrics[entry.Name] = entry.Value.GetInt32();
                }
            }
        }

        var resolved = new Dictionary<string, Rgb>();
        foreach (var role in r.GetProperty("roles").EnumerateObject())
        {
            var expr = role.Value.GetString()!;

            if (Literal.IsMatch(expr))
            {
                resolved[role.Name] = Rgb.Parse(expr);
                continue;
            }

            var m = Call.Match(expr);

            if (!m.Success)
            {
                if (!palette.TryGetValue(expr, out var direct))
                    throw new InvalidDataException(
                        $"{Path.GetFileName(path)}: role '{role.Name}' is '{expr}', which is " +
                        "neither a palette key, a #rrggbb literal, nor shadow()/shade()/toward()");
                resolved[role.Name] = direct;
                continue;
            }

            var key = m.Groups["key"].Value;
            if (!palette.TryGetValue(key, out var basis))
                throw new InvalidDataException(
                    $"{Path.GetFileName(path)}: role '{role.Name}' derives from " +
                    $"unknown color '{key}'");

            var arg = m.Groups["arg"].Value;
            resolved[role.Name] = m.Groups["fn"].Value switch
            {
                // Top shadow multiplies, but that blows out to pure white on the
                // lighter surfaces; fall back to a halfway-to-white highlight so
                // the bevel stays visible.
                "shadow" when arg == "top" =>
                    basis.WouldClamp(Factor("top"))
                        ? basis.TowardWhite(Factor("topFallback"))
                        : basis.Scale(Factor("top")),
                "shadow" when arg == "bottom" => basis.Scale(Factor("bottom")),
                "shade" => basis.Scale(Factor(arg)),
                // Toward white outright, with no multiply and no fallback. The 4Dwm frame
                // highlight is this and not `shadow(_, top)`: on the active titlebar's
                // #a59f80 the multiply does not clamp, so the fallback never fires and the
                // result comes out far lighter and yellower than the frame IRIX drew.
                "toward" => basis.TowardWhite(Factor(arg)),
                _ => throw new InvalidDataException(
                    $"{Path.GetFileName(path)}: unsupported derivation '{expr}'"),
            };
        }

        return new Palette
        {
            Id = r.GetProperty("id").GetString()!,
            Name = r.GetProperty("name").GetString()!,
            Gamma = r.GetProperty("gamma").GetString()!,
            Dark = r.TryGetProperty("dark", out var dark) && dark.GetBoolean(),
            Source = r.GetProperty("source").GetString()!,
            Resolved = resolved,
            Metrics = metrics,
        };
    }
}
