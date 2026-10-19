# Celeste iPadOS

[简体中文](README.md) · English

Unofficial iOS / iPadOS build tools for **Celeste**, using .NET iOS AOT to compile native ARM64 code with Metal rendering.

This project contains no official game assets. Build from your own purchased Steam macOS copy.

## Getting started

Follow the [build guide](#build-your-own-ipa) on a Mac to compile an IPA. Playing requires an external controller or keyboard.

```text
python3 build.py deps       Download and compile build dependencies
python3 build.py prepare    Generate the native iOS project
python3 build.py native     Compile an unsigned IPA
```

Use each command's `--help` for its arguments.

## Features

- Original 16:9 aspect ratio and 60 FPS gameplay.
- Controller and external keyboard input.
- Launch notice in Simplified Chinese, Traditional Chinese and English.
- System Settings switches for the launch notice, native Metal HUD and diagnostic logs.
- Save backup and replacement through Files.

Steam services, achievements and Everest/mods are not supported.

## Notice

**This project is completely free. Please buy and support the original Celeste.**

Do not sell or pay for IPA packages, paid groups, or test access. If you paid for these, request a refund.

## Dependencies

| Dependency | Source |
| --- | --- |
| Celeste 1.4.0.0 | Purchase and download the Steam macOS version |
| Python 3.12 and Pillow | Install Python 3.12; install Pillow using the commands below |
| .NET 10 SDK and iOS workload | [Microsoft downloads](https://dotnet.microsoft.com/download/dotnet/10.0), then `dotnet workload install ios` |
| Xcode | Install and open once to finish component setup |
| [ILSpy](https://github.com/icsharpcode/ILSpy) | Installed by `deps` |
| [FNA](https://github.com/FNA-XNA/FNA) | Fetched from the official repository by `deps` |
| SDL2, FNA3D, FAudio and Theorafile | Built from official sources by `deps` |
| FMOD 1.10.11 iOS SDK | Supply locally |
| Noto Sans CJK SC Medium | Download the official [NotoSansCJKsc-Medium.otf](https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Medium.otf) |

See [dependencies.json](dependencies.json) for pins and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.

## Build your own IPA

Build environment: Mac, .NET SDK **10.0.402**, iOS workload **26.0.11017**, Xcode **26.6**. Game version: Steam macOS **1.4.0.0**.

### Obtain the game

Sign into a Steam account that owns Celeste and open the console:

```sh
open 'steam://open/console'
```

In the Steam console:

```text
download_depot 504230 504232
```

Keep the complete `Celeste.app`, normally located under:

```text
~/Library/Application Support/Steam/steamapps/content/app_504230/depot_504232/Celeste.app
```

### Set up tools

From the repository directory:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
dotnet workload install ios

buildRoot="$HOME/CelesteBuild"
python3 build.py deps --output "$buildRoot/deps"
```

Keep build files outside the repository and reserve 10 GB of space. The `deps` output directory must not already exist. Continue in the same terminal.

### Prepare the project

Adjust these paths to your local files:

```sh
gameApp="$HOME/Library/Application Support/Steam/steamapps/content/app_504230/depot_504232/Celeste.app"
fmodSdk="$HOME/Downloads/fmod-1.10.11-ios"
noticeFont="$HOME/Downloads/NotoSansCJKsc-Medium.otf"
nativeOutput="$buildRoot/native"

python3 build.py prepare \
  --game-app "$gameApp" \
  --deps "$buildRoot/deps" \
  --fmod-sdk "$fmodSdk" \
  --font "$noticeFont" \
  --output "$nativeOutput" \
  --bundle-id 'org.example.celeste.personal'
```

`--fmod-sdk` must point to the FMOD **1.10.11** iOS SDK containing `libfmod_iphoneos.a` and `libfmodstudio_iphoneos.a`.

`prepare` requires a new output directory. Choose a different `nativeOutput` path to regenerate the project.

The default version is `1.4.0`, build number `8`; override with `--version` and `--build-number`. Keep the same `--bundle-id` for updates.

### Compile

```sh
python3 build.py native --work "$nativeOutput" --allow-newer-xcode
```

`--allow-newer-xcode` supports the Xcode and iOS workload versions above.

Output:

```text
native/output/Celeste-1.4.0-build8-unsigned.ipa
native/logs/native.log
```

Subsequent `native` runs reuse compilation caches.

Sign the unsigned IPA, then install it.

## Settings and logs

Open iPad Settings → Apps → Celeste:

- **Show Notice**: on by default; you can also skip future notices from the launch screen.
- **Performance Overlay**: off by default; shows FPS, frame time and GPU time. Requires iOS / iPadOS 16 or later.
- **Diagnostic Logs**: off by default; records startup, resource loading and input logs.

Close the game from the app switcher and relaunch after changing settings.

With diagnostics enabled, find `runtime.log`, `native.log` and `errorLog.txt` under Files → On My iPad → Celeste → Celeste. Export logs before relaunching. For build errors, see `logs/` in the build directory.

## Saves and updates

Saves are stored at `Documents/Celeste/Saves`. Back up the complete `Celeste` folder through Files before updating. Install over the existing app with the same Bundle ID and compatible signing identity to retain saves.

**Do not uninstall before updating. Uninstalling deletes your saves.**

Original adaptation code is under [MIT](LICENSE). Game files and dependencies retain their own licenses.
