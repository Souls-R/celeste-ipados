# 依赖、来源与许可范围

本仓库的 MIT 许可覆盖原创构建工具与适配代码，不改变 Celeste、FMOD、字体或其他上游项目的许可。

## Celeste

游戏程序、美术、字体图集、音效、音乐、剧情文本和其他资源属于各自权利人。本仓库不提供这些文件，也不收录游戏反编译源码。使用者从自己购买的游戏文件在本地生成构建输入。

源码转换工具为 ILSpy，来源：[icsharpcode/ILSpy](https://github.com/icsharpcode/ILSpy)。其版本固定于 `dependencies.json`，随各自上游许可使用。

## 框架与原生库

构建工具直接从各项目官方仓库获取固定版本源码，并使用源码内的 Xcode 工程编译 ARM64 iOS 静态库。

本仓库不附带第三方源码或预编译库。依赖下载和编译均在使用者指定的外部目录中完成，平台补丁应用于本地副本，保留原有版权与许可声明。

- 游戏框架：[FNA-XNA/FNA](https://github.com/FNA-XNA/FNA)。
- 窗口和输入：[libsdl-org/SDL](https://github.com/libsdl-org/SDL)，使用 SDL2 版本；托管绑定来自 [flibitijibibo/SDL2-CS](https://github.com/flibitijibibo/SDL2-CS)。
- 图形：[FNA-XNA/FNA3D](https://github.com/FNA-XNA/FNA3D)，使用 Metal 后端；着色器处理来自 [FNA-XNA/MojoShader](https://github.com/FNA-XNA/MojoShader)。
- 音频接口：[FNA-XNA/FAudio](https://github.com/FNA-XNA/FAudio)。游戏实际音频使用另行提供的 FMOD SDK。
- 视频：[FNA-XNA/Theorafile](https://github.com/FNA-XNA/Theorafile)，包括其内置的 Ogg、Vorbis 和 Theora 依赖。

上述组件各自的许可随官方源码提供。iOS 工程与启动画面由本仓库生成，应用图标从使用者自己的 `Celeste.app` 提取。

固定提交与工具版本见 [dependencies.json](dependencies.json)。

## FMOD

FMOD 是 Firelight Technologies 的音频中间件，按其自身许可提供。本仓库不提供 FMOD SDK 或静态库；构建时由使用者提供与已验证组合相符的 **1.10.11 iOS SDK**。

游戏自带托管绑定来自使用者的游戏文件。构建工具对创建入口的版本参数作适配，使其与已验证的 1.10.11 原生库组合一致。

## 字体与构建辅助工具

- 首屏优先使用本地游戏内的 Renogare 与中文位图字体，不在仓库中附带字体图像或生成后的声明图片。
- 缺字由使用者提供的 [Noto CJK](https://github.com/notofonts/noto-cjk) Medium 字体生成。该字体的许可见上游 OFL 文档；仓库不附带 OTF 文件。
- Pillow 用于本地解码图片与生成首屏文字，许可见 [Pillow](https://github.com/python-pillow/Pillow)。
- .NET、Xcode 与 Apple 平台 SDK 分别按其供应商条款使用，不包含在仓库中。

## 仓库组织

本仓库的工具入口、说明结构、免费声明与反馈模板参考 [Souls-R/silksong-ipados](https://github.com/Souls-R/silksong-ipados)。
