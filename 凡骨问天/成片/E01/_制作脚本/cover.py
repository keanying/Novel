# -*- coding: utf-8 -*-
"""生成第 1 集封面图：9:16，含剧名、集数、副标题与 AI 生成标识。"""
import os

from PIL import Image, ImageDraw, ImageFont

FIRST = r"D:\MiniMax\Novel\凡骨问天\成片\E01\首帧"
OUT = r"D:\MiniMax\Novel\凡骨问天\成片\E01\E01_封面.jpg"
SRC = os.path.join(FIRST, "E01_S07_首帧_v2.jpg")

W, H = 1080, 1920
DARK = (14, 16, 22)


def font(size, bold=False):
    paths = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
             r"C:\Windows\Fonts\simhei.ttf"]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    im = Image.open(SRC).convert("RGB")
    ratio = im.height / im.width
    im = im.resize((W, int(W * ratio)), Image.LANCZOS).crop((0, 0, W, H))
    # 底部压暗，文字更清晰
    grad = Image.new("L", (1, H), 0)
    gd = grad.load()
    for y in range(H):
        if y > H * 0.45:
            gd[0, y] = int(210 * (y - H * 0.45) / (H * 0.55))
    grad = grad.resize((W, H))
    im = Image.composite(Image.new("RGB", (W, H), DARK), im, grad)
    d = ImageDraw.Draw(im)

    f_title = font(132)
    f_sub = font(52)
    f_meta = font(38)

    title = "凡骨问天"
    tw = d.textbbox((0, 0), title, font=f_title)[2]
    d.text(((W - tw) / 2, H * 0.60), title, font=f_title, fill=(255, 255, 255),
           stroke_width=6, stroke_fill=(0, 0, 0))
    # 标题下的金色横线
    lw = tw + 80
    d.rectangle([(W - lw) / 2, H * 0.60 + 160, (W + lw) / 2, H * 0.60 + 166],
                fill=(214, 178, 96))

    ep = "第 01 集 · 测灵"
    ew = d.textbbox((0, 0), ep, font=f_sub)[2]
    d.text(((W - ew) / 2, H * 0.60 + 210), ep, font=f_sub, fill=(238, 222, 180),
           stroke_width=3, stroke_fill=(0, 0, 0))

    meta = "AI 短剧 · 古风修仙"
    mw = d.textbbox((0, 0), meta, font=f_meta)[2]
    d.text(((W - mw) / 2, H * 0.60 + 300), meta, font=f_meta, fill=(210, 210, 214),
           stroke_width=2, stroke_fill=(0, 0, 0))

    # AI 生成标识（合规要求）
    mark = "本片由 AI 生成"
    fw = font(30)
    wm = d.textbbox((0, 0), mark, font=fw)[2]
    d.rounded_rectangle([(W - wm - 44, H - 150), (W - 22, H - 96)], radius=8,
                        outline=(255, 255, 255), width=2)
    d.text((W - wm - 33, H - 142), mark, font=fw, fill=(255, 255, 255))

    im.save(OUT, quality=94)
    print("封面:", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
