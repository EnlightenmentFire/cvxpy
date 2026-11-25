# -*- coding: utf-8 -*-
"""Kokoro-82M v1.1-zh 旁白合成（Apache-2.0）。

要点
- 自己做 G2P（misaki 的 ZHFrontend），关闭儿化，按短语表纠正多音字/文言读音；
- 每行按「」和句末标点切段：文言引文慢读，白话正常速；段间停顿由我们控制；
- 用模型输出的 pred_dur 拿到逐词时间戳，供字幕和画面对点。
"""
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
import numpy as np
import soundfile as sf
import torch

SR = 24000
REPO = "hexgrad/Kokoro-82M-v1.1-zh"

# ── 读音表：短语 → 拼音（数字声调）。只放需要纠正、或必须锁定的词。─────────
PRON = {
    # 地名、人名
    "句章": "gou1 zhang1",
    "会稽": "kuai4 ji1",
    "江乘": "jiang1 cheng2",
    "覆舟山": "fu4 zhou1 shan1",
    "罗落桥": "luo2 luo4 qiao2",
    "樗蒲": "chu1 pu2",
    "王谧": "wang2 mi4",
    "刁逵": "diao1 kui2",
    "孟昶": "meng4 chang3",
    "皇甫敷": "huang2 fu3 fu1",
    "吴甫之": "wu2 fu3 zhi1",
    "琅邪": "lang2 ya2",
    "寄奴": "ji4 nu2",
    "萧方等": "xiao1 fang1 deng3",
    "王绥": "wang2 sui2",
    "王愉": "wang2 yu2",
    "桓谦": "huan2 qian1",
    "桓修": "huan2 xiu1",
    "桓玄": "huan2 xuan2",
    "桓温": "huan2 wen1",
    "刘牢之": "liu2 lao2 zhi1",
    "何无忌": "he2 wu2 ji4",
    "廿二史札记": "nian4 er4 shi3 zha2 ji4",
    # 文言
    "议欲不举": "yi4 yu4 bu4 ju3",
    "断怀敬乳": "duan4 huai2 jing4 ru3",
    "而自养高祖": "er2 zi4 yang3 gao1 zu3",
    "不治廉隅": "bu4 zhi4 lian2 yu2",
    "为时贱薄": "wei2 shi2 jian4 bo2",
    "樗蒲倾产": "chu1 pu2 qing1 chan3",
    "卿当为": "qing1 dang1 wei2",
    "一代英雄": "yi2 dai4 ying1 xiong2",
    "手奋长刀": "shou3 fen4 chang2 dao1",
    "长刀": "chang2 dao1",
    "被坚执锐": "pi1 jian1 zhi2 rui4",
    "为士卒先": "wei2 shi4 zu2 xian1",
    "法令明整": "fa3 ling4 ming2 zheng3",
    "一人三反": "yi4 ren2 san1 fan3",
    "何以自立": "he2 yi3 zi4 li4",
    "矫情任算": "jiao3 qing2 ren4 suan4",
    "必将用我辈也": "bi4 jiang1 yong4 wo3 bei4 ye3",
    "风骨不恒": "feng1 gu3 bu4 heng2",
    "盖人杰也": "gai4 ren2 jie2 ye3",
    "此儿可卖": "ci3 er2 ke3 mai4",
    "亦当不惜": "yi4 dang1 bu4 xi1",
    "二州之众": "er4 zhou1 zhi1 zhong4",
    "千七百人": "qian1 qi1 bai3 ren2",
    "汝欲作何死": "ru3 yu4 zuo4 he2 si3",
    "裕瞋目叱之": "yu4 chen1 mu4 chi4 zhi1",
    "敷辟易": "fu1 bi4 yi4",
    "谦等士卒多北府人": "qian1 deng3 shi4 zu2 duo1 bei3 fu3 ren2",
    "素畏伏裕": "su4 wei4 fu2 yu4",
    "莫有斗志": "mo4 you3 dou4 zhi4",
    "令民称力而取之": "ling4 min2 chen4 li4 er2 qu3 zhi1",
    "弥日不尽": "mi2 ri4 bu2 jin4",
    "王谧为公": "wang2 mi4 wei2 gong1",
    "刁逵亡族": "diao1 kui2 wang2 zu2",
    "酬恩报怨": "chou2 en1 bao4 yuan4",
    "何其狭哉": "he2 qi2 xia2 zai1",
    "江左诸帝": "jiang1 zuo3 zhu1 di4",
    "乃皆出自素族": "nai3 jie1 chu1 zi4 su4 zu2",
    "社钱三万": "she4 qian2 san1 wan4",
    "有田万顷": "you3 tian2 wan4 qing3",
    "奴婢数千人": "nu2 bi4 shu4 qian1 ren2",
    "岛夷刘裕": "dao3 yi2 liu2 yu4",
    # 白话里的多音字
    "还不上": "huan2 bu2 shang4",
    "辟易": "bi4 yi4",          # 关键词单独查时也要用对的读音（否则按默认 pì 判错）
    "称力": "chen4 li4",
    "替他还了钱": "ti4 ta1 huan2 le5 qian2",
    "替他还的": "ti4 ta1 huan2 de5",
    "王谧为公": "wang2 mi4 wei2 gong1",
    "一箭正中": "yi2 jian4 zheng4 zhong4",
    "还钱之恩": "huan2 qian2 zhi1 en1",
    "拴马桩": "shuan1 ma3 zhuang1",
    "大个子": "da4 ge4 zi5",
    "当了皇帝": "dang1 le5 huang2 di4",
    "喂活了他": "wei4 huo2 le5 ta1",
    "长大了": "zhang3 da4 le5",
    "一箭射中": "yi2 jian4 she4 zhong4",
    "瞪眼一喝": "deng4 yan3 yi4 he4",
    "吓得后退": "xia4 de5 hou4 tui4",
    "背靠大树": "bei4 kao4 da4 shu4",
    "带头冲阵": "dai4 tou2 chong1 zhen4",
    "冲阵": "chong1 zhen4",
    "冲进城": "chong1 jin4 cheng2",
    "冲在": "chong1 zai4",
    "带头冲": "dai4 tou2 chong1",
    "投降": "tou2 xiang2",
    "传诏官": "chuan2 zhao4 guan1",
    "假称奉诏": "jia3 cheng1 feng4 zhao4",
    "好几层": "hao3 ji3 ceng2",
    "散给百姓": "san4 gei3 bai3 xing4",
    "众人散去": "zhong4 ren2 san4 qu4",
    "先散了": "xian1 san4 le5",
    "一下子垮了": "yi2 xia4 zi5 kua3 le5",
    "重用": "zhong4 yong4",
    "门第": "men2 di4",
    "做官": "zuo4 guan1",
    "得有人": "dei3 you3 ren2",
    "都得": "dou1 dei3",
    "看得上": "kan4 de5 shang4",
    "看不起": "kan4 bu5 qi3",
    "觉得": "jue2 de5",
    "藏起": "cang2 qi3",
    "差点": "cha4 dian3",
    "名声也差": "ming2 sheng1 ye3 cha4",
    "撑到": "cheng1 dao4",
    "几千": "ji3 qian1",
    "几十人": "ji3 shi2 ren2",
    "几天之内": "ji3 tian1 zhi1 nei4",
    "一千多人": "yi4 qian1 duo1 ren2",
    "一千八百四十八人": "yi4 qian1 ba1 bai3 si4 shi2 ba1 ren2",
    "两万": "liang3 wan4",
    "三万钱": "san1 wan4 qian2",
    "二十七人": "er4 shi2 qi1 ren2",
    "掌兵": "zhang3 bing1",
    "刀把子": "dao1 ba4 zi5",
    "压邪": "ya1 xie2",
    "军袍": "jun1 pao2",
    "红布": "hong2 bu4",
    "噩梦": "e4 meng4",
    "堂妹": "tang2 mei4",
    "淝水之战": "fei2 shui3 zhi1 zhan4",
    "朝廷": "chao2 ting2",
    "南朝": "nan2 chao2",
    "南朝四朝": "nan2 chao2 si4 chao2",
    "四朝": "si4 chao2",
    "江东": "jiang1 dong1",
    "老将": "lao3 jiang4",
    "大将": "da4 jiang4",
    "守将": "shou3 jiang4",
    "长江": "chang2 jiang1",
    "流民": "liu2 min2",
    "主帅": "zhu3 shuai4",
    "篡位": "cuan4 wei4",
    "称帝": "cheng1 di4",
    "斩首": "zhan3 shou3",
    "灭族": "mie4 zu2",
    "子侄": "zi3 zhi2",
    "不论老少": "bu2 lun4 lao3 shao4",
    "位列三公": "wei4 lie4 san1 gong1",
    "玉玺": "yu4 xi3",
    "解下": "jie3 xia4",
    "豫州刺史": "yu4 zhou1 ci4 shi3",
    "公元": "gong1 yuan2",
    "高门": "gao1 men2",
    "素族": "su4 zu2",
    "寒人": "han2 ren2",
    "布衣": "bu4 yi1",
    "史家": "shi3 jia1",
    "赵翼": "zhao4 yi4",
    "措手不及": "cuo4 shou3 bu4 ji2",
    "一拥而上": "yi4 yong1 er2 shang4",
    "松懈": "song1 xie4",
    "纵兵抢掠": "zong4 bing1 qiang3 lve4",
    "漫山遍野": "man4 shan1 bian4 ye3",
    "不知多少": "bu4 zhi1 duo1 shao3",
    "烟焰冲天": "yan1 yan4 chong1 tian1",
    "顺风放火": "shun4 feng1 fang4 huo3",
    "备好了船": "bei4 hao3 le5 chuan2",
    "上船就跑": "shang4 chuan2 jiu4 pao3",
    "又服刘裕": "you4 fu2 liu2 yu4",
    "一向又怕刘裕": "yi2 xiang4 you4 pa4 liu2 yu4",
    "根本不想打": "gen1 ben3 bu4 xiang3 da3",
    "举戟喝问": "ju3 ji3 he4 wen4",
    "喝问": "he4 wen4",
    "一个人死战": "yi2 ge4 ren2 si3 zhan4",
    "撞上": "zhuang4 shang4",
    "孙恩作乱": "sun1 en1 zuo4 luan4",
    "反了三次": "fan3 le5 san1 ci4",
    "怎么立足": "zen3 me5 li4 zu2",
    "装样子": "zhuang1 yang4 zi5",
    "收人心": "shou1 ren2 xin1",
    "心没拿到": "xin1 mei2 na2 dao4",
    "兵拿到了": "bing1 na2 dao4 le5",
    "家当": "jia1 dang4",
    "全部家当": "quan2 bu4 jia1 dang4",
    "家财": "jia1 cai2",
    "地头": "di4 tou2",
    "说法不一": "shuo1 fa3 bu4 yi1",
    "横行一方": "heng2 xing2 yi4 fang1",
    "有地有钱": "you3 di4 you3 qian2",
    "这一笔": "zhe4 yi4 bi3",
    "最底层": "zui4 di3 ceng2",
    "立场相反": "li4 chang3 xiang1 fan3",
    "更难听": "geng4 nan2 ting1",
    "母亲": "mu3 qin1",
    "奶妈": "nai3 ma1",
    "不拘小节": "bu4 ju1 xiao3 jie2",
    "有志气": "you3 zhi4 qi4",
    "一般认为": "yi4 ban1 ren4 wei2",
    "被人看不起": "bei4 ren2 kan4 bu5 qi3",
    "被捆在": "bei4 kun3 zai4",
    "捆上马桩": "kun3 shang4 ma3 zhuang1",
    "马桩": "ma3 zhuang1",
    "责备": "ze2 bei4",
    "恨透了": "hen4 tou4 le5",
    "记住了": "ji4 zhu4 le5",
    "往上走": "wang3 shang4 zou3",
    "本钱": "ben3 qian2",
    "唯一的本钱": "wei2 yi1 de5 ben3 qian2",
    "比钱和门第都硬": "bi3 qian2 he2 men2 di4 dou1 ying4",
    "打仗": "da3 zhang4",
    "有脑子": "you3 nao3 zi5",
    "上吊自杀": "shang4 diao4 zi4 sha1",
    "不动": "bu2 dong4",
    "不急": "bu4 ji2",
    "他等": "ta1 deng3",
    "召集人手": "zhao4 ji2 ren2 shou3",
    "借口打猎": "jie4 kou3 da3 lie4",
    "同谋": "tong2 mou2",
    "跟着干的": "gen1 zhe5 gan4 de5",
    "愿从的": "yuan4 cong2 de5",
    "请功": "qing3 gong1",
    "名单": "ming2 dan1",
    "一层层": "yi4 ceng2 ceng2",
    "多起来": "duo1 qi3 lai2",
    "多出十倍": "duo1 chu1 shi2 bei4",
    "北府兵": "bei3 fu3 bing1",
    "北府": "bei3 fu3",
    "建康": "jian4 kang1",
    "京口": "jing1 kou3",
    "镇江": "zhen4 jiang1",
    "海盐": "hai3 yan2",
    "石头城": "shi2 tou2 cheng2",
    "报恩和报仇": "bao4 en1 he2 bao4 chou2",
    "心胸太窄了": "xin1 xiong1 tai4 zhai3 le5",
    "一个封公": "yi2 ge4 feng1 gong1",
    "一个灭族": "yi2 ge4 mie4 zu2",
    "被指谋反": "bei4 zhi3 mou2 fan3",
    "全族被杀": "quan2 zu2 bei4 sha1",
    "被斩首": "bei4 zhan3 shou3",
    "全被杀": "quan2 bei4 sha1",
    "有用的": "you3 yong4 de5",
    "压过了": "ya1 guo4 le5",
    "攒下的": "zan3 xia4 de5",
    "信任": "xin4 ren4",
    "欠下": "qian4 xia4",
    "能赢": "neng2 ying2",
    "本来就是他的": "ben3 lai2 jiu4 shi4 ta1 de5",
    "没有一个出身高门": "mei2 you3 yi2 ge4 chu1 shen1 gao1 men2",
    "开国皇帝": "kai1 guo2 huang2 di4",
    "社钱": "she4 qian2",
    "被抓": "bei4 zhua1",
    "举的例子": "ju3 de5 li4 zi5",
    "拿了一整天": "na2 le5 yi4 zheng3 tian1",
    "没拿完": "mei2 na2 wan2",
    "正闹饥荒": "zheng4 nao4 ji1 huang1",
    "能拿多少拿多少": "neng2 na2 duo1 shao3 na2 duo1 shao3",
}

