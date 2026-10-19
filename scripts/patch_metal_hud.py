import sys
import pathlib,plistlib,re,shutil
root=pathlib.Path(sys.argv[1]).resolve()
shutil.copy2(root/'iPadOSHUD.cs',root/'game/Celeste/iPadOSHUD.cs')
p=root/'game/Celeste/Celeste.cs'; text=p.read_text()
if 'iPadOSHUD.Apply();' not in text:
    anchor='\t\tSettings.Instance.ApplyScreen();\n\t\tSFX.Initialize();'
    assert anchor in text
    text=text.replace(anchor,'\t\tSettings.Instance.ApplyScreen();\n\t\tiPadOSHUD.Apply();\n\t\tSFX.Initialize();')
    p.write_text(text)
p=root/'game/Celeste/Celeste.cs'; text=p.read_text()
anchor='\tprotected override void RenderCore()\n\t{\n\t\tbase.RenderCore();'
if 'if (iPadOSHUD.Pending)' not in text:
    if anchor not in text: raise ValueError('Missing RenderCore anchor')
    text=text.replace(anchor,'\tprotected override void RenderCore()\n\t{\n        if (iPadOSHUD.Pending) iPadOSHUD.Apply();\n\t\tbase.RenderCore();')
p.write_text(text)
print('Direct SDL window Metal HUD initialization installed')
