"""Portable orchestration for the original-aspect Build 8 port."""
from pathlib import Path
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[1]
LOCK=json.loads((REPO/'dependencies.json').read_text(encoding='utf-8'))


def dotnet_environment(command):
    executable=shutil.which(command)
    if not executable: raise ValueError(f'.NET executable not found: {command}')
    executable=Path(executable).resolve()
    env=os.environ.copy()
    env['DOTNET_ROOT']=str(executable.parent)
    env['PATH']=str(executable.parent)+os.pathsep+env.get('PATH','')
    env['DOTNET_CLI_TELEMETRY_OPTOUT']='1'
    return str(executable),env


def outside_repo(path):
    path=path.expanduser().resolve()
    if path==REPO or path.is_relative_to(REPO) or REPO.is_relative_to(path):
        raise ValueError('Use a separate build/dependency directory outside the repository.')
    return path


def run(command,*,cwd=None,env=None,log=None):
    print('Running: '+' '.join(str(x) for x in command),flush=True)
    if log:
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('w',encoding='utf-8') as output:
            result=subprocess.run([str(x) for x in command],cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT)
        if result.returncode: raise RuntimeError(f'Command failed ({result.returncode}); see {log}')
    else:
        subprocess.run([str(x) for x in command],cwd=cwd,env=env,check=True)


def git_head(path):
    return subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()


def fetch_dependencies(args):
    if sys.platform!='darwin': raise ValueError('Dependency compilation requires macOS with Xcode.')
    output=outside_repo(args.output)
    if output.exists(): raise ValueError(f'Dependency directory already exists: {output}; choose a new path.')
    dotnet,env=dotnet_environment(args.dotnet)
    output.mkdir(parents=True)
    sources=output/'sources'; sources.mkdir()
    for name,source in LOCK['sources'].items():
        path=sources/name
        run(['git','clone','--filter=blob:none','--no-checkout',source['url'],path])
        run(['git','-C',path,'checkout','--detach',source['commit']])
    for name,paths in [('FNA',['lib/SDL2-CS','lib/FAudio','lib/Theorafile']),('FNA3D',['MojoShader'])]:
        run(['git','-C',sources/name,'-c','url.https://github.com/.insteadOf=git://github.com/','submodule','update','--init',*paths])
    validate_sources(output)
    run([dotnet,'tool','install','ilspycmd','--tool-path',output/'tools','--version',LOCK['ilspycmd']],env=env)
    from scripts.native_libraries import build_libraries
    build_libraries(output,jobs=args.jobs)
    (output/'dependencies.json').write_text(json.dumps(LOCK,indent=2)+'\n',encoding='utf-8')
    print(f'Dependencies ready: {output}')


def validate_sources(deps):
    expected={name:source['commit'] for name,source in LOCK['sources'].items()}
    expected.update(LOCK['submodules'])
    for name,commit in expected.items():
        path=deps/'sources'/name
        if git_head(path)!=commit: raise ValueError(f'Unexpected dependency revision at {path}')


def fmod_library(sdk,name):
    matches=list(sdk.rglob(name))
    if len(matches)!=1: raise ValueError(f'Expected exactly one {name} under {sdk}; found {len(matches)}.')
    return matches[0]


