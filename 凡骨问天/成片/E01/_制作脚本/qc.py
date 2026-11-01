# -*- coding: utf-8 -*-
"""第 1 集成片质检：技术参数 + 逐镜抽帧联系表（供目视核对 05 号文件第九节清单）。"""
import os
import subprocess

import sheet

ROOT = r"D:\MiniMax\Novel\凡骨问天\成片\E01"
OUT = os.path.join(ROOT, "E01_测灵_成片.mp4")
SEG = r"D:\MiniMax\work\e1seg"
QC = r"D:\MiniMax\work\sheets"


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size,bit_rate:stream=index,codec_type,codec_name,"
                        "width,height,r_frame_rate,channels,sample_rate",
                        "-of", "default=noprint_wrappers=1", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def main():
    if not os.path.exists(OUT):
        print("成片不存在")
        return
    print("=== 成片技术参数 ===")
    print(probe(OUT))
    print("=== 逐镜抽帧 ===")
    files = []
    for fn in sorted(os.listdir(SEG)):
        if not fn.startswith("S") or not fn.endswith(".mp4"):
            continue
        if fn == "silent.mp4":
            continue
        p = os.path.join(SEG, fn)
        thumb = os.path.join(QC, "qc_%s.jpg" % fn.replace(".mp4", ""))
        if not os.path.exists(thumb):
            subprocess.run(["ffmpeg", "-y", "-ss", "0.6", "-i", p, "-frames:v", "1",
                            "-vf", "scale=320:-1", thumb], capture_output=True)
        if os.path.exists(thumb):
            files.append((thumb, fn.replace(".mp4", "")))
    sheet.build(files, os.path.join(QC, "E01_qc_shots.jpg"), cols=5)
    print("镜头数: %d" % len(files))


if __name__ == "__main__":
    main()
