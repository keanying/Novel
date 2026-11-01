# -*- coding: utf-8 -*-
"""生成《定妆总览.jpg》——18 个角色定稿正脸 + 派生图 + 道具，中文标签。"""
import os

import sheet

OUT_ROOT = r"D:\MiniMax\Novel\凡骨问天\定妆"
OUT = os.path.join(OUT_ROOT, "定稿总览.jpg")

# 定稿正脸的角色顺序（按戏份）
ORDER = ["许听澜", "许小禾", "沈青棠", "宁鹤年", "顾长风", "严松", "老魏",
         "石头", "钱多宝", "镇长", "父亲许大河", "少年听澜",
         "剑宗弟子男", "剑宗弟子女", "云巅宫弟子", "镇民甲", "镇民乙", "镇民丙"]


def main():
    files = []
    for folder in ORDER:
        p = os.path.join(OUT_ROOT, folder, "%s_01_正脸.jpg" % folder)
        if os.path.exists(p):
            files.append((p, folder))
    sheet.build(files, OUT, cols=6)

    # 派生图 + 道具单独两张
    derived = []
    for folder in ORDER:
        d = os.path.join(OUT_ROOT, folder)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.startswith(folder + "_0") and fn != "%s_01_正脸.jpg" % folder:
                derived.append((os.path.join(d, fn),
                                "%s/%s" % (folder, fn.replace(".jpg", ""))))
    sheet.build(derived, os.path.join(r"D:\MiniMax\work\sheets", "derived.jpg"), cols=5)

    props = []
    d = os.path.join(OUT_ROOT, "道具")
    for fn in sorted(os.listdir(d)):
        if fn.lower().endswith(".jpg"):
            props.append((os.path.join(d, fn), fn.replace(".jpg", "")))
    sheet.build(props, os.path.join(r"D:\MiniMax\work\sheets", "props_all.jpg"), cols=5)


if __name__ == "__main__":
    main()
