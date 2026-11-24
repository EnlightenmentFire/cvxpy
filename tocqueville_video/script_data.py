# -*- coding: utf-8 -*-
"""《一个法国年轻人看美国小镇》—— 全片脚本（数据版）。

每一条 line:
  id     唯一编号
  k      'n' 旁白 / 'q' 引文的白话译文（配合法文字幕卡朗读，语速稍慢）
  say    给 TTS 的文本（数字写成汉字，必要时用同音字）
  sub    字幕文本（省略则同 say）
  fr     法文原文（只出字幕，不让中文 TTS 念）
  src    出处
  gap    这句之后的停顿（秒），默认 0.3
  cue    画面/音效提示（给渲染器）
"""

SCENES = []


def scene(sid, title, palette, lines, chapter=None):
    SCENES.append(dict(id=sid, title=title, palette=palette, chapter=chapter, lines=lines))


DA1 = "《论美国的民主》上卷"
DA2 = "《论美国的民主》下卷"
AR = "《旧制度与大革命》"

# ---------------------------------------------------------------- 0 冷启动
scene("s00", "冷启动", "sea", [
    dict(id="s00_01", k="n", say="一八三一年五月，一艘从法国开来的帆船，在美国罗德岛的纽波特靠了岸。",
         sub="1831 年 5 月，一艘从法国开来的帆船，在美国罗德岛的纽波特靠了岸。", cue="ship_arrive"),
    dict(id="s00_02", k="n", say="船上下来两个法国年轻人。一个二十五岁，一个二十九岁。", cue="two_figures"),
    dict(id="s00_03", k="n", say="他们带着法国政府的公函，差事写得清清楚楚：考察美国的新式监狱。", cue="letter"),
    dict(id="s00_04", k="n", say="他们确实去看了监狱。", gap=0.2),
    dict(id="s00_05", k="n", say="可这趟旅行真正留下来的，是他们在监狱外面看到的东西。", gap=0.6, cue="title_card"),
    dict(id="s00_06", k="n", say="二十五岁的那个，叫托克维尔。九个多月以后，他回到法国，写了一本书，想回答一个问题：自由，到底是从哪儿来的？",
         cue="map_route"),
    dict(id="s00_07", k="n", say="他找到的答案，不在首都，也不在宪法里。", gap=0.25),
    dict(id="s00_08", k="n", say="在小镇的路边。", gap=0.8),
])

# ---------------------------------------------------------------- 1 他是谁
scene("s01", "他是谁", "france", chapter="一 · 一个贵族家的孩子", lines=[
    dict(id="s01_01", k="n", say="托克维尔出身诺曼底的老贵族。他出生前十来年，大革命最血腥的那段日子里，他的父母被关进了监狱。",
         cue="prison_door"),
    dict(id="s01_02", k="n", say="他母亲的父亲、母亲、姐姐、姐夫，还有外祖父，都上了断头台。他的父母侥幸，恐怖统治一结束，才活着出来。",
         cue="guillotine_shadow"),
    dict(id="s01_03", k="n", say="家里人说，他父亲出狱的时候才二十二岁，头发已经全白了。", gap=0.5),
    dict(id="s01_04", k="n", say="所以这个年轻人从小就知道：一个国家，可以一夜之间翻天覆地。"),
    dict(id="s01_05", k="n", say="他对那个人人越来越平等的新时代，又怕，又好奇。", gap=0.5),
    dict(id="s01_06", k="n", say="一八三一年，他是凡尔赛法院里一个最低级的法官。他和同事博蒙向政府申请，去美国看监狱。差事是官方批的，路费得自己出。",
         sub="1831 年，他是凡尔赛法院里一个最低级的法官。他和同事博蒙向政府申请，去美国看监狱。差事是官方批的，路费得自己出。",
         cue="two_judges"),
    dict(id="s01_07", k="n", say="他们真的去看了：纽约的新新监狱，费城的东州监狱。在费城，他们一间牢房一间牢房地走，一个犯人一个犯人地问。",
         cue="prison_corridor"),
    dict(id="s01_08", k="n", say="可托克维尔在书的开头老实承认："),
    dict(id="s01_09", k="q", say="我在美国看到的，不只是美国。",
         fr="J’avoue que dans l’Amérique j’ai vu plus que l’Amérique ; j’y ai cherché une image de la démocratie elle-même…",
         src=DA1 + " · 绪论"),
    dict(id="s01_10", k="n", say="他想看清的，是一个人人平等的时代到底会长成什么样。因为法国，迟早也要走到这一步。"),
    dict(id="s01_11", k="n", say="他心里揣着一个问题：一个没有国王、没有贵族的国家，凭什么不乱？", gap=0.8),
])

