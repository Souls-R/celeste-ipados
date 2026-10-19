"""Build official SDL2/FNA library sources for ARM64 iOS with Xcode."""
from pathlib import Path
import shutil
import subprocess
import sys


def build_libraries(deps: Path, jobs=4):
    if sys.platform!='darwin': raise ValueError('Native library builds require macOS and Xcode.')
    deps=deps.resolve(); sources=deps/'sources'
    output=deps/'native'; output.mkdir(exist_ok=True)
    logs=deps/'logs'; logs.mkdir(exist_ok=True)
    sdl=sources/'SDL2/include'
    targets=[
        ('SDL2',sources/'SDL2/Xcode/SDL/SDL.xcodeproj','Static Library-iOS','libSDL2.a',[]),
        ('FNA3D',sources/'FNA3D/Xcode-iOS/FNA3D.xcodeproj','FNA3D','libFNA3D.a',[sources/'FNA3D/include',sources/'FNA3D/MojoShader']),
        ('FAudio',sources/'FNA/lib/FAudio/Xcode-iOS/FAudio.xcodeproj','FAudio','libFAudio.a',[]),
        ('Theorafile',sources/'FNA/lib/Theorafile/Xcode-iOS/theorafile.xcodeproj','theorafile','libtheorafile.a',[sources/'FNA/lib/Theorafile/lib']),
    ]
    for name,project,target,library,includes in targets:
        build=deps/'build'/name
        headers=' '.join('"'+str(path)+'"' for path in [sdl,*includes])
        command=['xcodebuild','-project',str(project),'-target',target,'-configuration','Release','-sdk','iphoneos','-jobs',str(jobs),
                 'ARCHS=arm64','ONLY_ACTIVE_ARCH=NO','IPHONEOS_DEPLOYMENT_TARGET=15.0','CODE_SIGNING_ALLOWED=NO',
                 'ENABLE_BITCODE=NO','DEBUG_INFORMATION_FORMAT=dwarf',f'SYMROOT={build/"products"}',f'OBJROOT={build/"objects"}',
                 f'HEADER_SEARCH_PATHS=$(inherited) {headers}']
        if name=='SDL2':
            command.append('GCC_PREPROCESSOR_DEFINITIONS=$(inherited) SDL_MAIN_HANDLED=1')
            # SDL_render_metal.m loads the official shader byte array from its
            # header. The standalone .metal build product is never loaded by
            # this static library, and FNA3D supplies the game's Metal renderer.
            command.append('EXCLUDED_SOURCE_FILE_NAMES=SDL_shaders_metal.metal')
        log=logs/f'{name}.log'
        print(f'Building {name} from official source; log: {log}',flush=True)
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        if result.returncode: raise RuntimeError(f'{name} build failed; see {log}')
        archive=build/'products/Release-iphoneos'/library
        if not archive.is_file(): raise RuntimeError(f'Native archive not found: {archive}')
        shutil.copy2(archive,output/library)
    print(f'Native libraries ready: {output}',flush=True)


if __name__=='__main__':
    build_libraries(Path(sys.argv[1]))