PAUSE_AFTER = {"。": 0.26, "？": 0.32, "！": 0.28, "；": 0.19, "：": 0.12, "——": 0.20, "，": 0.09}

_G = {}


def _init():
    if _G:
        return
    torch.set_num_threads(int(os.environ.get("TTS_THREADS", "4")))
    from kokoro import KModel, KPipeline
    import jieba
    from pypinyin import load_phrases_dict
    from pypinyin.contrib.tone_convert import to_tone
    from misaki.zh_frontend import ZHFrontend

    model = KModel(repo_id=REPO).eval()
    pipe = KPipeline(lang_code="z", repo_id=REPO, model=model)
    fe = ZHFrontend()  # 会先加载默认词典
    phrases = {}
    for w, py in PRON.items():
        syl = py.split()
        assert len(syl) == len(w), (w, py)
        phrases[w] = [[to_tone(s)] for s in syl]
        jieba.add_word(w, freq=2_000_000, tag="n")
    load_phrases_dict(phrases)
    _G.update(model=model, pipe=pipe, fe=fe)


def g2p(text):
    """返回 (phoneme 串, [(词, 该词在串里的起止位置)])"""
    _init()
    import cn2an
    from misaki.zh import ZHG2P
    fe = _G["fe"]
    t = cn2an.transform(text, "an2cn")
    t = ZHG2P.map_punctuation(t)
    _, tokens = fe(t, with_erhua=False)
    ps = ""
    spans = []
    for tk in tokens:
        ph = tk.phonemes if tk.phonemes is not None else ""
        s = len(ps)
        ps += ph
        spans.append((tk.text, s, len(ps)))
        ps += tk.whitespace
    return ps.strip(), spans