# ---------------------------------------------------------------- 2 路被堵了
scene("s02", "路被堵了", "america", chapter="二 · 路被堵了", lines=[
    dict(id="s02_01", k="n", say="他在书里写过这样一个场面。", cue="road_empty"),
    dict(id="s02_02", k="n", say="路上出了个障碍。书里没说是什么，我们就当它是一棵倒下的大树吧。路断了，车马过不去。",
         cue="tree_falls"),
    dict(id="s02_03", k="n", say="那么，接下来会发生什么呢？", gap=0.4),
    dict(id="s02_04", k="n", say="邻居们马上凑到一块儿商量。这个临时凑起来的小会，选出几个人，去把事办了。",
         cue="neighbors_gather"),
    dict(id="s02_05", k="n", say="锯树，搬走，路通了。", cue="saw_clear", gap=0.4),
    dict(id="s02_06", k="q", say="在任何人想到，在他们这些当事人头上，还有一个现成的上级之前，事情已经解决了。",
         fr="… les voisins s’établissent aussitôt en corps délibérant ; de cette assemblée improvisée sortira un pouvoir exécutif qui remédiera au mal, avant que l’idée d’une autorité préexistante à celle des intéressés se soit présentée à l’imagination de personne.",
         src=DA1 + " · 第二部分第四章"),
    dict(id="s02_07", k="n", say="整个过程，没有一个人说：去找官府。", cue="office_dark", gap=0.5),
    dict(id="s02_08", k="n", say="这种习惯是从哪儿来的？托克维尔说，从学校就开始了。", cue="playground"),
    dict(id="s02_09", k="q", say="孩子们连玩游戏，都服从自己定下的规矩；犯了他们自己规定的错，就由他们自己来罚。",
         fr="… dès l’école, où les enfants se soumettent, jusque dans leurs jeux, à des règles qu’ils ont établies, et punissent entre eux des délits par eux-mêmes définis.",
         src=DA1 + " · 第二部分第四章"),
    dict(id="s02_10", k="n", say="这说明什么？在这里，“我们几个自己来”是第一反应，不是最后的办法。"),
    dict(id="s02_11", k="n", say="它不是哪天突然学会的，是从小在操场上、在路边，一回一回练出来的。", gap=0.8),
])

