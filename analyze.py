# -*- coding: utf-8 -*-
"""生产良率与不良原因分析：口径计算 + 多维汇总 + 异常清单。

运行：python analyze.py
产出：data/processed/、reports/ 下的分析结果
"""
import os

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
PROCESSED = os.path.join(BASE, "data", "processed")
REPORTS = os.path.join(BASE, "reports")
for d in (PROCESSED, REPORTS):
    os.makedirs(d, exist_ok=True)

# ==================== 1. 读数据 ====================
df = pd.read_csv(os.path.join(RAW, "production.csv"), dtype=str).fillna("")
print(f"原始记录：{len(df)} 行")

# 数值列转数字
for col in ["计划产量", "实际产量", "检验数", "不良数"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ==================== 2. 找出异常（不删，先隔离）====================
bad = (
    df["检验数"].isna() | (df["检验数"] <= 0)          # 检验数缺失或为 0
    | df["不良数"].isna()
    | (df["不良数"] > df["检验数"])                      # 不良数大于检验数（录错）
    | (df["实际产量"] < 0)                               # 产量为负
    | (df["产线"].str.strip() == "")                     # 产线缺失
    | (~df["生产日期"].str.match(r"^\d{4}-\d{2}-\d{2}$"))  # 日期格式不对
)
exceptions = df[bad].copy()
exceptions["异常类型"] = "检验数缺失/为0、不良数大于检验数、产量为负、产线缺失或日期异常"
exceptions.to_csv(os.path.join(REPORTS, "exception_list.csv"), index=False, encoding="utf-8-sig")

clean = df[~bad].copy()
print(f"异常记录：{len(exceptions)} 行（已单独出清单）")
print(f"清洗后记录：{len(clean)} 行")

# ==================== 3. 算指标（口径写死在注释里）====================
# 良率 =（检验数 − 不良数）/ 检验数    —— 分母用检验数，不用计划产量
clean["良率"] = (clean["检验数"] - clean["不良数"]) / clean["检验数"] * 100
clean["不良率"] = clean["不良数"] / clean["检验数"] * 100
# 达成率 = 实际产量 / 计划产量（计划为 0 的不算）
clean["达成率"] = (clean["实际产量"] / clean["计划产量"].replace(0, pd.NA)) * 100

clean.to_csv(os.path.join(PROCESSED, "production_clean.csv"), index=False, encoding="utf-8-sig")

# ==================== 4. 整体指标 ====================
total_insp = clean["检验数"].sum()
total_def = clean["不良数"].sum()
overall = (total_insp - total_def) / total_insp * 100
print("\n" + "=" * 60)
print("【整体指标】")
print(f"  总检验数：{total_insp:,}")
print(f"  总不良数：{total_def:,}")
print(f"  整体良率：{overall:.2f}%")
print(f"  整体不良率：{total_def / total_insp * 100:.2f}%")


# ==================== 5. 多维汇总 ====================
def group_yield(keys, name):
    """按指定维度汇总：良率必须用 '总检验数/总不良数' 重算，不能对良率求平均！"""
    g = clean.groupby(keys).agg(检验数=("检验数", "sum"), 不良数=("不良数", "sum")).reset_index()
    g["良率"] = (g["检验数"] - g["不良数"]) / g["检验数"] * 100
    g["不良率"] = g["不良数"] / g["检验数"] * 100
    g = g.sort_values("良率")
    g.to_csv(os.path.join(REPORTS, f"summary_{name}.csv"), index=False, encoding="utf-8-sig")
    return g


print("\n【按产线】")
by_line = group_yield(["产线"], "line")
print(by_line.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n【按型号】")
by_product = group_yield(["产品编码", "产品名称"], "product")
print(by_product.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n【按班次】")
by_shift = group_yield(["班次"], "shift")
print(by_shift.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

print("\n【按不良原因】")
by_reason = (clean[clean["不良数"] > 0]
             .groupby("不良原因")["不良数"].sum().reset_index()
             .sort_values("不良数", ascending=False))
by_reason["占比"] = by_reason["不良数"] / by_reason["不良数"].sum() * 100
by_reason["累计占比"] = by_reason["占比"].cumsum()          # ← 帕累托分析的基础
by_reason.to_csv(os.path.join(REPORTS, "summary_defect.csv"), index=False, encoding="utf-8-sig")
print(by_reason.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

# ==================== 6. 按日趋势 ====================
daily = clean.groupby("生产日期").agg(检验数=("检验数", "sum"), 不良数=("不良数", "sum")).reset_index()
daily["良率"] = (daily["检验数"] - daily["不良数"]) / daily["检验数"] * 100
daily.to_csv(os.path.join(REPORTS, "summary_daily.csv"), index=False, encoding="utf-8-sig")
print(f"\n按日趋势：{len(daily)} 天，已导出 summary_daily.csv")

print("\n完成：data/processed/ 与 reports/ 已生成")