def _trim(wav, thr=0.006, pad=0.03):
    a = np.abs(wav)
    idx = np.where(a > thr)[0]
    if len(idx) == 0:
        return wav
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(wav), idx[-1] + int(pad * SR))
    return wav[s:e]


def synth_piece(text, voice, speed):
    """合成一小段，返回 (wav, 逐词时间[(词, t0, t1)])"""
    _init()
    from kokoro import KPipeline
    pipe, model = _G["pipe"], _G["model"]
    ps, spans = g2p(text)
    pack = pipe.load_voice(voice)
    out = KPipeline.infer(model, ps, pack, speed)
    wav = out.audio.numpy()
    # 逐音素时长 → 逐词时间
    vocab = model.vocab
    keep = [i for i, ch in enumerate(ps) if ch in vocab]
    dur = out.pred_dur.numpy().astype(float) * 600 / SR  # 秒
    # dur[0] 是 BOS
    t = dur[0]
    char_t = {}
    for k, i in enumerate(keep):
        d = dur[k + 1] if k + 1 < len(dur) else 0.0
        char_t[i] = (t, t + d)
        t += d
    words = []
    for w, s, e in spans:
        ts = [char_t[i] for i in range(s, e) if i in char_t]
        if ts:
            words.append((w, ts[0][0], ts[-1][1]))
    # 去掉首尾静音，时间同步平移
    a = np.abs(wav)
    idx = np.where(a > 0.006)[0]
    if len(idx):
        s0 = max(0, idx[0] - int(0.03 * SR))
        e0 = min(len(wav), idx[-1] + int(0.03 * SR))
        wav = wav[s0:e0]
        words = [(w, max(0.0, a0 - s0 / SR), max(0.0, a1 - s0 / SR)) for w, a0, a1 in words]
    return wav, words, ps


