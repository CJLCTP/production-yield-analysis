# -*- coding: utf-8 -*-
"""交叉分析：产线 × 不良原因、班次 × 不良原因，并测算改善空间。

运行：python cross_analysis.py
产出：reports/ 下 3 个 CSV + 2 张图
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

df = pd.read_csv(os.path.join(BASE, "data", "processed", "production_clean.csv"))
d = df[df["不良数"] > 0].copy()

# ==================== 1. 产线 × 不良原因 交叉表 ====================
cross_line = d.pivot_table(index="不良原因", columns="产线",
                           values="不良数", aggfunc="sum", fill_value=0)
cross_line["合计"] = cross_line.sum(axis=1)
cross_line = cross_line.sort_values("合计", ascending=False)
cross_line.to_csv(os.path.join(REPORTS, "cross_line_reason.csv"), encoding="utf-8-sig")

print("=" * 64)
print("【产线 × 不良原因】（不良数）")
print(cross_line.to_string())

# 每个产线内部的占比 —— 用来看"哪类原因在各产线都突出"
share = cross_line.drop(columns="合计")
share_pct = (share / share.sum(axis=0) * 100).round(2)
share_pct.to_csv(os.path.join(REPORTS, "cross_line_reason_pct.csv"), encoding="utf-8-sig")
print("\n【各产线内部的不良原因占比 %】")
print(share_pct.to_string())

# ==================== 2. 班次 × 不良原因 交叉表 ====================
cross_shift = d.pivot_table(index="不良原因", columns="班次",
                            values="不良数", aggfunc="sum", fill_value=0)
cross_shift["合计"] = cross_shift.sum(axis=1)
cross_shift = cross_shift.sort_values("合计", ascending=False)
cross_shift["晚班/早班"] = (cross_shift["晚班"] / cross_shift["早班"] * 100 - 100).round(1)
cross_shift.to_csv(os.path.join(REPORTS, "cross_shift_reason.csv"), encoding="utf-8-sig")
print("\n【班次 × 不良原因】")
print(cross_shift.to_string())

# ==================== 3. 改善空间测算 ====================
tot_i, tot_d = df["检验数"].sum(), df["不良数"].sum()
now = (tot_i - tot_d) / tot_i * 100
main_reason = cross_line.index[0]
main_defects = cross_line.loc[main_reason, "合计"]

print("\n" + "=" * 64)
print("【改善空间测算】")
print(f"  当前整体良率：{now:.2f}%（不良 {tot_d:,} / 检验 {tot_i:,}）")
print(f"  首要不良原因：{main_reason}（{main_defects:,} 个）")
for cut in (0.3, 0.5, 0.7):
    save = main_defects * cut
    new = (tot_i - tot_d + save) / tot_i * 100
    print(f"  {main_reason}降 {cut*100:.0f}% → 减少不良 {save:,.0f} 个，"
          f"良率 {now:.2f}% → {new:.2f}%（+{new-now:.2f} 个点）")

# ==================== 4. 图 1：各产线不良原因堆叠柱 ====================
fig, ax = plt.subplots(figsize=(8, 5))
share_pct.T.plot(kind="bar", stacked=True, ax=ax, colormap="tab20c", width=0.6)
ax.set_title("各产线不良原因构成（占比）", fontsize=13)
ax.set_ylabel("占比 (%)")
ax.set_xlabel("产线")
ax.legend(title="不良原因", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
plt.xticks(rotation=0)
fig.tight_layout()
plt.savefig(os.path.join(REPORTS, "cross_line_stacked.png"), dpi=150)
print("\n已生成: reports/cross_line_stacked.png")

# ==================== 5. 图 2：班次对比分组柱 ====================
fig, ax = plt.subplots(figsize=(8.5, 5))
cross_shift[["早班", "晚班"]].plot(kind="bar", ax=ax, width=0.7,
                                   color=["#4C78A8", "#E45756"])
ax.set_title("早班 vs 晚班 不良数对比", fontsize=13)
ax.set_ylabel("不良数")
ax.set_xlabel("不良原因")
plt.xticks(rotation=15)
fig.tight_layout()
plt.savefig(os.path.join(REPORTS, "cross_shift_bar.png"), dpi=150)
print("已生成: reports/cross_shift_bar.png")