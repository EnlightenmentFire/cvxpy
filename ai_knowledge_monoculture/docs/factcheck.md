# 《防暴君，也防暴民》史料核对表

核对方式：逐条回到原始文献或可靠转载，摘原文，再对照稿件措辞。
✅ = 原文支持；✏️ = 已按原文修正稿件；⚠️ = 有出入或限定条件，稿中已照实处理。
（"待核"项已全部清零。）

---

## 一、野兔实验（Nature 2024）

来源：Shumailov, Shumaylov, Zhao, Papernot, Anderson, Gal, "AI models collapse when trained on recursively generated data", *Nature* 631, 755–759。
Published 24 July 2024（印刷版 25 July 2024）。https://www.nature.com/articles/s41586-024-07566-y

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 2024 年 7 月《自然》 | "Published: 24 July 2024"；"volume 631, pages 755–759" | ✅ |
| 小模型 OPT-125m，用维基百科文章微调 | "We fine-tune the OPT-125m causal language model made available by Meta through Hugging Face." / "We fine-tune it on the wikitext2 dataset." | ✅（片中不提公司名） |
| 开头是一段讲英国教区教堂钟楼的文字 | Input: "some started before 1360 — was typically accomplished by a master mason and a small team of itinerant masons, supplemented by local parish labourers, according to Poyntz Wright. But other authors reject this model, suggesting instead that leading architects designed the parish church towers based on early examples of Perpendicular." | ✅ |
| 第 1 代：圣彼得大教堂"在罗马，也在布宜诺斯艾利斯" | Gen 1: "architecture such as St. Peter's Basilica in Rome or St. Peter's Basilica in Buenos Aires…" | ✅ |
| 第 5 代：背一长串语言的名字 | Gen 5: "ism, which had been translated into more than 100 languages including English, French, German, Italian, Spanish, Portuguese, Dutch, Swedish, Norwegian, Polish, Hungarian, …" | ✅（注：arXiv 预印本展示的是第 7 代，《自然》正式版展示第 5 代，片中按《自然》版） |
| 第 9 代：各种颜色尾巴的长耳大野兔 | Gen 9: "architecture. In addition to being home to some of the world's largest populations of black @-@ tailed jackrabbits, white @-@ tailed jackrabbits, blue @-@ tailed jackrabbits, red @-@ tailed jackrabbits, yellow @-." | ✅（"@-@"是 wikitext 数据集里连字符的写法，画面去掉并加注"原文如此"） |
| "模型崩溃"：先丢掉少见的东西（分布的尾巴） | Definition 2.1: "Model collapse is a degenerative process … Being trained on polluted data, they then mis-perceive reality." 摘要："tails of the original content distribution disappear. We refer to this effect as 'model collapse'" | ✅ |
| 每一代掺进 10% 原始真实数据，退化就只剩一点点 | "Ten epochs, 10% of original training data preserved … We find that preservation of the original data allows for better model fine-tuning and leads to only minor degradation of performance." | ⚠️ 稿中说"只剩下一点点"，不说"不再退化"；另外这组实验训练轮数也不同（10 轮对 5 轮），不能把改善全算在 10% 头上，旁白只引论文自己的结论 |

## 二、称牛（Galton 1907）