# ---------------------------------------------------------------- 3 自由的小学
scene("s03", "自由的小学", "america", chapter="三 · 自由的小学", lines=[
    dict(id="s03_01", k="n", say="那这些人平时在哪儿练？托克维尔的答案是：乡镇。", cue="town_wide"),
    dict(id="s03_02", k="n", say="乡镇是什么？就是一个几百到几千人的小镇。在美国东北角的新英格兰，一个镇一般两三千人。"),
    dict(id="s03_03", k="n", say="镇上没有议会，也没有镇长。每年开春，全镇有投票权的人聚到会堂里，开镇民大会。",
         cue="meeting_hall"),
    dict(id="s03_04", k="n", say="修哪条路，办不办学校，学校盖在哪儿，今年收多少钱，大家当场商量，举手表决。", cue="hands_up"),
    dict(id="s03_05", k="n", say="平时办事的，是大会选出来的几个行政委员。可他们想办件新事，比如盖一所学校，就得回到大会，让大家拍板。"),
    dict(id="s03_06", k="n", say="只要有十个人想提一件新事，就能要求召集全镇开会。"),
    dict(id="s03_07", k="n", say="除了行政委员，还有一长串小差事：估税的、收税的、管治安的、记录的、管穷人救济的、管学校的、管路的。托克维尔数了数，主要的就有十九种。",
         cue="offices_list"),
    dict(id="s03_08", k="n", say="选上了不干，要罚款。大多数差事给一点报酬，好让穷人也当得起。"),
    dict(id="s03_09", k="n", say="这样一来，管事就不是少数人的特权，而是镇上很多人都轮着干过的活儿。", cue="rotate", gap=0.5),
    dict(id="s03_10", k="n", say="于是，托克维尔写下了全书最有名的一句话："),
    dict(id="s03_11", k="q", say="乡镇对于自由，就像小学对于学问。它把自由放到老百姓够得着的地方，让人尝到自由平平和和的滋味，让人习惯去用它。",
         fr="Les institutions communales sont à la liberté ce que les écoles primaires sont à la science ; elles la mettent à la portée du peuple ; elles lui en font goûter l’usage paisible et l’habituent à s’en servir.",
         src=DA1 + " · 第一部分第五章", cue="quote_school"),
    dict(id="s03_12", k="q", say="没有乡镇这一层，一个国家也可以给自己弄出一个自由的政府，但它没有自由的精神。",
         fr="Sans institutions communales une nation peut se donner un gouvernement libre, mais elle n’a pas l’esprit de la liberté.",
         src=DA1 + " · 第一部分第五章"),
    dict(id="s03_13", k="n", say="他在说什么？自由不是写在纸上的一张证书，是一门要上的课。先在修路、办学这种小事上，学会商量、让步、选人、盯着选上的人，到了大事上，才用得上。"),
    dict(id="s03_14", k="n", say="他还说，乡镇好像是直接从上帝手里出来的，人一聚在一起，它自己就长出来了。可紧接着又说："),
    dict(id="s03_15", k="q", say="乡镇和人一样古老，可乡镇的自由，却稀罕，又脆弱。",
         fr="… la commune paraît sortir directement des mains de Dieu. Mais si la commune existe depuis qu’il y a des hommes, la liberté communale est chose rare et fragile.",
         src=DA1 + " · 第一部分第五章"),
    dict(id="s03_16", k="q", say="把乡镇的力量和独立拿走，你在那里只会找到被管的人，找不到自己做主的人。",
         fr="… ôtez la force et l’indépendance de la commune, vous n’y trouverez jamais que des administrés et point de citoyens.",
         src=DA1 + " · 第一部分第五章"),
    dict(id="s03_17", k="n", say="当然得说清楚：那时候能在镇民大会上举手的，基本只是成年白人男子。女人不能投票，黑人大多被挡在门外，印第安人更不在其中。托克维尔看到的，是这一部分人的自由。",
         cue="excluded"),
    dict(id="s03_18", k="n", say="这说明什么？自由的根，扎在小事里。而这门课，当时只有一部分人坐得进教室。", gap=0.8),
])

