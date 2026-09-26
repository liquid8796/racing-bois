using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
if (args.Length != 2) { Console.Error.WriteLine("Usage: RacingBois.AuditVerifier <source-dir> <inventory.json>"); return 2; }
try
{
    string root=Path.GetFullPath(args[0]).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
    using var doc=JsonDocument.Parse(File.ReadAllText(args[1]));
    var entries=doc.RootElement.ValueKind==JsonValueKind.Array?doc.RootElement:doc.RootElement.GetProperty("files");
    var known=new HashSet<string>(StringComparer.OrdinalIgnoreCase);var failures=new List<string>();long total=0;
    foreach(var entry in entries.EnumerateArray())
    {
        string relative=entry.GetProperty("path").GetString()??throw new InvalidDataException("Missing path");
        string path=Path.GetFullPath(Path.Combine(root,relative));
        if(!path.StartsWith(root,StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("Path escapes source");
        if(!known.Add(path))throw new InvalidDataException("Duplicate path");
        if(!File.Exists(path)){failures.Add(relative+": missing");continue;}
        using var input=File.OpenRead(path);total+=input.Length;
        string hash=Convert.ToHexString(SHA256.HashData(input)).ToLowerInvariant();
        if(input.Length!=entry.GetProperty("bytes").GetInt64()||hash!=entry.GetProperty("sha256").GetString())failures.Add(relative+": changed");
    }
    foreach(var path in Directory.EnumerateFiles(root,"*",SearchOption.AllDirectories))
        if(!known.Contains(Path.GetFullPath(path)))failures.Add(Path.GetRelativePath(root,path)+": added");
    Console.WriteLine(JsonSerializer.Serialize(new{assemblyVersion=Assembly.GetExecutingAssembly().GetName().Version?.ToString(),files=known.Count,bytes=total,verified=failures.Count==0,failures},new JsonSerializerOptions{WriteIndented=true}));
    return failures.Count==0?0:1;
}
catch(Exception e) when(e is IOException or UnauthorizedAccessException or JsonException or InvalidOperationException or ArgumentException)
{ Console.Error.WriteLine(e.Message);return 2; }