来源：Francis Galton, "Vox Populi", *Nature* 75, 450–451（1907 年 3 月 7 日），本人逐字读过《自然》原版扫描：https://gwern.net/doc/statistics/prediction/1907-galton.pdf

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 普利茅斯的牲畜展览会 | "the annual show of the West of England Fat Stock and Poultry Exhibition recently held at Plymouth" | ✅ |
| 1906 年 | 原文只说"recently held"，没写年份。Galton《Memories of My Life》（1908）："A little more than a year ago, I happened to be at Plymouth…" | ✏️ 稿中只说"1906 年"，删去"秋天"（季节无据） |
| 牵出一头**活**肥牛，猜它宰好、收拾干净以后多重 | "A fat ox having been selected, competitors bought stamped and numbered cards, for 6d. each, on which to inscribe their respective names, addresses, and estimates of what the ox would weigh after it had been slaughtered and 'dressed.'" 表题："estimates of the dressed weight of a particular **living** ox" | ✏️ 原简报写"一头宰好的牛"，已改 |
| 六便士一张 | "for 6d. each"；"The sixpenny fee deterred practical joking" | ✅ |
| 有屠夫和农夫，有的是行家；也有人凭听来的消息和自己的感觉 | "The competitors included butchers and farmers, some of whom were highly expert in judging the weight of cattle; others were probably guided by such information as they might pick up, and by their own fancies." | ✏️ 原稿"压根不懂牛的普通人"改为贴近原文 |
| 787 张有效票 | "About 800 tickets were issued … After weeding thirteen cards out of the collection, as being defective or illegible, there remained 787 for discussion." | ✅ |
| 中位数 1207 磅，实际 1198 磅，差 9 磅（0.8%） | "Now the middlemost estimate is 1207 lb., and the weight of the dressed ox proved to be 1198 lb.; so the vox populi was in this case 9 lb., or 0·8 per cent. of the whole weight too high." | ✅ |
| 没被情绪左右，也没被谁的演说带偏 | "The judgments were unbiassed by passion and uninfluenced by oratory and the like." | ✅（原文拼作 unbiassed，屏幕照原文） |
| 分布图 | 按原文表格的 5%–95% 分位数（1074…1207…1293 磅）生成 787 个点；两端各 5% 原文没印，画面标"示意" | ✅ |
| 后来有学者复核，差不多；平均数正好等于实际重量 | Kenneth F. Wallis, "Revisiting Francis Galton's Forecasting Competition", ***Statistical Science*** 29(3): 420–424 (2014), DOI 10.1214/14-STS468：中位数应为 1208 磅；组织者来信记载净重 1197 磅；"using the correct value of the outcome, the mean estimate has zero error"。平均数 1197 磅见 Galton 1907 年 3 月 28 日《自然》来信 "The Ballot-Box" | ✏️ 刊名更正：不是英国皇家统计学会会刊，是 *Statistical Science* |
| 高尔顿发明了"优生学"一词 | Galton, *Inquiries into Human Faculty*（1883）脚注："The word eugenics would sufficiently express the idea…"；NHGRI："coined the term 'eugenics' in 1883" | ✅ |

## 三、孔多塞陪审团定理（1785）

来源：Condorcet, *Essai sur l'application de l'analyse à la probabilité des décisions rendues à la pluralité des voix*（1785）；现代表述用斯坦福哲学百科 "Jury Theorems" 与 "Social Choice Theory" 两个词条。

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 每人对的可能性略高于一半、彼此独立 → 人越多，多数越接近百分之百正确 | "the probability of majority correctness … increases in (odd) group size n and converges to 1"（前提：独立 + 能力 > ½） | ✅ |
| 不到一半 → 人越多，多数越可能错 | "if they are worse than random (p < 1/2) … the probability of a correct majority decision … converges to 0, as the jury size increases" | ✅ |
| 都跟着同一两个人投 → 人再多也不比那一两个人更可靠 | "If all individuals' votes are perfectly correlated with one another or mimic a small number of opinion leaders, the collective judgment is no more reliable than the judgment among a small number of independent individuals." | ✏️ 原简报"人越多错得越确定"用在"抄同一个人"上不准确，已按词条改写 |