# ---------------------------------------------------------------- 4 十万人戒酒
scene("s04", "十万人戒酒", "america", chapter="四 · 十万人戒酒", lines=[
    dict(id="s04_01", k="n", say="在美国待得越久，托克维尔越发现，美国人不光在镇上自己办事。"),
    dict(id="s04_02", k="q", say="美国人，不论年纪、地位、想法，总在不停地凑到一起。",
         fr="Les Américains de tous les âges, de toutes les conditions, de tous les esprits, s’unissent sans cesse.",
         src=DA2 + " · 第二部分第五章"),
    dict(id="s04_03", k="n", say="办节庆、盖教堂、开客栈、印书、建医院、办学校，都是自己凑起来干的。"),
    dict(id="s04_04", k="n", say="有一件事，他一开始觉得好笑。", gap=0.3),
    dict(id="s04_05", k="q", say="我第一次在美国听说，十万人公开发誓不喝烈酒，觉得这事好笑多过严肃。",
         fr="La première fois que j’ai entendu dire aux États-Unis que cent mille hommes s’étaient engagés publiquement à ne pas faire usage de liqueurs fortes, la chose m’a paru plus plaisante que sérieuse…",
         src=DA2 + " · 第二部分第五章", cue="dots_gather"),
    dict(id="s04_06", k="n", say="他想不通：不喝就不喝呗，在自己家里喝白开水不就完了，干嘛要弄得人人都知道？"),
    dict(id="s04_07", k="n", say="后来他想明白了。这些人是眼看身边喝醉的人越来越多，怕了，要凑在一起，给清醒撑腰。"),
    dict(id="s04_08", k="n", say="接着，他补了一句："),
    dict(id="s04_09", k="q", say="要是这十万人住在法国，他们会每个人单独给政府写信，请政府去管全国的酒馆。",
         fr="… si ces cent mille hommes eussent vécu en France, chacun d’eux se serait adressé individuellement au gouvernement, pour le prier de surveiller les cabarets sur toute la surface du royaume.",
         src=DA2 + " · 第二部分第五章", cue="letters_fly"),
    dict(id="s04_10", k="n", say="同一个问题。一边的人想：我们自己凑起来办。另一边的人想：请上面来管。", cue="split_both"),
    dict(id="s04_11", k="q", say="一件新事情，在法国，你看到政府牵头；在英国，是大贵族牵头；在美国，你一定会看到一个自发的团体在牵头。",
         fr="Partout où, à la tête d’une entreprise nouvelle, vous voyez en France le gouvernement, et en Angleterre un grand seigneur, comptez que vous apercevrez aux États-Unis une association.",
         src=DA2 + " · 第二部分第五章"),
    dict(id="s04_12", k="n", say="为什么非得这样？他的解释很朴素："),
    dict(id="s04_13", k="q", say="在人人平等的地方，每个人都独立，也都弱小，一个人几乎什么也办不成。他们要是不学会自愿地互相帮忙，就全都会落到无能为力的地步。",
         fr="… tous les citoyens sont indépendants et faibles ; ils ne peuvent presque rien par eux-mêmes… Ils tombent donc tous dans l’impuissance s’ils n’apprennent à s’aider librement.",
         src=DA2 + " · 第二部分第五章"),
    dict(id="s04_14", k="n", say="没有贵族老爷能一声令下叫一群人干活，那就只能自己商量着来。所以他说："),
    dict(id="s04_15", k="q", say="在人人平等的国家，怎么凑到一起办事，是所有学问的母亲；别的学问能进步多少，都看这门学问。",
         fr="Dans les pays démocratiques, la science de l’association est la science mère ; le progrès de toutes les autres dépend des progrès de celle-là.",
         src=DA2 + " · 第二部分第五章"),
    dict(id="s04_16", k="n", say="他也看到了反方向的危险："),
    dict(id="s04_17", k="q", say="政府越是替人们把事都包了，人们就越忘了怎么自己凑起来办事，也就越离不开政府来帮。这是互为因果、停不下来的循环。",
         fr="Plus il se mettra à la place des associations, et plus les particuliers, perdant l’idée de s’associer, auront besoin qu’il vienne à leur aide : ce sont des causes et des effets qui s’engendrent sans repos.",
         src=DA2 + " · 第二部分第五章", cue="loop"),
    dict(id="s04_18", k="n", say="这说明什么？自己办事是一种习惯。用得越多越熟，交出去越多越生。它会自己长，也会自己萎缩。", gap=0.8),
])

# ---------------------------------------------------------------- 5 木屋里的书
scene("s05", "木屋里的书", "forest", chapter="五 · 木屋里的书", lines=[
    dict(id="s05_01", k="n", say="一八三一年七月，托克维尔和博蒙骑着马，钻进了密歇根的大森林。那时候，那里还是一片荒野。",
         sub="1831 年 7 月，托克维尔和博蒙骑着马，钻进了密歇根的大森林。那时候，那里还是一片荒野。", cue="forest_ride"),
    dict(id="s05_02", k="n", say="林子深处，偶尔冒出一块刚砍出来的空地，一间圆木搭的小屋，只开一扇窄窄的窗。", cue="cabin_ext"),
    dict(id="s05_03", k="n", say="你以为里面住的是没见过世面的穷汉？推门进去，粗糙的桌子上，摆着书和报纸。", cue="cabin_int"),
    dict(id="s05_04", k="n", say="主人穿着跟城里人一样的衣服，拉着他打听欧洲最近出了什么事，还在纸上给他画起了比利时该怎么打仗，又一本正经地告诉他，法国要兴旺，还得做些什么。"),
    dict(id="s05_05", k="q", say="拓荒的人，是带着圣经、一把斧头和几份报纸，走进新大陆的荒野的。",
         fr="… il s’enfonce dans les déserts du Nouveau-Monde avec la Bible, une hache et des journaux.",
         src=DA1 + " · 第二部分第九章", cue="bible_axe_paper"),
    dict(id="s05_06", k="q", say="几乎每间拓荒者的木屋里，都能找到几本零散的莎士比亚。我第一次读《亨利五世》，就是在一间圆木屋里。",
         fr="Il n’y a guère de cabane de pionnier où l’on ne rencontre quelques tomes dépareillés de Shakespeare. Je me rappelle avoir lu pour la première fois le drame féodal d’Henri V dans une log-house.",
         src=DA2 + " · 第一部分第十三章", cue="shakespeare"),
    dict(id="s05_07", k="n", say="这说明什么？这些住在天边的人关心公共的事，是因为公共的事真的归他们管。管得着，才会关心；关心了，才会去学。", gap=0.8),
])

