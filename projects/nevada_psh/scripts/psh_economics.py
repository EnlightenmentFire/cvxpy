#!/usr/bin/env python3
"""本地块抽水蓄能（PSH）从小到大各方案的经济性测算：造价、收入、运维、税费、NPV/IRR、平衡电价，并与公开案例交叉验证。
所有输入都在 P（参数）里，来源见 notes/17_ca_policy_and_psh_economics.md。单位：2026 美元，实际值（不含通胀），实际折现率。
输出：outputs/econ_cases.csv、outputs/econ_sensitivity.csv、outputs/econ_chart.png、outputs/econ_capex_vs_cases.png。
用法：python3 scripts/psh_economics.py"""
from __future__ import annotations
import csv, json, math, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); OUT = os.path.join(ROOT, "outputs")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]; matplotlib.rcParams["axes.unicode_minus"] = False
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

FT = 0.3048
P = {
    # ---- 地形/水头（本地块）
    "nwl_upper_ft": 4030.0,          # 上库水位（东半环/B1 方案）
    "nwl_lower_ft": 2750.0,          # 下库水位：南 Yuba 河为州级 Wild & Scenic（PRC 5093.545），不能筑坝 → 下库只能是地块低处的封闭库（假设 2,750 ft）
    "head_alt_ft": 2400.0,           # 敏感性：若下库能在 2,400 ft（河谷）
    "eta_turbine": 0.85, "rte": 0.80,   # PNNL 2022：PSH 循环效率 80%
    # ---- 造价单价（2026 美元）
    "rcc_usd_m3": 110.0,             # RCC 坝体每 m³（含胶材、拌合、碾压；美国 2020s 大坝 70–150）
    "cfrd_usd_m3": 25.0,             # 堆石每 m³（未用）
    "cut_usd_m3": 12.0,              # 库内岩石开挖每 m³（钻爆 + 装运 ≤1 km；资料 9 的 Cat 手册产量 → $8–15）
    "lower_res_usd_m3": 15.0,        # 下库（开挖 + 围坝 + 部分衬砌）每 m³ 库容
    "reservoir_ancillary": 1.15,     # 基础处理、灌浆、观测、进出水口土建
    "power_usd_kw_1000": 2300.0,     # 与功率相关的全部造价（引水隧洞/压力管、地下厂房、可逆机组、E&M、开关站、设计与业主费）在 1,000 MW 时的单价
    "power_scale_exp": -0.077,       # PNNL 2022：功率每 ×10，$/kW 降 16%
    "tx_line_usd": 60e6,             # 230 kV 双回约 20 km 到 PG&E Drum 系统
    "network_upgrade_usd_kw": 300.0, # LBNL 2026：CAISO 独立储能网络升级中位数约 $300/kW 量级
    "contingency_civil": 0.20, "owner_dev": 0.08, "idc": 0.18,   # 不可预见费（土建）、业主/开发/许可费、建设期利息（6 年，7%）
    # ---- 收入（$/kW-年，2026 美元）
    "ra_usd_kw_mo": {"低": 8.0, "中": 11.5, "高": 20.0},      # CPUC RA：2023 加权 11.1、2024 14.5（MPB 终值 28.65）、2025 11.9、2026 MPB 预测 11.53；Modo 2025H1 8.77
    "energy_12h_usd_kw_yr": {"低": 40.0, "中": 60.0, "高": 90.0},  # CAISO DMM：4 h 电池能量净收入 2022 $103→2024 $43→2025 $35；Argonne Goldendale 12 h：$65–181 含容量
    "as_usd_kw_yr": {"低": 5.0, "中": 9.0, "高": 12.0},          # CAISO DMM：电池调频收入 2024 $7、2025 $9
    "duration_energy_factor": {8: 0.85, 10: 0.95, 12: 1.0, 24: 1.15, 48: 1.2, 100: 1.2},
    "contract_usd_kw_yr": 200.0,     # 合同替代：Willow Rock 3CE 200 MW×8 h，25 年约 $10 亿 ≈ $200/kW-年
    # ---- 运维与持有成本
    "fom_usd_kw_yr_100": 28.2, "fom_usd_kw_yr_1000": 15.6,    # PNNL 2022 表 4.29（10 h 系统，含翻修准备金）；Goldendale 预算 $16.6M/1,200 MW = $13.8
    "storage_om_frac": 0.003,        # 水库相关运维：水库造价的 0.3%/年（PNNL：0.43% × 超出 10 h 的库容造价）
    "property_tax": 0.010,           # 加州 Prop 13：1% + 地方附加；按造价计（保守，评估值随时间降）
    "insurance": 0.004, "admin_usd_kw_yr": 2.0,
    # ---- 财务
    "discount_real": 0.05, "life_yr": 50, "itc": 0.30, "cycles_per_yr": {8: 330, 10: 320, 12: 300, 24: 180, 48: 90, 100: 40},
}
GWH_PER_MM3 = lambda head_m: 1e6 * 1000 * 9.81 * head_m * P["eta_turbine"] / 3.6e12   # 每 Mm³ 可发电量 GWh
HEAD_M = (P["nwl_upper_ft"] - P["nwl_lower_ft"]) * FT

