# -*- coding: utf-8 -*-
"""SPC 控制图：用移动极差法算控制限，标出越界点（特殊原因）。

运行：python spc_chart.py
产出：reports/spc_daily_yield.png + 控制限计算结果
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")

daily = pd.read_csv(os.path.join(REPORTS, "summary_daily.csv"))
x = daily["良率"]

# ==================== 控制限计算（移动极差法）====================
# 适用于"每次一个观测值"的情形（这里是每天的良率）
cl = x.mean()                                  # 中心线 = 平均值
mr = x.diff().abs()                            # 移动极差 = 相邻两点的差值
mrbar = mr.mean()                              # 移动极差平均值
sigma = mrbar / 1.128                          # d2 系数（n=2 时取 1.128）
ucl = cl + 3 * sigma
lcl = cl - 3 * sigma

print("=" * 60)
print("【控制限计算】")
print(f"  中心线 CL : {cl:.3f}%")
print(f"  移动极差均值 MR̄ : {mrbar:.3f}")
print(f"  标准差估计 σ : {sigma:.4f}（MR̄ / 1.128）")
print(f"  上限 UCL : {ucl:.3f}%（CL + 3σ）")
print(f"  下限 LCL : {lcl:.3f}%（CL − 3σ）")

# ==================== 判定越界点 ====================
out_of_control = (x > ucl) | (x < lcl)
print(f"\n  越界点：{int(out_of_control.sum())} 个")
for i in daily[out_of_control].itertuples():
    side = "高于 UCL" if i.良率 > ucl else "低于 LCL"
    print(f"      {i.生产日期}  良率 {i.良率:.2f}%  {side}")

# ==================== 画图 ====================
fig, ax = plt.subplots(figsize=(11, 5))
idx = range(len(daily))

ax.plot(idx, x, marker="o", markersize=4, linewidth=1.3, color="#4C78A8", label="每日良率")
ax.axhline(cl, color="green", linestyle="-", linewidth=1.2, label=f"CL = {cl:.2f}%")
ax.axhline(ucl, color="red", linestyle="--", linewidth=1.2, label=f"UCL = {ucl:.2f}%")
ax.axhline(lcl, color="red", linestyle="--", linewidth=1.2, label=f"LCL = {lcl:.2f}%")

# 越界点标红放大
bad = daily[out_of_control]
ax.scatter([daily.index.get_loc(i) for i in bad.index], bad["良率"],
           color="red", s=90, zorder=5, label="越界点（特殊原因）")

# x 轴：每 10 天显示一个日期，避免挤在一起
step = max(1, len(daily) // 10)
ax.set_xticks(list(idx)[::step])
ax.set_xticklabels(daily["生产日期"][::step], rotation=45, fontsize=8)

ax.set_title("每日良率 SPC 控制图", fontsize=13)
ax.set_ylabel("良率 (%)")
ax.set_xlabel("生产日期")
ax.legend(fontsize=9)
fig.tight_layout()
out = os.path.join(REPORTS, "spc_daily_yield.png")
plt.savefig(out, dpi=150)
print(f"\n已生成: {out}")

# ==================== 附加：分层控制图（按产线分别看）====================
clean = pd.read_csv(os.path.join(BASE, "data", "processed", "production_clean.csv"))
fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=False)
for ax, line in zip(axes, ["SMT-1线", "SMT-2线", "组装线"]):
    sub = (clean[clean["产线"] == line]
           .groupby("生产日期").agg(检验数=("检验数", "sum"), 不良数=("不良数", "sum")))
    sub["良率"] = (sub["检验数"] - sub["不良数"]) / sub["检验数"] * 100
    c, m = sub["良率"].mean(), sub["良率"].diff().abs().mean() / 1.128
    ax.plot(range(len(sub)), sub["良率"], linewidth=1.1, color="#4C78A8")
    ax.axhline(c, color="green", linewidth=1)
    ax.axhline(c + 3 * m, color="red", linestyle="--", linewidth=1)
    ax.axhline(c - 3 * m, color="red", linestyle="--", linewidth=1)
    ax.set_title(f"{line}（CL={c:.2f}%, UCL={c+3*m:.2f}%, LCL={c-3*m:.2f}%）", fontsize=11)
    ax.set_ylabel("良率 (%)")
fig.suptitle("各产线每日良率 SPC 控制图", fontsize=14)
fig.tight_layout()
plt.savefig(os.path.join(REPORTS, "spc_by_line.png"), dpi=150)
print("已生成: reports/spc_by_line.png")
