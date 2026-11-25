# 55 · 修行几万小时的人，大脑有什么不一样？（佛法与心智 ·「静坐的科学」之四）

竖屏 1080×1920 / 25fps / H.264 + AAC 128k。**未发布、未上传。**

| 文件 | 说明 |
| --- | --- |
| `final_music.mp4` | 成片（含自制底乐），-15 LUFS，真峰值 ≤ -1.5 dBTP |
| `final_nomusic.mp4` | 无配乐备用版（旁白 + 开场磬声） |
| `cover_1080x1920.png` / `cover_1080x1440.png` | 封面（竖版 / 3:4） |
| `发布包.md` | 标题、简介、话题、声明 |
| `script.txt` | 分场旁白稿（`## 场景名` + 一行一句） |
| `narration.srt` | 字幕（按配音时间轴） |
| `QA.md` | 音画同步、响度、ASR 回读结果 |
| `src/` | 全部制作代码（画面、配音、配乐、混音、封面） |

## 配音：当前为云扬过渡版，托克维尔版待 box 生成
本云端会话**没有 GPU**，也拿不到 box 上的参考音频 `voice_samples_20261125/A0b_托克维尔设计音色参考_18秒_-15LUFS.mp3`，所以没法跑 Qwen3-TTS 托克维尔克隆。
按今天标准第 5 条，逐句旁白稿已导出到 `exports/55/sentences.json` 和 `sentences.txt`，共 88 句。
当前成片先用 VOICE_SPEC 里的 edge-tts `zh-CN-YunyangNeural`（-8%，+0Hz，句间 0.5 秒）出了完整版，方便先审内容和画面。

托克维尔版的回填步骤（box 上或任意有 Python 的机器）：
1. 用 `sentences.txt` 逐句生成 `line_0001.wav` … `line_0088.wav`，一句一个文件，不改字。
2. 把这些 wav 放进一个目录，再在本目录运行：
   ```
   python3 -m venv .venv && . .venv/bin/activate
   pip install numpy scipy soundfile pyloudnorm skia-python
   bash src/build.sh /path/to/tocqueville_wavs
   ```
   脚本会裁掉首尾静音，句间统一停 0.5 秒。时间轴、字幕和每一场的画面会按新声音自动重排，再重新混音，输出两版成片。
   字体是 Noto Serif/Sans CJK 的 SC/TC 子集（OFL 授权），先运行 `bash src/fetch_fonts.sh` 下载到 `~/fonts`（也可以用环境变量 `EP_FONT_DIR` 换目录）。

## 核实结果（制作会话自查，均对过 PubMed / PMC / 期刊页）
| 内容 | 结果 |
| --- | --- |
| Lutz 等 2004，PNAS 101(46):16369–73 | **已核**。修行者 8 人，平均 49 岁，修行 1 万–5 万小时、跨 15–40 年；对照 10 名学生，平均 21 岁，受训 1 周。冥想为 "unconditional loving-kindness and compassion"（nonreferential compassion）。与修行时长相关的**只有冥想前静息基线的伽马/慢波比**（r=0.79）。原文写 "to our knowledge, the highest reported in the literature in a nonpathological context"。作者自注了肌电污染的可能，并写明因果有待未来研究证明。 |
| 伽马测量的方法争议 | **已核**。Whitham 等 2007，Clin Neurophysiol 118(8):1877–88：肌肉麻痹对照显示，头皮 20Hz 以上信号大部分源自肌电。另有反方：Braboszcz 等 2017，PLOS ONE 12(1):e0170647，用 ICA 排除眼动和肌电伪迹后，冥想者伽马仍更高。片中两方都讲了。 |
| Lazar 等 2005，NeuroReport 16(17):1893–97 | **已核**。20 对 15；不是僧人，是有工作、有家庭的西方练习者；平均冥想 9.1 年，多数每天约 40 分钟；两组都是 100% 白人。英文引文与摘要逐字一致。年龄效应针对的是**前额叶**。**更正**：与冥想经验相关的两个区域是**右前脑岛和枕颞视觉皮层**，不是「前额叶和前脑岛」，片中已按原文改。 |
| Kral 等 2022，Sci Adv 8(20):eabk3316 | **已核**，标题与 brief 一致。218 名从未冥想的人，随机分到 MBSR（75）、主动对照 HEP（73）、等待组（70）三组。测了灰质体积、灰质密度、皮层厚度，均未复现先前发现。**注意**：该文**没有**比较长期冥想者，片中没有这样说。 |
| Van Dam 等 2018，Perspect Psychol Sci 13(1):36–61 | **已核**。片中标题译作《警惕炒作》，标了「意译」。 |
| Goleman & Davidson，*Altered Traits*，Avery 2017 | **部分核实**。brief 里「作者承认很多早期研究质量不高」这句，没找到可引用的原文段落，所以片中**只用访谈里能核实的话**：Goleman 说研究有六千多项，书里只取方法最严谨的约 60 项；Davidson 说早期许多研究，包括他实验室的，看的是冥想当下的变化，真正要紧的是持久改变（Sam Harris 播客 #111）。片中标「据作者介绍」「访谈意译」「二手材料·作者自评」。 |
| 新增：Draganski 等 2004，Nature 427:311–12 | 出版方摘要已核（"transient and selective structural change"）。「三个月杂耍」「停练后回落」来自二手报道，片中柱图标「示意」。 |
| 新增：Hölzel 等 2011，Psychiatry Res Neuroimaging 191(1):36–43 | **已核**。16 对 17，**非随机**，左海马等区域灰质密度增加。片中标「初步线索」。 |
| 新增：Fox 等 2014，Neurosci Biobehav Rev 43:48–73 | **已核**。21 项研究、约 300 名修行者，平均 d≈0.46，作者警示发表偏倚与方法局限。 |
| 《六祖坛经·定慧品》引文 | brief 已核，沿用。上屏用繁体原文，字幕用简体。 |

## 过审自查
- 没有出现达赖喇嘛的名字、画面、引语或著作，也没有 Mind & Life、西藏、流亡或机构背景。
- Lutz 研究只说「长期修行的僧人」。马蒂厄·里卡尔只在讲期待效应时点了一次名，没有提他的背景。
- 片中有两处明说「印照，不是证明」：约 0:50 的标题卡，以及约 9:47 收束段的「印照、类比，而不是证明」。
- 每一场下方都有证据标签（实证 / 小样本 / 相关 / 方法争议 / 二手），还有出处行。示意图都标了「示意」。
- 没有法事画面，不劝信，也没有求关注、小铃铛或打字音效。开场声音钩子是自制的磬声，加上电极亮起的轻微电子音。
