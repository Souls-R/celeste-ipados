import sys
"""Root the exact XNB readers used by this Celeste depot for iOS full AOT."""
import io, json, pathlib, re, struct
root=pathlib.Path(sys.argv[1]).resolve()
content=root/'input/Celeste.app/Contents/Resources/Content'
def read7(stream):
    value=shift=0
    while True:
        b=stream.read(1)[0]; value|=(b&127)<<shift
        if not b&128: return value
        shift+=7
constructors={
    'SpriteFontReader':'SpriteFontReader', 'Texture2DReader':'Texture2DReader',
    'RectangleReader':'RectangleReader','CharReader':'CharReader','Vector3Reader':'Vector3Reader','EffectReader':'EffectReader',
}
registrations={}; inventory=[]
for p in content.rglob('*.xnb'):
    data=p.read_bytes(); assert data[:3]==b'XNB' and not data[5]&128, str(p)
    stream=io.BytesIO(data); stream.seek(10)
    names=[]
    for _ in range(read7(stream)):
        name=stream.read(read7(stream)).decode(); version=struct.unpack('<I',stream.read(4))[0]
        short=name.removeprefix('Microsoft.Xna.Framework.Content.')
        if short.startswith('ListReader`1[[System.Char,'): constructor='ListReader<char>'
        elif short.startswith('ListReader`1[[Microsoft.Xna.Framework.Rectangle,'): constructor='ListReader<Rectangle>'
        elif short.startswith('ListReader`1[[Microsoft.Xna.Framework.Vector3,'): constructor='ListReader<Vector3>'
        else: constructor=constructors[short.split(',')[0]]
        registrations[name]=constructor; names.append(name)
    inventory.append({'asset':p.relative_to(content).as_posix(),'readers':names})
path=root/'FNA/src/Content/ContentTypeReaderManager.cs'
text=path.read_text(encoding='utf-8-sig')
start='\t\t\t// Celeste iOS AOT XNB factories: begin'
end='\t\t\t// Celeste iOS AOT XNB factories: end'
if start in text: text=text[:text.index(start)]+text[text.index(end)+len(end):]
lines=[start,'\t\t\t// Explicit constructors avoid legacy mscorlib name resolution and root closed generics.']
for name,constructor in registrations.items():
    lines.append('\t\t\ttypeCreators['+json.dumps(name)+'] = () => new '+constructor+'();')
lines.append(end)
anchor='assemblyName = typeof(ContentTypeReaderManager).Assembly.FullName;'
assert anchor in text
text=text.replace(anchor,anchor+'\n'+'\n'.join(lines))
path.write_text(text,encoding='utf-8')
(root/'xnb-reader-inventory.json').write_text(json.dumps(inventory,indent=2))
print('Registered',len(registrations),'concrete AOT reader factories for',len(inventory),'XNB assets.')
