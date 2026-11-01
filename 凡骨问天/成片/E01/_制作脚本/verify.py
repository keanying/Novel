# -*- coding: utf-8 -*-
"""校验并重下损坏的产出文件（配音/音乐/首帧/视频）。"""
import os
import subprocess
import sys

import gen
import ep1_run

ROOT = ep1_run.ROOT
VOICE = ep1_run.VOICE
MUSIC = ep1_run.MUSIC
FIRST = ep1_run.FIRST
VIDEO = ep1_run.VIDEO


def probe_ok(path, want_type):
    sel = {"audio": "a", "video": "v"}.get(want_type, want_type)
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel,
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip().startswith(want_type)


def check_dir(d, ext, want_type):
    bad = []
    if not os.path.isdir(d):
        return bad
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(ext):
            continue
        p = os.path.join(d, fn)
        if not os.path.exists(p) or os.path.getsize(p) < 2000:
            bad.append((fn, "过小/缺失"))
            continue
        if want_type and not probe_ok(p, want_type):
            bad.append((fn, "格式异常"))
    return bad


def redownload(pairs):
    for nid, dest in pairs:
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except Exception as e:
                print("  删除失败", dest, e)
        try:
            gen.download(nid, dest)
            print("  重下成功", os.path.basename(dest), os.path.getsize(dest))
        except Exception as e:
            print("  重下失败", dest, str(e)[:120])


def main():
    st = ep1_run.load_state("tts")
    print("=== 配音 ===")
    bad = check_dir(VOICE, ".mp3", "audio")
    for fn, why in bad:
        print("  损坏:", fn, why)
    fix = []
    for fn, why in bad:
        for key, info in st.items():
            if key == fn[:-4]:
                ext = os.path.splitext(info.get("file_name") or ".mp3")[1] or ".mp3"
                fix.append((info["node_id"], os.path.join(VOICE, fn)))
    redownload(fix)

    print("=== 音乐 ===")
    bad = check_dir(MUSIC, ".mp3", "audio")
    for fn, why in bad:
        print("  损坏:", fn, why)
    mst = ep1_run.load_state("music")
    fix = []
    for fn, why in bad:
        for key, info in mst.items():
            if key == fn[:-4]:
                fix.append((info["node_id"], os.path.join(MUSIC, fn)))
    redownload(fix)

    print("=== 首帧 ===")
    for fn, why in check_dir(FIRST, ".jpg", None):
        print("  异常:", fn, why)

    print("=== 视频 ===")
    for fn, why in check_dir(VIDEO, ".mp4", "video"):
        print("  异常:", fn, why)


if __name__ == "__main__":
    main()
