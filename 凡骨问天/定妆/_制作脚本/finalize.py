# -*- coding: utf-8 -*-
"""定妆资产收尾：
1. 把选定的候选正脸重命名为规范名（<角色>_01_正脸.jpg），其余候选归档到 _候选/
2. 导出《生成提示词全表.md》——可直接粘到即梦/可灵/海螺/Midjourney 复现
"""
import json
import os
import re
import shutil

import gen

SEL = gen.load_json(gen.SELECTED_PATH, {})
STATE = gen.load_json(gen.STATE_PATH, {})
FILES = STATE.get("A", {}).get("__files__", {})

# key -> (文件夹, 显示名)
KEY_NAME = {}


def collect_keys():
    for folder, key, anchor, extra, suffix, aspect in gen.PHASE_A + gen.EXTRA_CAST:
        KEY_NAME[key] = folder


collect_keys()


def finalize_names():
    moved = 0
    for key, info in SEL.items():
        folder = KEY_NAME.get(key)
        if not folder:
            continue
        nid = info["node_id"]
        # 找出该候选对应的源文件名
        src_name = None
        for fn, f in FILES.items():
            if f["node_id"] == nid:
                src_name = fn
                break
        if not src_name:
            print("  找不到源文件:", key)
            continue
        src = os.path.join(gen.OUT_ROOT, folder, src_name + ".jpg")
        dst = os.path.join(gen.OUT_ROOT, folder, "%s_01_正脸.jpg" % folder)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.move(src, dst)
            moved += 1
        # 其余候选归档
        cdir = os.path.join(gen.OUT_ROOT, folder, "_候选")
        fdir = os.path.join(gen.OUT_ROOT, folder)
        for fn in sorted(os.listdir(fdir)):
            p = os.path.join(fdir, fn)
            if not os.path.isfile(p):
                continue
            if fn.startswith(folder + "_01_正脸_c"):
                os.makedirs(cdir, exist_ok=True)
                shutil.move(p, os.path.join(cdir, fn))
                moved += 1
    print("整理完成，移动 %d 个文件" % moved)


def export_prompt_table():
    out = []
    out.append("# 《凡骨问天》定妆生成提示词全表\n")
    out.append("> 本文件由 `04_定妆包.md` 的提示词自动汇总，附实际生成结果与定稿文件对应关系。")
    out.append("> 换工具复现时：**正脸用文生图，其余全部用正脸定稿图做参考图**。\n")
    out.append("> 通用负面词（拼在提示词末尾）：\n")
    out.append("> " + gen.NEG_TEXT + "\n")
    out.append("> ⚠️ 服装色必须按 04 号文件「服装色标准」表翻译，「青白色」在模型里会跑偏成绿色。\n")
    out.append("---\n")
    out.append("## 一、正脸定妆照（文生图，3:4，2K）\n")
    out.append("| 角色 | 提示词（锚点＋造型＋正脸后缀＋负面词） | 定稿文件 |")
    out.append("|---|---|---|")
    for folder, key, anchor, extra, suffix, aspect in gen.PHASE_A + gen.EXTRA_CAST:
        p = gen.ph_a_prompt(key, anchor, extra, suffix)
        fin = "%s/%s_01_正脸.jpg" % (folder, folder)
        out.append("| %s | %s | `定妆/%s` |" % (folder, p.replace("|", "/"), fin))
    out.append("\n---\n")
    out.append("## 二、三视图 / 表情组 / 造型变体（图生图，参考图＝正脸定稿）\n")
    out.append("| 角色 | 提示词 | 比例 | 参考图 |")
    out.append("|---|---|---|---|")
    for folder, key, filename, prompt, aspect in gen.PHASE_B:
        out.append("| %s | %s | %s | `定妆/%s/%s_01_正脸.jpg` |"
                   % (folder, prompt.replace("|", "/"), aspect, folder, folder))
    out.append("\n---\n")
    out.append("## 三、道具定妆（文生图，1:1，2K）\n")
    out.append("| 道具 | 提示词 |")
    out.append("|---|---|")
    for name, desc in gen.PHASE_C:
        out.append("| %s | %s |" % (name, (desc + "，" + gen.PROP_SUFFIX).replace("|", "/")))
    out.append("\n---\n")
    out.append("## 四、定稿清单\n")
    out.append("| 角色 | 定稿正脸 | 其他定妆 |")
    out.append("|---|---|---|")
    for folder, key, anchor, extra, suffix, aspect in gen.PHASE_A + gen.EXTRA_CAST:
        others = [fn for fn, k, *_ in gen.PHASE_B if k == folder]
        extra_files = []
        if others:
            extra_files = ["%s/%s.jpg" % (folder, o) for o in others]
        out.append("| %s | `定妆/%s/%s_01_正脸.jpg` | %s |"
                   % (folder, folder, folder, "、".join("`定妆/%s`" % e for e in extra_files) or "—"))
    path = os.path.join(os.path.dirname(gen.OUT_ROOT), "定妆生成提示词全表.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("已导出:", path)


if __name__ == "__main__":
    finalize_names()
    export_prompt_table()
