# -*- coding: utf-8 -*-
"""旁白稿（唯一来源）。字幕、配音、时间轴都从这里生成。

每行: (场景, 字幕文本, 选项)
  字幕文本里的 "|" 是字幕换屏点，配音时去掉。
  选项:
    en   英文原话（屏幕下方小字）
    src  出处（小字）
    q    1 = 这一行是引语译文（字幕加引号样式）
    big  1 = 大字处理
    pre / gap  行前 / 行后停顿秒数（默认 gap 0.32）
    cue  画面同步点名字
    tts  配音专用文本（覆盖自动替换）
"""

S_SEQ = "Jensen Huang · Sequoia Capital《Crucible Moments》"
S_NTU = "Jensen Huang · 台大毕业典礼演讲 2023-05"
S_ACQ = "Jensen Huang · Acquired 专访 2023-10"
S_WITT_BOOK = "Stephen Witt《The Thinking Machine》· Inc. 书摘 2025-04-09"

LINES = [
    # ───────── 冷开场
    ("cold", "1996年。一家芯片公司的休息室里，|乒乓球台被推到一边，", dict(cue="cold")),
    ("cold", "腾出地方，放一台冰箱那么大的机器。", dict(cue="machine")),
    ("cold", "旁边的屏幕上，一个画面要等很久，|才一行一行画出来。", dict(cue="paint")),
    ("cold", "这家公司剩下的钱，|有一大块，换成了这台机器。", dict(cue="cash")),
    ("cold", "这家公司，叫英伟达。|今天，它是全世界最值钱的公司之一。", dict(cue="name")),
    ("cold", "但当年救它的，不是坚持。|是认错。", dict(cue="thesis", gap=0.9)),
    ("title", "黄仁勋的商业决断，第一期：|先认错，再活下来。", dict(cue="title", gap=0.9)),

    # ───────── 一 方向：餐馆
    ("diner", "1993年，三个工程师|在圣何塞一家连锁餐馆的卡座里，|商量开公司。", dict(cue="diner")),
    ("diner", "黄仁勋，30岁，|已婚，两个孩子。", dict(cue="thirty")),
    ("diner", "15岁时，他就在这个牌子的¦另一家分店，|洗过盘子，收过桌子。", dict(cue="busboy")),
    ("diner", "说起那一天，他说：", dict(gap=0.25)),
    ("diner", "说实话，我不知道该怎么做，|他们俩也不知道。|我们谁都不知道怎么做任何事。",
     dict(q=1, cue="q_noidea",
          en="Frankly, I had no idea how to do it, nor did they. None of us knew how to do anything.",
          src="Jensen Huang · CBS《60 Minutes》2024")),
    ("diner", "大白话就是：|三个人，没一个开过公司。", {}),
    ("diner", "据《财富》杂志，|公司成立时，账上只有4万美元。", dict(cue="40k")),
    ("diner", "但有一件事他们押对了：|电脑上的3D游戏，会火。", dict(cue="bet3d")),
    ("diner", "游戏画面要动起来，|电脑里得有一块专门画画面的芯片。", dict(cue="chip")),
    ("diner", "打个比方：CPU是管家，什么都管；|这块芯片是画师，只管画。", dict(cue="painter")),
    ("diner", "这说明什么？|方向，他们一开始就是对的。|错的，是下一步。", dict(cue="so1", gap=0.8)),

    # ───────── 二 章鱼
    ("octo", "1995年，第一颗芯片NV1发布。", dict(cue="nv1")),
    ("octo", "它想全包：画3D，出声音，插游戏手柄，|全塞在一块卡上。", dict(cue="stuff")),
    ("octo", "黄仁勋后来这样评价它：", dict(gap=0.25)),
    ("octo", "那是了不起的技术成就，|也是一个糟糕的产品。",
     dict(q=1, cue="q_terrible",
          en="It was a great technology achievement. It was a terrible product.", src=S_SEQ)),
    ("octo", "他说，把它的功能从头数一遍，|听起来就像一只章鱼。",
     dict(cue="octopus", en="When you're done describing NV1, it sounds like an octopus.", src=S_SEQ)),
    ("octo", "他到底在说什么？技术不差，是没人要这么多。|用他的话：没有人会去商店买瑞士军刀。",
     dict(q=0, cue="knife", en="Nobody goes to the store to buy a Swiss Army knife. It's something you get for Christmas.", src=S_SEQ)),
    ("octo", "结果，他自己的说法是：|卖出去25万片，|差不多24万9千片被退了回来。",
     dict(cue="returns", en="250,000 units went out. 250,000, well, 249,000 came back.", src=S_SEQ + "（他本人的说法）")),
    ("octo", "这说明什么？|产品好不好，工程师说了不算，|掏钱的人说了算。", dict(cue="so2", gap=0.8)),

    # ───────── 三 规则
    ("rule", "更要命的是，它押错了规则。", dict(cue="rule")),
    ("rule", "电脑画3D画面，|是把东西拆成很多小块，再拼起来。", dict(cue="mesh")),
    ("rule", "小块用什么形状？|同行大多用三角形。|英伟达押的是四边形。", dict(cue="triquad")),
    ("rule", "这就像大家都用公制，|你偏偏用英制。", dict(cue="metric")),
    ("rule", "然后微软出手了。|Windows 95之后，它推出DirectX。", dict(cue="directx")),
    ("rule", "这是一套画画规则，游戏都按它来写。", dict(cue="rulebook")),
    ("rule", "它的3D部分，只认三角形。|不按它来，游戏就跑不起来。", dict(cue="onlytri")),
    ("rule", "黄仁勋回忆，当时大约50家公司，|都在这套规则里。只有英伟达在外面。",
     dict(cue="fifty",
          en="…DirectX is the architecture that everybody else uses except us. … the rest of the industry, now some 50 companies, are all over us.",
          src=S_SEQ)),
    ("rule", "这说明什么？|平台一旦定了标准，|一家小公司再聪明，也扛不住。", dict(cue="so3", gap=0.8)),

    # ───────── 四 两难
    ("dilemma", "偏偏这时候，英伟达手里还有一份合同：|给世嘉的下一代游戏机，做芯片NV2。", dict(cue="contract")),
    ("dilemma", "用的，还是四边形那一套。", {}),
    ("dilemma", "做完它，等于在错的路上越走越远，|再也追不上别人。", dict(cue="pathA")),
    ("dilemma", "不做完，公司马上没钱。", dict(cue="pathB")),
    ("dilemma", "黄仁勋的原话是：", dict(cue="hush", gap=2.0)),
    ("dilemma", "做完这个项目，会死。|不做完，马上就死。",
     dict(q=1, big=1, cue="q_die", gap=2.0,
          en="…we would finish the project and die, or not finish the project and die right away.", src=S_SEQ)),
    ("dilemma", "两条路，尽头都是倒闭。|区别只是早一点，晚一点。", dict(cue="both", gap=0.8)),

    # ───────── 五 认错一：世嘉
    ("sega", "他选了第三条路：|去认错。", dict(cue="third")),
    ("sega", "他找到世嘉的高管入交昭一郎，|把话摊开：", dict(cue="table")),
    ("sega", "他说，英伟达的路线错了，这块芯片做不完，|世嘉应该另找伙伴。",
     dict(cue="confess",
          en="…our invention was the wrong approach, … Sega should find another partner, … we could not complete the contract and the console.",
          src=S_NTU)),
    ("sega", "然后，他提了一个按常理不该提的请求：|请对方解除合同。但是钱，照付。",
     dict(cue="ask", en="…let us off of our contract … but pay us in full.", src=S_SEQ)),
    ("sega", "他后来说：|我很不好意思开这个口。",
     dict(cue="embarrassed", en="I was embarrassed to ask.", src=S_NTU)),
    ("sega", "这话难在哪儿？他什么都给不了对方，|还要对方把钱照样给他。", {}),
    ("sega", "按他的回忆，对方考虑了两天，|说：我愿意帮你。",
     dict(cue="agree", en="He thought about it for a couple days … and said, I'd like to help you.", src=S_SEQ)),
    ("sega", "大约500万美元。|他说，这笔钱，给了我们六个月的命。",
     dict(cue="5m", en="His understanding and generosity gave us six months to live.", src=S_NTU)),
    ("sega", "这笔钱到底算什么？|几方的说法，不一样。", dict(cue="versions")),
    ("sega", "黄仁勋2025年说：|他请对方把最后这500万，改成投资。", dict(cue="v1")),
    ("sega", "入交昭一郎2026年说：是他自己说服总部，|用剩下的开发费买英伟达的股票，|当作分手礼物。", dict(cue="v2")),
    ("sega", "他还说：我欣赏黄仁勋的为人，|把一切都押在了他身上。",
     dict(cue="v2q", en="I came to like Jensen Huang's character, and bet everything on him.",
          src="入交昭一郎 · 时事通讯社，《日本时报》2026-09-12 刊")),
    ("sega", "世嘉公司的回应是：批过这笔钱，|但确切的记录已经找不到了。", dict(cue="v3")),
    ("sega", "英伟达的上市文件又不一样：|1995年7月，合作方就花500万美元买了股份，|开发款另算。", dict(cue="v4")),
    ("sega", "这几种说法，我们不替他们统一。|能确定的只有一点：钱，到了英伟达手里。", dict(cue="money", gap=0.5)),
    ("sega", "这说明什么？|按入交昭一郎的说法，他押的不是芯片，是人。|坦白，成了黄仁勋唯一的筹码。", dict(cue="so5", gap=0.8)),

    # ───────── 六 认错二：对内
    ("inner", "对外认错难。|对内，更难。", dict(cue="inner")),
    ("inner", "NV2那套架构，也就是芯片的总体设计，|是联合创始人、技术负责人普里姆做的。", dict(cue="priem")),
    ("inner", "据记者威特写的传记：|普里姆想沿着它继续做；|黄仁勋要的，是顾客别再退货。", dict(cue="split")),
    ("inner", "一场关着门的技术争论，|最后变成当着员工的面争吵。",
     dict(cue="shout",
          en="…what had begun as a closed-door argument about circuit architecture had escalated into public shouting in full view of employees.",
          src=S_WITT_BOOK)),
    ("inner", "结果，这套架构被放弃。|公司掉头，去做一块按微软规则来的芯片。", dict(cue="shelve")),
    ("inner", "同时，裁员。|一百多人，剩下多少？", dict(cue="layoff")),
    ("inner", "《英伟达之道》说40人左右，|威特的书说35名工程师，", dict(cue="n40")),
    ("inner", "公司的上市文件写的是：1996年底，42人。", dict(cue="n42")),
    ("inner", "书里写，那年来的一位图形专家，开的条件是：|每个工作周结束，当面领一张纸质支票。",
     dict(cue="check",
          en="Kirk insisted on receiving a hand-delivered paper check at the end of each workweek.",
          src=S_WITT_BOOK)),
    ("inner", "书里写，他不确定这家公司，|还能不能撑过一个星期。",
     dict(en="He wasn't sure the company would stay in business longer than that.", src=S_WITT_BOOK)),
    ("inner", "这说明什么？认错不是说一句话。|是放下自己人的心血，送走一大半同事。", dict(cue="so6", gap=0.8)),

    # ───────── 七 认错三：时间
    ("time", "剩下的问题，是时间。", dict(cue="time")),
    ("time", "规则是微软定的，几十家公司都按它做。|在别人的规则里，能比的只剩一样：|谁快。", dict(cue="speed", gap=0.6)),
    ("time", "芯片平常怎么做？|设计好，送去工厂生产，这叫流片。", dict(cue="tapeout")),
    ("time", "工厂先做几片样品回来，这叫打样。|有错就改，改完再送。一来一回，按月算。", dict(cue="loop")),
    ("time", "黄仁勋说，照这个流程，|错还没改完，公司已经倒闭了。",
     dict(cue="toolate", en="…by the time that we found all the bugs … We would've been out of business already.", src=S_ACQ)),
    ("time", "于是他买了一台机器：|模拟器。", dict(cue="emu")),
    ("time", "它能假装自己就是¦那块还没造出来的芯片，|让软件先在它上面跑起来。", dict(cue="pretend")),
    ("time", "大约100万美元。占剩下现金的多少，说法不一：|《福布斯》说三分之一，威特写的是最后的钱。", dict(cue="1m")),
    ("time", "机器太大，机房放不下，|才摆进了休息室。", dict(cue="room")),
    ("time", "它非常、非常慢。|黄仁勋回忆，他们就坐在那儿，看着它画。",
     dict(cue="slow", en="We would just sit there and watch it paint.", src=S_ACQ)),
    ("time", "但本来，要等芯片做回来，|才能写软件，找毛病。这些活得排队干。", dict(cue="queue")),
    ("time", "现在芯片还没造出来，|这些活已经同时干起来了。", dict(cue="parallel")),
    ("time", "这不是买机器，是拿钱买时间。", dict(cue="buytime", gap=0.6)),
    ("time", "然后是最险的一步：不打样，直接量产。|也就是不做样品，直接成批生产。", dict(cue="noproto")),
    ("time", "公司的几位负责人问他：|你怎么知道它会是完美的？", dict(cue="ask2", gap=0.3)),
    ("time", "他答：我知道它会是完美的。|因为如果不是，我们就倒闭了。|所以，让它完美。我们只有一次机会。",
     dict(cue="q_perfect",
          en="I know it's going to be perfect, because if it's not, we'll be out of business. So let's make it perfect. We get one shot.",
          src=S_ACQ)),
    ("time", "这话狠在哪儿？他给的理由不是有把握，|是没有退路。", dict(gap=0.6)),
    ("time", "芯片做出来了。|它并不完美。", dict(cue="back")),
    ("time", "微软那套规则里，有32种混合模式，|也就是32种叠颜色的办法。", dict(cue="g32")),
    ("time", "这块芯片，只支持8种。", dict(cue="g8")),
    ("time", "很多年后，主持人当面问起。|黄仁勋答：", dict(cue="host", gap=0.9)),
    ("time", "另外24种，没那么重要。",
     dict(q=1, big=1, cue="q_24", gap=1.3, en="The other 24 weren't that important.", src=S_ACQ)),
    ("time", "接着他补了实话：这不是计划好的，|他知道得太晚了。",
     dict(cue="honest", en="I didn't learn about it until it was too late.", src=S_ACQ)),
    ("time", "我们本该32种全做。|但做出来就是这样，|只能把它用到最好。",
     dict(q=1, cue="q_best",
          en="We should have implemented all 32. But we built what we built, so we had to make the best of it.", src=S_ACQ)),
    ("time", "这说明什么？第三次认错，|是认自己做不到完美。先到，够用，活下来。", dict(cue="so7", gap=0.8)),

    # ───────── 八 结果
    ("result", "1997年，这块芯片发布。|名字叫RIVA 128。", dict(cue="riva")),
    ("result", "开始出货后四个月，|超过100万片。", dict(cue="million")),
    ("result", "那年第四季度，|英伟达成立以来第一次单季盈利。", dict(cue="profit")),
    ("result", "此后很多年，黄仁勋在公司内部讲话，|开头都是同一句：", dict(cue="years", gap=0.5)),
    ("result", "我们公司，离倒闭只有30天。",
     dict(q=1, big=1, cue="q_30", gap=0.9,
          en="Our company is thirty days from going out of business.",
          src="Stephen Witt ·《The New Yorker》2023-11")),
    ("result", "这说明什么？活下来之后，他没有讲胜利。|他讲的，还是公司随时会倒闭。", dict(cue="so8", gap=0.8)),

    # ───────── 收尾
    ("end", "很多年后，他这样回看：", dict(cue="end", gap=0.25)),
    ("end", "我们年轻的时候，很多事都做得很烂。|我们熬过了自己。|我们是自己最大的敌人。",
     dict(q=1, cue="q_enemy",
          en="When we were younger … we sucked at a lot of things. … We survived ourselves. We were our own worst enemy.",
          src="Jensen Huang · Tae Kim《The Nvidia Way》引言")),
    ("end", "还有一句：直面我们的错误，|带着谦卑去求助，救了英伟达。",
     dict(cue="q_confront",
          en="Confronting our mistake and, with humility, asking for help saved NVIDIA.", src=S_NTU)),
    ("end", "所以，这不是一个咬牙坚持的故事。", dict(cue="not", gap=0.5)),
    ("end", "是三次认错：|对客户，对自己人，对完美。", dict(cue="three", gap=0.7)),
    ("end", "他押对了方向，却押错了规则。", dict(cue="l1", gap=0.5)),
    ("end", "他认了错，把剩下的钱，换成了时间。", dict(cue="l2", gap=0.5)),
    ("end", "这一次，他向别人的标准低头。", dict(cue="l3", gap=0.9)),
    ("end", "后来，他要让别人，|向他的标准低头。", dict(cue="l4", gap=0.9)),
    ("end", "我们下一期见。", dict(cue="next", gap=1.5)),
]

