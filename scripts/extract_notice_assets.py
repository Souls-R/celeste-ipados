import sys
import pathlib,struct,io,json,xml.etree.ElementTree as ET
from PIL import Image
root=pathlib.Path(sys.argv[1]).resolve()
content=root/'input/Celeste.app/Contents/Resources/Content'
out=root/'native-ui/assets'; out.mkdir(exist_ok=True)
def string(s):
    value=shift=0
    while True:
        b=s.read(1)[0]; value|=(b&127)<<shift
        if not b&128: break
        shift+=7
    return s.read(value).decode()
def data_image(p):
    b=p.read_bytes(); w,h=struct.unpack_from('<ii',b); alpha=b[8]; pos=9; pixels=bytearray()
    while len(pixels)<w*h*4:
        count=b[pos]; pos+=1
        a=b[pos] if alpha else 255
        if alpha: pos+=1
        if a:
            blue,green,red=b[pos:pos+3]; pos+=3; pixel=bytes([red,green,blue,a])
        else: pixel=b'\0\0\0\0'
        pixels.extend(pixel*count)
    assert len(pixels)==w*h*4
    # Game texture data is premultiplied; PNG/UIKit use straight alpha.
    for i in range(0,len(pixels),4):
        a=pixels[i+3]
        if a and a!=255:
            for c in range(3): pixels[i+c]=min(255,round(pixels[i+c]*255/a))
    return Image.frombytes('RGBA',(w,h),bytes(pixels))
s=io.BytesIO((content/'Graphics/Atlases/Gui.meta').read_bytes()); s.read(4); string(s); s.read(4)
sprites={}; sheets={}
for _ in range(struct.unpack('<h',s.read(2))[0]):
    sheet=string(s)
    for _ in range(struct.unpack('<h',s.read(2))[0]):
        name=string(s).replace('\\','/'); coords=struct.unpack('<8h',s.read(16)); sprites[name]=(sheet,coords)
(out/'gui-index.json').write_text(json.dumps(sprites,indent=2))
print('Candidate textures:',[x for x in sprites if any(k in x for k in ['title','logo','background','font','renogare','snow'])])
def sprite(name):
    sheet,(x,y,w,h,fx,fy,fw,fh)=sprites[name]
    if sheet not in sheets: sheets[sheet]=data_image(content/'Graphics/Atlases'/(sheet+'.data'))
    crop=sheets[sheet].crop((x,y,x+w,y+h)); image=Image.new('RGBA',(fw,fh)); image.alpha_composite(crop,(-fx,-fy)); return image
for name in ['logo','title','dotarrow']:
    if name in sprites:
        image=sprite(name); image.save(out/(name+'.png')); print(name,image.size)
font=ET.parse(content/'Dialog/Fonts/renogare64.fnt').getroot()
print('Font page in GUI:',[x for x in sprites if 'renogare64' in x])
for p in font.findall('pages/page'):
    name=p.get('file').removesuffix('.png'); matches=[x for x in sprites if x.endswith(name)]
    assert len(matches)==1,matches
    sprite(matches[0]).save(out/(name+'.png'))
for name in ['renogare64.fnt','chinese.fnt','chinese_0.png']:
    import shutil
    shutil.copy2(content/'Dialog/Fonts'/name,out/name)
strings=json.loads((root/'native-ui/strings.json').read_text(encoding='utf-8'))
chars={int(e.get('id')) for e in ET.parse(content/'Dialog/Fonts/chinese.fnt').getroot().findall('chars/char')}
latin={int(e.get('id')) for e in font.findall('chars/char')}
for language,values in strings.items():
    missing=sorted({c for text in values.values() for c in text if ord(c) not in chars|latin and c!='\n'})
    print(language,'Missing original bitmap glyphs:',''.join(missing))