# ---------------------------------------------------------------- 6 为什么是这里
scene("s06", "为什么是这里", "america", chapter="六 · 为什么偏偏是这里", lines=[
    dict(id="s06_01", k="n", say="为什么这种习惯，偏偏在这里长得这么旺？托克维尔找了好几层原因。"),
    dict(id="s06_02", k="n", say="第一层：在新英格兰，小镇比国家还老。", cue="layer1"),
    dict(id="s06_03", k="n", say="一六二〇年，第一批清教徒移民到了岸边，还在船上，就签下一份约定：大家自愿结成一个团体，一起定规矩，一起选管事的人。",
         sub="1620 年，第一批清教徒移民到了岸边，还在船上，就签下一份约定：大家自愿结成一个团体，一起定规矩，一起选管事的人。",
         cue="mayflower"),
    dict(id="s06_04", k="n", say="他们的教会，本来就是信徒自己管自己。到一六五〇年前后，新英格兰的乡镇已经完全成了形。",
         sub="他们的教会，本来就是信徒自己管自己。到 1650 年前后，新英格兰的乡镇已经完全成了形。"),
    dict(id="s06_05", k="q", say="在欧洲，政治生活是从上往下传的。在美国，先有乡镇，再有县，再有州，最后才有联邦。",
         fr="En Amérique, au contraire, on peut dire que la commune a été organisée avant le comté, le comté avant l’État, l’État avant l’Union.",
         src=DA1 + " · 第一部分第二章", cue="pyramid_up"),
    dict(id="s06_06", k="n", say="第二层：这里没有世袭的贵族，也没有一个远在天边、什么都管的衙门。", cue="layer2"),
    dict(id="s06_07", k="q", say="一个欧洲人在美国走一圈，最吃惊的，是看不到我们那种政府和衙门。一切都在转，可你哪儿也找不到那台发动机。",
         fr="Ce qui frappe le plus l’Européen qui parcourt les États-Unis, c’est l’absence de ce qu’on appelle chez nous le gouvernement ou l’administration… tout se meut autour de vous, et on ne découvre nulle part le moteur.",
         src=DA1 + " · 第一部分第五章"),
    dict(id="s06_08", k="n", say="第三层：地多，人少，衙门离得又远。路坏了，桥塌了，学校没人办，不自己动手，就真的没人管。", cue="layer3"),
    dict(id="s06_09", k="n", say="这说明什么？不是哪国人天生就会自己管自己。是历史、信仰和土地凑到了一起，让这里的人不得不练，也一直在练。", gap=0.8),
])

