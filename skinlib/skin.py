"""Skin and Layout builders that turn Python calls into a skins2 theme.xml plus images.

Coordinates passed to a Layout are logical 1x units; Skin.scale multiplies them and the
bitmap/font resources in the generated theme. An `anchor` names how a control follows the
window when it is resized:

    tl tr bl br   pinned to that corner, fixed size
    top bottom    stretches horizontally, pinned to the top / bottom edge
    left right    stretches vertically, pinned to the left / right edge
    fill          stretches both ways
"""
import re
import shutil
from contextlib import contextmanager
from os import PathLike
from pathlib import Path

from PIL import Image

from .paint import is_binary_alpha
from .xmlgen import E

ALPHA = "#FF00FF"  # skins2 needs a colour key; no image here uses pure magenta

ANCHORS = {
    "tl": ("lefttop", "lefttop"),
    "tr": ("righttop", "righttop"),
    "bl": ("leftbottom", "leftbottom"),
    "br": ("rightbottom", "rightbottom"),
    "top": ("lefttop", "righttop"),
    "bottom": ("leftbottom", "rightbottom"),
    "left": ("lefttop", "leftbottom"),
    "right": ("righttop", "rightbottom"),
    "fill": ("lefttop", "rightbottom"),
}


class Skin:
    def __init__(self, name, author, outdir, font_files, font_licenses=None, webpage="", scale=1):
        if not isinstance(scale, int) or isinstance(scale, bool) or scale not in (1, 2):
            raise ValueError("scale must be the integer 1 or 2")
        if font_licenses is None:
            font_licenses = ()
        elif isinstance(font_licenses, (str, bytes, PathLike)):
            font_licenses = (font_licenses,)
        self.name, self.author = name, author
        self.dir = Path(outdir)
        self.font_files = font_files  # weight -> path of a .ttf/.otf to bundle
        self.font_licenses = tuple(font_licenses)
        self.webpage = webpage
        self.scale = scale
        self.fonts, self.menus, self.windows = [], [], []
        self._images = {}        # bitmap id -> image, packed into sheets by write()
        self._aliases = {}       # requested id -> id of an identical image already registered
        self._by_content = {}    # (size, pixels) -> bitmap id
        self._font_ids = set()

    # resources ---------------------------------------------------------------

    def bitmap(self, bid, make):
        """Register bitmap `bid` and return the id to use for it; `make` is an image or a
        zero-argument callable that draws it. An image identical to one already registered
        returns that one's id, so each picture is stored once."""
        if bid in self._aliases:
            return self._aliases[bid]
        if bid not in self._images:
            img = make() if callable(make) else make
            if not is_binary_alpha(img):
                raise ValueError(f"{bid}: partly transparent pixels render dark in skins2; "
                                 "draw it with the surface it sits on (paint.solidify)")
            if self.scale == 2:
                img = img.convert("RGBa").resize((img.width * 2, img.height * 2),
                                                 Image.Resampling.LANCZOS).convert("RGBA")
                img.putalpha(img.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
            key = (img.size, img.tobytes())
            if key in self._by_content:
                self._aliases[bid] = self._by_content[key]
                return self._aliases[bid]
            self._by_content[key] = bid
            self._images[bid] = img
        return bid

    def font(self, size, weight="regular"):
        size *= self.scale
        fid = f"{weight}{size}"
        if fid not in self._font_ids:
            self.fonts.append(E("Font", id=fid, file=f"fonts/{Path(self.font_files[weight]).name}", size=size))
            self._font_ids.add(fid)
        return fid

    def menu(self, mid, items):
        """items: (label, action) pairs; None for a separator."""
        m = E("PopupMenu", id=mid)
        for item in items:
            m.add(E("MenuSeparator") if item is None else E("MenuItem", label=item[0], action=item[1]))
        self.menus.append(m)
        return mid

    def window(self, wid, **attrs):
        w = E("Window", id=wid, **attrs)
        self.windows.append(w)
        return w

    # output ------------------------------------------------------------------

    def write(self):
        fonts_dir = self.dir / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)
        for path in [*self.font_files.values(), *self.font_licenses]:
            shutil.copy2(path, fonts_dir / Path(path).name)
        theme = E("Theme", version="2.0", tooltipfont="defaultfont", magnet=15 * self.scale,
                  alpha="255", movealpha="255")
        theme.add(E("ThemeInfo", name=self.name, author=self.author, email="", webpage=self.webpage))
        theme.add(E("Font", id="defaultfont", file=f"fonts/{Path(self.font_files['regular']).name}",
                    size=12 * self.scale))
        theme.add(*self.fonts, *self._sheets(), *self.menus, *self.windows)
        xml = ('<?xml version="1.0" encoding="utf-8" standalone="no"?>\n'
               '<!DOCTYPE Theme PUBLIC "-//VideoLAN//DTD VLC Skins V2.0//EN" "skin.dtd">\n'
               "<!-- Generated by build.py from the Figma 'VLC Redesign (Community)' file. Do not edit by hand. -->\n"
               + theme.render())
        (self.dir / "theme.xml").write_text(xml, encoding="utf-8")


    def _sheets(self, wide=2048):
        """Pack every image into sprite sheets and return their Bitmap elements, each image a
        SubBitmap. A .vlt is unpacked to a temp folder on every start and each image is
        decoded separately: with ~470 single files VLC took 8 s to show this skin, against
        0.3 s for its default skin.

        Images wider than `wide` (the seek fill strips) get a sheet of their own, so they do
        not make the main sheet that wide."""
        img_dir = self.dir / "img"
        img_dir.mkdir(parents=True, exist_ok=True)
        normal = [b for b in self._images if self._images[b].width <= wide]
        wides = sorted(b for b in self._images if self._images[b].width > wide)

        sheets = []
        if normal:
            # try a few widths and keep the one that wastes least
            max_width = max(self._images[b].width for b in normal)
            sheets.append(min((skyline(normal, self._images, w) for w in (1024, 1280, 1536, 2048)
                               if w >= max_width), key=lambda r: r[1] * r[2]))
        if wides:
            place, y = {}, 0
            for bid in wides:
                place[bid] = (0, y)
                y += self._images[bid].height + 1
            sheets.append((place, max(self._images[b].width for b in wides), y - 1))

        out = []
        for n, (place, w, h) in enumerate(sheets):
            sheet = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            el = E("Bitmap", id=f"sheet{n}", file=f"img/sheet{n}.png", alphacolor=ALPHA)
            for bid, (x, y) in sorted(place.items(), key=lambda kv: (kv[1][1], kv[1][0])):
                img = self._images[bid]
                sheet.paste(img, (x, y))
                el.add(E("SubBitmap", id=bid, x=x, y=y, width=img.width, height=img.height))
            sheet.save(img_dir / f"sheet{n}.png", optimize=True)
            out.append(el)
        return out