# 方案（来自笔记 15/16 与交付物 1）：上库水量 Mm³、坝体 RCC Mm³、库内开挖 Mm³、坝长 m
SCHEMES = {
    "S29 沟谷坝（H 50 m）": {"vol": 4.4, "rcc": 1.55, "cut": 2.1, "dam_m": 728},
    "S29 沟谷坝（H 60 m）": {"vol": 5.9, "rcc": 1.97, "cut": 3.5, "dam_m": 813},
    "东半环 4,050（料平衡坑）": {"vol": 28.7, "rcc": 10.3, "cut": 10.3, "dam_m": 2530},
    "东半环 4,050（深挖）": {"vol": 40.4, "rcc": 10.3, "cut": 22.0, "dam_m": 2530},
    "全环 B1 4,050（挖后）": {"vol": 61.4, "rcc": 29.7, "cut": 36.3, "dam_m": 3900},
}
CASES = [  # 名称, 方案, 装机 MW, 目标时长 h
    ("1  小：250 MW", "S29 沟谷坝（H 50 m）", 250, 12),
    ("2  小：500 MW", "S29 沟谷坝（H 60 m）", 500, 10),
    ("3  中：1,000 MW × 12 h", "东半环 4,050（料平衡坑）", 1000, 12),
    ("4  中：1,000 MW × 24 h", "东半环 4,050（料平衡坑）", 1000, 24),
    ("5  中：2,000 MW × 12 h", "东半环 4,050（料平衡坑）", 2000, 12),
    ("6  大：2,000 MW × 24 h", "全环 B1 4,050（挖后）", 2000, 24),
    ("7  大：1,000 MW × 48 h（多日）", "全环 B1 4,050（挖后）", 1000, 48),
    ("8  大：500 MW × 100 h（多日）", "全环 B1 4,050（挖后）", 500, 100),
]


def capex(scheme, mw, hours, head_m=HEAD_M):
    s = SCHEMES[scheme]; e_avail = s["vol"] * GWH_PER_MM3(head_m); e_need = mw * hours / 1000
    hours_eff = hours if e_avail >= e_need else e_avail / mw * 1000
    v_low = (mw * hours_eff / 1000) / GWH_PER_MM3(head_m)            # 下库水量 = 一次放空的水量
    upper = (s["rcc"] * 1e6 * P["rcc_usd_m3"] + s["cut"] * 1e6 * P["cut_usd_m3"]) * P["reservoir_ancillary"]
    lower = v_low * 1e6 * P["lower_res_usd_m3"] * 1.2
    civil = (upper + lower) * (1 + P["contingency_civil"])
    power = P["power_usd_kw_1000"] * (mw / 1000) ** P["power_scale_exp"] * mw * 1000
    tx = P["tx_line_usd"] + P["network_upgrade_usd_kw"] * mw * 1000
    direct = civil + power + tx
    total = direct * (1 + P["owner_dev"]) * (1 + P["idc"])
    return {"e_avail_GWh": e_avail, "hours_eff": hours_eff, "v_low_Mm3": v_low, "upper": upper, "lower": lower, "civil": civil, "power": power, "tx": tx,
            "total": total, "total_kw": total / (mw * 1000), "total_kwh": total / (mw * hours_eff * 1000)}


