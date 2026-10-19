import sys
import pathlib,json,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
root=pathlib.Path(sys.argv[1]).resolve(); assets=root/'native-ui/assets'; out=root/'native-ui/rendered'; out.mkdir(exist_ok=True)
fonts=[]
for name in ['renogare64','chinese']:
    xml=ET.parse(assets/(name+'.fnt')).getroot()
    page=Image.open(assets/xml.find('pages/page').get('file')).convert('RGBA')
    chars={int(c.get('id')):{k:int(v) for k,v in c.attrib.items()} for c in xml.findall('chars/char')}
    fonts.append((chars,page))
fallback=ImageFont.truetype(str(assets/'NotoSansCJKsc-Medium.otf'),43)
fallback_chars=set()
def glyph(c):
    code=ord(c)
    preferred=[0,1] if code<0x250 else [1,0]
    for index in preferred:
        chars,page=fonts[index]
        if code in chars:
            g=chars[code]; x,y,w,h=[g[k] for k in ['x','y','width','height']]
            return page.crop((x,y,x+w,y+h)),g['xoffset'],g['yoffset'],g['xadvance']
    fallback_chars.add(c)
    image=Image.new('RGBA',(80,80)); ImageDraw.Draw(image).text((0,51),c,font=fallback,anchor='ls',fill='white')
    return image,0,0,round(fallback.getlength(c))
cache={}
def get(c):
    if c not in cache: cache[c]=glyph(c)
    return cache[c]
spec={
    'noticeTitle':(30,440), 'noticeFree':(20,440), 'noticeResale':(18,440),
    'enterGame':(26,400), 'nextLaunch':(14,190), 'showNotice':(17,225), 'skipNotice':(17,225),
    'noticeHelp':(13,440), 'controls':(11,440), 'subtitle':(13,440),
}
strings=json.loads((root/'native-ui/strings.json').read_text(encoding='utf-8'))
for language,values in strings.items():
    folder=out/language; folder.mkdir(exist_ok=True)
    for key,(size,width) in spec.items():
        text=values[key]; cap=35 if language=='en' else 38; scale=size/cap
        # Word wrapping for English; character wrapping for Chinese.
        limit=width/scale; lines=[]
        for paragraph in text.split('\n'):
            words=paragraph.split(' ') if language=='en' else list(paragraph)
            current=''
            for word in words:
                candidate=current+(' ' if current and language=='en' else '')+word
                if current and sum(get(c)[3] for c in candidate)>limit:
                    lines.append(current); current=word
                else: current=candidate
            lines.append(current)
        w=max(sum(get(c)[3] for c in line) for line in lines)+12
        image=Image.new('RGBA',(w,64*len(lines)+18))
        for row,line in enumerate(lines):
            x=6
            for c in line:
                bitmap,dx,dy,advance=get(c); image.alpha_composite(bitmap,(x+dx,8+row*64+dy)); x+=advance
        # Only the original bitmap alpha is used; tint comes from the native menu.
        alpha=image.getchannel('A'); image=Image.new('RGBA',image.size,'white'); image.putalpha(alpha)
        box=image.getbbox()
        if box: image=image.crop((max(0,box[0]-2),max(0,box[1]-2),min(image.width,box[2]+2),min(image.height,box[3]+2)))
        image.resize((max(1,round(image.width*scale*3)),max(1,round(image.height*scale*3))),Image.Resampling.LANCZOS).save(folder/(key+'.png'))
logo=Image.open(assets/'logo.png').convert('RGBA'); logo.crop(logo.getbbox()).save(out/'logo.png')
import shutil
shutil.copy2(assets/'dotarrow.png',out/'dotarrow.png')
(out/'font-audit.json').write_text(json.dumps({'english':'Original Celeste Renogare bitmap font','chinese':'Original Celeste Noto Sans CJK SC Medium bitmap font; missing glyphs use official same-family Medium OTF','fallback_glyphs':''.join(sorted(fallback_chars))},ensure_ascii=False,indent=2),encoding='utf-8')
print('Rendered original-font labels for three languages. Same-family fallback glyphs:',len(fallback_chars))
