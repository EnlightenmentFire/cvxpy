#!/usr/bin/env python3
"""加州电网政策与本地块抽蓄经济性的简版交付（HTML）：读 outputs/econ_cases.csv、econ_sensitivity.csv、econ_params.json 与两张图。
先运行 scripts/psh_economics.py。资料与推理见 notes/17_ca_policy_and_psh_economics.md。"""
import base64, csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(ROOT, "outputs"); DEL = os.path.join(ROOT, "deliverables")
rows = list(csv.DictReader(open(os.path.join(OUT, "econ_cases.csv"))))
sens = list(csv.DictReader(open(os.path.join(OUT, "econ_sensitivity.csv"))))
prm = json.load(open(os.path.join(OUT, "econ_params.json")))
img64 = lambda p: "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
esc = lambda x: str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
fig = lambda p, cap: f'<figure><img src="{img64(p)}"><figcaption>{cap}</figcaption></figure>'
def table(cols, rows_, raw=False):
    e = (lambda x: str(x)) if raw else esc
    h = ['<div class="wrap"><table><tr>' + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr>"]
    for r in rows_: h.append("<tr>" + "".join(f"<td>{e(x)}</td>" for x in r) + "</tr>")
    return "\n".join(h) + "</table></div>"
CSS = """body{font-family:"Noto Sans CJK SC","WenQuanYi Zen Hei","PingFang SC","Microsoft YaHei",Arial,sans-serif;max-width:1150px;margin:0 auto;padding:18px 26px 50px;line-height:1.6;color:#1f2328;background:#fff}
h1{font-size:21px;border-bottom:2px solid #333;padding-bottom:6px} h2{font-size:17px;margin-top:28px;border-left:5px solid #00695c;padding-left:10px} h3{font-size:15px;margin-top:18px}
table{border-collapse:collapse;font-size:12.5px;margin:8px 0 12px} th,td{border:1px solid #bfc4cc;padding:4px 7px;vertical-align:top;text-align:left} th{background:#eef1f5}
tr:nth-child(even) td{background:#f8f9fb} .wrap{overflow-x:auto} figure{margin:12px 0} img{max-width:100%;border:1px solid #d8dbe0} figcaption{font-size:12.5px;color:#444}
.box{background:#e0f2f1;border-left:4px solid #00695c;padding:8px 14px;margin:10px 0} .ans{background:#e8f5e9;border-left:4px solid #2e7d32;padding:10px 14px;margin:10px 0}
.warn{background:#fff8e1;border-left:4px solid #f0b400;padding:8px 14px;margin:10px 0} .bad{background:#fdecea;border-left:4px solid #c62828;padding:8px 14px;margin:10px 0}
.f{font-family:Menlo,Consolas,monospace;background:#f1f3f5;padding:1px 5px;border-radius:3px;font-size:12.5px} .small{font-size:12px;color:#555} li{margin:4px 0}"""
doc = lambda title, body: f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{CSS}</style></head><body>{body}</body></html>'
fm = lambda v: f"{int(round(float(v))):,}"
h = []
h.append("<h1>加州电网政策与本地块抽蓄经济性：从小到大能赚多少钱（简版）</h1>")
h.append('<p class="small">2026-09-18 · 数据与推理：<span class="f">notes/17_ca_policy_and_psh_economics.md</span> · 模型：<span class="f">scripts/psh_economics.py</span> · 单位：2026 美元实际值；所有 IRR 为实际 IRR（名义再加约 2.5% 通胀）</p>')
h.append(f"""<div class="ans"><b>一句话结论</b>：在现行加州市场价格下，本地块<b>任何规模</b>的抽蓄靠市场收入都收不回投资（中价情景实际 IRR −0.4% 到 2.8%）。
要成立需要每年 <b>$263–460/kW</b> 的收入（12–24 h 方案），而市场中价只有 $207、历史高价 $342、现有 LDES 合同约 $200。
最接近可融资的点是 <b>2,000 MW × 12 h（东半环 4,050）</b>：$4,670/kW，高价情景 IRR 7.7%，签到 $263/kW-年 的合同即可平。多日（48–100 h）方案在"容量按 kW 付费"的机制下无法回收库容投资。</div>""")

# ---------------- 1 政策
h.append("<h2>1. 法规政策：哪些帮忙、哪些挡路</h2>")
h.append(table(["层面", "法规 / 决定", "内容", "对本项目"], [
    ["需求", "SB 100（2018）", "2045 年 100% 零碳零售电", "长时储能需求的根源（+）"],
    ["需求", "CPUC D.21-06-035（2021）/ D.23-02-040（2023）", "中期可靠性采购 15.5 GW，其中 1 GW 长时储能（≥8 h），交付期限 2028", "有 LDES 采购口径，但时间窗赶不上（±）"],
    ["需求", "AB 1373（2023，PUC §454.52(h)）+ CPUC D.24-08-064（2024）", "DWR 集中采购：多日 LDES ≤1 GW、12 h+ LDES ≤1 GW、海上风电、地热；<b>§454.52(h)(2)：抽蓄只在 ≤500 MW 且 2023 年前已获州资金时才可纳入</b>", "<b>新抽蓄被挡在唯一的多日储能付费口径之外（−）</b>"],
    ["收入", "CPUC 资源充裕度（RA）切片日制度（2025 起）", "按每小时可放电量计合格容量；12 h 抽蓄全天满额", "抽蓄的主要收入来源；价格 2024 $28.65 → 2026 $11.53/kW-月（−）"],
    ["收入", "CAISO 能量 / 辅助服务市场", "日前、实时、调频、备用、灵活爬坡；2026 年 EDAM", "4 h 电池套利 $103（2022）→ $35/kW-年（2025）（−）"],
    ["税收", "IRA §48E ITC + IRS TD 10015（2025-01）+ OBBBA（2025-07）", "储能 ITC 30%（+10% 本土含量，+10% 能源社区），抽蓄明确合格，保留到 2033 年后退坡；FEOC 供应链限制", "初始投资少 30–40%（+）"],
    ["税收", "加州 Prop 13 房产税", "评估值 1% + 地方附加", "$B 级土建每年 1%，是运维之外最大持有成本（−）"],
    ["许可", "FERC 18 CFR Part 7（AWIA 2018）", "闭式抽蓄两年快速许可", "下库不在河上 → 可用（+）"],
    ["场地", "加州 Wild & Scenic Rivers Act（PRC §5093.545）", "南 Yuba 河 Lang Crossing 至 Bridgeport 段禁止筑坝引水", "<b>下库不能建在河上，只能在地块低处建封闭库：水头 497 → 390 m，多一座库（−）</b>"],
    ["场地", "SWRCB 水权 / CEQA+NEPA / Nevada 县 TPZ 分区 / CAISO 并网", "初次充水与补水水权；州与联邦环评 3–5 年；林地生产区改用途需县批准；并网排队 3–5 年、网络升级约 $250–340/kW", "都是时间与费用，不是否决项（±）"],
], raw=True))
h.append('<div class="warn"><b>两个硬约束</b>：(1) AB 1373 把新抽蓄排除在 DWR 集中采购之外，所以本项目只能跟 PG&E 或社区电力（3CE、CCCE 等）签双边合同，或者推动修法；(2) 南 Yuba 河 Wild & Scenic 意味着下库必须是地块内的封闭库，本文所有数字按下库 2,750 ft、水头 390 m 计。</div>')

# ---------------- 2 收入
h.append("<h2>2. 能收到多少钱：市场基准</h2>")
h.append(table(["来源", "年份", "数字（$/kW-年，除非注明）", "说明"], [
    ["CPUC 2023 RA 报告", "2023", "系统 RA 加权 $11.34/kW-月 ≈ 136", "2023-09 单月 $24.07"],
    ["CPUC 2024 市场价格基准（MPB）", "2024", "$28.65/kW-月 ≈ 344", "缺容量时的峰值，已过去"],
    ["CPUC 2026 MPB 预测 / Modo 2025H1", "2025–26", "$11.53 / $8.8/kW-月 ≈ 138 / 105", "电池一年新增 >5 GW 压价"],
    ["CAISO DMM 年报：4 h 电池净能量收入", "2022→2025", "103 → 78 → 53 → 35；调频另 9", "抽蓄 12 h 可跨更多小时，略高于 4 h 电池"],
    ["Argonne Goldendale 技术经济（12 h）", "2019$", "65–181（含容量）", "BCR 多数 <1，仅 ITC30% + 高可再生 >1"],
    ["Argonne Banner Mountain（10 h）", "2019$", "127–633", "基准 BCR 0.56–0.91，IRR 1.9–5.6%"],
    ["Willow Rock CAES 500 MW × 8 h（加州）", "2023–25", "3CE 200 MW 25 年约 $1B ≈ 200", "加州唯一可查的大型 LDES 合同单价"],
    ["CAISO DMM：新气机年固定成本", "2025", "联合循环 145，燃气轮机 176", "若不建新气机，抽蓄可争取的容量价上限量级"],
]))
h.append("<h3>本模型采用的三档 + 合同（12 h 基准）</h3>")
h.append(table(["档", "RA（$/kW-月 × 12）", "能量套利", "辅助服务", "合计 $/kW-年", "对应情形"], [
    ["低", "8 × 12 = 96", "40", "5", "141", "2025–26 现价延续"], ["中", "11.5 × 12 = 138", "60", "9", "207", "2023 / 2026 MPB 水平"],
    ["高", "20 × 12 = 240", "90", "12", "342", "2024 MPB 峰值 + 2022 套利"], ["合同", "—", "—", "—", "200", "Willow Rock 型固定付费"]]))
h.append('<p class="small">时长修正：24 h 能量收入 ×1.15，48/100 h ×1.2。RA 按 kW 付、不随时长增加——这就是多日方案亏损的原因。</p>')

# ---------------- 3 成本
h.append("<h2>3. 要花多少钱：造价与运维基准</h2>")
h.append(table(["案例 / 研究", "规模", "造价", "$/kW", "备注"], [
    ["PNNL ESGC 2022", "1,000 MW × 10 h 闭式", "约 $2,500/kW（2021$）", "2,500", "功率 ×10，$/kW −16%；RTE 80%；寿命 60 年"],
    ["NREL ATB 2024", "闭式 10 h", "$3,029–4,501/kW（2022$）", "3,765", "全美站址成本模型"],
    ["Goldendale WA", "1,200 MW × 12 h", "$2.853B（2019$）", "2,378", "运营预算 $16.6M/年 = $13.8/kW-年"],
    ["Swan Lake OR / Seminoe WY", "393 MW × 8 h / 900 MW", "$1.0B / $2.5B", "2,545 / 2,778", "均已 FERC 许可，未开工"],
    ["San Vicente CA", "500 MW × 8 h", "$1.5B（2022）", "3,000", "已有下库"],
    ["Mokelumne CA / Lewis Ridge KY", "400 MW × 8 h / 266 MW × 8 h", "$1.8B / $1.3B", "4,500 / 4,900", "两库新建 / 废煤矿"],
    ["Kidston AU / Snowy 2.0 AU", "250 MW × 8 h / 2,200 MW × 159 h", "A$777M / A$12–18B", "≈2,100 / 3,600+", "都严重超支；Snowy 原估 A$2B"],
    ["Coire Glas UK / Willow Rock CA（CAES）", "1,500 MW × 20 h / 500 MW × 8 h", ">£1.5B / $1.9B", "≈2,600 / 3,800", "cap-and-floor 保底 / DOE 贷款 $1.76B + CEC 补助"],
    ["PNNL 2022 表 4.29 运维", "100 / 1,000 MW", "$28.19 / $15.60 /kW-年", "—", "人工 + 备件 + 翻修准备金；另加库容相关 0.43%"],
]))
h.append(fig(os.path.join(OUT, "econ_capex_vs_cases.png"), "图 1：单位造价交叉验证。蓝色 = 本地块八个方案（本模型，2026 美元）；灰色 = 公开案例与基准（当年美元）。本地块 12–24 h 方案比美国近年估价高 20–50%，原因是上库 RCC 10–30 Mm³（$1.1–3.3B）与必须新建的下库。"))

# ---------------- 4 结果
h.append("<h2>4. 本地块八个方案：造价、运维、收入、回报</h2>")
h.append(f"""<div class="box"><b>模型输入</b>：上库方案与库容来自笔记 15/16（S29 沟谷坝、东半环 4,050、全环 B1）；水头 {prm['head_m']:.0f} m，每 Mm³ 可发 {prm['gwh_per_Mm3']:.2f} GWh；
RCC $110/m³、库内开挖 $12/m³、下库 $15/m³ 库容；与功率相关造价 $2,300/kW @1,000 MW（隧洞、地下厂房、机组、E&M、开关站），功率 ×10 降 16%；送出 $60M + 网络升级 $300/kW；土建不可预见 20%，业主/许可 8%，建设期利息 18%。
运维按 PNNL 表 4.29 插值 + 库容相关 0.3% + 管理 $2/kW-年；房产税 1%、保险 0.4% 造价/年。实际折现率 5%、50 年、ITC 30%。</div>""")
h.append(table(["#", "方案", "上库", "造价 $M", "$/kW", "$/kWh", "年运维+税+保 $M", "其中运维 / 房产税 / 保险", "年收入 低/中/高 $M", "EBITDA 中 $M", "实际 IRR 低/中/高/合同 %", "盈亏平衡所需 $/kW-年（ITC30 / 无 ITC）", "LCOS $/MWh"],
    [[r["case"].split("  ")[0], r["case"].split("  ")[1] if "  " in r["case"] else r["case"], r["scheme"], fm(r["capex_total_MUSD"]), fm(r["capex_usd_kw"]), r["capex_usd_kwh"], r["opex_total_MUSD"],
      f"{r['opex_om_MUSD']} / {r['opex_tax_MUSD']} / {r['opex_ins_MUSD']}", f"{r['rev_低_MUSD']} / {r['rev_中_MUSD']} / {r['rev_高_MUSD']}", r["ebitda_中_MUSD"],
      f"{r['irr_低']} / {r['irr_中']} / {r['irr_高']} / {r['irr_contract']}", f"{r['req_rev_usd_kw_yr_itc30']} / {r['req_rev_usd_kw_yr_itc0']}", r["lcos_usd_mwh"]] for r in rows]))
h.append(fig(os.path.join(OUT, "econ_chart.png"), "图 2：每 kW 的年收入（柱）与盈亏平衡所需收入（横线）。黑线 = 含 30% ITC，红线 = 无 ITC，三角 = 年运维+税+保。横线高于所有柱子 = 收不回投资。"))
h.append("""<div class="bad"><b>怎么读</b>：
<ul><li><b>年收入</b>（中价）：250 MW 约 $52M，1,000 MW 约 $207M，2,000 MW 约 $414–432M；<b>扣运维税费后（EBITDA）</b> $25M–$246M/年。这是现金流，不是利润。</li>
<li><b>回收投资</b>要每年 $263–460/kW（12–24 h）。市场中价 $207、高价 $342、合同 $200 都不够；没有一个方案在中价下 NPV 为正。</li>
<li><b>小方案不便宜</b>：250–500 MW 的 $/kW 与 1,000 MW 相当（上库同样贵、功率造价无规模效应），且做不到 12 h 以上。</li>
<li><b>多日方案</b>（1,000 MW × 48 h、500 MW × 100 h）：$11,000–20,000/kW，LCOS $146–272/MWh；库容投资在 RA 按 kW 付费下收不回来。</li></ul></div>""")

# ---------------- 5 敏感性
h.append("<h2>5. 敏感性：什么能把中型方案救回来</h2>")
s3 = [s for s in sens if s["case"].startswith("3")]; s7 = [s for s in sens if s["case"].startswith("7")]
h.append(table(["变化（中价）", "方案 3：1,000 MW × 12 h → $/kW", "实际 IRR %", "所需收入 $/kW-年", "方案 7：1,000 MW × 48 h → $/kW", "实际 IRR %", "所需收入"],
    [[a["test"], fm(a["capex_usd_kw"]), a["irr_pct"], a["req_rev_usd_kw_yr"], fm(b["capex_usd_kw"]), b["irr_pct"], b["req_rev_usd_kw_yr"]] for a, b in zip(s3, s7)]))
h.append('<p>没有单一变量能把方案 3 拉到 6% 以上；需要"造价 −30% + RA $20/kW-月 + ITC 40%"这种组合。方案 7 在所有情形下 IRR 都 &lt;0。</p>')

# ---------------- 6 交叉验证
h.append("<h2>6. 交叉验证：模型数字 vs 公开案例</h2>")
h.append(table(["项", "本模型", "公开案例 / 研究", "判断"], [
    ["造价 $/kW（12–24 h）", "4,670–7,186", "美国新建估价 2,400–4,900（当年$）；ATB 3,029–4,501（2022$）；折 2026$ 约 3,000–5,500", "本地块高 20–50%，原因可量化：上库 RCC 10.3–29.7 Mm³ = $1.1–3.3B（上库单独 $120/kWh，典型站址 $30–60/kWh），加新建下库、2026 美元、不可预见与建设期利息"],
    ["运维 $/kW-年（人工+备件+翻修）", "13.1–22.3", "PNNL 15.6–28.2；Goldendale 13.8", "一致"],
    ["运维+税+保 $/kW-年", "84–108（12–24 h）", "房产税+保险占 2/3，是加州特有持有成本，案例研究常漏算", "合理、偏保守（评估值折旧后下降）"],
    ["收入 $/kW-年", "141 / 207 / 342", "DMM 电池 44–103 + RA 96–344；Argonne 65–181 与 127–633；Willow Rock 合同 ≈200", "一致"],
    ["盈亏平衡所需收入", "263–460", "Argonne 两项目 BCR 多数 <1；美国 1990 年代以来无一座纯市场化抽蓄建成；Snowy 2.0 政府项目、Coire Glas 靠 cap-and-floor、Willow Rock 靠 DOE 贷款 + 补助 + 合同", "一致：抽蓄靠合同 / 费率基础 / 政府，不靠市场"],
    ["LCOS $/MWh（不含抽水电费）", "73–93（12–24 h）", "Lazard 2025：4 h 电池 $115–250 全口径；抽蓄 8–12 h 约 $100–200", "量级一致；加电费（$30 ÷ 0.8）后 $110–130"],
]))

# ---------------- 7 结论
h.append("<h2>7. 结论</h2>")
h.append("""<div class="ans"><ol>
<li><b>政策要长时储能，但机制没给新抽蓄留位置</b>：SB 100 与 CPUC 采购决定确立了 LDES 需求，联邦 ITC 30% 明确覆盖抽蓄，闭式抽蓄有两年快速许可；但 AB 1373 把新抽蓄排除在 DWR 集中采购之外，南 Yuba 河 Wild & Scenic 把下库赶上山（水头 −22%、多一座库）。</li>
<li><b>市场价格正在下行</b>：RA 从 2024 年 $28.65 跌到 2026 年 $11.5/kW-月，电池套利四年跌 2/3。现价下任何规模的抽蓄都不能靠市场收回投资，与 Argonne 两份研究、美国 30 年无新建抽蓄的事实一致。</li>
<li><b>规模上，2,000 MW × 12 h（东半环 4,050）是最接近成立的点</b>：$4,670/kW，年收入中价 $414M、EBITDA $246M，高价 IRR 7.7%，合同 $263/kW-年 可平。小方案 $/kW 不低、时长不够；B1 全环与多日方案经济上不成立。</li>
<li><b>要成立必须三件事同时发生</b>：(a) 20–25 年、$250–300/kW-年 的容量合同（比 Willow Rock 高 25–50%，需 CPUC 认定"抽蓄替代新气机"）；(b) 造价压到 $4,000/kW 以下（RCC $80/m³、短隧洞、机组竞标）；(c) ITC 40% + DOE LPO 低息债。任何一件不成都是负 NPV。</li>
<li><b>下一步</b>：用 CAISO Drum 节点逐时历史价做调度模拟替换平均单价；向 PG&E / 3CE / CCCE 探合同价；把下库选址（决定水头与造价）做实。</li></ol></div>""")
h.append("<h2>8. 资料来源（2026-09 访问）</h2>")
h.append("""<p class="small">政策：SB 100（2018）；SB 350（2015）；CPUC D.21-06-035、D.23-02-040、D.24-08-064；AB 1373 / PUC §454.52(h)；CPUC RA 切片日 D.23-04-010、D.24-06-004；CEC LDES 计划；E3《Long-Duration Energy Storage for California》。
市场：CAISO DMM《2024 / 2025 Annual Report on Market Issues and Performance》；CPUC《2023 Resource Adequacy Report》；CPUC 2024、2026 市场价格基准；Modo Energy 2025。
税收 / 联邦：IRA §48E；IRS TD 10015；OBBBA（P.L. 119-21）；DOE LPO；FERC 18 CFR Part 7；AWIA 2018 §3003。
场地：PRC §5093.545；Water Code §1200；Gov Code §51120/51130；LBNL《Interconnection Cost Analysis: CAISO》（2026）。
成本 / 案例：PNNL-33283（2022）表 4.29；NREL ATB 2024；Argonne Goldendale 与 Banner Mountain 技术经济分析（2022）；Goldendale 经济影响报告（2020）；Swan Lake、Seminoe、San Vicente、Mokelumne、Lewis Ridge、Kidston、Snowy 2.0、Coire Glas、Willow Rock、Eagle Mountain 公开文件；Lazard LCOS 2025。
完整清单与数字出处见 <span class="f">notes/17_ca_policy_and_psh_economics.md</span>。</p>""")
os.makedirs(DEL, exist_ok=True)
open(os.path.join(DEL, "D_ca_market_economics_brief.html"), "w").write(doc("加州政策与抽蓄经济性（简版）", "".join(h)))
print("written", os.path.join(DEL, "D_ca_market_economics_brief.html"))
