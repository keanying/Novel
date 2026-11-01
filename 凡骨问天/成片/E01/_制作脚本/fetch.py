# -*- coding: utf-8 -*-
"""把 state.json 里已生成的图下载到 定妆/ 目录（可重复执行，已存在的跳过）。"""
import json
import os
import time

import gen


def read_state():
    for _ in range(10):
        try:
            with open(gen.STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            time.sleep(0.5)
    return {}


def main():
    state = read_state()
    items = []
    for phase in ("A", "B", "C"):
        for name, info in state.get(phase, {}).items():
            if name == "__files__":
                # 阶段 A 的明细放在 __files__ 里
                for fn, sub in info.items():
                    items.append((fn, sub.get("folder") or fn.split("_")[0], sub["node_id"]))
                continue
            if isinstance(info, dict) and info.get("node_id"):
                items.append((name, info.get("folder") or name.split("_")[0], info["node_id"]))
    n = 0
    for name, folder, nid in items:
        dest = os.path.join(gen.OUT_ROOT, folder, name + ".jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            n += 1
            continue
        try:
            gen.download(nid, dest)
            n += 1
        except Exception as e:
            print("  下载失败", name, e)
    print("已落盘 %d 张 / 共 %d 张" % (n, len(items)))


if __name__ == "__main__":
    main()
