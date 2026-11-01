# -*- coding: utf-8 -*-
"""《凡骨问天》第 1 集《测灵》生产执行器
用法:
    python ep1_run.py frames     # 第2步：出 20 个镜头的首帧图
    python ep1_run.py video      # 第3步：图生视频
    python ep1_run.py tts        # 第4步：配音
    python ep1_run.py music      # 第6步：主题配乐
    python ep1_run.py assemble   # 第6-7步：剪辑成片
    python ep1_run.py status     # 查看进度
"""
import json
import os
import shutil
import subprocess
import sys
import time

import ep1
import gen

ROOT = ep1.ROOT
FIRST = os.path.join(ROOT, "首帧")
VIDEO = os.path.join(ROOT, "视频")
VOICE = os.path.join(ROOT, "配音")
MUSIC = os.path.join(ROOT, "音乐")
LEGACY_STATE = os.path.join(ep1.WORK, "ep1_state.json")


def state_file(stage):
    """每个阶段一个独立状态文件，避免并发起跑时互相覆盖"""
    return os.path.join(ep1.WORK, "ep1_%s.json" % stage)


def load_state(stage):
    s = gen.load_json(state_file(stage), {})
    if not s:
        legacy = gen.load_json(LEGACY_STATE, {})
        if stage in legacy:
            s = legacy[stage] if isinstance(legacy[stage], dict) else {}
            gen.save_json(state_file(stage), s)
    return s


def save_state(stage, s):
    gen.save_json(state_file(stage), s)

# 每镜出几版首帧
VERSIONS = int(os.environ.get("EP1_VERSIONS", "2"))
# 视频模型与参数（可由环境变量覆盖）
VIDEO_MODEL = os.environ.get("EP1_VIDEO_MODEL", "MiniMax-H3-Max")
VIDEO_RES = os.environ.get("EP1_VIDEO_RES", "768P")
VIDEO_DUR = int(os.environ.get("EP1_VIDEO_DUR", "6"))

for d in (ROOT, FIRST, VIDEO, VOICE, MUSIC):
    os.makedirs(d, exist_ok=True)

# 逐镜首帧选版（人工挑过：构图/表情/道具最对的那一张）
PICKS = {
    1: 2,   # 手按黑石特写，v1 是半身侧脸不符合"特写"
    2: 2,   # 钱多宝居中，折扇开，人群层次好
    3: 2,   # 低头搓手茧，脸部清晰
    4: 1,   # 石碑、白台、幡旗、镇民都入画，比 v2 紧凑
    5: 2,   # 小禾仰头看哥哥，表情更自然
    6: 1,   # 浅蓝袖小手按碑，符合"小女孩的手"
    7: 2,   # 光柱笔直冲天撞开云层
    8: 1,   # 蓝光照脸的眼部特写，瞳孔收缩可见
    9: 2,   # 兄妹逆光站立更突出
    10: 2,  # 严松弯腰更近，小女孩怯生生的表情清晰
    11: 2,  # 小禾探出半张脸，眼睫毛可见
    12: 2,  # 两人隔一步对视，锦袋在两人之间
    13: 2,  # 镇长焦急摊手，表情有张力
    14: 1,  # 手背老茧与旧伤特写
    15: 3,  # v3 女孩眼眶含泪、哥哥替她整理发髻并挂上桃木牌
    16: 2,  # 仙童服＋飞舟，小禾哭喊表情生动
    17: 2,  # 奔跑姿态更自然，古街纵深好
    18: 2,  # 甲板三人同框（严松/云巅宫弟子/小禾）
    19: 3,  # v3 满脸泪水攥紧桃木牌，"平安"二字清晰
}


