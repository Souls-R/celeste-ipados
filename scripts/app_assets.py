"""Create app icons from the user's original macOS game icon."""
from pathlib import Path
import json
import plistlib
from PIL import Image


def generate_icons(app: Path, output: Path):
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    name=info.get('CFBundleIconFile','Celeste')
    if not name.endswith('.icns'): name+='.icns'
    icon=Image.open(app/'Contents/Resources'/name).convert('RGBA')
    output.mkdir(parents=True)
    (output/'Contents.json').write_text(json.dumps({'info':{'author':'xcode','version':1}})+'\n')
    folder=output/'AppIcon.appiconset'; folder.mkdir()
    images=[]
    specs=[('iphone',size,scale) for size in [20,29,40,60] for scale in [2,3]]
    specs += [('ipad',size,scale) for size in [20,29,40,76] for scale in [1,2]]
    specs += [('ipad',83.5,2),('ios-marketing',1024,1)]
    for idiom,size,scale in specs:
        pixels=round(size*scale)
        image=Image.new('RGBA',(pixels,pixels),(16,24,47,255))
        image.alpha_composite(icon.resize((pixels,pixels),Image.Resampling.LANCZOS))
        filename=f'{idiom}-{size}@{scale}x.png'
        image.convert('RGB').save(folder/filename)
        images.append(dict(idiom=idiom,size=f'{size}x{size}',scale=f'{scale}x',filename=filename))
    (folder/'Contents.json').write_text(json.dumps(dict(images=images,info=dict(author='xcode',version=1)),indent=2)+'\n')