# ---------------------------------------------------------------- 7 一座钟楼
scene("s07", "一座钟楼", "oldfrance", chapter="七 · 一座钟楼", lines=[
    dict(id="s07_01", k="n", say="二十多年后，托克维尔写了另一本书，叫《旧制度与大革命》。他钻进法国各省的旧档案，想看看大革命以前，法国的村子是怎么过日子的。",
         cue="archives"),
    dict(id="s07_02", k="n", say="他吃了一惊：中世纪的时候，法国乡下的教区，和新英格兰的乡镇，原本是同一个出身。"),
    dict(id="s07_03", k="n", say="一个漂洋过海，离开了领主，自己当家，长成了新英格兰的乡镇；另一个留在原地，被国家的大手攥得紧紧的。"),
    dict(id="s07_04", k="q", say="说到底，两者长得很像，就像一个活人，像一个死人。",
         fr="Elles se ressemblent, en un mot, autant qu’un vivant peut ressembler à un mort.",
         src=AR + " · 第二编第三章"),
    dict(id="s07_05", k="n", say="大革命以前，一个法国村子，教堂屋顶被风掀了，神父住的房子墙要塌了，想修？", cue="village"),
    dict(id="s07_06", k="q", say="得等巴黎的御前会议下一道批文。离巴黎最远的村子，也一样。",
         fr="Il fallait un arrêt de ce conseil pour réparer le dommage que le vent venait de causer au toit de l’église ou relever le mur croulant du presbytère. La paroisse rurale la plus éloignée de Paris était soumise à cette règle comme les plus proches.",
         src=AR + " · 第二编第三章", cue="paper_route"),
    dict(id="s07_07", k="n", say="公文从村里出发，先到省里的总督，再到巴黎，批下来以后，再一层一层往回走。"),
    dict(id="s07_08", k="q", say="我见过有的村子，为了花二十五个里弗尔，也要向御前会议申请。",
         fr="J’ai vu des paroisses demander au conseil le droit de dépenser vingt-cinq livres.",
         src=AR + " · 第二编第三章"),
    dict(id="s07_09", k="n", say="要等多久？他翻遍了档案："),
    dict(id="s07_10", k="q", say="一个村子想重修钟楼、修补神父的住所，我从没见过不到一年就批下来的；多数要等两三年。",
         fr="… je n’ai jamais remarqué qu’il s’écoulât moins d’un an avant qu’une paroisse pût obtenir l’autorisation de relever son clocher ou de réparer son presbytère ; le plus souvent deux ou trois années se passent avant que la demande soit accordée.",
         src=AR + " · 第二编第六章", cue="calendar"),
    dict(id="s07_11", k="n", say="一个连修钟楼都要等巴黎点头的地方，老百姓遇到事，自然只会想：写信，求上面。"),
    dict(id="s07_12", k="n", say="更让他吃惊的是：大革命推翻了国王，废掉了贵族，可这套什么都往上报的做法，却原封不动地活了下来。"),
    dict(id="s07_13", k="q", say="它是旧制度的政治架构里，唯一挺过了大革命的那一块。",
         fr="… la seule portion de la constitution politique de l’ancien régime qui ait survécu à la Révolution…",
         src=AR + " · 第二编第二章"),
    dict(id="s07_14", k="n", say="这说明什么？王朝可以一夜倒掉，习惯却比王朝活得长。这不是谁好谁坏，是两种习惯：一种是“我们自己来”，一种是“请上面来管”。",
         gap=0.9),
])

# ---------------------------------------------------------------- 8 暗面一：一个圈
scene("s08", "暗面一", "gray", chapter="八 · 一个圈", lines=[
    dict(id="s08_01", k="n", say="讲到这里，好像托克维尔是来给美国唱赞歌的。可同一本书里，他写了一段很冷的话。", cue="circle_intro"),
    dict(id="s08_02", k="q", say="我不知道还有哪个国家，一般说来，比美国更缺少思想的独立和真正的讨论自由。",
         fr="Je ne connais pas de pays où il règne, en général, moins d’indépendance d’esprit et de véritable liberté de discussion qu’en Amérique.",
         src=DA1 + " · 第二部分第七章"),
    dict(id="s08_03", k="n", say="怎么会这样？"),
    dict(id="s08_04", k="q", say="在美国，多数人在思想的周围画了一个大圈。在圈里，作家是自由的；谁敢走出这个圈，就要倒霉。",
         fr="En Amérique, la majorité trace un cercle formidable autour de la pensée. Au-dedans de ces limites, l’écrivain est libre ; mais malheur à lui s’il ose en sortir.",
         src=DA1 + " · 第二部分第七章", cue="circle_draw"),
    dict(id="s08_05", k="n", say="倒什么霉？不是坐牢，也不是上火刑架。是另一种东西。", cue="step_out"),
    dict(id="s08_06", k="q", say="你可以不跟我想的一样。你的命、你的财产，都还是你的。但从今天起，你在我们中间，是个外人了。",
         fr="Vous êtes libre de ne point penser ainsi que moi ; votre vie, vos biens, tout vous reste ; mais de ce jour vous êtes un étranger parmi nous.",
         src=DA1 + " · 第二部分第七章", cue="turn_backs"),
    dict(id="s08_07", k="n", say="骂他的人大声说话。和他想法一样的人，没有他的胆量，一个个不吭声，躲开了。"),
    dict(id="s08_08", k="q", say="他让步了，终于在日复一日的压力下弯了腰，回到沉默里，好像说了真话，是件让他后悔的事。",
         fr="Il cède, il plie enfin sous l’effort de chaque jour, et rentre dans le silence, comme s’il éprouvait des remords d’avoir dit vrai.",
         src=DA1 + " · 第二部分第七章", cue="bubble_shrink"),
    dict(id="s08_09", k="n", say="他在说什么？一群自己管自己的人抱成一团的时候，也会变成压人的那一方。压人用的不是铁链，是冷眼。"),
    dict(id="s08_10", k="q", say="在我们这个时代，少数人也能凑到一起、发出声音的权利，成了对付多数人暴政必不可少的保障。",
         fr="De notre temps, la liberté d’association est devenue une garantie nécessaire contre la tyrannie de la majorité.",
         src=DA1 + " · 第二部分第四章"),
    dict(id="s08_11", k="n", say="这说明什么？自己管自己，不等于公道。多数人的手，也得有东西拦着。", gap=1.0),
])

