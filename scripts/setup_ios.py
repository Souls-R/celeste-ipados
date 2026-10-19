import sys
import pathlib, plistlib, re, shutil, subprocess
root=pathlib.Path(sys.argv[1]).resolve()
fna=root/'FNA'
for p in fna.rglob('*.cs'):
    if '.git' in p.parts: continue
    text=p.read_text(encoding='utf-8-sig')
    text=re.sub(r'DllImport\("(?:SDL2|FNA3D|FAudio|libtheorafile)"', 'DllImport("__Internal"', text)
    text=re.sub(r'(const string\s+(?:nativeLibName|libName|NativeLibName)\s*=\s*)"(?:SDL2|FNA3D|FAudio|libtheorafile)"',r'\1"__Internal"',text)
    p.write_text(text,encoding='utf-8')
csproj=(fna/'FNA.Core.csproj').read_text()
csproj=csproj.replace('<TargetFrameworks>net40;netstandard2.0</TargetFrameworks>','<TargetFramework>net10.0</TargetFramework>')
(fna/'FNA.iOS.csproj').write_text(csproj)
game=root/'game'
p=game/'Celeste.csproj'
s=p.read_text()
s=re.sub(r'<ItemGroup><Reference Include="FNA">.*?</ItemGroup>','<ItemGroup><ProjectReference Include="../FNA/FNA.iOS.csproj" /></ItemGroup>',s,flags=re.S)
if '<Compile Remove="Monocle/SaveLoad.cs"' not in s:
    s=s.replace('</Project>','<ItemGroup><Compile Remove="Monocle/SaveLoad.cs" /></ItemGroup></Project>')
p.write_text(s)
# The public FMOD SDK is 1.10.11. This shares the 1.10 ABI and bank format;
# This binding/native combination was used in the local Build 8 port.
for p in [game/'FMOD/Factory.cs',game/'FMOD.Studio/System.cs']:
    s=p.read_text().replace('69652u', '69649u').replace('69652', '69649')
    p.write_text(s)
app=root/'ios'; app.mkdir(exist_ok=True)
libs=app/'native'; libs.mkdir(exist_ok=True)
for p in (root/'native-libraries').glob('*.a'):
    shutil.copy2(p,libs/p.name)
shutil.copy2(root/'fmod-sdk/libfmod_iphoneos.a',libs/'libfmod.a')
shutil.copy2(root/'fmod-sdk/libfmodstudio_iphoneos.a',libs/'libfmodstudio.a')
sdk=subprocess.check_output(['xcrun','--sdk','iphoneos','--show-sdk-path'],text=True).strip()
subprocess.run(['xcrun','--sdk','iphoneos','clang','-arch','arm64','-isysroot',sdk,
                '-miphoneos-version-min=15.0','-O2','-c',str(root/'platform_stubs.c'),
                '-o',str(libs/'platform_stubs.o')],check=True)
subprocess.run(['xcrun','ar','rcs',str(libs/'libPlatformStubs.a'),str(libs/'platform_stubs.o')],check=True)
subprocess.run(['xcrun','--sdk','iphoneos','clang','-arch','arm64','-isysroot',sdk,
                '-miphoneos-version-min=15.0','-O2','-fobjc-arc','-c',str(root/'uikit_input_fix.m'),
                '-o',str(libs/'uikit_input_fix.o')],check=True)
subprocess.run(['xcrun','ar','rcs',str(libs/'libUIKitInputFix.a'),str(libs/'uikit_input_fix.o')],check=True)
subprocess.run(['xcrun','--sdk','iphoneos','clang','-arch','arm64','-isysroot',sdk,
                '-miphoneos-version-min=15.0','-O2','-fobjc-arc','-c',str(root/'native_ui.m'),
                '-o',str(libs/'native_ui.o')],check=True)
