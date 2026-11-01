# -*- coding: utf-8 -*-
"""把定妆候选图拼成联系表，便于一次性肉眼比对锚点特征。"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

OUT_ROOT = r"D:\MiniMax\Novel\凡骨问天\定妆"
SHEET_DIR = r"D:\MiniMax\work\sheets"
TILE_W = 320
COLS = 4
LABEL_H = 34

# 中文标签需要 CJK 字体，否则渲染成方框
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]


def get_font(size=18):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def build(files, out_path, cols=COLS):
    if not files:
        print("没有文件")
        return
    tiles = []
    font = get_font(18)
    for path, label in files:
        if not os.path.exists(path):
            continue
        try:
            im = Image.open(path).convert("RGB")
        except Exception as e:
            print("skip", path, e)
            continue
        ratio = im.height / im.width
        h = int(TILE_W * ratio)
        im = im.resize((TILE_W, h), Image.LANCZOS)
        tile = Image.new("RGB", (TILE_W, h + LABEL_H), "white")
        tile.paste(im, (0, LABEL_H))
        d = ImageDraw.Draw(tile)
        d.rectangle([0, 0, TILE_W - 1, LABEL_H - 1], fill=(25, 25, 30))
        d.text((6, 7), label, fill=(255, 235, 120), font=font)
        tiles.append(tile)
    if not tiles:
        print("没有可用图")
        return
    rows = (len(tiles) + cols - 1) // cols
    tw = max(t.width for t in tiles)
    th = max(t.height for t in tiles)
    sheet = Image.new("RGB", (cols * tw, rows * th), (210, 210, 214))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path, quality=88)
    print("%s  (%d 张, %dx%d)" % (out_path, len(tiles), sheet.width, sheet.height))


def collect_all():
    files = []
    for folder in sorted(os.listdir(OUT_ROOT)):
        d = os.path.join(OUT_ROOT, folder)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith((".jpg", ".png")):
                files.append((os.path.join(d, fn),
                              "%s/%s" % (folder, fn.replace(".jpg", "").replace(".png", ""))))
    return files


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(SHEET_DIR, exist_ok=True)
    if which == "all":
        files = collect_all()
        # 每 8 张一张联系表
        for i in range(0, len(files), 8):
            build(files[i:i + 8], os.path.join(SHEET_DIR, "sheet_%02d.jpg" % (i // 8 + 1)))
    else:
        build([(os.path.join(OUT_ROOT, which, f),
                f.rsplit(".", 1)[0]) for f in sorted(os.listdir(os.path.join(OUT_ROOT, which)))],
              os.path.join(SHEET_DIR, "%s.jpg" % which))
