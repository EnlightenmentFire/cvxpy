# -*- coding: utf-8 -*-
"""东印度公司 — script data. Each scene: id, chapter, lines.
line: t = subtitle text (digits allowed); say = narration override; q = quote card; cue = visual cue; gap = pause after.
Narration text is derived from t by num_say() unless `say` is given.
"""
import re

SCENES = [
 dict(id="s0", chapter="", lines=[
  dict(t="1757年，一场打了不到一天的仗，让一家伦敦的贸易公司，开始统治一片比英国还大的土地。", cue="open"),
  dict(t="这一天是6月23日，地点是孟加拉的普拉西。", cue="title"),
  dict(t="一边是孟加拉纳瓦布的大军，大约5万人，50多门大炮，还有战象。", cue="nawab"),
  dict(t="另一边，是东印度公司的部队，大约3000人，其中三分之二是印度士兵。", cue="company"),
  dict(t="中午，一场暴雨。公司的炮兵用油布盖住火药，对面的火药，湿透了。", cue="rain"),
  dict(t="可真正决定胜负的，不是这场雨，而是战场上有一支大军，从头到尾，一枪没放。", cue="grey"),
  dict(t="当天下午，纳瓦布骑着骆驼逃离战场。公司一方，阵亡不过二十来人。", cue="flee"),
  dict(t="8年之后，莫卧儿皇帝把孟加拉、比哈尔、奥里萨三省的征税权，交给了这家公司。", cue="diwani"),
  dict(t="到1803年，它手里的军队有20多万人，大约是英国本土常备军的两倍。", cue="army"),
  dict(t="而它在伦敦利德贺街的总部，楼面只有五扇窗那么宽；公司成立一百年时，总部的正式职员只有35人。", cue="hq"),
  dict(t="一家公司，怎么会有自己的军队、法庭和税收？", cue="question"),
  dict(t="这一期不只讲故事，更讲机制：股东、董事、驻印度的职员和英国议会，四方的算盘怎么错了位，把一家做买卖的公司，一步步推成了一个政府。", cue="nodes"),
  dict(t="亚当·斯密为这件事下过一句很重的判断，我们放在最后。", cue="smith_tease"),
 ]),
 dict(id="s1", chapter="一纸特许状", lines=[
  dict(t="故事要从150多年前说起。", cue="charter"),
  dict(t="1600年的最后一天，12月31日，伊丽莎白一世在一张羊皮纸上盖了印。", cue="seal"),
  dict(t="拿到特许状的，是一群伦敦商人，公司的全名叫“伦敦商人对东印度贸易的总督与公司”。", cue="name"),
  dict(t="特许状给了他们一样最值钱的东西：好望角以东的贸易，只有他们能做，期限15年。", cue="monopoly"),
  dict(t="为什么要垄断？因为这门生意风险太大。", cue="route0"),
  dict(t="一条船从泰晤士河出发，绕过好望角进入印度洋，单程就要五六个月，一来一回，常常要一年半以上。", cue="route"),
  dict(t="船可能沉，可能遇上海盗，也可能撞上葡萄牙人和荷兰人的炮。", cue="risk"),
  dict(t="所以商人们凑钱入股，赚了按股分，亏了一起扛。这就是股份公司早期的样子。", cue="shares"),
  dict(t="两年后，1602年，荷兰人成立了联合东印度公司，资本大约是英国公司的十倍，而且一开始就带着宣战、缔约、建要塞的授权。", cue="voc"),
  dict(t="英国公司起初是一次航行凑一次钱，回来就分账散伙，到1657年，才有了长期的股本。", cue="voyages"),
  dict(t="但特许状这条路，本身就埋着另一颗种子。", cue="seed"),
  dict(t="17世纪60年代以后，英国王室陆续授权公司：可以对非基督教的君主宣战媾和，可以铸币、驻军、建要塞，还可以审判。", cue="powers"),
  dict(t="美国历史学家菲利普·斯特恩，把它叫做“公司国家”。", cue="stern"),
  dict(t="他认为，东印度公司从17世纪起就把自己当成一个政治体，不是到了18世纪才意外变成政府。", cue="stern2"),
  dict(t="另一位历史学家达尔林普尔讲法不同：在他笔下，这是一家商业公司，在莫卧儿帝国崩塌的乱局里，一步步滑向了帝国。", cue="dalrymple"),
  dict(t="两种说法哪个更对？先记住这个问题，往下看机制。", cue="debate"),
 ]),
 dict(id="s2", chapter="从商栈到要塞", lines=[
  dict(t="公司在印度落脚，靠的是三个据点。", cue="forts0"),
  dict(t="东南海岸的马德拉斯，1640年前后建起了圣乔治堡。", cue="madras"),
  dict(t="西海岸的孟买，原是葡萄牙公主嫁给英王查理二世的嫁妆，1668年转租给公司，年租金10英镑。", cue="bombay"),
  dict(t="东边恒河三角洲上的加尔各答，1690年开埠，后来修起了威廉堡。", cue="calcutta"),
  dict(t="起初，它们只是商栈：仓库、码头、账房，外加几门看护仓库的炮。", cue="factory"),
  dict(t="可1707年奥朗则布皇帝死后，莫卧儿帝国开始碎裂。", cue="mughal"),
  dict(t="各省总督各自为政，马拉塔人四处征战，1739年，波斯的纳迪尔沙还攻破了德里。", cue="chaos"),
  dict(t="秩序一乱，保护生意就要花钱：要塞要加固，兵要多招。", cue="cost"),
  dict(t="这时，法国东印度公司的总督杜布雷先走了一步棋：招募印度士兵，用欧洲的方式操练，再把这支部队借给地方王公打仗。", cue="dupleix"),
  dict(t="王公付不起现钱，就把一片土地的税收划给公司抵账。", cue="land"),
  dict(t="英国人很快学会了这一套。机制在这里第一次转了弯：保护贸易的武力成本，变成了出租武力的生意。", cue="mech1"),
  dict(t="还有一个漏洞。早在1717年，莫卧儿皇帝颁下敕令，公司在孟加拉的货物免缴关税，凭公司的通行证放行。", cue="dastak"),
  dict(t="公司职员薪水不高，却拿着这张通行证做自己的私人生意，逃掉本该交给孟加拉的税。", cue="private"),
  dict(t="1756年，年轻的西拉杰·乌德-达乌拉继位，做了孟加拉的纳瓦布。", say="一七五六年，年轻的西拉杰乌德达乌拉继位，做了孟加拉的纳瓦布。", cue="siraj"),
  dict(t="他不满公司私自加固加尔各答，又滥用免税通行证，当年6月，出兵攻下了加尔各答。", cue="fall"),
  dict(t="第二年1月，克莱武带着马德拉斯的援军夺回了城。", cue="clive"),
  dict(t="克莱武本是公司的一个小文书，后来转去带兵。这一次，他没打算只把城夺回来。", cue="clive2"),
 ]),
 dict(id="s3", chapter="普拉西：一场算好的仗", lines=[
  dict(t="纳瓦布的宫廷里，有不少人想换掉他。", cue="court"),
  dict(t="一位是掌管军饷的统帅，米尔·贾法尔。", say="一位是掌管军饷的统帅，米尔贾法尔。", cue="jafar"),
  dict(t="一个是孟加拉最大的银行家族，贾加特·塞特，他们担心年轻的纳瓦布会动他们的钱。", say="一个是孟加拉最大的银行家族，贾加特塞特，他们担心年轻的纳瓦布会动他们的钱。", cue="seth"),
  dict(t="1757年6月初，公司和米尔·贾法尔签下密约：打掉西拉杰，扶他上位；他则向公司和公司职员支付巨额补偿。", say="一七五七年六月初，公司和米尔贾法尔签下密约：打掉西拉杰，扶他上位；他则向公司和公司职员支付巨额补偿。", cue="pact"),
  dict(t="所以普拉西这一仗，开打之前，账就已经算好了一半。", cue="pact2"),
  dict(t="6月23日清晨，克莱武的部队背靠一片芒果林，旁边是胡格利河的河湾。", cue="b_grove"),
  dict(t="纳瓦布的大军摆成一道大弧线，从三面压过来。", cue="b_arc"),
  dict(t="离公司最近的左翼，正是米尔·贾法尔的部队。", say="离公司最近的左翼，正是米尔贾法尔的部队。", cue="b_left"),
  dict(t="双方对轰了几个小时，谁也没占到便宜。", cue="b_cannon"),
  dict(t="中午，暴雨来了。公司用油布盖住弹药，纳瓦布的火药大多湿透，炮火一下子稀了。", cue="b_rain"),
  dict(t="纳瓦布最忠诚的将领米尔·马丹，以为对面的炮也哑了，带着骑兵冲锋，迎面撞上霰弹，受了致命伤。", say="纳瓦布最忠诚的将领米尔马丹，以为对面的炮也哑了，带着骑兵冲锋，迎面撞上霰弹，受了致命伤。", cue="b_charge"),
  dict(t="西拉杰慌了，把米尔·贾法尔叫进大帐，据说把自己的头巾扔在他脚下，求他守住这份尊严。", say="西拉杰慌了，把米尔贾法尔叫进大帐，据说把自己的头巾扔在他脚下，求他守住这份尊严。", cue="b_turban"),
  dict(t="米尔·贾法尔满口答应，转身就派人给克莱武送信，催他进攻。", say="米尔贾法尔满口答应，转身就派人给克莱武送信，催他进攻。", cue="b_letter"),
  dict(t="西拉杰听了身边人的劝，骑上骆驼，先回了首都穆尔希达巴德。", cue="b_flee"),
  dict(t="大军没了主帅，阵线开始松动。公司部队向前推进，纳瓦布的营地被攻破。", cue="b_advance"),
  dict(t="而米尔·贾法尔的那一大片部队，从头到尾站在原地，最后跟着撤出了战场。", say="而米尔贾法尔的那一大片部队，从头到尾站在原地，最后跟着撤出了战场。", cue="b_grey"),
  dict(t="账面上是5万对3000，真正和公司交过手的，只是忠于纳瓦布的一小部分。", cue="b_count"),
  dict(t="公司一方，阵亡22人，伤50人。", cue="b_loss"),
  dict(t="与其说这是一场战斗，不如说是一笔交易。战场，只是交割的地点。", cue="b_deal"),
  dict(t="几天后，西拉杰被米尔·贾法尔的儿子杀死。新纳瓦布开始兑现承诺。", say="几天后，西拉杰被米尔贾法尔的儿子杀死。新纳瓦布开始兑现承诺。", cue="pay"),
  dict(t="第一笔75拉克卢比，将近一百万英镑，装上两百条船，奏着乐，顺河运回加尔各答。", say="第一笔七十五拉克卢比，将近一百万英镑，装上两百条船，奏着乐，顺河运回加尔各答。", cue="boats"),
  dict(t="克莱武个人拿到大约23万英镑，外加一块每年收租约3万英镑的封地。", cue="clive_money"),
  dict(t="有个英文单词，就是在这个年代从印地语进入英语的：loot，抢来的财物。", say="有个英文单词，就是在这个年代从印地语进入英语的：loot，抢来的财物。", cue="loot"),
 ]),
 dict(id="s4", chapter="迪瓦尼：从买卖到收税", lines=[
  dict(t="扶起来的纳瓦布，很快就成了提款机。", cue="atm"),
  dict(t="从1757年到1765年，历任纳瓦布以“政治礼物”的名义付给公司和职员的钱，估计约有250万英镑。", cue="gifts"),
  dict(t="米尔·贾法尔付不出钱，1760年，公司换上了他的女婿米尔·卡西姆。", say="米尔贾法尔付不出钱，一七六零年，公司换上了他的女婿米尔卡西姆。", cue="qasim"),
  dict(t="米尔·卡西姆想做真正的统治者，干脆取消了所有商人的关税，公司职员的免税特权一下子没了优势。", say="米尔卡西姆想做真正的统治者，干脆取消了所有商人的关税，公司职员的免税特权一下子没了优势。", cue="duty"),
  dict(t="战争随之爆发。1764年10月，在布克萨尔，公司击败了米尔·卡西姆、奥德的纳瓦布和莫卧儿皇帝沙·阿拉姆二世的联军。", say="战争随之爆发。一七六四年十月，在布克萨尔，公司击败了米尔卡西姆、奥德的纳瓦布和莫卧儿皇帝沙阿拉姆二世的联军。", cue="buxar"),
  dict(t="1765年8月12日，阿拉哈巴德，克莱武的营帐里，举行了一场仪式。", cue="tent"),
  dict(t="据记载，皇帝的宝座，是一把搭着布的扶手椅，摆在一张英国式的餐桌上。", cue="chair"),
  dict(t="皇帝把“迪瓦尼”，也就是孟加拉、比哈尔、奥里萨三省的财政和征税权，授予公司。", cue="grant"),
  dict(t="敕令写明，这个职位交给公司，世世代代，永远不得撤换。", cue="forever"),
  dict(t="公司的回报，是每年给皇帝26拉克卢比的贡金。", cue="tribute"),
  dict(t="这一下，公司的账本换了一栏。", cue="ledger0"),
  dict(t="过去，它要从英国运白银到印度，才买得到棉布和生丝。", cue="ledger_silver"),
  dict(t="现在，孟加拉的田赋直接进了公司金库：用孟加拉的税，买孟加拉的布，再运到伦敦去卖。", cue="ledger_tax"),
  dict(t="收入的来源，从市场竞争，变成了行政垄断。做买卖要讨好客户，收税只需要握住入口。", cue="mech2"),
  dict(t="克莱武还设计了所谓的“双重政府”：税归公司收，治理的责任，名义上还留在纳瓦布身上。", cue="dual"),
  dict(t="权力和责任，就这样被拆开了。", cue="dual2"),
  dict(t="亚当·斯密看穿了其中的矛盾。他在《国富论》里写道：", cue="smith1"),
  dict(t="“作为君主，公司的利益和它统治的国家完全一致；作为商人，它的利益恰恰与之相反。”", k="q", cue="q_smith1",
       q=dict(en="As sovereigns, their interest is exactly the same with that of the country which they govern. As merchants their interest is directly opposite to that interest.",
              src="亚当·斯密《国富论》卷四 第七章 第三节（1776）")),
  dict(t="一个想低买高卖的商人，偏偏坐上了本该让百姓富起来的君主之位。", cue="smith1b"),
 ]),
 dict(id="s5", chapter="代价与反噬", lines=[
  dict(t="矛盾很快以最残酷的方式爆发。", cue="drought0"),
  dict(t="1769年，孟加拉和比哈尔的雨季几乎没有下雨。第二年，大饥荒来了。", cue="drought"),
  dict(t="死了多少人？当时公司的说法是三分之一的人口，后来被推算成上千万；现代学者认为这很可能被夸大，估计从一百多万到上千万不等，至今没有定论。", cue="toll"),
  dict(t="据19世纪史家亨特整理的公司档案，饥荒那一年，田赋减免不到百分之五，第二年反而加征了百分之十。", cue="remit"),
  dict(t="但有一份文件，几乎不需要解读。", cue="doc0"),
  dict(t="1772年11月3日，黑斯廷斯主持的加尔各答参事会，在给伦敦董事会的信里写道：", cue="doc"),
  dict(t="“尽管本省至少损失了三分之一的居民，1771年的净征收，仍然超过了1768年。”", k="q", cue="q_hastings",
       q=dict(en="notwithstanding the loss of at least one-third of the Inhabitants of the Province, and the consequent decrease of the Cultivation, the nett collections of the year 1771 exceeded even those of 1768",
              src="加尔各答参事会致董事会函，1772年11月3日（据 W. W. Hunter《孟加拉农村年鉴》）")),
  dict(t="人少了三分之一，税反而收得更多。", cue="doc2"),
  dict(t="钱去了哪里？一部分变成股东的分红，一部分填进越来越贵的军费，还有很大一部分，进了职员自己的口袋。", cue="flows"),
  dict(t="发了财的职员回到英国，被人叫做“纳勃布”，他们买庄园，买议席。", cue="nabob"),
  dict(t="公司本身，却在1772年的信用危机里周转不灵，只好向英国政府求援。", cue="crisis"),
  dict(t="1773年，议会借给公司140万英镑，同时通过《管理法》：设孟加拉总督，在加尔各答设最高法院，第一任总督就是黑斯廷斯。", cue="regulating"),
  dict(t="同一年，为了帮公司清掉积压的茶叶，议会又通过《茶叶法》；几个月后，波士顿的茶叶被倒进了海里。", cue="tea"),
  dict(t="克莱武本人也被叫到议会接受质询。他说，普拉西之后，一位君主听凭他发落，银行家争相讨好他，满库的金银只为他一人打开。", cue="clive_q0"),
  dict(t="“主席先生，此刻，我对自己的克制，感到惊讶。”", k="q", cue="q_clive",
       q=dict(en="Mr. Chairman, at this moment I stand astonished at my own moderation!",
              src="克莱武在下院特别委员会的答辩（1772）")),
  dict(t="斯密的判断更冷。他说，这是一种很奇特的政府：每个官员都想尽快离开这个国家；等他带着全部财产走了，哪怕这个国家被地震吞没，也与他无关。", cue="q_smith2",
       q=dict(en="It is a very singular government in which every member of the administration wishes to get out of the country... it is perfectly indifferent though the whole country was swallowed up by an earthquake.",
              src="亚当·斯密《国富论》卷四 第七章 第三节")),
  dict(t="斯密还特意说明：他指责的不是哪个人的品格，而是这些人所处的位置和制度。", cue="system"),
  dict(t="两千多年前，孟子对梁惠王讲过同一个道理：上下交征利，而国危矣。", k="q", cue="q_mencius",
       q=dict(zh="上下交征利而國危矣。", src="《孟子·梁惠王上》")),
  dict(t="上上下下都在争夺私利，国家就危险了。", cue="mencius2"),
  dict(t="公司的困境正在这里：命令从伦敦出发，单程要走五六个月；钱，却当场就进了个人的口袋。", cue="lag"),
  dict(t="1784年，《印度法》设立监督委员会，公司的重大决策，从此要受英国政府管束。", cue="india_act"),
 ]),
 dict(id="s6", chapter="收束：谁在做决定", lines=[
  dict(t="1788年2月，伦敦威斯敏斯特大厅，议会对卸任的黑斯廷斯发起弹劾。", cue="westminster"),
  dict(t="主控官伯克一连讲了四天。开场演说的结尾，他这样说：", cue="burke0"),
  dict(t="“我以印度人民的名义弹劾他：他颠覆了他们的法律、权利与自由，毁掉了他们的财产，让他们的国土荒芜凋零。”", k="q", cue="q_burke",
       q=dict(en="I impeach him in the name of the people of India, whose laws, rights and liberties he has subverted; whose properties he has destroyed; whose country he has laid waste and desolate.",
              src="伯克，弹劾黑斯廷斯开场演说（1788年2月）")),
  dict(t="审判拖了七年。1795年，黑斯廷斯被宣告无罪。", cue="acquit"),
  dict(t="但风向已经变了，议会一点点把公司的权力收了回去。", cue="tide"),
  dict(t="1813年，公司失去了对印度贸易的垄断；1833年，它干脆停止了一切商业活动。", cue="t1813"),
  dict(t="一家公司，不做生意了，只剩下统治。", cue="t1833"),
  dict(t="1857年，公司军队里的印度士兵发动大起义，战火烧遍北印度。", cue="t1857"),
  dict(t="第二年，英国议会立法，统治权移交王室。1874年，东印度公司正式解散。", cue="t1874"),
  dict(t="回到开头的问题：它是意外滑成了帝国，还是从一开始就是一个政治体？", cue="debate2"),
  dict(t="也许两种说法各对一半：特许状给了它当政府的工具，莫卧儿的崩塌给了它机会，而股东、董事、职员各自的算盘，把它一步一步推了过去。", cue="synth"),
  dict(t="放到今天的工作里，有一个判断可以带走：", cue="lesson0"),
  dict(t="当一个团队的收入，从赢得客户变成掌握垄断入口，它的动作就会悄悄从“服务”变成“征收”。", cue="lesson1"),
  dict(t="分清命令链和钱的流向，才看得清，到底是谁在做决定。", cue="lesson2"),
  dict(t="最后，是亚当·斯密那句话。他写这句时说的是丹麦公司治理加勒比海的小岛，但在同一章里，他用了大量篇幅批评英国东印度公司。", cue="smith_ctx"),
  dict(t="“由一家拥有专营权的商人公司来当政府，可能是任何国家所能遇到的最坏的政府。”", k="q", cue="q_smith_final",
       q=dict(en="The government of an exclusive company of merchants is, perhaps, the worst of all governments for any country whatever.",
              src="亚当·斯密《国富论》卷四 第七章 第二节（1776）")),
 ]),
]