def revenue(mw, hours, price):
    ra = P["ra_usd_kw_mo"][price] * 12
    dk = min(P["duration_energy_factor"], key=lambda k: abs(k - hours)); en = P["energy_12h_usd_kw_yr"][price] * P["duration_energy_factor"][dk]
    return {"ra": ra, "energy": en, "as": P["as_usd_kw_yr"][price], "total": ra + en + P["as_usd_kw_yr"][price]}


def opex(mw, cx):
    fom = P["fom_usd_kw_yr_100"] * (mw / 100) ** (math.log(P["fom_usd_kw_yr_1000"] / P["fom_usd_kw_yr_100"]) / math.log(10)) if mw >= 100 else P["fom_usd_kw_yr_100"]
    fom = min(fom, P["fom_usd_kw_yr_100"])
    om = fom * mw * 1000 + P["storage_om_frac"] * cx["civil"] + P["admin_usd_kw_yr"] * mw * 1000
    tax = P["property_tax"] * cx["total"]; ins = P["insurance"] * cx["total"]
    return {"fom_kw": fom, "om": om, "tax": tax, "ins": ins, "total": om + tax + ins}


def finance(cx, rev_total_kw, ox, mw, hours, itc=None):
    itc = P["itc"] if itc is None else itc
    r = P["discount_real"]; n = P["life_yr"]; ann = r / (1 - (1 + r) ** -n)
    rev = rev_total_kw * mw * 1000; ebitda = rev - ox["total"]; net_capex = cx["total"] * (1 - itc)
    npv = -net_capex + ebitda / ann
    # IRR（实际）：解 -net_capex + ebitda × 年金因子(irr) = 0
    irr = np.nan
    if ebitda > 0:
        lo, hi = -0.05, 0.5
        f = lambda x: -net_capex + ebitda * ((1 - (1 + x) ** -n) / x if abs(x) > 1e-9 else n)
        if f(lo) > 0 and f(hi) < 0:
            for _ in range(80):
                mid = 0.5 * (lo + hi); (lo, hi) = (mid, hi) if f(mid) > 0 else (lo, mid)
            irr = 0.5 * (lo + hi)
    req_rev = (net_capex * ann + ox["total"]) / (mw * 1000)             # NPV=0 所需收入 $/kW-年
    dk = min(P["cycles_per_yr"], key=lambda k: abs(k - hours)); mwh = mw * hours * P["cycles_per_yr"][dk]
    lcos = (net_capex * ann + ox["total"]) / mwh if mwh else np.nan       # $/MWh 放电（不含抽水电费）
    return {"rev": rev, "ebitda": ebitda, "net_capex": net_capex, "npv": npv, "irr": irr, "req_rev_kw": req_rev, "lcos": lcos, "yield": ebitda / net_capex}


rows = []
for name, scheme, mw, hours in CASES:
    cx = capex(scheme, mw, hours); ox = opex(mw, cx); h = cx["hours_eff"]
    rec = {"case": name, "scheme": scheme, "MW": mw, "hours": round(h, 1), "GWh": round(mw * h / 1000, 1), "e_avail_GWh": round(cx["e_avail_GWh"], 1),
           "capex_total_MUSD": round(cx["total"] / 1e6), "capex_usd_kw": round(cx["total_kw"]), "capex_usd_kwh": round(cx["total_kwh"]),
           "capex_upper_MUSD": round(cx["upper"] / 1e6), "capex_lower_MUSD": round(cx["lower"] / 1e6), "capex_power_MUSD": round(cx["power"] / 1e6), "capex_tx_MUSD": round(cx["tx"] / 1e6),
           "fom_usd_kw_yr": round(ox["fom_kw"], 1), "opex_total_MUSD": round(ox["total"] / 1e6, 1), "opex_om_MUSD": round(ox["om"] / 1e6, 1), "opex_tax_MUSD": round(ox["tax"] / 1e6, 1), "opex_ins_MUSD": round(ox["ins"] / 1e6, 1)}
    for price in ("低", "中", "高"):
        rv = revenue(mw, h, price); fn = finance(cx, rv["total"], ox, mw, h)
        rec.update({f"rev_{price}_usd_kw_yr": round(rv["total"]), f"rev_{price}_MUSD": round(fn["rev"] / 1e6), f"ebitda_{price}_MUSD": round(fn["ebitda"] / 1e6), f"npv_{price}_MUSD": round(fn["npv"] / 1e6), f"irr_{price}": round(fn["irr"] * 100, 1) if np.isfinite(fn["irr"]) else "<0", f"yield_{price}": round(fn["yield"] * 100, 1)})
    fc = finance(cx, P["contract_usd_kw_yr"], ox, mw, h)
    rec.update({"rev_contract_MUSD": round(fc["rev"] / 1e6), "ebitda_contract_MUSD": round(fc["ebitda"] / 1e6), "npv_contract_MUSD": round(fc["npv"] / 1e6), "irr_contract": round(fc["irr"] * 100, 1) if np.isfinite(fc["irr"]) else "<0",
                "req_rev_usd_kw_yr_itc30": round(fc["req_rev_kw"]), "req_rev_usd_kw_yr_itc0": round(finance(cx, 0, ox, mw, h, itc=0.0)["req_rev_kw"]), "lcos_usd_mwh": round(fc["lcos"])})
    rows.append(rec)