## 四、雅典（公元前 399 年）

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 约 500 名公民陪审员 | 柏拉图没给人数；学界通常说 500 或 501 | ⚠️ 稿中说"大约 500" |
| 罪名：不敬城邦的神、败坏青年 | 《申辩篇》24b–c（Fowler 译）："Socrates is a wrongdoer because he corrupts the youth and does not believe in the gods the state believes in, but in other new spiritual beings." | ✅ |
| 七十岁 | 《申辩篇》17d 苏格拉底自称七十岁 | ✅ |
| （成片已删）在座很多人从小听着关于我的坏话长大 | 《申辩篇》18b–c：早年的控告者 "got hold of most of you from childhood" | ✅ |
| 再有三十票投到另一边，我就无罪了 | 《申辩篇》36a（Fowler 译）："if only thirty votes had been cast the other way, I should have been acquitted." | ✅ |
| 第二轮判死刑，比投有罪的多了八十票 | 第欧根尼·拉尔修《名哲言行录》2.42（Hicks 译）："Sentence of death was passed, with an accession of eighty fresh votes." | ⚠️ 这是公元 3 世纪传记作家的记载，稿中写明"据后来一位古代传记作家记载" |

## 五、玉米小斑病（1970）

来源：Balint-Kurti（美国农业部 ARS）& Pataky, *Phytopathology* 114(9): 2007–2016（2024，美国植物病理学会）；NASA NTRS 19720021767（1972）；Bruns, *Agronomy Journal* 109:1218（2017）。

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 1970 年约 85% 的商品玉米种子靠 T 型细胞质生产 | "In 1970, about 85% of corn seed planted commercially in the United States was produced by one of the two methods using cms-T." | ✏️ 稿中改为"约 85% 的商品玉米种子，都是靠它生产的"（不说"同一种玉米"，它们是不同杂交种、带同一种细胞质） |
| 新菌株专门对付 T 型细胞质 | race T of *Cochliobolus heterostrophus*（旧称 *Helminthosporium maydis*） | ✅ |
| 从南方（佛罗里达）往北，夏末到明尼苏达 | NASA："from late February to June, in Florida, Georgia, Alabama, Mississippi … By late August, the disease was found as far north as Minnesota" | ✅ |
| 减产约 15%，损失逾 10 亿美元 | Balint-Kurti & Pataky："nearly 700 million bushels lower than expected … a yield reduction of about 16% with an economic value of more than $1 billion (about $8 billion current value)"；Bruns 2017："destroying 15% of the crop at a cost of US$1.0 billion" | ⚠️ 各文献 15%–16%，稿中说"大约 15%" |
| 相当于今天的 80 多亿美元 | 美国劳工统计局 CPI-U 年均：1970 = 38.8；2025 = 321.943 → 10 亿 × 8.30 = 83 亿 | ✅（2025 年均值缺 10 月数据，影响可忽略） |

## 六、闪电崩盘（2010 年 5 月 6 日）

