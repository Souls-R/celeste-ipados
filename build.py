#!/usr/bin/env python3
"""Build a personal native Celeste iOS application from your own game files."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    if not __debug__:
        raise SystemExit('Run Python without -O; source conversion assertions must remain enabled.')
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    deps=commands.add_parser('deps',help='Fetch and compile official build dependencies')
    deps.add_argument('--output',type=Path,required=True)
    deps.add_argument('--dotnet',default='dotnet')
    deps.add_argument('--jobs',type=int,choices=range(1,17),default=4,help='Parallel native compiler jobs')
    prepare=commands.add_parser('prepare',help='Generate the native project from a macOS game bundle')
    prepare.add_argument('--game-app',type=Path,required=True,help='Your unmodified Celeste.app (Steam macOS 1.4.0.0)')
    prepare.add_argument('--deps',type=Path,required=True)
    prepare.add_argument('--fmod-sdk',type=Path,required=True,help='Local FMOD 1.10.11 iOS SDK directory')
    prepare.add_argument('--font',type=Path,required=True,help='NotoSansCJKsc-Medium.otf, for missing notice glyphs')
    prepare.add_argument('--output',type=Path,required=True,help='New build directory outside this repository')
    prepare.add_argument('--bundle-id',required=True,help='Keep this identifier for future updates')
    prepare.add_argument('--version',default='1.4.0')
    prepare.add_argument('--build-number',default='8')
    prepare.add_argument('--dotnet',default='dotnet')
    prepare.add_argument('--ilspy',type=Path,help='Override the pinned ilspycmd executable')
    native=commands.add_parser('native',help='Build an unsigned ARM64 AOT IPA on macOS')
    native.add_argument('--work',type=Path,required=True)
    native.add_argument('--dotnet',default='dotnet')
    native.add_argument('--allow-newer-xcode',action='store_true',help='Skip the .NET Xcode version check (used for the documented Xcode 26.6 build)')
    args=parser.parse_args()
    try:
        from scripts.workflow import fetch_dependencies,prepare_project,build_native
        {'deps':fetch_dependencies,'prepare':prepare_project,'native':build_native}[args.command](args)
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as exc:
        print(f'Build stopped: {exc}',file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