with open(os.path.join(OUT, "econ_cases.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows:
    print(f"{r['case']:<26} {r['MW']:>5} MW × {r['hours']:>5} h  capex ${r['capex_total_MUSD']:>6,}M (${r['capex_usd_kw']:,}/kW, ${r['capex_usd_kwh']}/kWh)  opex ${r['opex_total_MUSD']:>6}M/yr  "
          f"rev 低/中/高 {r['rev_低_usd_kw_yr']}/{r['rev_中_usd_kw_yr']}/{r['rev_高_usd_kw_yr']} $/kW-yr  EBITDA中 ${r['ebitda_中_MUSD']}M  IRR 低/中/高/合同 {r['irr_低']}/{r['irr_中']}/{r['irr_高']}/{r['irr_contract']}%  需收入(ITC30/无) {r['req_rev_usd_kw_yr_itc30']}/{r['req_rev_usd_kw_yr_itc0']} $/kW-yr  LCOS ${r['lcos_usd_mwh']}/MWh")

# ------------------------------------------------------------ 敏感性（方案 3 与 7）
sens = []
for name, scheme, mw, hours in (CASES[2], CASES[6]):
    base = finance(capex(scheme, mw, hours), revenue(mw, capex(scheme, mw, hours)["hours_eff"], "中")["total"], opex(mw, capex(scheme, mw, hours)), mw, capex(scheme, mw, hours)["hours_eff"])
    tests = [("基准", {}), ("与功率相关造价 −25%", {"power_usd_kw_1000": 1725}), ("与功率相关造价 +30%", {"power_usd_kw_1000": 2990}), ("RCC 单价 $80/m³", {"rcc_usd_m3": 80}), ("RCC 单价 $150/m³", {"rcc_usd_m3": 150}),
             ("下库在 2,400 ft（水头 +38%）", {"nwl_lower_ft": 2400}), ("无 ITC", {"itc": 0.0}), ("ITC 40%（本土含量）", {"itc": 0.40}), ("折现率 4%", {"discount_real": 0.04}), ("折现率 7%", {"discount_real": 0.07}),
             ("房产税 0.5%", {"property_tax": 0.005}), ("RA $20/kW-月", {"ra_usd_kw_mo": {"低": 8, "中": 20, "高": 20}}), ("RA $6/kW-月", {"ra_usd_kw_mo": {"低": 6, "中": 6, "高": 20}})]
    for lab, over in tests:
        saved = {k: P[k] for k in over}; P.update(over)
        cx = capex(scheme, mw, hours, head_m=(P["nwl_upper_ft"] - P["nwl_lower_ft"]) * FT); ox = opex(mw, cx); h = cx["hours_eff"]; rv = revenue(mw, h, "中"); fn = finance(cx, rv["total"], ox, mw, h)
        sens.append({"case": name, "test": lab, "capex_usd_kw": round(cx["total_kw"]), "rev_usd_kw_yr": round(rv["total"]), "opex_MUSD": round(ox["total"] / 1e6, 1), "npv_MUSD": round(fn["npv"] / 1e6), "irr_pct": round(fn["irr"] * 100, 1) if np.isfinite(fn["irr"]) else "<0", "req_rev_usd_kw_yr": round(fn["req_rev_kw"])})
        P.update(saved)
with open(os.path.join(OUT, "econ_sensitivity.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sens[0].keys())); w.writeheader(); w.writerows(sens)

# ------------------------------------------------------------ 图 1：每 kW 的年收入 vs 年成本（含资本回收）
fig, ax = plt.subplots(figsize=(12, 6.2)); x = np.arange(len(rows)); wdt = 0.18
ann = P["discount_real"] / (1 - (1 + P["discount_real"]) ** -P["life_yr"])
for i, (price, col) in enumerate((("低", "#9e9e9e"), ("中", "#1565c0"), ("高", "#2e7d32"))):
    ax.bar(x + (i - 1.5) * wdt, [r[f"rev_{price}_usd_kw_yr"] for r in rows], wdt, color=col, label=f"市场收入（{price}价）$/kW-年")
ax.bar(x + 1.5 * wdt, [P["contract_usd_kw_yr"]] * len(rows), wdt, color="#ef6c00", label="合同收入（Willow Rock 型 $200/kW-年）")
ax.plot(x, [r["req_rev_usd_kw_yr_itc30"] for r in rows], "k_", ms=28, mew=2.5, label="盈亏平衡所需收入（ITC 30%，实际折现 5%，50 年）")
ax.plot(x, [r["req_rev_usd_kw_yr_itc0"] for r in rows], "_", color="#b71c1c", ms=28, mew=2, label="盈亏平衡所需收入（无 ITC）")
ax.plot(x, [r["opex_total_MUSD"] * 1e6 / (r["MW"] * 1000) for r in rows], "v", color="#6d4c41", ms=8, label="年运维+税费+保险 $/kW-年")
ax.set_xticks(x); ax.set_xticklabels([r["case"].replace("：", "\n") for r in rows], fontsize=8); ax.set_ylim(0, 1500); ax.set_ylabel("$/kW-年（2026 美元）"); ax.grid(axis="y", alpha=0.3); ax.legend(fontsize=8, loc="upper left")
ax.set_title("各方案每 kW 的年收入与盈亏平衡所需收入：横线在柱子之上 = 不赚钱", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "econ_chart.png"), dpi=120); plt.close(fig)

# ------------------------------------------------------------ 图 2：单位造价 vs 案例
CASES_PUB = [("Goldendale WA 1,200 MW/12 h（2019$）", 2378), ("Swan Lake OR 393 MW/8 h", 2545), ("Seminoe WY 900 MW", 2778), ("San Vicente CA 500 MW/8 h（已有下库）", 3000), ("Mokelumne CA 400 MW/8 h", 4500), ("Lewis Ridge KY 266 MW/8 h", 4900),
             ("Kidston AU 250 MW/8 h（A$777M）", 2100), ("Snowy 2.0 AU 2,200 MW/159 h（A$12–18B）", 3600), ("Willow Rock CA CAES 500 MW/8 h", 3800), ("NREL ATB 2024 闭式 10 h：3,029–4,501", 3765), ("Eagle Mountain CA 1,300 MW/18 h（旧估）", 1923)]
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.barh([c[0] for c in CASES_PUB], [c[1] for c in CASES_PUB], color="#90a4ae", label="公开案例/基准（\\$/kW，未统一到 2026 美元）")
ax.barh([r["case"] for r in rows], [r["capex_usd_kw"] for r in rows], color="#1565c0", label="本地块方案（本模型，2026$）")
ax.set_xlabel("单位造价 $/kW"); ax.grid(axis="x", alpha=0.3); ax.legend(fontsize=8, loc="lower right"); ax.set_title("单位造价交叉验证", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "econ_capex_vs_cases.png"), dpi=120); plt.close(fig)
json.dump({"head_m": HEAD_M, "gwh_per_Mm3": GWH_PER_MM3(HEAD_M), "params": {k: v for k, v in P.items()}}, open(os.path.join(OUT, "econ_params.json"), "w"), ensure_ascii=False, indent=1)
print(f"水头 {HEAD_M:.0f} m，每 Mm³ {GWH_PER_MM3(HEAD_M):.2f} GWh；年金因子 {ann:.4f}")
