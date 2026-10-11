# -*- coding: utf-8 -*-
"""帕累托图：不良原因排序 + 累计占比（找关键少数）。

运行：python pareto_chart.py
产出：reports/pareto_defect.png
"""
import os

import matplotlib
matplotlib.use("Agg")          # 不弹窗，直接存文件
import matplotlib.pyplot as plt
import pandas as pd

# 中文字体，否则图里中文会变方块
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(BASE, "reports")

df = pd.read_csv(os.path.join(REPORTS, "summary_defect.csv"))
df = df.sort_values("不良数", ascending=False).reset_index(drop=True)
df["累计占比"] = df["占比"].cumsum()

# ---------- 画图 ----------
fig, ax1 = plt.subplots(figsize=(9, 5.5))

bars = ax1.bar(df["不良原因"], df["不良数"], color="#4C78A8", width=0.6, label="不良数")
ax1.set_xlabel("不良原因")
ax1.set_ylabel("不良数")
ax1.set_ylim(0, df["不良数"].max() * 1.25)

# 柱子上标数值
for b, v in zip(bars, df["不良数"]):
    ax1.text(b.get_x() + b.get_width() / 2, v, f"{int(v):,}", ha="center", va="bottom", fontsize=9)

# 右侧次坐标轴：累计占比曲线
ax2 = ax1.twinx()
ax2.plot(df["不良原因"], df["累计占比"], color="#E45756", marker="o", linewidth=2, label="累计占比")
ax2.set_ylabel("累计占比 (%)")
ax2.set_ylim(0, 105)
for x, y in zip(df["不良原因"], df["累计占比"]):
    ax2.text(x, y + 3, f"{y:.1f}%", ha="center", fontsize=9, color="#E45756")

# 80% 参考线（帕累托的经典标准）
ax2.axhline(80, color="gray", linestyle="--", linewidth=1)
ax2.text(len(df) - 0.5, 81.5, "80% 参考线", color="gray", fontsize=9, ha="right")

plt.title("不良原因帕累托图", fontsize=14, pad=12)
fig.tight_layout()
out = os.path.join(REPORTS, "pareto_defect.png")
plt.savefig(out, dpi=150)
print("已生成:", out)

# ---------- 顺带打印结论 ----------
print("\n帕累托结论：")
cum = 0
for i, row in df.iterrows():
    cum += row["占比"]
    flag = "  ← 累计过 80%" if cum >= 80 and (cum - row["占比"]) < 80 else ""
    print(f"  第{i+1}项 {row['不良原因']}：{row['不良数']:,} 个（{row['占比']:.2f}%），累计 {cum:.2f}%{flag}")
print(f"\n前 3 项累计：{df['占比'].head(3).sum():.2f}%")