来源：SEC/CFTC 联合报告 *Findings Regarding the Market Events of May 6, 2010*（2010 年 9 月 30 日），https://www.cftc.gov/sites/default/files/idc/groups/public/@otherif/documents/ifdocs/staff-findings050610.pdf

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 14:32 一家大基金公司启动自动卖出程序，75,000 份 E-Mini 合约，约 41 亿美元 | "At 2:32 p.m. … a large fundamental trader (a mutual fund complex) initiated a sell program to sell a total of 75,000 E-Mini contracts (valued at approximately $4.1 billion)" | ✅（报告未点名，片中也不点名） |
| 按前一分钟成交量的 9% 卖，不看价格、不看时间 | "an execution rate set to 9% of the trading volume calculated over the previous minute, but without regard to price or time" | ✅ |
| "烫手山芋"；14 秒倒手 27,000 多份，净买进约 200 份 | "a 'hot-potato' volume effect … Between 2:45:13 and 2:45:27, HFTs traded over 27,000 contracts, which accounted for about 49 percent of the total trading volume, while buying only about 200 additional contracts net." | ✅ |
| 成交量越大卖得越快 | 报告：卖出程序随成交量上升而加快下单 | ✅ |
| 已跌 4% 之后，几分钟里又跌 5%–6% | "each already down over 4% from their prior-day close, suddenly plummeted a further 5-6% in a matter of minutes before rebounding almost as quickly" | ✅ |
| 道指一度比前一天收盘低近 1000 点（−9.16%，14:47） | 联合报告未给点数。SEC 主席 2010 年 5 月 20 日参议院证词："hitting 9,872.57 at 2:47 p.m., for a total drop of 9.16 percent from the previous day's close"；纽交所证词："an intraday decline of 998.5 points" | ⚠️ 片中写"比前一天收盘"低近 1000 点，不说"几分钟跌了 1000 点"（几分钟内的跌幅约 573 点） |
| 有的成交在 1 美分以下，有的 10 万美元一股 | "many of these trades were executed at prices of a penny or less, or as high as $100,000" | ✅ |
| 14:45:28 芝加哥期货交易所自动暂停 5 秒 | "At 2:45:28 p.m., trading on the E-Mini was paused for five seconds when the Chicago Mercantile Exchange ('CME') Stop Logic Functionality was triggered" | ✅ |
| 到三点左右大部分收回 | "from 2:45 p.m. to about 3:00 p.m. broad market indices recovered" | ✅ |
| 单只股票熔断：5 分钟涨跌超 10% → 全市场暂停 5 分钟 | SEC 2010-98 新闻稿（2010 年 6 月 10 日）："trading in a stock would pause across U.S. equity markets for a five-minute period in the event that the stock experiences a 10 percent change in price over the preceding five minutes"；6 月 11 日起分批实施，先覆盖标普 500 成分股 | ✅ |

## 七、45 分钟（骑士资本，2012 年 8 月 1 日）

来源：SEC 处罚令 Release No. 34-70694（2013 年 10 月 16 日），https://www.sec.gov/litigation/admin/2013/34-70694.pdf

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 45 分钟里成交 400 多万笔，154 只股票 | "SMARS routed millions of orders into the market over a 45-minute period, and obtained over 4 million executions in 154 stocks for more than 397 million shares" | ✅ |
| 8 台服务器有 1 台漏装新代码，旧程序被意外唤醒 | "one of Knight's technicians did not copy the new code to one of the eight SMARS computer servers"；"orders sent with the repurposed flag to the eighth server triggered the defective Power Peg code still present on that server" | ✅ |
| 亏损 4.6 亿多美元 | "Ultimately, Knight lost over $460 million from these unwanted positions." | ✏️ 一般报道 4.4 亿–4.6 亿；按 SEC 处罚令用"4.6 亿多" |
| 几天后靠投资者注资 4 亿美元 | Knight 2012 年 8 月 6 日公告："$400 million in equity financing" | ✅ |
| 第二年与另一家公司合并 | SEC 处罚令：2013 年 7 月 1 日 Knight Capital Group 与 GETCO 合并为 KCG Holdings | ✅（片中不点名） |

## 八、嫌弃"女子"二字的招聘机器（路透社 2018）

来源：Jeffrey Dastin, "Amazon scraps secret AI recruiting tool that showed bias against women", Reuters, 2018 年 10 月 10 日。

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 据知情人透露，2014 年起做简历自动打分程序 | "The team had been building computer programs since 2014 to review job applicants' resumes … five people familiar with the effort told Reuters." | ✅ |
| 学的是过去十年的简历，大多来自男性 | "trained to vet applicants by observing patterns in resumes submitted to the company over a 10-year period. Most came from men" | ✅ |
| 遇到"women's"扣分；两所女子大学毕业生被降分 | "It penalized resumes that included the word 'women's,' as in 'women's chess club captain.' And it downgraded graduates of two all-women's colleges" | ✅ |
| 改了程序，但无法保证不以别的方式歧视 | "Amazon edited the programs to make them neutral to these particular terms. But that was no guarantee that the machines would not devise other ways of sorting candidates that could prove discriminatory" | ✅ |
| 2017 年初团队解散 | "ultimately disbanded the team by the start of last year"（报道发于 2018 年） | ✅ |
| 知情人说：招聘人员看过推荐，但从没只靠排名 | "Amazon's recruiters looked at the recommendations generated by the tool … but never relied solely on those rankings, they said."（"they"是匿名知情人） | ✏️ 稿中写明是"知情人说" |
| 亚马逊方面表示：从没被招聘人员用来评估求职者 | 这句**不在**路透社原文里（路透社原文：亚马逊拒绝置评）。是发稿后亚马逊发言人对 The Verge 等媒体说的："This was never used by Amazon recruiters to evaluate candidates." | ✏️ 保留亚马逊的回应，但来源记为发言人事后表态 |