# ---------------------------------------------------------------- 9 暗面二：孟菲斯的冬天
scene("s09", "孟菲斯的冬天", "ice", chapter="九 · 孟菲斯的冬天", lines=[
    dict(id="s09_01", k="n", say="一八三一年十二月，托克维尔和博蒙一路往南，被困在密西西比河边一个叫孟菲斯的小地方。",
         sub="1831 年 12 月，托克维尔和博蒙一路往南，被困在密西西比河边一个叫孟菲斯的小地方。", cue="ice_river"),
    dict(id="s09_02", k="n", say="那年冬天冷得出奇。地上的雪冻得梆硬，河面上漂着大块的冰。"),
    dict(id="s09_03", k="n", say="一天，林子里传来鼓声、马嘶和狗叫。一大群乔克托人走了出来，老人、妇女、孩子，带着全部家当，由一个政府派来的人领着。",
         cue="column_arrives"),
    dict(id="s09_04", k="n", say="乔克托人世世代代住在大河东边。经过长时间的谈判，他们被劝着、也被逼着签了约，要搬到大河西边去。已经有六七千人过了河。"),
    dict(id="s09_05", k="n", say="这群人来孟菲斯，是要上船，跟着同胞往西走。托克维尔也搭上了这条船。"),
    dict(id="s09_06", k="n", say="他在给母亲的信里写：有一个据说一百一十岁的老妇人，只裹着一条毯子，由两三代孙辈搀着上了船。", cue="boarding"),
    dict(id="s09_07", k="n", say="还有一个姑娘，一个星期前摔断了胳膊，没人医治，也只能跟着队伍走。"),
    dict(id="s09_08", k="n", say="后来，他在书里写："),
    dict(id="s09_09", k="q", say="这一大群人里，听不到哭声，也听不到抱怨。他们沉默着。",
         fr="On n’entendait parmi cette foule assemblée ni sanglots ni plaintes ; ils se taisaient.",
         src=DA1 + " · 第二部分第十章"),
    dict(id="s09_10", k="q", say="他们的苦难由来已久，他们觉得，已经无可挽回。",
         fr="Leurs malheurs étaient anciens et ils les sentaient irrémédiables.",
         src=DA1 + " · 第二部分第十章"),
    dict(id="s09_11", k="n", say="人都上了船。狗还留在岸上。", cue="dogs_shore", gap=0.6),
    dict(id="s09_12", k="q", say="等它们终于明白，主人要永远离开了，它们一齐发出可怕的长嚎，一起跳进冰冷的密西西比河，跟着船游。",
         fr="… lorsque ces animaux virent enfin qu’on allait s’éloigner pour toujours, ils poussèrent ensemble d’affreux hurlements, et s’élançant à la fois dans les eaux glacées du Mississipi, ils suivirent leurs maîtres à la nage.",
         src=DA1 + " · 第二部分第十章", cue="dogs_howl", gap=2.6),
    dict(id="s09_13", k="n", say="船上有一个会说英语的乔克托人。托克维尔问他，你们为什么要离开家乡？", cue="question"),
    dict(id="s09_14", k="n", say="他只回答了一句：为了自由。", gap=1.0),
    dict(id="s09_15", k="n", say="托克维尔说，别的话，他一句也问不出来。", gap=1.0),
    dict(id="s09_16", k="n", say="在书里，托克维尔用最冷的反话，写下了这件事。美国人做成这件事，"),
    dict(id="s09_17", k="q", say="安安静静，合法合规，满怀善意，不流一滴血，在世人眼里，没违背任何一条重大的道德原则。要毁掉一群人，没有比这更尊重人道法则的办法了。",
         fr="… tranquillement, légalement, philanthropiquement, sans répandre de sang, sans violer un seul des grands principes de la morale aux yeux du monde. On ne saurait détruire les hommes en respectant mieux les lois de l’humanité.",
         src=DA1 + " · 第二部分第十章"),
    dict(id="s09_18", k="n", say="他在说什么？条约签了，法律讲了，程序走了。结果一样是一个民族，被赶出了祖先的土地。"),
    dict(id="s09_19", k="n", say="同一章里，他也写了南方的奴隶制，认为那是威胁这个国家前途的最大祸患。"),
    dict(id="s09_20", k="n", say="这说明什么？自己管自己的人，也可能一起把别人赶出家园。多数人抱成一团，并不保证公道。", gap=0.6),
    dict(id="s09_21", k="n", say="托克维尔自己也不是完人。他觉得女人就该守着家；后来当了议员，还支持法国在阿尔及利亚的殖民战争。他看得清别人的暗处，自己也有看不见的地方。",
         gap=1.0),
])