def prepare_project(args):
    if sys.platform!='darwin': raise ValueError('Project preparation requires macOS and Xcode command line tools.')
    output=outside_repo(args.output)
    if output.exists(): raise ValueError(f'Build directory already exists: {output}; choose a new path.')
    app=args.game_app.expanduser().resolve()
    resources=app/'Contents/Resources'
    executable=resources/'Celeste.exe'
    if not executable.is_file() or not (resources/'Content/Graphics/Atlases/Gui.meta').is_file():
        raise ValueError('Supply the complete unmodified Steam macOS Celeste.app bundle.')
    digest=hashlib.sha256(executable.read_bytes()).hexdigest()
    if digest!=LOCK['game']['celeste_exe_sha256']:
        raise ValueError('Celeste.exe differs from the supported Steam macOS 1.4.0.0 build. No files were changed.')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z0-9][A-Za-z0-9-]*)+',args.bundle_id):
        raise ValueError('Provide a reverse-DNS bundle identifier such as org.example.celeste.personal.')
    if not re.fullmatch(r'\d+(?:\.\d+){0,2}',args.version) or not re.fullmatch(r'[1-9]\d*',args.build_number):
        raise ValueError('Version must be numeric (for example 1.4.0), and build number must be a positive integer.')
    font=args.font.expanduser().resolve()
    if not font.is_file(): raise ValueError(f'Notice fallback font not found: {font}')
    deps=args.deps.expanduser().resolve()
    validate_sources(deps)
    libraries=['libSDL2.a','libFNA3D.a','libFAudio.a','libtheorafile.a']
    for name in libraries:
        if not (deps/'native'/name).is_file(): raise ValueError(f'Missing native library: {name}; complete deps first.')
    sdk=args.fmod_sdk.expanduser().resolve()
    fmod=[fmod_library(sdk,name) for name in ['libfmod_iphoneos.a','libfmodstudio_iphoneos.a']]
    ilspy=args.ilspy.expanduser().resolve() if args.ilspy else deps/'tools/ilspycmd'
    if not ilspy.is_file(): raise ValueError(f'ilspycmd not found: {ilspy}; run deps first.')
    dotnet,env=dotnet_environment(args.dotnet)
    run(['xcrun','--sdk','iphoneos','--show-sdk-path'],env=env)
    output.mkdir(parents=True)
    logs=output/'logs'; logs.mkdir()
    shutil.copytree(app,output/'input/Celeste.app')
    ignore=shutil.ignore_patterns('.git','bin','obj')
    shutil.copytree(deps/'sources/FNA',output/'FNA',ignore=ignore)
    native=output/'native-libraries'; native.mkdir()
    for name in libraries: shutil.copy2(deps/'native'/name,native/name)
    native_sdk=output/'fmod-sdk'; native_sdk.mkdir()
    for library in fmod: shutil.copy2(library,native_sdk/library.name)
    for source in (REPO/'src/runtime').iterdir(): shutil.copy2(source,output/source.name)
    (output/'native-ui').mkdir()
    shutil.copy2(REPO/'src/launch/strings.json',output/'native-ui/strings.json')
    shutil.copy2(REPO/'src/launch/LaunchScreen.storyboard',output/'LaunchScreen.storyboard')
    from scripts.app_assets import generate_icons
    generate_icons(output/'input/Celeste.app',output/'Assets.xcassets')
    run([ilspy,'-p','-o',output/'decompiled','-r',output/'input/Celeste.app/Contents/Resources',output/'input/Celeste.app/Contents/Resources/Celeste.exe'],env=env,log=logs/'01-decompile.log')
    run([sys.executable,REPO/'scripts/prepare_source.py',output/'decompiled',output/'game'],env=env,log=logs/'02-source.log')
    steps=['setup_ios.py','patch_xnb_readers.py','patch_controller_input.py','configure_native_ui.py','patch_metal_hud.py','extract_notice_assets.py']
    for index,step in enumerate(steps,3):
        run([sys.executable,REPO/'scripts'/step,output],env=env,log=logs/f'{index:02d}-{Path(step).stem}.log')
    shutil.copy2(font,output/'native-ui/assets/NotoSansCJKsc-Medium.otf')
    run([sys.executable,REPO/'scripts/render_notice_text.py',output],env=env,log=logs/'09-notice-fonts.log')
    finalize_project(output,args)
    metadata=dict(format=1,version=args.version,build_number=args.build_number,bundle_id=args.bundle_id,aspect='16:9',game_sha256=digest,dependencies=LOCK)
    (output/'build-manifest.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(f'Project ready: {output}\nNext: python3 build.py native --work "{output}"')


def finalize_project(work,args):
    path=work/'ios/Main.cs'
    path.write_text(path.read_text().replace('Build 8 (original 16:9)',f'Build {args.build_number} (original 16:9)'),encoding='utf-8')
    project=work/'ios/Celeste.iOS.csproj'
    text=project.read_text()
    for tag,value in [('ApplicationId',args.bundle_id),('ApplicationVersion',args.build_number),('ApplicationDisplayVersion',args.version)]:
        text=re.sub(fr'<{tag}>[^<]*</{tag}>',f'<{tag}>{value}</{tag}>',text)
    project.write_text(text,encoding='utf-8')
    path=work/'ios/Info.plist'; info=plistlib.loads(path.read_bytes())
    info.pop('MetalHUDEnabled',None)
    info.update(CFBundleIdentifier=args.bundle_id,CFBundleVersion=args.build_number,CFBundleShortVersionString=args.version,MetalHudEnabled=True)
    path.write_bytes(plistlib.dumps(info))
    path=work/'ios/Settings.bundle/Info.plist'; info=plistlib.loads(path.read_bytes()); info['CFBundleIdentifier']=args.bundle_id+'.settings'; path.write_bytes(plistlib.dumps(info))
    ET.fromstring(text)


def build_native(args):
    if sys.platform!='darwin': raise ValueError('IPA compilation requires macOS with Xcode and the .NET iOS workload.')
    work=outside_repo(args.work)
    manifest=json.loads((work/'build-manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format')!=1 or manifest.get('aspect')!='16:9': raise ValueError('Unsupported build manifest.')
    dotnet,env=dotnet_environment(args.dotnet)
    command=[dotnet,'build','ios/Celeste.iOS.csproj','-c','Release','-v','minimal']
    if args.allow_newer_xcode: command.append('-p:ValidateXcodeVersion=false')
    run(command,cwd=work,env=env,log=work/'logs/native.log')
    ipa=work/'ios/bin/Release/net10.0-ios/ios-arm64/CelesteiPadOS.ipa'
    if not ipa.is_file(): raise RuntimeError(f'IPA was not generated: {ipa}')
    destination=work/'output'/f'Celeste-{manifest["version"]}-build{manifest["build_number"]}-unsigned.ipa'
    destination.parent.mkdir(exist_ok=True); shutil.copy2(ipa,destination)
    # Replace only the manifest entry; avoid recompressing the user's Content.
    with zipfile.ZipFile(destination,'a') as archive:
        names=[name for name in archive.namelist() if name.startswith('Payload/') and name.count('/')==2 and name.endswith('/Info.plist')]
        if len(names)!=1: raise ValueError('Expected one application Info.plist in the IPA.')
        name=names[0]; entry=archive.getinfo(name); info=plistlib.loads(archive.read(entry))
        info.pop('MetalHUDEnabled',None)
        info.update(MetalHudEnabled=True,CFBundleIdentifier=manifest['bundle_id'],CFBundleVersion=manifest['build_number'],CFBundleShortVersionString=manifest['version'])
        archive.filelist.remove(entry); archive.NameToInfo.pop(name)
        archive.writestr(name,plistlib.dumps(info),compress_type=zipfile.ZIP_DEFLATED)
    shutil.copy2(work/'build-manifest.json',destination.parent/'build-manifest.json')
    print(f'Unsigned IPA: {destination}\nBuild log: {work/"logs/native.log"}')
