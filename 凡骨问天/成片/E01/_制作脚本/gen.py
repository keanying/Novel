# -*- coding: utf-8 -*-
"""
《凡骨问天》定妆图批量生成器
调用 mcode-tools connector__matrix__generate_image，支持文生图与参考图（image-to-image）。
用法:
    python gen.py phaseA            # 生成所有角色正脸候选（文生图）
    python gen.py select <name>      # 选定某角色正脸，写入 selected.json
    python gen.py phaseB             # 以选定正脸为参考图生成三视图/表情/变体
    python gen.py download           # 把所有已生成但未落盘的图下载到 定妆/
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

WORK = r"D:\MiniMax\work"
OUT_ROOT = r"D:\MiniMax\Novel\凡骨问天\定妆"
STATE_PATH = os.path.join(WORK, "state.json")
SELECTED_PATH = os.path.join(WORK, "selected.json")
BATCH = 3

# ---------------- 通用后缀 ----------------
S_FRONT = ("写实摄影，真实人像，胸部以上半身正面照，直视镜头，表情自然，纯浅灰色背景，"
           "影棚柔光，真实皮肤纹理与毛孔，85mm 人像镜头，超高清细节")
S_FRONT_DARK = ("写实摄影，真实人像，胸部以上半身正面照，直视镜头，纯深灰近黑背景，"
                "冷蓝色侧光，真实皮肤纹理与毛孔，85mm 人像镜头，超高清细节")
S_TURN = ("角色设定图，同一人物的三视图：正面全身、侧面全身、背面全身并排站立，纯白背景，"
          "影棚均匀光，写实摄影风格，服装细节清晰，人物比例准确")
S_EXPR = ("同一人物的四宫格表情图：左上微笑、右上愤怒、左下悲伤落泪、右下震惊，"
          "胸部以上，纯浅灰背景，写实摄影，真实皮肤纹理")

# 该接口没有独立负面词参数，必须把负面内容并进提示词末尾
NEG_TEXT = ("避免出现：卡通，动漫，插画，3D 渲染，CG 感，塑料皮肤，过度磨皮，网红脸，锥子脸，"
            "浓妆，美颜滤镜，明星脸，现代服装，现代发型，眼镜，耳钉，文身，"
            "立领，盘扣，纽扣，翻领衬衫，中山装，西式烟斗，厨师帽，额头系白布带，"
            "衣服上的文字、汉字、书法字符、符号纹样，文字，水印，畸形五官，多余手指，模糊")

# ---------------- 锚点（与 04_定妆包.md 一致，一个字都不要改） ----------------
A_XTL = ("18 岁中国青年男子，清瘦结实，小麦色皮肤，轮廓分明的瘦长脸，剑眉，"
         "左眉尾有一道浅浅的旧疤，单眼皮，细长眼，眼神沉静内敛，高鼻梁，薄唇，"
         "黑发用旧布条束成低马尾，额前垂着几缕碎发")
A_SQT = ("20 岁中国女子，身材高挑纤细，鹅蛋脸，冷白皮，细长锋利的眉，丹凤眼，眼尾微微上挑，"
         "左眼下方约一厘米处有一颗小小的深色泪痣，眼神清冷，鼻梁高挺，薄唇，唇色偏淡，乌黑长发，未施粉黛")
A_XH = ("10 岁中国小女孩，圆脸，脸颊红润，一双又大又圆的双眼皮眼睛，笑起来右脸有一个小酒窝，"
        "小巧的鼻子，梳两个双丫髻，系红色头绳，脖子上用红绳挂着一块刻着“平安”二字的小桃木牌")
A_NHN = ("外表约 50 岁的中国男子，面容清癯儒雅，长脸，花白长眉斜飞入鬓，细长的凤眼，"
         "目光温和而深不见底，鼻梁挺直，花白的长山羊胡和长髯，黑白相间的长发束在银色发冠中")
A_GCF = ("25 岁中国男子，面容俊朗，皮肤白净，桃花眼，眼尾微微下垂，鼻梁高挺，唇角天生微微上扬，"
         "看起来温润如玉，眼底却带着一丝阴沉，黑发用白玉冠高束")
A_YS = "40 岁中国男子，瘦长脸，颧骨略高，细长眼，薄唇，留八字短须，神情倨傲"
A_LW = "50 岁中国男子，方脸，皮肤黝黑粗糙，浓眉，额头三道深深的皱纹，花白的络腮胡，左耳缺了一小角"
A_ST = "16 岁中国少年，圆脸，小眼睛，门牙略大，皮肤晒得黝黑，头发短而乱，在头顶扎一个小揪"
A_QDB = "17 岁中国胖少年，白胖的圆脸，双下巴，小眼睛，嘴角挂着得意的笑"
A_ZZ = "60 岁中国老者，瘦小，脸上皱纹多，留山羊胡，眼神精明又怕事"
A_FQ = ("40 岁中国男子，和许听澜一样的剑眉和单眼皮细长眼，面容沧桑，皮肤黝黑，"
        "下巴满是胡茬，笑容温厚")
A_STL = "8 岁中国男孩，瘦小，小麦色皮肤，剑眉，单眼皮细长眼，眼神认真，头发扎成小揪"

# ---------------- 阶段 A：正脸候选（文生图） ----------------
# key 用于 selected.json 寻址；cand 数量=候选张数
PHASE_A = [
    ("许听澜", "XTL", A_XTL,
     "，穿褪色的土褐色粗麻交领短打，领口微敞，神情平静略带疲惫", S_FRONT, "3:4"),
    ("沈青棠", "SQT", A_SQT,
     "，长发半束，插一根青玉发簪，几缕发丝散落在脸侧，穿青白色交领剑宗长袍，神情冷傲", S_FRONT, "3:4"),
    ("许小禾", "XH", A_XH,
     "，穿打着补丁的浅蓝色粗布交领小袄，天真地微笑", S_FRONT, "3:4"),
    ("宁鹤年", "NHN", A_NHN,
     "，穿白底金色云纹宽袖长袍，面带温和的微笑", S_FRONT, "3:4"),
    ("顾长风", "GCF", A_GCF,
     "，穿白色偏淡青色的剑宗长袍，衣襟镶一道银边，腰佩白玉，温和地微笑", S_FRONT, "3:4"),
    ("严松", "YS", A_YS,
     "，戴白色方冠，穿白色交领执事长袍，袍边绣窄窄的金色云纹，腰挂一块云纹玉令牌", S_FRONT, "3:4"),
    ("老魏", "LW", A_LW,
     "，头缠旧蓝布巾，穿深褐色粗布短打，嘴里叼着旱烟杆，眼神严厉", S_FRONT, "3:4"),
    ("石头", "ST", A_ST,
     "，穿打补丁的灰褐色粗布短打，咧嘴憨笑", S_FRONT, "3:4"),
    ("钱多宝", "QDB", A_QDB,
     "，头戴镶玉小冠，穿宝蓝色绸缎锦袍，手摇折扇", S_FRONT, "3:4"),
    ("镇长", "ZZ", A_ZZ,
     "，头戴灰色方巾，穿深蓝色长衫", S_FRONT, "3:4"),
    ("父亲许大河", "FQ", A_FQ,
     "，头缠布巾，穿土褐粗布短打，背着竹背篓，温和地笑，暖黄色调", S_FRONT, "3:4"),
    ("少年听澜", "STL", A_STL,
     "，穿过大的粗布短打，暖黄色调", S_FRONT, "3:4"),
    ("剑宗弟子男", "JZM",
     "20 岁左右中国青年男子，五官端正，黑发高束",
     "，穿白色偏淡青色的剑宗长袍，衣襟无银边，背负长剑，神情严肃", S_FRONT, "3:4"),
    ("剑宗弟子女", "JZN",
     "20 岁左右中国青年女子，五官清秀，黑发高束",
     "，穿白色偏淡青色的剑宗长袍，背负长剑，神情冷淡", S_FRONT, "3:4"),
    ("云巅宫弟子", "YZG",
     "20 岁左右中国青年，面无表情",
     "，穿纯白交领长袍，袖口有极细的金线，黑发束白色发带", S_FRONT, "3:4"),
]

# 群演：镇民改为单人定妆（群像一次画多张脸必然重复脸）
EXTRA_CAST = [
    ("镇民甲", "ZM1",
     "50 岁左右中国男子，面容朴实，皮肤黝黑粗糙，眉毛稀薄，眼睛眯着，嘴唇干裂",
     "，头上包着旧灰布巾，穿灰褐色粗布对襟上衣，神情木然地看着前方", S_FRONT, "3:4"),
    ("镇民乙", "ZM2",
     "45 岁左右中国妇人，圆脸，皮肤粗糙偏黄，眉毛淡，眼睛温和，颧骨有雀斑",
     "，头发用深靛色布巾包住，穿藏青色粗布交领上衣，双手交握在身前，神情担忧", S_FRONT, "3:4"),
    ("镇民丙", "ZM3",
     "70 岁左右中国老头，脸颊深凹，皱纹很多，皮肤黝黑，眼睛浑浊，嘴唇干瘪",
     "，穿褪色的灰蓝色粗布对襟衣，弓着背，神情麻木", S_FRONT, "3:4"),
]

# 需要重做锚点的角色：key -> (锚点, 造型描述)
OVERRIDE = {
    "SQT": (A_SQT,
            "，长发半束，插一根青玉发簪，几缕发丝散落在脸侧，"
            "穿白色偏淡青色的交领剑宗长袍，衣料素净没有任何图案和文字，神情冷傲"),
    "XH": (A_XH.replace("笑起来右脸有一个小酒窝",
                        "笑起来右脸颊有一个明显的凹陷酒窝"),
           "，穿打着补丁的浅蓝色粗布交领小袄，张嘴大笑露出右脸颊的酒窝"),
    # ===== v2.1 定妆质检返工 =====
    "YS": (A_YS,
           "，头戴低矮的白玉小冠，用一根白玉簪横穿固定，"
           "穿白色交领执事长袍，袍边绣窄窄的金色云纹，腰挂一块云纹玉令牌，神情倨傲"),
    "ZZ": (A_ZZ,
           "，头戴灰色方巾，穿深蓝色交领右衽长衫，衣料素净，眼神精明又怕事"),
    "LW": (A_LW,
           "，头缠旧蓝布巾，穿深褐色粗布交领右衽短打，"
           "嘴里叼着一根细长的竹杆旱烟袋，烟杆约一尺长，末端是小小的黄铜烟锅，眼神严厉"),
    "ZM1": ("50 岁左右中国男子，面容朴实，皮肤黝黑粗糙，眉毛稀薄，眼睛眯着，嘴唇干裂",
            "，头缠旧灰布巾，穿灰褐色粗布交领右衽短衣，神情木然地看着前方"),
    "ZM3": ("70 岁左右中国老头，脸颊深凹，皱纹很多，皮肤黝黑，眼睛浑浊，嘴唇干瘪",
            "，穿褪色的灰蓝色粗布交领右衽短衣，腰系草绳，弓着背，神情麻木"),
    "YZG": ("20 岁左右中国青年，面无表情",
            "，穿纯白交领长袍，袖口有极细的金线，黑发高束成髻，插一根素白玉簪，"
            "头上不系任何布带"),
}


def ph_a_prompt(key, anchor, extra, suffix):
    if key in OVERRIDE:
        anchor, extra = OVERRIDE[key]
    return anchor + extra + "，" + suffix + "，" + NEG_TEXT


# ---------------- 阶段 B：参考图派生（image-to-image） ----------------
# (folder, key, filename, prompt, aspect)
PHASE_B = [
    ("许听澜", "XTL", "许听澜_02_三视图",
     A_XTL + "，穿褪色土褐色粗麻短打，袖口挽到小臂，小臂结实，腰系草绳，深色粗布裤，裤脚扎紧，"
     "脚穿草鞋，背着一个高大的竹编背篓，手持一根丁字形木拐，" + S_TURN, "16:9"),
    ("许听澜", "XTL", "许听澜_03_表情",
     A_XTL + "，穿土褐色粗麻短打，" + S_EXPR, "1:1"),
    ("许听澜", "XTL", "许听澜_04_背夫装湿",
     A_XTL + "，全身湿透，头发湿漉漉地贴在额头和脸颊上，土褐色粗麻短打湿透贴身，"
     "左脸颊有一道擦伤，耳下有一道干涸的血迹，神情疲惫而坚毅，幽暗的蓝色冷光从侧面照亮，"
     + S_FRONT_DARK, "3:4"),
    ("许听澜", "XTL", "许听澜_05_听脉",
     A_XTL + "，闭着双眼，头微微侧向一边，像在专注地倾听，眉头微蹙，右耳下渗出一道细细的血线，"
     "耳边浮现几圈幽蓝色的发光涟漪，" + S_FRONT_DARK, "3:4"),

    ("沈青棠", "SQT", "沈青棠_02_三视图",
     A_SQT + "，长发半束、青玉簪，穿白色偏淡青色的剑宗长袍，衣襟和袖口绣淡青色水波纹，"
     "腰束青色宽腰带，衣摆有撕裂的破口，左肩布料破损并有干涸的血迹，"
     "右手握着一柄从中间折断的长剑，剑柄垂着青色剑穗，" + S_TURN, "16:9"),
    ("沈青棠", "SQT", "沈青棠_03_表情",
     A_SQT + "，穿白色偏淡青色的剑宗长袍，" + S_EXPR, "1:1"),
    ("沈青棠", "SQT", "沈青棠_04_剑宗服盛",
     A_SQT + "，长发高束，戴青玉小冠，穿一尘不染的青白色剑宗长袍，水波纹刺绣精致，"
     "神采飞扬，嘴角带着自信的浅笑，手持完整的长剑，背景是巨大瀑布与水雾，" + S_FRONT, "3:4"),

    ("许小禾", "XH", "许小禾_02_三视图",
     A_XH + "，穿打补丁的浅蓝粗布小袄和深蓝粗布裤，脚穿布鞋，" + S_TURN, "16:9"),
    ("许小禾", "XH", "许小禾_03_表情",
     A_XH + "，穿浅蓝粗布小袄，" + S_EXPR, "1:1"),
    ("许小禾", "XH", "许小禾_04_仙童服",
     A_XH + "，双丫髻改系白玉珠，穿白色金边交领仙童服，胸前仍然挂着那块桃木平安牌，"
     "神情不安，眼眶微红，" + S_FRONT, "3:4"),

    ("宁鹤年", "NHN", "宁鹤年_02_眼部特写",
     A_NHN + "，眼部极近特写，眼睛刚刚睁开，瞳孔中倒映着跳动的烛火，眼角有细纹，"
     "背景是金色阵纹的暗影，写实摄影，微距镜头，超高清细节", "1:1"),
    ("宁鹤年", "NHN", "宁鹤年_03_手部特写",
     "一只苍白修长、保养极好的中老年男子的手，轻轻捻着一柄白玉柄拂尘，"
     "白底金色云纹的宽大袖口，背景是金色阵纹和烛火，写实摄影，微距镜头，超高清细节", "1:1"),

    ("顾长风", "GCF", "顾长风_02_回忆侧脸",
     A_GCF + "，侧脸，站在月光下，周身散发青绿色的灵光，嘴角带着得逞的微笑，"
     "背景是月夜下的瀑布，冷蓝色调，写实摄影，电影感光影，超高清细节", "3:4"),

    ("严松", "YS", "严松_02_三视图",
     A_YS + "，头戴低矮的白玉小冠，用一根白玉簪横穿固定，"
     "穿白色交领执事长袍，袍边绣窄窄的金色云纹，腰挂云纹令牌，双手负在身后，" + S_TURN, "16:9"),
    ("老魏", "LW", "老魏_02_三视图",
     A_LW + "，头缠旧布巾，穿深褐色粗布交领右衽短打，绑腿，草鞋，背着高大竹背篓，"
     "手里握着一根细长的竹杆旱烟袋，末端是小小的黄铜烟锅，" + S_TURN, "16:9"),
    ("石头", "ST", "石头_02_三视图",
     A_ST + "，穿打补丁的灰褐短打，草鞋，背着小一号的竹背篓，" + S_TURN, "16:9"),
]


# ---------------- 阶段 C：道具定妆（文生图，1:1） ----------------
PROP_SUFFIX = ("写实静物摄影，纯浅灰背景，柔和的影棚光，真实材质细节，85mm 微距镜头，"
               "超高清细节，物体居中")
PHASE_C = [
    ("平安牌", "一块手掌大小的桃木牌，木色发黄，边缘磨得圆滑，正面用刀刻着“平安”两个字，"
     "刻痕深且歪斜，背面刻着一个粗糙的“夫”字，红绳穿过顶部一个小孔，绳子磨得起毛"),
    ("断剑青霜", "一柄从中间折断的古代长剑，断口呈锯齿状的金属撕裂面，剑身青白色，"
     "护手处刻水波纹，剑柄缠着已经散开的青色剑穗，握柄被血浸成暗褐色，横放在素色布上"),
    ("丁字拐", "一根丁字形的木杖，深褐色硬木，顶端横木被手磨得发亮，中段有明显弯折和裂纹，"
     "缠着一圈麻绳"),
    ("竹背篓", "一个高大的竹编背篓，编法细密，表面被磨得油亮发黑，底部沾着红土和盐霜，"
     "边缘用麻绳加固，背带是粗麻编的，已经磨出毛边"),
    ("旱烟杆", "一根黄铜烟杆，斗里还剩着烧过的烟丝，杆身被手指摩挲得发亮"),
    ("测灵石碑", "一块一人高的黑色石碑，石头表面平整如镜，没有任何刻字，"
     "边缘被雨水侵蚀得圆润，底部埋进青石板地面，碑面完全没有光泽，不反光"),
    ("剑符", "一枚青色玉片，巴掌大小，薄如纸片，表面刻着一道剑形纹路，边缘锋利，"
     "玉质温润带一点絮状棉"),
    ("镇渊铃", "一口巨大的古铜铃，表面布满绿锈和岁月斑驳，铃身铸着模糊的云雷纹，"
     "铃口有一道旧裂痕，用粗铁链悬吊"),
    ("九渊水图", "一张泛黄的古老皮纸质地地图，上面用朱砂和墨线画着盘根错节的地下暗河"
     "和九个圆形标记，边缘破损发脆，烛光照明"),
    ("白玉拂尘", "一柄白玉柄拂尘，玉柄温润半透明，穗子是细密的白丝，丝头略微散乱"),
]


# ---------------- 基础设施 ----------------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_cli(args):
    # Windows 下 CreateProcess 无法直接执行 .cmd，需走 shell 并自行转义
    cmdline = subprocess.list2cmdline(args)
    p = subprocess.run(cmdline, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", shell=True)
    if p.returncode != 0:
        raise RuntimeError("CLI failed: %s\n%s" % (p.stdout, p.stderr))
    out = p.stdout.strip()
    # CLI 可能打印多行，取最后一个 JSON 对象
    idx = out.find("{")
    if idx < 0:
        raise RuntimeError("no JSON in output: " + out[:500])
    return json.loads(out[idx:])


def generate(jobs, on_item=None, max_attempts=40):
    """jobs: list of dict(prompt, aspect_ratio, resolution, output_file) -> list of result dict
    单批失败自动重试；未返回的请求重新排队；已成功的实时回调落库（可断点续跑）。"""
    results = []
    pending = list(jobs)
    attempt = 0
    while pending and attempt < max_attempts:
        chunk = pending[:BATCH]
        attempt += 1
        argsf = os.path.join(WORK, "_args_%d.json" % (attempt % 97))
        save_json(argsf, {"requests": chunk})
        try:
            r = run_cli(["mcode-tools", "connector", "call", "connector__matrix__generate_image",
                         "--args-file", argsf])
        except Exception as e:
            print("  [尝试%d] 失败: %s" % (attempt, str(e)[:160]))
            time.sleep(min(5 * attempt, 30))
            # 把失败的这批轮转到队尾，先让后面的请求跑
            pending = pending[BATCH:] + chunk
            continue
        ok = r.get("success_items", [])
        fail = r.get("failed_items", [])
        print("  尝试%d  batch ok=%d fail=%d (待处理 %d)" % (attempt, len(ok), len(fail),
                                                            max(0, len(pending) - BATCH)))
        for f in fail:
            print("    FAIL:", json.dumps(f, ensure_ascii=False)[:300])
        by_stem = {os.path.splitext(j["output_file"])[0]: j for j in chunk}
        got = set()
        for item in ok:
            stem = os.path.splitext(item.get("file_name", ""))[0]
            job = by_stem.get(stem)
            if job is None:
                print("    未匹配:", item.get("file_name"))
                continue
            got.add(stem)
            item["requested_file"] = job["output_file"]
            item["prompt"] = job["prompt"]
            if on_item:
                on_item(item)          # 每张落库，中断可续跑
            results.append(item)
        pending = [j for j in pending
                   if os.path.splitext(j["output_file"])[0] not in got]
        if pending:
            print("    %d 张未返回，重新排队" % len(pending))
            time.sleep(3)
    if pending:
        print("  警告：仍有 %d 张未完成: %s" % (len(pending),
                                          [p["output_file"] for p in pending]))
    return results


def download(node_id, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 10000:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last = None
    for attempt in range(4):
        try:
            r = run_cli(["mcode-tools", "get_asset_url", node_id])
            url = r["download_url"]
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) < 10000:
                raise IOError("下载内容过小: %d" % len(data))
            with open(dest, "wb") as f:
                f.write(data)
            return dest
        except Exception as e:
            last = e
            print("    下载重试 %d: %s" % (attempt + 1, str(e)[:120]))
            time.sleep(3 * (attempt + 1))
    raise IOError("下载失败 %s: %s" % (node_id, last))


def fetch_urls(node_ids):
    """批量换取下载链接（用于作为 image-to-image 的 input_urls）"""
    urls = {}
    for nid in node_ids:
        try:
            r = run_cli(["mcode-tools", "get_asset_url", nid])
            urls[nid] = r["download_url"]
        except Exception as e:
            print("    url fail", nid, e)
    return urls


# ---------------- 阶段实现 ----------------
def phase_a():
    state = load_json(STATE_PATH, {})
    state.setdefault("A", {})
    jobs = []
    for folder, key, anchor, extra, suffix, aspect in PHASE_A + EXTRA_CAST:
        if key in state["A"] and len(state["A"][key]) >= 2 and key not in OVERRIDE:
            continue
        base = "%s_01_正脸" % folder
        for c in (1, 2):
            fn = "%s_c%d" % (base, c)
            if fn in state["A"].get("__files__", {}):
                continue
            jobs.append({
                "prompt": ph_a_prompt(key, anchor, extra, suffix),
                "aspect_ratio": aspect,
                "resolution": "2K",
                "output_file": fn,
            })
    if not jobs:
        print("阶段A：无待生成任务")
        return
    print("阶段A：生成 %d 张正脸候选" % len(jobs))

    def _on(item):
        fn = item["requested_file"]
        state["A"].setdefault("__files__", {})[fn] = {
            "node_id": item["node_id"], "folder": fn.split("_")[0]}
        save_json(STATE_PATH, state)

    res = generate(jobs, on_item=_on)
    # 按 key 归组（按候选编号数字排序，redo 追加的 c3/c4 也要算进去）
    files = state["A"].get("__files__", {})

    def cnum(fn):
        try:
            return int(fn.split("_c")[-1])
        except ValueError:
            return 0

    for folder, key, anchor, extra, suffix, aspect in PHASE_A + EXTRA_CAST:
        cands = [files[fn]["node_id"] for fn in sorted(files, key=cnum)
                 if fn.startswith(folder + "_01_正脸_c") and fn in files]
        if cands:
            state["A"][key] = cands
    save_json(STATE_PATH, state)
    print("阶段A完成，共 %d 个候选" % len(res))


def do_redo():
    """为某个角色追加候选正脸：python gen.py redo SQT 2"""
    key = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    state = load_json(STATE_PATH, {})
    state.setdefault("A", {})
    files = state["A"].setdefault("__files__", {})
    target = None
    for folder, k, anchor, extra, suffix, aspect in PHASE_A + EXTRA_CAST:
        if k == key:
            target = (folder, k, anchor, extra, suffix, aspect)
            break
    if not target:
        print("未知 key:", key)
        return
    folder, k, anchor, extra, suffix, aspect = target

    def cand_num(fn):
        try:
            return int(fn.split("_c")[-1])
        except ValueError:
            return 0

    used = [cand_num(fn) for fn in files if fn.startswith(folder + "_01_正脸_c")]
    nxt = (max(used) + 1) if used else 1
    jobs = []
    for i in range(n):
        fn = "%s_01_正脸_c%d" % (folder, nxt + i)
        jobs.append({"prompt": ph_a_prompt(key, anchor, extra, suffix),
                     "aspect_ratio": aspect, "resolution": "2K", "output_file": fn})
    print("重做 %s -> %s" % (key, [j["output_file"] for j in jobs]))

    def _on(item):
        fn = item["requested_file"]
        files[fn] = {"node_id": item["node_id"], "folder": fn.split("_")[0]}
        save_json(STATE_PATH, state)

    generate(jobs, on_item=_on)
    cands = []
    for fn in sorted(files, key=cand_num):
        if fn.startswith(folder + "_01_正脸_c"):
            cands.append(files[fn]["node_id"])
    state["A"][key] = cands
    save_json(STATE_PATH, state)
    print("完成，当前候选数:", len(cands))


SELECT_MAP = {
    "XTL": 2,   # 许听澜 —— 左眉尾疤清晰、凡人气质足
    "SQT": 4,   # 沈青棠 —— 白袍+青玉簪+泪痣在位、袖口无字
    "XH": 3,    # 许小禾 —— 右脸酒窝明显、桃木牌"平安"清晰
    "NHN": 1,   # 宁鹤年 —— 长山羊胡、白底金云纹
    "GCF": 1,   # 顾长风 —— 桃花眼眼尾下垂、银边青白袍、白玉冠
    "YS": 1,    # 严松 —— 方冠、玉令牌、八字短须、倨傲
    "LW": 2,    # 老魏 —— 蓝布巾、花白络腮胡、旱烟杆
    "ST": 2,    # 石头 —— 大门牙、憨笑
    "QDB": 2,   # 钱多宝 —— 展开折扇、得意笑
    "ZZ": 1,    # 镇长 —— 山羊胡、灰方巾、精明眼神
    "FQ": 1,    # 父亲许大河 —— 布巾背篓、眉眼似听澜
    "STL": 1,   # 少年听澜 —— 小揪、认真眼神
    "JZM": 1,   # 剑宗弟子男
    "JZN": 2,   # 剑宗弟子女
    "YZG": 1,   # 云巅宫弟子
    "ZM1": 1,   # 镇民甲
    "ZM2": 1,   # 镇民乙
    "ZM3": 1,   # 镇民丙
}

# v2.1 质检返工后的改选（优先级高于 SELECT_MAP）
# 统一选 c3：厨师帽→白玉小冠、立领盘扣→交领右衽、翻领衬衫→交领右衽、
# 西式烟斗→竹杆旱烟袋、额头白布带→高束发髻+白玉簪
SELECT_OVERRIDE = {
    "YS": 3,   # 严松 —— 白玉小冠+白玉簪横穿，不再是厨师帽
    "ZZ": 3,   # 镇长 —— 深蓝交领右衽长衫，不再是立领盘扣
    "ZM1": 3,  # 镇民甲 —— 交领右衽短衣，不再是翻领衬衫
    "ZM3": 3,  # 镇民丙 —— 交领右衽短衣+草绳
    "YZG": 3,  # 云巅宫弟子 —— 高束发髻+白玉簪，额头无白布带
    "LW": 3,   # 老魏 —— 竹杆旱烟袋，不再是西式烟斗
}


def redo_b(names):
    """只重做指定的几张派生图：python gen.py redoB 严松_02_三视图 老魏_02_三视图"""
    state = load_json(STATE_PATH, {})
    sel = load_json(SELECTED_PATH, {})
    state.setdefault("B", {})
    need = []
    for v in sel.values():
        if v["node_id"] not in need:
            need.append(v["node_id"])
    urls = fetch_urls(need)
    jobs, meta = [], []
    for fname in names:
        hit = None
        for folder, key, filename, prompt, aspect in PHASE_B:
            if filename == fname:
                hit = (folder, key, filename, prompt, aspect)
                break
        if not hit:
            print("  未知派生图:", fname)
            continue
        folder, key, filename, prompt, aspect = hit
        ref = urls.get(sel[key]["node_id"])
        if not ref:
            print("  无参考图:", fname)
            continue
        jobs.append({"prompt": prompt + "，" + NEG_TEXT, "aspect_ratio": aspect,
                     "resolution": "2K", "input_urls": [ref], "output_file": filename})
        meta.append((folder, filename))
    print("重做派生图 %d 张" % len(jobs))
    meta_by_file = {fn: (fd, fn) for fd, fn in meta}

    def _on(item):
        fn = item["requested_file"]
        folder = meta_by_file.get(fn, (fn.split("_")[0], fn))[0]
        state["B"][fn] = {"node_id": item["node_id"], "folder": folder}
        save_json(STATE_PATH, state)

    generate(jobs, on_item=_on)
    save_json(STATE_PATH, state)
    print("完成")


def do_selectall():
    state = load_json(STATE_PATH, {})
    sel = load_json(SELECTED_PATH, {})
    files = state.get("A", {}).get("__files__", {})

    def cnum(fn):
        try:
            return int(fn.split("_c")[-1])
        except ValueError:
            return 0

    ok, bad = 0, []
    for key, idx in SELECT_MAP.items():
        if key in SELECT_OVERRIDE:
            idx = SELECT_OVERRIDE[key]
        cands = state.get("A", {}).get(key)
        if not cands:
            bad.append((key, "state 无候选"))
            continue
        if idx > len(cands):
            bad.append((key, "候选不足 %d" % len(cands)))
            continue
        sel[key] = {"node_id": cands[idx - 1], "candidates": cands, "chosen_index": idx}
        ok += 1
    save_json(SELECTED_PATH, sel)
    print("已选定 %d 个角色" % ok)
    for k, why in bad:
        print("  失败", k, why)
    # 输出每个角色对应的文件名，方便人工核对
    for key, idx in SELECT_MAP.items():
        if key not in sel:
            continue
        if key in SELECT_OVERRIDE:
            idx = SELECT_OVERRIDE[key]
        fn = [f for f in sorted(files, key=cnum)
              if files[f]["node_id"] == sel[key]["node_id"]]
        print("  %-5s -> %s" % (key, fn[0] if fn else "?"))


def do_select():
    key = sys.argv[2]
    idx = int(sys.argv[3])
    state = load_json(STATE_PATH, {})
    cands = state["A"][key]
    nid = cands[idx - 1]
    sel = load_json(SELECTED_PATH, {})
    sel[key] = {"node_id": nid, "candidates": cands, "chosen_index": idx}
    save_json(SELECTED_PATH, sel)
    print("已选定 %s -> candidate %d (%s)" % (key, idx, nid))


def phase_b():
    state = load_json(STATE_PATH, {})
    sel = load_json(SELECTED_PATH, {})
    if not sel:
        print("阶段B：请先选定正脸")
        return
    # 换 URL
    need = []
    for v in sel.values():
        if v["node_id"] not in need:
            need.append(v["node_id"])
    urls = fetch_urls(need)
    jobs = []
    meta = []
    for folder, key, filename, prompt, aspect in PHASE_B:
        ref = urls.get(sel[key]["node_id"])
        if not ref:
            print("  跳过（无参考图）:", filename)
            continue
        jobs.append({
            "prompt": prompt + "，" + NEG_TEXT,
            "aspect_ratio": aspect,
            "resolution": "2K",
            "input_urls": [ref],
            "output_file": filename,
        })
        meta.append((folder, filename))
    print("阶段B：生成 %d 张派生图" % len(jobs))
    state.setdefault("B", {})
    meta_by_file = {fn: (fd, fn) for fd, fn in meta}

    def _on(item):
        fn = item["requested_file"]
        folder = meta_by_file.get(fn, (fn.split("_")[0], fn))[0]
        state["B"][fn] = {"node_id": item["node_id"], "folder": folder}
        save_json(STATE_PATH, state)

    res = generate(jobs, on_item=_on)
    save_json(STATE_PATH, state)
    print("阶段B完成")


def phase_c():
    state = load_json(STATE_PATH, {})
    state.setdefault("C", {})
    jobs = []
    for name, desc in PHASE_C:
        fn = "道具_%s" % name
        if fn in state["C"]:
            continue
        jobs.append({
            "prompt": desc + "，" + PROP_SUFFIX + "，" + NEG_TEXT,
            "aspect_ratio": "1:1",
            "resolution": "2K",
            "output_file": fn,
        })
    if not jobs:
        print("阶段C：无待生成任务")
        return
    print("阶段C：生成 %d 张道具图" % len(jobs))

    def _on(item):
        fn = item["requested_file"]
        state["C"][fn] = {"node_id": item["node_id"], "folder": "道具"}
        save_json(STATE_PATH, state)

    res = generate(jobs, on_item=_on)
    save_json(STATE_PATH, state)
    print("阶段C完成")


def do_download():
    state = load_json(STATE_PATH, {})
    total = 0
    for phase in ("A", "B", "C"):
        for name, info in state.get(phase, {}).items():
            if name == "__files__":
                continue
            folder = info.get("folder")
            if not folder:
                continue
            dest = os.path.join(OUT_ROOT, folder, name + ".jpg")
            try:
                download(info["node_id"], dest)
                total += 1
            except Exception as e:
                print("  下载失败", name, e)
    print("已落盘 %d 张到 %s" % (total, OUT_ROOT))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "phaseA":
        phase_a()
    elif cmd == "select":
        do_select()
    elif cmd == "selectall":
        do_selectall()
    elif cmd == "redoB":
        redo_b(sys.argv[2:])
    elif cmd == "redo":
        do_redo()
    elif cmd == "phaseB":
        phase_b()
    elif cmd == "phaseC":
        phase_c()
    elif cmd == "download":
        do_download()
    else:
        print(__doc__)
