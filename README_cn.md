# VLC Redesign 简体中文高 DPI 皮肤

基于 [VLC Redesign](https://github.com/mamogh/vlc-redesign-skin) 修改的 VLC 3 皮肤，新增简体中文化、中文字体支持，以及适合 4K / 200% 缩放显示器的 2× 版本。

原始设计来自 Juxtopposed 的 VLC Redesign：

- [Figma 设计稿](https://www.figma.com/community/file/1691465999134370980/vlc-redesign)
- [设计介绍视频](https://www.youtube.com/watch?v=ERFeOgqk324)

![皮肤播放视频时的效果](docs/screenshots/video.png)

## 主要改进

- **完整简体中文界面**：翻译固定标签、按钮提示、菜单、播放列表、迷你播放器和均衡器。
- **中文内容正常显示**：内置 Noto Sans SC，媒体标题和播放列表中的简体中文、繁体中文及中英混排不再显示为方块。
- **2× 高 DPI 版本**：窗口、控件、字体、滑块和位图均按两倍尺寸生成，适合 4K / 200% 缩放。
- **保留英文版本**：英文和简体中文各有 1×、2× 两个独立安装包。

## 安装

### 4K / 200% 缩放（推荐）

下载并使用 [`dist/VLC-Redesign-CN-2x.vlt`](dist/VLC-Redesign-CN-2x.vlt)。

### 其他版本

| 语言 | 1× 标准尺寸 | 2× 高 DPI 尺寸 |
| --- | --- | --- |
| 简体中文 | [`VLC-Redesign-CN.vlt`](dist/VLC-Redesign-CN.vlt) | [`VLC-Redesign-CN-2x.vlt`](dist/VLC-Redesign-CN-2x.vlt) |
| English | [`VLC-Redesign.vlt`](dist/VLC-Redesign.vlt) | [`VLC-Redesign-2x.vlt`](dist/VLC-Redesign-2x.vlt) |

安装步骤：

1. 在 VLC 中打开 **工具 → 偏好设置 → 界面**。
2. 选择 **使用自定义皮肤**，再选择下载的 `.vlt` 文件。
3. 保存设置并重启 VLC。

启用皮肤后，设置入口位于窗口左上角的 **••• → 设置**。

> VLC 3 的 skins2 引擎无法让同一个皮肤包自动跟随系统 DPI，也无法在运行中跨不同缩放的显示器自动切换。系统缩放改变后，请重新选择对应的 1× 或 2× 包并重启 VLC。

## 已包含的界面

- 深色和浅色播放器
- 播放列表侧栏
- 迷你播放器
- 均衡器
- 全屏播放控制条
- 中文菜单和按钮工具提示

2× 包使用双倍字号重新绘制动态文字，并将现有点阵图标和位图资源放大到两倍分辨率。它改善了高 DPI 屏幕上的尺寸和可用性，但不会增加原始图标资源中不存在的细节。

## 未包含的内容

皮肤只能修改 VLC 的播放器窗口。设置页面、文件对话框等仍使用 VLC 原有界面；原生菜单的外观也由操作系统和 VLC 决定。设计稿中的媒体库页面不属于 VLC 3 皮肤引擎的能力范围。更多技术说明见 [`docs/notes.md`](docs/notes.md)。

## 从源码构建

需要 Python 3、Pillow 和 fontTools。默认构建会生成英文、简体中文各 1× 和 2×，共四个安装包：

```bash
python build.py
```

如果系统安装了 [uv](https://docs.astral.sh/uv/)，可以直接运行：

```bash
uv run --with pillow --with fonttools --with lxml python build.py
```

其中 lxml 用于完整的 DTD 校验。

只构建简体中文的两个版本：

```bash
python build.py --language zh-CN
```

只构建简体中文 2× 版本：

```bash
python build.py --language zh-CN --scale 2
```

构建结果位于 `dist/`，同时生成解包目录和可直接安装的 `.vlt` 文件。每次构建都会自动运行主题检查。

## 测试

创建测试媒体需要 FFmpeg：

```bash
python tools/make_testmedia.py
```

运行中文 2× 交互测试：

```bash
python tools/smoke_test.py --language zh-CN --scale 2
python tools/edge_cases.py --language zh-CN --scale 2
```

测试会启动真实 VLC 窗口并模拟点击。运行期间请避免操作鼠标、键盘或切换窗口；如果 VLC 显示上一次运行的崩溃提示，请先关闭该提示。

## 致谢与许可证

- **原始项目**：[mamogh/vlc-redesign-skin](https://github.com/mamogh/vlc-redesign-skin)。
- **设计**：Juxtopposed 的 [VLC Redesign](https://www.figma.com/community/file/1691465999134370980/vlc-redesign)，采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可。皮肤中的衍生图片遵循相同许可。
- **Inter 字体**：Inter Project Authors，采用 SIL Open Font License，见 [`fonts/Inter-LICENSE.txt`](fonts/Inter-LICENSE.txt)。
- **Noto Sans SC 字体**：来自官方 [Noto CJK](https://github.com/notofonts/noto-cjk) 项目，采用 SIL Open Font License 1.1，见 [`fonts/NotoSansSC-LICENSE.txt`](fonts/NotoSansSC-LICENSE.txt)。
- **代码**：`build.py`、`skinlib/` 和 `tools/` 采用 [CC0 1.0](LICENSE)。CC0 仅覆盖代码，不包括设计、衍生图片和字体。

本项目是非官方皮肤，与 VideoLAN 没有隶属关系，也未获得其认可。VLC 及 VLC 交通锥标志属于 VideoLAN。
