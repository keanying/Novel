# 第 1 集制作脚本

《凡骨问天》第 1 集《测灵》样片的完整生产脚本。依赖 `mcode-tools` CLI（图像/视频/TTS/音乐接口）与 ffmpeg。

## 目录约定

| 变量 | 路径 |
|---|---|
| 仓库根 | `D:\MiniMax\Novel` |
| 工作目录 | `D:\MiniMax\work`（状态文件、中间产物都在这里，不进 git） |
| 成片输出 | `D:\MiniMax\Novel\凡骨问天\成片\E01` |

## 执行顺序

```bash
cd D:\MiniMax\work

# 第 2 步：出 20 镜首帧（每镜 2 版，共 38 张）
python ep1_run.py frames

# 第 3 步：图生视频（19 段 × 6 秒，MiniMax-H3-Max 768P）
python ep1_run.py video

# 第 4 步：配音（15 条）
python ep1_run.py tts

# 第 5 步：主题配乐
python ep1_run.py music

# 第 6/7 步：剪辑、字幕、AI 标识、片尾卡
python ep1_run.py assemble

# 质检：技术参数 + 逐镜抽帧联系表
python qc.py
```

各阶段可独立重跑，状态分文件保存在 `ep1_frames.json` / `ep1_video.json` / `ep1_tts.json` / `ep1_music.json`，中断后可续跑。

## 改内容改哪里

- **改镜头**（画面/台词/提示词）→ `ep1.py` 的 `SHOTS` 表；
- **改每镜时长** → `ep1.py` 的 `EDIT_TIMES`；
- **改某镜用第几版首帧** → `ep1_run.py` 的 `PICKS`；
- **改角色音色** → `ep1.py` 的 `VOICES` 与 `EMOTION`；
- **改负面词** → `gen.py` 的 `NEG_TEXT`；
- **重新生成定妆** → `gen.py`（`phaseA` / `redo` / `selectall` / `phaseB` / `phaseC` / `redoB`）。

## 已知坑位

见 `凡骨问天/06_第01集制作清单与模板.md` 第七节「本集踩过的坑」，重点三条：

1. 视频接口有并发配额，必须「提交一段 → 轮询完成 → 再提交下一段」；
2. 提交后必须确认拿到 `task_id`，否则会静默丢镜头；
3. 背景音乐要循环铺满，否则 `-shortest` 会截掉片尾卡。