# ---------------------------------------------------------------- 10 收尾
scene("s10", "收尾", "dawn", chapter="十 · 一门手艺", lines=[
    dict(id="s10_01", k="n", say="一八三二年二月，两个年轻人从纽约上船，回了法国。",
         sub="1832 年 2 月，两个年轻人从纽约上船，回了法国。", cue="ship_leave"),
    dict(id="s10_02", k="n", say="一八三五年，托克维尔出版了《论美国的民主》上卷；一八四〇年，出了下卷。",
         sub="1835 年，托克维尔出版了《论美国的民主》上卷；1840 年，出了下卷。", cue="books"),
    dict(id="s10_03", k="n", say="他一辈子都在想同一个问题：人和人越来越平等的时候，怎么才能不被一个什么都管的大力量吞掉，也不被多数人淹没？"),
    dict(id="s10_04", k="n", say="他担心的那种大力量，不打人，也不骂人。它替你操心一切。"),
    dict(id="s10_05", k="q", say="它像父亲的权力，如果它的目的是让人长大成人的话；可它恰恰相反，只想把人永远留在童年。",
         fr="Il ressemblerait à la puissance paternelle, si, comme elle, il avait pour objet de préparer les hommes à l’âge viril ; mais il ne cherche, au contraire, qu’à les fixer irrévocablement dans l’enfance…",
         src=DA2 + " · 第四部分第六章"),
    dict(id="s10_06", k="n", say="小学，是让人长大的地方。包办一切，是让人长不大的办法。"),
    dict(id="s10_07", k="n", say="他给的答案并不复杂：别把小事全交出去。", gap=0.9),
    dict(id="s10_08", k="n", say="自由不是一句口号，是一门手艺。", cue="final1", gap=0.6),
    dict(id="s10_09", k="n", say="手艺是在修路、办学、开会这种小事里练出来的。", cue="final2", gap=0.6),
    dict(id="s10_10", k="n", say="什么都等别人来管，人就会慢慢忘了，怎么自己管自己。", cue="final3", gap=2.0),
])


def all_lines():
    for s in SCENES:
        for i, ln in enumerate(s["lines"]):
            d = dict(ln)
            d.setdefault("sub", d["say"])
            d.setdefault("gap", 0.3)
            d["scene"] = s["id"]
            d["idx"] = i
            yield d


if __name__ == "__main__":
    import re
    n = 0
    for d in all_lines():
        n += len(re.sub(r"[，。？！：；、“”《》\s]", "", d["say"]))
    print("lines:", sum(len(s['lines']) for s in SCENES), "chars:", n)