subprocess.run(['xcrun','ar','rcs',str(libs/'libCelesteNativeUI.a'),str(libs/'native_ui.o')],check=True)
shutil.copy2(root/'Main.cs', app/'Main.cs')
(app/'Celeste.iOS.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0-ios</TargetFramework>
    <OutputType>Exe</OutputType>
    <AssemblyName>CelesteiPadOS</AssemblyName>
    <ApplicationId>com.soulsr.celeste</ApplicationId>
    <ApplicationTitle>Celeste</ApplicationTitle>
    <ApplicationVersion>1</ApplicationVersion>
    <ApplicationDisplayVersion>1.4.0</ApplicationDisplayVersion>
    <SupportedOSPlatformVersion>15.0</SupportedOSPlatformVersion>
    <RuntimeIdentifier>ios-arm64</RuntimeIdentifier>
    <BuildIpa>true</BuildIpa>
    <EnableCodeSigning>false</EnableCodeSigning>
    <CodesignRequireProvisioningProfile>false</CodesignRequireProvisioningProfile>
    <MtouchLink>SdkOnly</MtouchLink>
    <UseInterpreter>false</UseInterpreter>
    <MtouchUseLlvm>true</MtouchUseLlvm>
    <Optimize>true</Optimize>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <Nullable>disable</Nullable>
    <NoWarn>$(NoWarn);CA1416;CS0436</NoWarn>
    <MtouchExtraArgs>--marshal-managed-exceptions=unwindnativecode</MtouchExtraArgs>
  </PropertyGroup>
  <ItemGroup>
    <ProjectReference Include="../game/Celeste.csproj" />
    <ProjectReference Include="../FNA/FNA.iOS.csproj" />
    <BundleResource Include="../input/Celeste.app/Contents/Resources/Content/**/*">
      <Link>Content/%(RecursiveDir)%(Filename)%(Extension)</Link>
    </BundleResource>
    <BundleResource Include="../input/Celeste.app/Contents/Resources/gamecontrollerdb.txt" Link="gamecontrollerdb.txt" />
    <InterfaceDefinition Include="../LaunchScreen.storyboard" Link="LaunchScreen.storyboard" />
    <ImageAsset Include="../Assets.xcassets/**/*" Link="Assets.xcassets/%(RecursiveDir)%(Filename)%(Extension)" />
    <NativeReference Include="native/*.a">
      <Kind>Static</Kind><ForceLoad>true</ForceLoad><IsCxx>true</IsCxx>
      <Frameworks>AVFoundation AudioToolbox CoreAudio CoreGraphics Metal QuartzCore OpenGLES GameController CoreMotion MobileCoreServices ImageIO CoreHaptics CoreBluetooth IOSurface UIKit Foundation Security SystemConfiguration IOKit</Frameworks>
      <LinkerFlags>-lz -liconv -lc++ -lresolv</LinkerFlags>
    </NativeReference>
  </ItemGroup>
  <ItemGroup>
    <NativeReference Update="native/libtheorafile.a"><ForceLoad>false</ForceLoad></NativeReference>
    <LinkerArgument Include="-Wl,-no_fixup_chains" />
  </ItemGroup>
</Project>
''')
info={
    'CFBundleDisplayName':'Celeste', 'CFBundleName':'Celeste',
    'CFBundleIdentifier':'com.soulsr.celeste', 'CFBundleShortVersionString':'1.4.0',
    'CFBundleVersion':'1', 'LSRequiresIPhoneOS':True, 'MinimumOSVersion':'15.0',
    'UIDeviceFamily':[1,2], 'UIRequiredDeviceCapabilities':['arm64'],
    'UISupportedInterfaceOrientations':['UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'],
    'UISupportedInterfaceOrientations~ipad':['UIInterfaceOrientationLandscapeLeft','UIInterfaceOrientationLandscapeRight'],
    'UIApplicationSupportsIndirectInputEvents':True,
    'UIRequiresFullScreen':True, 'UIStatusBarHidden':True,
    'UIViewControllerBasedStatusBarAppearance':False,
    'CADisableMinimumFrameDurationOnPhone':True,
    'UIFileSharingEnabled':True, 'LSSupportsOpeningDocumentsInPlace':True,
    'UILaunchStoryboardName':'LaunchScreen',
    'XSAppIconAssets':'Assets.xcassets/AppIcon.appiconset',
}
(app/'Info.plist').write_bytes(plistlib.dumps(info))
print('iOS project prepared at',app)
