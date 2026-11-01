# -*- coding: utf-8 -*-
"""下载老魏 c3/c4 并拼对比图"""
import os
import gen
import sheet

OUT = r"D:\MiniMax\work\chk"
os.makedirs(OUT, exist_ok=True)

items = [("老魏", "老魏_01_正脸_c3", "458544347628568"),
         ("老魏", "老魏_01_正脸_c4", "458543871050938")]
paths = []
for folder, name, nid in items:
    dest = os.path.join(OUT, name + ".jpg")
    gen.download(nid, dest)
    paths.append((dest, name))
    print("ok", dest)

sheet.build(paths, os.path.join(r"D:\MiniMax\work\sheets", "redo_qc3.jpg"), cols=2)
print("done")
