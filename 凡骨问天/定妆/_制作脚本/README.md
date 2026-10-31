# 定妆生成脚本

> 这套脚本是本次定妆创作的实际执行工具，可以重跑、增补角色、返工某一张图。
> 依赖：`mcode-tools` CLI（已随 MiniMax Code 安装）、Python 3.11+、`Pillow`（仅拼联系表时需要）。

## 目录

| 文件 | 作用 |
|---|---|
| `gen.py` | 核心脚本。持有全部角色锚点、提示词、后缀、负面词，并调用 `connector__matrix__generate_image` |
| `fetch.py` | 把 `state.json` 里已生成的图按目录结构下载到 `定妆/` |
| `sheet.py` | 把定妆图拼成联系表（contact sheet），方便一次性肉眼比对锚点特征 |
| `finalize.py` | 收尾：候选图重命名为规范名、其余归档到 `_候选/`、导出提示词全表 |

## ⚠️ 换机器先改这两个路径

`gen.py` 顶部：

```python
WORK = r"D:\MiniMax\work"                          # 中间产物（state.json 等）
OUT_ROOT = r"D:\MiniMax\Novel\凡骨问天\定妆"        # 成图输出目录
```

## 常用命令

```bash
cd 定妆/_制作脚本

python gen.py phaseA      # 所有角色正脸候选（文生图，每角 2 张）
python gen.py redo SQT 2  # 给某个角色追加候选：参数是角色 key 和张数
python gen.py selectall   # 批量选定定稿（映射表在 gen.py 的 SELECT_MAP 里）
python gen.py phaseB      # 以定稿正脸为参考图，生成三视图/表情组/造型变体
python gen.py phaseC      # 道具定妆图
python fetch.py           # 下载已生成的图到 定妆/
python finalize.py        # 改名归档 + 导出提示词全表
```

## 关键机制

1. **断点续跑**：每张图生成成功就立刻写入 `state.json`，中途断网或超时可以原地续跑，不会重复扣费。
2. **自动重试**：批次失败会重新排队，最多重试 40 次；单批 3 张，避免服务端响应超时。
3. **参考图一致性**：阶段 B 把选定正脸的 `node_id` 换成临时下载链接，放进 `input_urls`，
   实现图生图。这是跨集不变脸的关键，**不要改成文生图**。
4. **负面词内嵌**：该接口没有独立负面词参数，`NEG_TEXT` 会拼在每条提示词末尾。

## 角色 key 对照

| key | 角色 | key | 角色 |
|---|---|---|---|
| XTL | 许听澜 | QDB | 钱多宝 |
| SQT | 沈青棠 | ZZ | 镇长 |
| XH | 许小禾 | FQ | 父亲许大河 |
| NHN | 宁鹤年 | STL | 少年听澜 |
| GCF | 顾长风 | JZM | 剑宗弟子男 |
| YS | 严松 | JZN | 剑宗弟子女 |
| LW | 老魏 | YZG | 云巅宫弟子 |
| ST | 石头 | ZM1/ZM2/ZM3 | 镇民甲/乙/丙 |

## 新增角色（第 11 集起出场的杨阿公、季无咎、花三娘、丹九）

1. 在 `gen.py` 的 `PHASE_A` 里加一行：`(文件夹名, key, 锚点, 造型描述, S_FRONT, "3:4")`；
2. 在 `SELECT_MAP` 里加 `key: 1`；
3. 跑 `python gen.py phaseA` → `python gen.py selectall` → `python gen.py phaseB`。

锚点写法照抄 `04_定妆包.md` 第六节，**同一个字都不要改**——锚点变了，前面所有集的定妆图就对不上了。
