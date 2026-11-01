# -*- coding: utf-8 -*-
"""补出指定镜头的额外版本首帧（用于修正情绪不符的镜头）。"""
import os
import sys

import ep1
import ep1_run
import gen

# 镜号 -> 追加的情绪强化描述
EXTRA = {
    15: "女孩眼眶含泪，泪水在眼眶里打转将落未落，嘴唇微微发颤，神情不舍又委屈",
    19: "女孩满脸泪水，泪水顺着脸颊滑落，眉头紧皱，嘴唇微微发抖，神情悲伤委屈，"
        "不是微笑不是大笑",
}


def main():
    shots = {s[0]: s for s in ep1.SHOTS}
    st = ep1_run.load_state("frames")
    jobs = []
    for no, extra in EXTRA.items():
        _, dur, size, move, refs, img, vid, subs = shots[no]
        need = ep1_run.ref_urls(refs)
        prompt = img + "，" + extra + "，" + ep1.STYLE + "，" + ep1.NEG_ALL
        fn = "E01_S%02d_首帧_v3" % no
        if fn in st:
            print("已存在", fn)
            continue
        job = {"prompt": prompt, "aspect_ratio": "9:16", "resolution": "2K",
               "output_file": fn}
        if refs:
            job["input_urls"] = [need[r] for r in refs if r in need]
        jobs.append(job)

    def _on(item):
        fn = item["requested_file"]
        st[fn] = {"node_id": item["node_id"]}
        ep1_run.save_state("frames", st)
        print("  已生成", fn)

    gen.generate(jobs, on_item=_on)
    for fn, info in st.items():
        dest = os.path.join(ep1_run.FIRST, fn + ".jpg")
        if not os.path.exists(dest):
            try:
                gen.download(info["node_id"], dest)
            except Exception as e:
                print("  下载失败", fn, str(e)[:80])


if __name__ == "__main__":
    main()