def cli(args):
    p = subprocess.run(subprocess.list2cmdline(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", shell=True)
    if p.returncode != 0:
        raise RuntimeError("CLI failed: %s %s" % (p.stdout[:400], p.stderr[:400]))
    out = p.stdout.strip()
    i = out.find("{")
    if i < 0:
        raise RuntimeError("no JSON: " + out[:400])
    return json.loads(out[i:])


def get_url(node_id):
    r = cli(["mcode-tools", "get_asset_url", node_id])
    return r["download_url"]


def ref_urls(keys):
    """角色 key -> 定妆定稿图的临时下载链接"""
    sel = gen.load_json(gen.SELECTED_PATH, {})
    out = {}
    for k in keys:
        if k not in sel:
            print("  !! 未选定定妆:", k)
            continue
        out[k] = get_url(sel[k]["node_id"])
    return out


# ---------------- 第 2 步：首帧图 ----------------
def cmd_frames():
    st = load_state("frames")
    need = {}
    for k in set(sum([s[4] for s in ep1.SHOTS], [])):
        need.update(ref_urls([k]))
    print("参考图就绪: %s" % ", ".join(need.keys()))

    jobs = []
    for no, dur, size, move, refs, img, vid, subs in ep1.SHOTS:
        if not refs and no == 20:
            continue          # 黑场，剪辑时做
        for v in range(1, VERSIONS + 1):
            fn = "E01_S%02d_首帧_v%d" % (no, v)
            if fn in st:
                continue
            prompt = img + "，" + ep1.STYLE + "，" + ep1.NEG_ALL
            job = {"prompt": prompt, "aspect_ratio": "9:16", "resolution": "2K",
                   "output_file": fn}
            if refs:
                job["input_urls"] = [need[r] for r in refs if r in need]
            jobs.append(job)
    if not jobs:
        print("首帧图：无需生成")
        return
    print("首帧图：待生成 %d 张" % len(jobs))
    res = gen.generate(jobs, on_item=lambda it: _save_frame(st, it))
    save_state("frames", st)
    print("首帧图完成 %d 张" % len(res))
    download_frames(st)


def _save_frame(st, item):
    fn = item["requested_file"]
    st[fn] = {"node_id": item["node_id"]}
    save_state("frames", st)


def download_frames(st):
    for fn, info in st.items():
        dest = os.path.join(FIRST, fn + ".jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            continue
        try:
            gen.download(info["node_id"], dest)
        except Exception as e:
            print("  下载失败", fn, e)


# ---------------- 第 3 步：图生视频 ----------------
def cmd_video():
    st = load_state("video")
    frames_st = load_state("frames")
    # 清掉历史上提交失败留下的空记录
    for k in [k for k, v in st.items() if not v.get("task_id")]:
        print("  清理无效记录", k)
        del st[k]
        save_state("video", st)

    # 待生成的镜头队列
    queue = []
    for no, dur, size, move, refs, img, vid, subs in ep1.SHOTS:
        if no == 20:
            continue
        key = "S%02d" % no
        if key in st and st[key].get("status") == "succeeded":
            continue
        frame = None
        want = PICKS.get(no)
        order = []
        if want:
            order.append(want)
        for v in range(VERSIONS, 0, -1):
            if v not in order:
                order.append(v)
        for v in order:
            fn = "E01_S%02d_首帧_v%d" % (no, v)
            if fn in frames_st:
                frame = fn
                break
        if not frame:
            print("  跳过 S%02d：没有首帧" % no)
            continue
        queue.append((no, key, frame, vid))
    print("待生成 %d 段" % len(queue))

    waited = 0
    while queue or any(v.get("status") not in ("succeeded", "failed")
                       for v in st.values()):
        # 1) 轮询在途任务（完成后即释放并发配额）
        for key in [k for k, v in st.items()
                    if v.get("status") not in ("succeeded", "failed") and v.get("task_id")]:
            info = st[key]
            qf = os.path.join(ep1.WORK, "_vquery_%s.json" % key)
            gen.save_json(qf, {"task_id": info["task_id"], "model": VIDEO_MODEL})
            try:
                r = cli(["mcode-tools", "connector", "call",
                         "connector__matrix__query_video_generation", "--args-file", qf])
            except Exception as e:
                print("  %s 查询异常 %s" % (key, str(e)[:80]))
                continue
            status = r.get("status") or r.get("state")
            if status == "succeeded":
                info.update({"status": "succeeded", "node_id": r.get("node_id"),
                             "file_name": r.get("file_name")})
                st[key] = info
                save_state("video", st)
                print("  %s 完成 -> %s" % (key, r.get("file_name")))
            elif status in ("failed", "cancelled"):
                info.update({"status": "failed",
                             "error": json.dumps(r, ensure_ascii=False)[:300]})
                st[key] = info
                save_state("video", st)
                print("  %s 失败: %s" % (key, info["error"][:120]))
            else:
                print("  %s %s" % (key, status))
        save_state("video", st)

        # 2) 提交下一段（受服务端并发配额限制，失败就等下一轮）
        if queue:
            no, key, frame, vid = queue[0]
            furl = get_url(frames_st[frame]["node_id"])
            args = {"model": VIDEO_MODEL, "prompt": vid, "duration": VIDEO_DUR,
                    "reference_type": "first_frame",
                    "input_image": {"url": furl, "mime_type": "image/jpeg"}}
            if VIDEO_MODEL.startswith("MiniMax-H3"):
                args["resolution"] = VIDEO_RES
            argsf = os.path.join(ep1.WORK, "_video_%02d.json" % no)
            gen.save_json(argsf, args)
            task_id = None
            for attempt in range(4):
                try:
                    r = cli(["mcode-tools", "connector", "call",
                             "connector__matrix__submit_video_generation",
                             "--args-file", argsf])
                except Exception as e:
                    print("  S%02d 提交异常: %s" % (no, str(e)[:100]))
                    time.sleep(10)
                    continue
                task_id = r.get("task_id") or r.get("id")
                if task_id:
                    break
                print("  S%02d 提交受限(第%d次)" % (no, attempt + 1))
                time.sleep(10)
            if task_id:
                st[key] = {"task_id": task_id, "frame": frame, "status": "submitted"}
                save_state("video", st)
                print("  S%02d 提交成功 task=%s" % (no, task_id))
                queue.pop(0)
            else:
                print("  S%02d 等待配额" % no)

        if queue or any(v.get("status") not in ("succeeded", "failed")
                        for v in st.values()):
            time.sleep(20)
            waited += 20
        if waited > 3300:
            print("轮询超时")
            break
    save_state("video", st)
    download_videos(st)


def poll_video(max_wait=3600):
    st = load_state("video")
    todo = {k: v for k, v in st.items()
            if v.get("status") not in ("succeeded", "failed") and v.get("task_id")}
    if not todo:
        print("没有待轮询任务")
        return
    waited = 0
    while todo and waited < max_wait:
        for key in list(todo.keys()):
            info = todo[key]
            qargs = {"task_id": info["task_id"], "model": VIDEO_MODEL}
            qf = os.path.join(ep1.WORK, "_vquery_%s.json" % key)
            gen.save_json(qf, qargs)
            r = cli(["mcode-tools", "connector", "call",
                     "connector__matrix__query_video_generation", "--args-file", qf])
            status = r.get("status") or r.get("state")
            if status == "succeeded":
                info.update({"status": "succeeded", "node_id": r.get("node_id"),
                             "file_name": r.get("file_name")})
                st[key] = info
                todo.pop(key, None)
                print("  %s 完成 -> %s" % (key, r.get("file_name")))
            elif status in ("failed", "cancelled"):
                info.update({"status": "failed", "error": json.dumps(r, ensure_ascii=False)[:300]})
                st[key] = info
                todo.pop(key, None)
                print("  %s 失败: %s" % (key, info["error"][:150]))
            else:
                print("  %s %s" % (key, status))
        save_state("video", st)
        if todo:
            time.sleep(25)
            waited += 25
    save_state("video", st)
    download_videos(st)


def download_videos(st):
    for key, info in st.items():
        if info.get("status") != "succeeded":
            continue
        ext = os.path.splitext(info.get("file_name") or ".mp4")[1] or ".mp4"
        dest = os.path.join(VIDEO, "%s_v1%s" % (key, ext))
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            continue
        try:
            gen.download(info["node_id"], dest)
            print("  下载", dest)
        except Exception as e:
            print("  下载失败", key, e)


# ---------------- 第 4 步：配音 ----------------
def cmd_tts():
    st = load_state("tts")
    lines = ep1.tts_lines()
    todo = []
    for no, who, text, emo, sp, pi, vid, fid in lines:
        fn = fid
        if fn in st:
            continue
        todo.append((fn, {"text": text, "voice_id": vid, "emotion": emo,
                           "speed": sp, "pitch": pi, "output_file": fn}))
    if not todo:
        print("配音：无需生成")
        return
    print("配音：待生成 %d 条" % len(todo))
    attempt = 0
    while todo and attempt < 12:
        attempt += 1
        for i in range(0, len(todo), 10):
            chunk = todo[i:i + 10]
            argsf = os.path.join(ep1.WORK, "_tts_%d.json" % i)
            gen.save_json(argsf, {"requests": [c[1] for c in chunk]})
            try:
                r = cli(["mcode-tools", "connector", "call",
                         "connector__matrix__batch_text_to_audio", "--args-file", argsf])
            except Exception as e:
                print("  批次异常:", str(e)[:150])
                continue
            ok = r.get("success_items", [])
            fail = r.get("failed_items", [])
            if fail:
                print("  第%d轮 失败 %d 条: %s" % (attempt, len(fail),
                      json.dumps(fail, ensure_ascii=False)[:180]))
            by_stem = {os.path.splitext(c[1]["output_file"])[0]: c[0] for c in chunk}
            done = set()
            for item in ok:
                stem = os.path.splitext(item.get("file_name", ""))[0]
                fn = by_stem.get(stem, stem)
                st[fn] = {"node_id": item["node_id"], "file_name": item["file_name"]}
                done.add(fn)
                save_state("tts", st)
            todo = [t for t in todo if t[0] not in done]
            if todo:
                time.sleep(20)
    save_state("tts", st)
    if todo:
        print("仍有 %d 条未完成: %s" % (len(todo), [t[0] for t in todo]))
    for fn, info in st.items():
        ext = os.path.splitext(info.get("file_name") or ".mp3")[1] or ".mp3"
        dest = os.path.join(VOICE, fn + ext)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            continue
        try:
            gen.download(info["node_id"], dest)
        except Exception as e:
            print("  下载失败", fn, e)
    print("配音完成")


# ---------------- 第 5 步：配乐 ----------------
def cmd_music():
    st = load_state("music")
    jobs = [
        {"lyrics": "", "prompt": "古风仙侠短剧主题曲，竹笛主旋律配低频鼓点，悠远苍凉，"
                                "贵州山野的空灵感，中国传统民族乐器，纯净器乐，无人声，"
                                "开场大气，情感克制，适合短视频BGM", "output_file": "主题旋律"},
    ]
    todo = [j for j in jobs if j["output_file"] not in st]
    if not todo:
        print("配乐：无需生成")
        return
    argsf = os.path.join(ep1.WORK, "_music.json")
    gen.save_json(argsf, {"requests": todo})
    attempt = 0
    while todo and attempt < 10:
        attempt += 1
        try:
            r = cli(["mcode-tools", "connector", "call",
                     "connector__matrix__batch_text_to_music", "--args-file", argsf])
        except Exception as e:
            print("  配乐调用异常:", str(e)[:200])
            time.sleep(20)
            continue
        ok = r.get("success_items", [])
        fail = r.get("failed_items", [])
        print("  第%d轮 ok=%d fail=%d %s" % (attempt, len(ok), len(fail),
                                            json.dumps(fail, ensure_ascii=False)[:200]))
        for item in ok:
            st["主题旋律"] = {"node_id": item["node_id"], "file_name": item["file_name"]}
            save_state("music", st)
        if ok:
            break
        time.sleep(20)
    if not st:
        print("配乐生成失败")
        return
    for name, info in st.items():
        ext = os.path.splitext(info.get("file_name") or ".mp3")[1] or ".mp3"
        dest = os.path.join(MUSIC, name + ext)
        if os.path.exists(dest):
            continue
        try:
            gen.download(info["node_id"], dest)
        except Exception as e:
            print("  下载失败", name, e)
    print("配乐完成")


# ---------------- 第 6/7 步：剪辑 ----------------
def cmd_assemble():
    st = {"tts": load_state("tts"), "music": load_state("music")}
    tl, total = ep1.timeline()
    seg_dir = os.path.join(ep1.WORK, "e1seg")
    os.makedirs(seg_dir, exist_ok=True)

    # 1) 逐镜裁剪到分镜时长、统一 1080x1920 / 30fps
    segs = []
    for no, dur, size, move, refs, img, vid, subs in ep1.SHOTS:
        key = "S%02d" % no
        target = round(tl[no][1] - tl[no][0], 2)
        if no == 20:
            seg = os.path.join(seg_dir, "S20.mp4")
            if not os.path.exists(seg):
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                                "color=c=black:s=1080x1920:d=%d:r=30" % target,
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", seg],
                               capture_output=True)
            segs.append(seg)
            continue
        src = None
        for ext in (".mp4", ".webm", ".mov"):
            p = os.path.join(VIDEO, "%s_v1%s" % (key, ext))
            if os.path.exists(p):
                src = p
                break
        if not src:
            print("  缺少视频", key)
            continue
        seg = os.path.join(seg_dir, "S%02d.mp4" % no)
        # tpad: 源视频不足目标时长时克隆最后一帧补足；-t 精确裁到目标时长
        subprocess.run(["ffmpeg", "-y", "-i", src,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,"
                               "tpad=stop_mode=clone:stop_duration=8",
                        "-t", str(target),
                        "-r", "30", "-an", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "20", "-pix_fmt", "yuv420p", seg], capture_output=True)
        segs.append(seg)
        print("  裁剪 S%02d -> %ss" % (no, target))

    if not segs:
        print("没有可用片段")
        return
    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for s in segs:
            f.write("file '%s'\n" % s.replace("\\", "/").replace("'", "\\'"))
    silent = os.path.join(seg_dir, "silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], capture_output=True)
    print("拼接完成:", silent, os.path.getsize(silent) // 1024, "KB")

    # 2) 音频：配音按镜号延迟混入 + 背景音乐压低
    inputs, filters = [], []
    tts_items = st.get("tts", {})
    idx = 1
    delay_map = []
    plan = plan_speech(tl, tts_items)
    for path, start, dlen, who, text in plan:
        delay_map.append((path, start, who))
    for i, (path, delay, who) in enumerate(delay_map):
        inputs += ["-i", path]
        filters.append("[%d:a]aresample=48000,aformat=channel_layouts=mono[a%d]"
                       % (idx, i))
        idx += 1
    mix = []
    if delay_map:
        # 先把每条配音统一成 48k 单声道并命名 a0..aN
        mix.append(";".join(filters))
        # 再按时间点延迟
        mix.append(";".join("[a%d]adelay=%d|%d[v%d]" % (i, int(d * 1000), int(d * 1000), i)
                            for i, (_, d, _) in enumerate(delay_map)))
        mix.append("".join("[v%d]" % i for i in range(len(delay_map))) +
                   "amix=inputs=%d:duration=longest:dropout_transition=0:normalize=0[dlg]"
                   % len(delay_map))
    music = None
    for f in os.listdir(MUSIC):
        music = os.path.join(MUSIC, f)
        break
    if music:
        inputs += ["-i", music]
        # 循环铺满全片，片尾淡出；否则音乐只有 57 秒会把成片截短
        mix.append("[%d:a]aresample=48000,volume=0.16,"
                   "aloop=loop=-1:size=2147483647,atrim=0:%.2f,"
                   "afade=t=in:st=0:d=2,afade=t=out:st=%.2f:d=3[bg]"
                   % (idx, total, max(0, total - 3)))
        mix.append("[dlg][bg]amix=inputs=2:duration=longest:normalize=0[aout]")
        out_label = "[aout]"
    else:
        out_label = "[dlg]"

    # 3) 字幕 ASS + AI 标识 + 片尾卡
    ass = os.path.join(ep1.WORK, "e1.ass")
    write_ass(ass, tl, total, plan)
    wm = "AI生成"
    ass_path = ass.replace("\\", "/").replace(":", "\\:")
    vfc = ("[0:v]subtitles='%s':fontsdir='C\\:/Windows/Fonts',"
           "drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':text='%s':"
           "fontcolor=white@0.55:fontsize=26:x=w-tw-28:y=40:box=1:"
           "boxcolor=black@0.28:boxborderw=6[vout]" % (ass_path, wm))

    out = os.path.join(ROOT, "E01_测灵_成片.mp4")
    cmd = ["ffmpeg", "-y", "-i", silent]
    cmd += inputs
    cmd += ["-filter_complex", ";".join([vfc] + mix),
            "-map", "[vout]", "-map", out_label,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", out]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("FFMPEG 失败:\n", r.stderr[-2500:])
        return
    print("成片:", out, os.path.getsize(out) // 1024, "KB")
    probe(out)


def audio_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=nw=1:nk=1", path],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    try:
        return float(r.stdout.strip())
    except Exception:
        return 2.0


def plan_speech(tl, tts_items):
    """台词排布：同一镜头内多条台词按顺序串行开口。
    返回 [(音频路径, 起始秒, 音频时长, 角色, 台词)]"""
    by_shot = {}
    for no, who, text, emo, sp, pi, vid, fid in ep1.tts_lines():
        by_shot.setdefault(no, []).append((who, text, fid))
    plan = []
    for no in sorted(by_shot):
        start = tl[no][0] + 0.15
        shot_end = tl[no][1]
        for who, text, fid in by_shot[no]:
            info = tts_items.get(fid)
            if not info:
                continue
            ext = os.path.splitext(info.get("file_name") or ".mp3")[1] or ".mp3"
            path = os.path.join(VOICE, fid + ext)
            if not os.path.exists(path):
                print("  缺配音:", fid)
                continue
            dlen = audio_dur(path)
            plan.append((path, start, dlen, who, text))
            start += dlen + 0.12
        over = start - shot_end
        if over > 0.3:
            print("  ! S%02d 台词超出镜头 %.2fs" % (no, over))
    return plan


def write_ass(path, tl, total, plan=None):
    """生成字幕文件：台词 + 画面字幕 + 片尾卡"""

    def t(s):
        s = s.replace("\n", "\\N")
        return s

    def ts(sec):
        """ASS 时间戳格式 H:MM:SS.CC"""
        sec = max(0.0, float(sec))
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return "%d:%02d:%05.2f" % (h, m, s)

    def dlg(start, end, style, text):
        lines.append("Dialogue: 0,%s,%s,%s,,0,0,0,,%s" % (ts(start), ts(end), style, text))

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080", "PlayResY: 1920",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Dlg,Microsoft YaHei,46,&H00FFFFFF,&H000000FF,&H00202020,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,60,60,330,1",
        "Style: Card,Microsoft YaHei,64,&H00FFFFFF,&H000000FF,&H00202020,&H80000000,1,0,0,0,100,100,2,0,1,3,1,2,80,80,0,1",
        "Style: Small,Microsoft YaHei,30,&H00C8C8C8,&H000000FF,&H00202020,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,60,60,120,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    # 台词字幕：用音频实际时长定位，与声音对齐
    if plan:
        for apath, s2, dlen, who, text in plan:
            e2 = s2 + max(dlen, 0.8)
            dlg(s2, e2, "Dlg", t(text))
    else:
        for no, dur, size, move, refs, img, vid, subs in ep1.SHOTS:
            start, end = tl[no]
            d = end - start
            for who, text in subs:
                if who not in ("字幕", "片尾", "取景"):
                    dlg(start + d * 0.12, start + d * 0.95, "Dlg", t(text))
    # 画面字幕（场景卡）
    for no, dur, size, move, refs, img, vid, subs in ep1.SHOTS:
        start, end = tl[no]
        for who, text in subs:
            if who == "字幕":
                dlg(start, end, "Card", t(text))
    # 片尾卡（S20）
    s20 = tl[20][0]
    dlg(s20 + 0.3, s20 + 1.6, "Card", "下一集 · 盐道")
    dlg(s20 + 1.8, s20 + 2.9, "Small", "取景 青岩古镇 · 加榜梯田")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=codec_name,width,height,r_frame_rate",
                        "-of", "default=noprint_wrappers=1", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout)


def cmd_status():
    st = {"frames": load_state("frames"), "video": load_state("video"),
          "tts": load_state("tts"), "music": load_state("music")}
    tl, total = ep1.timeline()
    print("首帧: %d 张" % len(st.get("frames", {})))
    print("视频: %d 条" % len(st.get("video", {})))
    print("配音: %d 条" % len(st.get("tts", {})))
    print("配乐: %d 条" % len(st.get("music", {})))
    print("目标时长: %.1f 秒" % total)
    out = os.path.join(ROOT, "E01_测灵_成片.mp4")
    if os.path.exists(out):
        print("成片已存在: %.1f MB" % (os.path.getsize(out) / 1024 / 1024))
        probe(out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"frames": cmd_frames, "video": cmd_video, "tts": cmd_tts, "music": cmd_music,
     "assemble": cmd_assemble, "status": cmd_status}.get(cmd, cmd_status)()