# 配音读法替换（只影响 TTS，不影响字幕）
TTS_SUBS = [
    ("NV1", " N V 一 "), ("NV2", " N V 二 "),
    ("DirectX", " Direct X "), ("RIVA 128", " Riva 一二八 "),
    ("Windows 95", " Windows 九五 "), ("CPU", " C P U "), ("3D", "三D"),
    ("《", ""), ("》", ""),
    ("24万9千", "二十四万九千"), ("25万", "二十五万"),
    ("100万", "一百万"), ("500万", "五百万"), ("4万", "四万"),
    ("32种", "三十二种"), ("24种", "二十四种"), ("8种", "八种"),
    ("1993年", "一九九三年"), ("1995年", "一九九五年"), ("1996年", "一九九六年"), ("1997年", "一九九七年"),
    ("2025年", "二零二五年"), ("2026年", "二零二六年"),
    ("30岁", "三十岁"), ("15岁", "十五岁"), ("30天", "三十天"), ("7月", "七月"),
    ("40人", "四十人"), ("35名", "三十五名"), ("42人", "四十二人"), ("50家", "五十家"),
    ("一行一行", "一航一航"),
]


def tts_text(zh, opts):
    if opts.get("tts"):
        return opts["tts"]
    t = zh.replace("|", "").replace("¦", "")
    for a, b in TTS_SUBS:
        t = t.replace(a, b)
    return " ".join(t.split())


if __name__ == "__main__":
    import re
    n = 0
    for sc, zh, o in LINES:
        n += len(re.sub(r"[^一-鿿A-Za-z0-9]", "", zh))
    print("lines", len(LINES), "chars", n)
