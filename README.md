# Celeste iPadOS

简体中文 · [English](README_EN.md)

《蔚蓝 / Celeste》非官方 iOS / iPadOS 构建工具，使用 .NET iOS AOT 编译为 ARM64 原生程序，通过 Metal 渲染。

本项目不包含官方游戏资源，你需要从自己购买的 Steam macOS 版游戏文件开始构建。

## 开始构建

在 Mac 上按[构建教程](#构建自己的-ipa)编译 IPA，游玩需要外接手柄或键盘。

```text
python3 build.py deps       下载并编译构建依赖
python3 build.py prepare    生成 iOS 工程
python3 build.py native     编译未签名 IPA
```

运行对应命令的 `--help` 查看参数。

## 功能

- 原版 16:9 显示、60 帧运行。
- 手柄与外接键盘。
- 首屏声明，支持简体中文、繁体中文和英文。
- 在系统设置中配置首屏声明、原生 Metal 性能面板和诊断日志。
- 通过「文件」App 备份和替换存档。

不支持 Steam 组件、成就及 Everest / Mod。

## 声明

**本项目完全免费，请支持正版并购买原游戏。**

请勿倒卖或购买 IPA 包、付费群或测试资格等，如你已付费购买请立即申请退款。

## 依赖与来源

| 项目 | 获取方式 |
| --- | --- |
| Celeste 1.4.0.0 | 在 Steam 购买并下载 macOS 版 |
| Python 3.12、Pillow | 安装 Python 3.12，Pillow 按下方命令安装 |
| .NET 10 SDK 与 iOS workload | [Microsoft .NET 下载](https://dotnet.microsoft.com/download/dotnet/10.0)，安装后运行 `dotnet workload install ios` |
| Xcode | 安装后打开一次，完成组件安装 |
| [ILSpy](https://github.com/icsharpcode/ILSpy) | `deps` 自动安装 |
| [FNA](https://github.com/FNA-XNA/FNA) | `deps` 从官方仓库获取 |
| SDL2、FNA3D、FAudio、Theorafile | `deps` 从官方源码编译 |
| FMOD 1.10.11 iOS SDK | 自行准备 |
| Noto Sans CJK SC Medium | 下载官方 [NotoSansCJKsc-Medium.otf](https://github.com/notofonts/noto-cjk/blob/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Medium.otf) |

依赖版本见 [dependencies.json](dependencies.json)，来源与许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 构建自己的 IPA

构建环境：Mac、.NET SDK **10.0.402**、iOS workload **26.0.11017**、Xcode **26.6**。游戏版本：Steam macOS **1.4.0.0**。

### 获取游戏文件

登录已购买游戏的 Steam 账号，在终端打开 Steam 控制台：

```sh
open 'steam://open/console'
```

在 Steam 控制台执行：

```text
download_depot 504230 504232
```

下载完成后，目录通常为：

```text
~/Library/Application Support/Steam/steamapps/content/app_504230/depot_504232/Celeste.app
```

保留完整 `.app` 目录。

### 安装工具和下载依赖

在仓库目录打开终端：

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
dotnet workload install ios

buildRoot="$HOME/CelesteBuild"
python3 build.py deps --output "$buildRoot/deps"
```

构建目录放在仓库外，预留 10 GB 空间；`deps` 输出目录必须尚不存在。后续命令在同一终端执行。

### 生成工程

下面的路径按实际文件位置修改：

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

`--fmod-sdk` 指向 FMOD **1.10.11** iOS SDK 目录，需包含 `libfmod_iphoneos.a` 和 `libfmodstudio_iphoneos.a`。

`prepare` 输出目录必须尚不存在；重新生成时更换 `nativeOutput` 路径。

默认版本为 `1.4.0`、构建号为 `8`，可用 `--version` 和 `--build-number` 修改。覆盖更新时沿用原来的 `--bundle-id`。

### 编译 IPA

```sh
python3 build.py native --work "$nativeOutput" --allow-newer-xcode
```

`--allow-newer-xcode` 用于上述 Xcode 与 iOS workload 版本组合。

输出位置：

```text
native/output/Celeste-1.4.0-build8-unsigned.ipa
native/logs/native.log
```

再次运行 `native` 会复用编译缓存。

IPA 未签名，签名后即可安装。

## 设置与日志

打开 iPad 系统「设置 → App → 蔚蓝」：

- **显示声明**：默认开启，也可以在首屏选择下次直接进入游戏。
- **性能面板**：默认关闭，显示帧率、帧时间和 GPU 耗时，需 iOS / iPadOS 16 或以上。
- **诊断日志**：默认关闭，记录启动、资源加载和输入日志。

修改后从后台关闭并重新打开游戏。开启日志后，可在「文件 → 我的 iPad → 蔚蓝 → Celeste」中找到 `runtime.log`、`native.log` 和错误文件 `errorLog.txt`。

`runtime.log` 和 `native.log` 在启用日志的每次启动时重写，请先导出。构建日志位于构建目录的 `logs/`。

## 存档与程序更新

存档位于 `Documents/Celeste/Saves`。更新前，通过「文件」App 备份整个 `Celeste` 文件夹。

使用相同 Bundle ID 和兼容签名身份覆盖安装，可保留存档。

**更新时不要先卸载应用，卸载会删除存档。**

仓库原创适配代码采用 [MIT](LICENSE)。原游戏与各依赖分别受其自身许可约束。
