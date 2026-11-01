# -*- coding: utf-8 -*-
"""只下载已完成的首帧图（可与生成任务并行跑）。"""
import json
import os
import time

import gen
import ep1_run


def read_state():
    for _ in range(20):
        try:
            with open(ep1_run.state_file("frames"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            time.sleep(0.5)
    return {}


def main():
    st = read_state()
    n = 0
    for fn, info in st.items():
        dest = os.path.join(ep1_run.FIRST, fn + ".jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            n += 1
            continue
        try:
            gen.download(info["node_id"], dest)
            n += 1
        except Exception as e:
            print("  下载失败", fn, str(e)[:80])
    print("已落盘 %d / %d" % (n, len(st)))


if __name__ == "__main__":
    main()
