# VLC Redesign skin

[简体中文说明](README_cn.md)

A skin for VLC 3 based on Juxtopposed's redesign of VLC.

- Design: [VLC Redesign on Figma Community](https://www.figma.com/community/file/1691465999134370980/vlc-redesign)
- Video: [I Redesigned VLC After 25 Years](https://www.youtube.com/watch?v=ERFeOgqk324)

![VLC playing a video with the skin](docs/screenshots/video.png)

## Install

1. Download the package for your language and display scaling:
   - English: [`dist/VLC-Redesign.vlt`](dist/VLC-Redesign.vlt) (1×) or
     [`dist/VLC-Redesign-2x.vlt`](dist/VLC-Redesign-2x.vlt) (2×).
   - Simplified Chinese: [`dist/VLC-Redesign-CN.vlt`](dist/VLC-Redesign-CN.vlt) (1×) or
     [`dist/VLC-Redesign-CN-2x.vlt`](dist/VLC-Redesign-CN-2x.vlt) (2×).
   For a 4K display used at 200% scaling, choose the 2× package for your language; Simplified
   Chinese users should choose `VLC-Redesign-CN-2x.vlt`.
2. In VLC, open **Tools → Preferences → Interface**, choose **Use custom skin** and pick that file.
3. Save and restart VLC.

VLC 3's skins2 engine cannot make one package automatically follow the system DPI or adapt while
VLC is running, including when its window moves between monitors with different scaling. If your
scaling changes, select the matching package and restart VLC.

With the skin on, Preferences are under **Settings** in the ••• menu at the top left.

## What's included

- The player, in dark and light
- A playlist sidebar
- A mini player
- An equalizer
- Controls in fullscreen

The ••• menu switches theme and opens the mini player and playlist.
The Simplified Chinese packages localize fixed labels, button tooltips, menus and the equalizer.
Dynamic media titles and playlist entries are still drawn by VLC with Noto Sans SC, so Chinese and
mixed-script text remains supported. More [screenshots](docs/screenshots).

## Not included

A skin can only restyle VLC's player window. Settings, dialogs and menus keep VLC's own look,
and the design's library views don't exist in VLC 3. [docs/notes.md](docs/notes.md) has the details.

## Building

`python build.py` regenerates all four `.vlt` packages in `dist/`: English and Simplified Chinese,
each at 1× and 2×. Use `--language` to build only one language, or `--scale 1` / `--scale 2` to
build only one scale; the options can be combined. The build needs Python 3 with Pillow and
fontTools. With [uv](https://docs.astral.sh/uv/), you can instead run
`uv run --with pillow --with fonttools --with lxml python build.py`; lxml enables full DTD validation.

The 2× packages resample the existing bitmap and icon resources at twice their resolution. Dynamic
text is redrawn by VLC at doubled font sizes rather than upscaled as an image. Inter is used for
static English labels; Noto Sans SC is used for dynamic media titles and playlist text.
[docs/notes.md](docs/notes.md) explains how it works.

## Credits and license

- **Design:** ["VLC Redesign"](https://www.figma.com/community/file/1691465999134370980/vlc-redesign) by Juxtopposed, licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This skin adapts it for VLC 3. The
  icons are cut from the design; the images in `dist/`, `docs/screenshots/` and `reference/figma/`
  are derived from it and shared under the same license.
- **Inter:** [Inter](https://github.com/rsms/inter) by the Inter Project Authors, under the SIL Open
  Font License ([fonts/Inter-LICENSE.txt](fonts/Inter-LICENSE.txt)), used for static English labels.
- **Noto Sans SC:** [Noto Sans SC](https://github.com/notofonts/noto-cjk) from the official Noto CJK
  project, by the Noto Project Authors, under the
  [SIL Open Font License 1.1](https://openfontlicense.org/)
  ([fonts/NotoSansSC-LICENSE.txt](fonts/NotoSansSC-LICENSE.txt)), used for dynamic media titles and
  playlist text.
- **Code:** `build.py`, `skinlib/` and `tools/` are dedicated to the public domain under
  [CC0 1.0](LICENSE). CC0 covers only those source files, not the design, derived images or fonts.
  The `.vlt` packages combine assets under each of the licenses above.

This is an unofficial skin, not affiliated with or endorsed by VideoLAN. VLC and the VLC cone are
trademarks of VideoLAN.