CN = "零一二三四五六七八九"

def _int_cn(n):
    if n == 0:
        return "零"
    units = [(100000000, "亿"), (10000, "万"), (1000, "千"), (100, "百"), (10, "十")]
    def under10k(m):
        s = ""; zero = False
        for v, u in [(1000, "千"), (100, "百"), (10, "十"), (1, "")]:
            d = m // v; m %= v
            if d:
                if zero and s: s += "零"
                s += CN[d] + u; zero = False
            else:
                zero = True
        return s
    if n >= 10000:
        hi, lo = divmod(n, 10000)
        s = under10k(hi) + "万"
        if lo:
            s += ("零" if lo < 1000 else "") + under10k(lo)
        return s
    s = under10k(n)
    if s.startswith("一十"):
        s = s[1:]
    return s

def num_say(t):
    t = re.sub(r"(\d{4})(?=年)", lambda m: "".join(CN[int(c)] for c in m.group(1)), t)
    t = re.sub(r"\d+", lambda m: _int_cn(int(m.group(0))), t)
    t = t.replace("·", "").replace("“", "").replace("”", "").replace("《", "").replace("》", "")
    return t

def all_lines():
    out = []
    for s in SCENES:
        for i, d in enumerate(s["lines"]):
            d = dict(d)
            d["id"] = f"{s['id']}_{i:02d}"
            d.setdefault("k", "n")
            d["scene"] = s["id"]
            d["say"] = d.get("say") or num_say(d["t"])
            d["say"] = d["say"].replace("“", "").replace("”", "")
            out.append(d)
    return out

if __name__ == "__main__":
    L = all_lines()
    tot = 0
    for d in L:
        n = len(re.sub(r"[，。？！：；、“”《》·\s\-a-zA-Z]", "", d["say"]))
        tot += n
        print(d["id"], n, d["say"])
    print("lines", len(L), "chars", tot, "est min @255/min", round(tot / 255, 1))