def skyline(ids, images, width, pad=1):
    """Skyline bottom-left packing: each image, tallest first, goes where its bottom edge
    sits highest on the sheet. Returns ({id: (x, y)}, width, height)."""
    sky = [[0, 0, width + pad]]                 # contiguous [x, top, w] segments
    place = {}
    for bid in sorted(ids, key=lambda b: (-images[b].height, -images[b].width, b)):
        w, h = images[bid].width + pad, images[bid].height + pad
        best = None
        for i, (x, _, _) in enumerate(sky):
            top, covered, j = 0, 0, i
            while covered < w and j < len(sky):
                top, covered, j = max(top, sky[j][1]), covered + sky[j][2], j + 1
            if covered < w:
                break
            if best is None or (top + h, x) < (best[0] + h, best[1]):
                best = (top, x)
        top, x = best
        place[bid] = (x, top)
        segs = []
        for sx, sy, sw in sky:
            if sx + sw <= x or sx >= x + w:
                segs.append([sx, sy, sw])
                continue
            if sx < x:
                segs.append([sx, sy, x - sx])
            if sx + sw > x + w:
                segs.append([x + w, sy, sx + sw - x - w])
        segs.append([x, top + h, w])
        segs.sort()
        sky = []
        for seg in segs:
            if sky and sky[-1][1] == seg[1]:
                sky[-1][2] += seg[2]
            else:
                sky.append(seg)
    height = max(place[b][1] + images[b].height for b in place)
    used_w = max(place[b][0] + images[b].width for b in place)
    return place, used_w, height