## 九、AI 时代的新证据

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 2021 年两位学者在 PNAS：大家都用同一个更准的算法，整体决策质量反而可能变差 | Kleinberg & Raghavan, "Algorithmic monoculture and social welfare", *PNAS* 118(22) e2018340118："monocultural convergence on a single algorithm … even when the algorithm is more accurate for any one agent in isolation, can reduce the overall quality of the decisions being made by the full collection of agents." | ✅ |
| 论文也提到另一层担心：被看走眼的人走到哪家都被拒 | 同文："If all employers or lenders use the same algorithm … particular applicants might find themselves locked out of the market when this shared algorithm doesn't like their application for some reason." | ✏️ 这是论文提到但没有展开的担心，不是它的结论（系统研究见 Bommasani 等，NeurIPS 2022）；稿中写"论文里也提到另一层担心" |
| 2024 年研究：大模型给新闻摘要打分，能一定程度认出自己写的，并倾向给自己打高分，哪怕人看来差不多 | Panickssery, Bowman, Feng, "LLM Evaluators Recognize and Favor Their Own Generations"（NeurIPS 2024）："self-preference, where an LLM evaluator scores its own outputs higher than others' while human annotators consider them of equal quality"；实验用 XSUM 与 CNN/DailyMail 新闻摘要 | ✅（片中不点具体模型名） |

## 十、联邦党人文集（1788）

来源：耶鲁 Avalon Project、美国国会图书馆文本；Founders Online 的 1788 年 McLean 版。

| 稿中说法 | 原文 | 状态 |
|---|---|---|
| 第 51 篇："如果人都是天使，就不需要政府了" | "If men were angels, no government would be necessary." | ✅ |
| 第 51 篇："要用野心对抗野心" | "Ambition must be made to counteract ambition." | ✅ |
| 第 55 篇："就算每个雅典公民都是苏格拉底……仍是乌合之众" | "Had every Athenian citizen been a Socrates, every Athenian assembly would still have been a mob." | ✅ |
| 1788 年；一般认为出自麦迪逊 | 第 51 篇 1788 年 2 月 6 日/8 日，第 55 篇 2 月 13 日/15 日（不同报纸）；Avalon/国会图书馆标"Hamilton or Madison"，Mosteller & Wallace（1963）统计研究支持麦迪逊 | ⚠️ 稿中说"一般认为出自麦迪逊之手" |

---

## 用词与边界自查（第一轮）

- 不出现"三权分立""宪政""宪法"；美国一段只说"美国建国时一批讨论怎么立规矩的文章"。✅
- 不讲内容审核、网络管理、监控、舆论、选举、任何国家的 AI 政策、当代政治。✅（"投票"只出现在古雅典陪审团、称牛比赛、孔多塞定理三处）
- 不点评今天任何 AI 公司；Nature 实验里的模型不提公司名；2024 年自评研究不提模型名。✅
- 亚马逊故事同时给出知情人说法与亚马逊回应。✅
- 不出现任何真实公司标志；所有图形均为程序绘制。✅
- "暴君""暴民"只在讲概念时出现，每次都紧跟 AI/历史的具体对象；没有用"暴政""独裁""专制"等词。✅
