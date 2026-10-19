import sys
import json, pathlib, plistlib
root=pathlib.Path(sys.argv[1]).resolve()
app=root/'ios'
strings=json.loads((root/'native-ui/strings.json').read_text())
settings=app/'Settings.bundle'; settings.mkdir(exist_ok=True)
items=[]
for section,footer,key,title,default in [
    ('sectionLaunch','noticeFooter','NativeShowNotice','settingNotice',True),
    ('sectionPerformance','hudFooter','NativeMetalHUD','settingHud',False),
    ('sectionDiagnostics','logsFooter','NativeDiagnosticLogs','settingLogs',False),
]:
    items.extend([dict(Type='PSGroupSpecifier',Title=section,FooterText=footer),
                  dict(Type='PSToggleSwitchSpecifier',Title=title,Key=key,DefaultValue=default)])
(settings/'Root.plist').write_bytes(plistlib.dumps(dict(PreferenceSpecifiers=items,StringsTable='Root')))
(settings/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier='com.soulsr.celeste.settings',CFBundleVersion='1',CFBundlePackageType='BNDL')))
def write_strings(p,values):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text('\n'.join(json.dumps(k,ensure_ascii=False)+' = '+json.dumps(v,ensure_ascii=False)+';' for k,v in values.items())+'\n',encoding='utf-8')
for language,values in strings.items():
    write_strings(settings/(language+'.lproj')/'Root.strings',values)
    write_strings(app/(language+'.lproj')/'InfoPlist.strings',{'CFBundleDisplayName':values['appName'],'CFBundleName':values['appName']})
p=app/'Info.plist'; info=plistlib.loads(p.read_bytes())
info.update(CFBundleDevelopmentRegion='en',CFBundleLocalizations=list(strings))
p.write_bytes(plistlib.dumps(info))
p=app/'Celeste.iOS.csproj'; source=p.read_text()
import re
source=source.replace('</Project>','''<ItemGroup>
    <BundleResource Include="Settings.bundle/**/*"><Link>Settings.bundle/%(RecursiveDir)%(Filename)%(Extension)</Link></BundleResource>
    <BundleResource Include="*.lproj/InfoPlist.strings"><Link>%(Identity)</Link></BundleResource>
    <BundleResource Include="../native-ui/strings.json" Link="native-ui/strings.json" />
    <BundleResource Include="../native-ui/rendered/**/*"><Link>native-ui/rendered/%(RecursiveDir)%(Filename)%(Extension)</Link></BundleResource>
  </ItemGroup>
</Project>''')
p.write_text(source)
print('Localized Celeste notice + Settings.bundle (notice, native Metal HUD, diagnostic logs)')