class Layout:
    def __init__(self, skin, window, lid, w, h, min_size=None):
        """min_size=None makes a fixed-size layout; otherwise (minw, minh) and it can grow freely."""
        self.skin, self.id, self.w, self.h = skin, lid, w, h
        if min_size:
            minw, minh, maxw, maxh = min_size[0], min_size[1], 99999, 99999
        else:
            minw, maxw, minh, maxh = w, w, h, h
        s = skin.scale
        self.el = E("Layout", id=lid, width=w * s, height=h * s, minwidth=minw * s, maxwidth=maxw * s,
                    minheight=minh * s, maxheight=maxh * s)
        window.add(self.el)
        self._n = 0
        self._stack = [self.el]

    @property
    def _top(self):
        return self._stack[-1]

    @contextmanager
    def panel(self, x, y, w, h, anchor="fill"):
        """Controls added inside the `with` block are placed relative to this panel's
        top-left corner and anchored to its edges rather than the layout's."""
        p = E("Panel", id=self._id("panel"), **self._place(x, y, anchor),
              width=self._size(w), height=self._size(h))
        self._top.add(p)
        self._stack.append(p)
        try:
            yield p
        finally:
            self._stack.pop()

    def _id(self, hint):
        self._n += 1
        return f"{self.id}.{hint}{self._n}"

    def _size(self, value):
        return None if value is None else value * self.skin.scale

    def _points(self, points):
        if self.skin.scale == 1:
            return points
        return re.sub(r"-?\d+", lambda m: str(int(m.group()) * self.skin.scale), points)

    def _place(self, x, y, anchor, keep=None):
        lt, rb = ANCHORS[anchor]
        return dict(x=self._size(x), y=self._size(y), lefttop=lt, rightbottom=rb,
                    xkeepratio="true" if keep and "x" in keep else None,
                    ykeepratio="true" if keep and "y" in keep else None)

    def comment(self, text):
        self._top.add(text)

    def image(self, bid, x, y, w=None, h=None, anchor="tl", resize=None, action=None,
              action2=None, visible=None, art=None, keep=None, hint="img"):
        self._top.add(E("Image", id=self._id(hint), **self._place(x, y, anchor, keep),
                      width=self._size(w), height=self._size(h), image=bid, resize=resize,
                      action=action, action2=action2, art="true" if art else None, visible=visible))

    def button(self, states, x, y, action, tip=None, anchor="tl", visible=None, keep=None, hint="btn"):
        up, over, down = states
        self._top.add(E("Button", id=self._id(hint), **self._place(x, y, anchor, keep), up=up, over=over,
                      down=down, action=action, tooltiptext=tip, visible=visible))

    def checkbox(self, state, off, on, action_off, action_on, tip_off=None, tip_on=None,
                 x=0, y=0, anchor="tl", visible=None, keep=None, hint="chk"):
        """`off` and `on` are (up, over, down) image triples. action_off runs when clicked
        while `state` is false, action_on when it is true."""
        self._top.add(E("Checkbox", id=self._id(hint), **self._place(x, y, anchor, keep),
                      up1=off[0], over1=off[1], down1=off[2], up2=on[0], over2=on[1], down2=on[2],
                      state=state, action1=action_off, action2=action_on,
                      tooltiptext1=tip_off, tooltiptext2=tip_on, visible=visible))

    def toggle(self, state, off, on, action_off, action_on, tip_off=None, tip_on=None,
               x=0, y=0, anchor="tl", visible=None, hint="tgl"):
        """Like a Checkbox, but as two buttons shown by the state's value. skins2's Checkbox
        flips its image on every change notice rather than reading the state, so one that
        starts out of step (vlc.isMute did) stays wrong; visibility is evaluated by value.
        `visible` is an extra condition of the form "a" or "not a" (no parentheses in skins2)."""
        both = (lambda cond: f"{visible} and {cond}") if visible else (lambda cond: cond)
        self.button(off, x, y, action_off, tip_off, anchor, both(f"not {state}"), hint=hint)
        self.button(on, x, y, action_on, tip_on, anchor, both(state), hint=hint)

    def text(self, text, x, y, w, font, color, align="left", anchor="tl", visible=None,
             scrolling="none", keep=None, hint="txt"):
        self._top.add(E("Text", id=self._id(hint), **self._place(x, y, anchor, keep),
                      width=self._size(w), text=text, font=font, color=color, alignment=align,
                      scrolling=scrolling, focus="false", visible=visible))

    def slider(self, value, x, y, points, up, over=None, down=None, w=None, h=None, thickness=None,
               tip=None, anchor="tl", visible=None, background=None, hint="sld"):
        """background: (bitmap id, columns, rows) of a SliderBackground's frame grid."""
        el = E("Slider", id=self._id(hint), **self._place(x, y, anchor),
               width=self._size(w), height=self._size(h), up=up, over=over, down=down,
               points=self._points(points), thickness=self._size(thickness), value=value,
               tooltiptext=tip, visible=visible)
        if background:
            el.add(E("SliderBackground", id=self._id("bg"), image=background[0], nbhoriz=background[1],
                     nbvert=background[2]))
        self._top.add(el)

    def video(self, x, y, w, h, anchor="fill", visible=None, autoresize=False):
        self._top.add(E("Video", id=self._id("video"), **self._place(x, y, anchor),
                      width=self._size(w), height=self._size(h), autoresize=autoresize, visible=visible))

    def playtree(self, x, y, w, h, font, colors, item, anchor="left", scrollbar=None):
        el = E("Playtree", id=self._id("playtree"), **self._place(x, y, anchor),
               width=self._size(w), height=self._size(h), font=font, flat="true", itemimage=item, **colors)
        if scrollbar:
            sx, sy, points, up, over = scrollbar
            el.add(E("Slider", id=self._id("scroll"), **self._place(sx, sy, anchor),
                     points=self._points(points), up=up, over=over, down=over,
                     thickness=self._size(6)))
        self._top.add(el)