QUOTE_RE = re.compile(r"(「[^」]*」)")


def split_line(text):
    """把一行拆成 [(片段文字, 是否文言, 片段后停顿)]。"""
    parts = []
    for chunk in QUOTE_RE.split(text):
        if not chunk:
            continue
        if chunk.startswith("「"):
            parts.append((chunk[1:-1], True))
        else:
            # 白话再按句末标点细分（保持标点在段尾）
            for seg in re.findall(r"[^。？！；]*[。？！；]?", chunk):
                if seg.strip():
                    parts.append((seg, False))
    out = []
    for i, (seg, q) in enumerate(parts):
        nxt = parts[i + 1][0] if i + 1 < len(parts) else ""
        tail = seg.rstrip()
        pause = 0.0
        if q:
            pause = 0.22 if nxt.startswith("——") else 0.14
        else:
            for p, v in PAUSE_AFTER.items():
                if tail.endswith(p):
                    pause = v
                    break
            if not pause and nxt:  # 白话 → 引文：“说他「…」”
                pause = 0.10
        clean = seg.strip()
        if clean.startswith("——"):
            clean = clean[2:]
        if clean:
            out.append((clean, q, pause))
    return out


def synth_line(text, voice, speed, quote_speed):
    pieces = split_line(text)
    wavs, words, t = [], [], 0.0
    for seg, q, pause in pieces:
        w, ws, _ = synth_piece(seg, voice, quote_speed if q else speed)
        wavs.append(w)
        words += [(x, a + t, b + t, q) for x, a, b in ws]
        t += len(w) / SR
        if pause:
            wavs.append(np.zeros(int(pause * SR), dtype=np.float32))
            t += pause
    # 行尾停顿交给时间轴；去掉最后一段停顿
    if pieces and pieces[-1][2]:
        wavs = wavs[:-1]
        t -= pieces[-1][2]
    return np.concatenate(wavs).astype(np.float32), words


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import script
    voice = sys.argv[1] if len(sys.argv) > 1 else "zm_011"
    speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.1
    qspeed = float(sys.argv[3]) if len(sys.argv) > 3 else 0.95
    outdir = sys.argv[4] if len(sys.argv) > 4 else f"/home/user/work/narr_{voice}"
    only = sys.argv[5].split(",") if len(sys.argv) > 5 else None
    os.makedirs(outdir, exist_ok=True)
    meta = []
    total = 0.0
    for d in script.LINES:
        if only and d["id"] not in only:
            continue
        txt = d["tts"] or d["text"]
        wav, words = synth_line(txt, voice, speed, qspeed)
        sf.write(f"{outdir}/{d['id']}.wav", wav, SR)
        dur = len(wav) / SR
        total += dur + d["gap"]
        meta.append(dict(id=d["id"], dur=dur, words=words))
        print(f"{d['id']}: {dur:5.2f}s  {txt[:24]}", flush=True)
    json.dump(meta, open(f"{outdir}/meta.json", "w"), ensure_ascii=False, indent=1)
    print(f"TOTAL narration+gaps: {total:.1f}s")
