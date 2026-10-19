import pathlib, re, shutil, sys

src=pathlib.Path(sys.argv[1]); dst=pathlib.Path(sys.argv[2])
shutil.copytree(src,dst,dirs_exist_ok=True)

def rewrite(relative, fn):
    p=dst/relative; p.write_text(fn(p.read_text(encoding='utf-8-sig')),encoding='utf-8')

def method(text, signature, body):
    start=text.index(signature); opening=text.index('{',start); depth=1; end=opening+1
    while depth:
        depth += (text[end]=='{') - (text[end]=='}'); end+=1
    return text[:opening]+'{\n'+body+'\n\t}'+text[end:]

for p in dst.rglob('*.cs'):
    s=p.read_text(encoding='utf-8-sig')
    s=s.replace('Assembly.GetEntryAssembly()', 'typeof(global::Celeste.Celeste).Assembly')
    s=s.replace('[DllImport("fmod")]', '[DllImport("__Internal")]').replace('[DllImport("fmodstudio")]', '[DllImport("__Internal")]')
    p.write_text(s,encoding='utf-8')

def main(s):
    s=s.replace('using Steamworks;','').replace('public static readonly AppId_t SteamID = new AppId_t(504230u);','')
    s=s.replace('SteamAPI.RunCallbacks();','')
    start=s.index('\t\t\tif (SteamAPI.RestartAppIfNecessary(')
    end=s.index('\t\t\tif (!Settings.Existed)',start)
    s=s[:start]+s[end:]
    s=s.replace('SteamApps.GetCurrentGameLanguage()', '"schinese"')
    return s.replace('private static void Main(string[] args)', 'public static void Main(string[] args)')
rewrite('Celeste/Celeste.cs',main)
rewrite('Monocle/Engine.cs',lambda s: s.replace('Path.GetDirectoryName(typeof(global::Celeste.Celeste).Assembly.Location)','AppContext.BaseDirectory').replace('GCSettings.LatencyMode = GCLatencyMode.SustainedLowLatency;', '/* iOS Mono uses the platform GC latency policy. */'))
rewrite('Celeste/UserIO.cs',lambda s: method(s,'private static string GetSavePath(string dir)', '\t\treturn Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Celeste", dir);'))
rewrite('Monocle/ErrorLog.cs',lambda s: method(method(s,'public static void Open()', '\t\tConsole.WriteLine("Celeste error log: " + Filename);'),'private static string GetLogPath()', '\t\treturn Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Celeste", "errorLog.txt");'))
def settings(s):
    start=s.index('\t[XmlAnyElement("LaunchInDebugModeComment")]')
    end=s.index('\tpublic int MaxScale', start)
    return s[:start]+s[end:]
rewrite('Celeste/Settings.cs', settings)
(dst/'Celeste/Stats.cs').write_text('''using System.Collections.Generic;
namespace Celeste;
public static class Stats {
    static readonly Dictionary<Stat,int> values = new();
    public static void MakeRequest() {}
    public static bool Has() => true;
    public static void Increment(Stat stat, int increment=1) => values[stat] = Local(stat)+increment;
    public static int Local(Stat stat) => values.TryGetValue(stat,out int n) ? n : 0;
    public static long Global(Stat stat) => 0;
    public static void Store() {}
    public static string Name(Stat stat) => Dialog.Clean("STAT_"+stat);
}
''',encoding='utf-8')
(dst/'Celeste/Achievements.cs').write_text('''namespace Celeste;
public static class Achievements {
    public static string ID(Achievement achievement) => achievement.ToString();
    public static bool Has(Achievement achievement) => false;
    public static void Register(Achievement achievement) {}
}
''',encoding='utf-8')
# The optional Stadia SDL/FMOD bridge can never execute on iOS; eliminate its native import.
rewrite('Celeste/Audio.cs',lambda s: re.sub(r'\[DllImport\("fmod_SDL"[^\]]*\)\]\s*private static extern void FMOD_SDL_Register\(([^;]+)\);',r'private static void FMOD_SDL_Register(\1) {}',s))
(dst/'Celeste.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <AssemblyName>Celeste</AssemblyName>
    <OutputType>Library</OutputType>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <Nullable>disable</Nullable>
    <NoWarn>SYSLIB0051;SYSLIB0003;CS0436;CS0169;CS0649;CS0618</NoWarn>
  </PropertyGroup>
  <ItemGroup><Compile Remove="Monocle/SaveLoad.cs" /></ItemGroup>
  <ItemGroup><Reference Include="FNA"><HintPath>../input/Celeste.app/Contents/Resources/FNA.dll</HintPath></Reference></ItemGroup>
</Project>
''',encoding='utf-8')
print('Prepared',dst)
