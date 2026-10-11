# -*- coding: utf-8 -*-
"""生成 3 个月模拟生产数据（含故意混入的脏数据）。

运行：python gen_data.py
产出：data/raw/production.csv
说明：所有数据由脚本随机生成，不含任何真实企业数据。
"""
import csv
import os
import random
from datetime import date, timedelta

random.seed(20261010)

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)

LINES = ["SMT-1线", "SMT-2线", "组装线"]
SHIFTS = ["早班", "晚班"]
INSPECTORS = ["张伟", "李娜", "王强", "陈静"]
PRODUCTS = [
    ("P-1001", "控制主板", 1200),
    ("P-1002", "电源模块", 900),
    ("P-1003", "显示模组", 1500),
    ("P-1004", "连接线束", 2000),
]
DEFECTS = ["外观不良", "尺寸超差", "焊接不良", "功能不良", "来料不良"]

# 不同产线的基础不良率不同 —— 这样看板才能"看出差异"，
# 否则三条线良率一样，分析就没结论了
BASE_RATE = {"SMT-1线": 0.012, "SMT-2线": 0.020, "组装线": 0.032}
# 某些不良原因更集中（用于帕累托分析：让"尺寸超差"成为主因）
DEFECT_WEIGHT = {"尺寸超差": 0.30, "焊接不良": 0.22, "外观不良": 0.20,
                 "功能不良": 0.16, "来料不良": 0.12}

START = date(2026, 9, 1)
DAYS = 90

rows = []
for d in range(DAYS):
    day = START + timedelta(days=d)
    if day.weekday() == 6:          # 周日不排产
        continue
    for line in LINES:
        for code, name, base in PRODUCTS:
            for shift in SHIFTS:
                plan = int(base * random.uniform(0.85, 1.15) / 2)   # 分两个班次
                actual = int(plan * random.uniform(0.90, 1.00))
                inspected = int(actual * random.uniform(0.95, 1.00))

                rate = BASE_RATE[line]
                if code == "P-1003":
                    rate += 0.008                       # 显示模组更难做
                if shift == "晚班":
                    rate *= 1.15                        # 晚班稍差（班次对比的素材）

                defect_qty = 0
                if inspected:
                    defect_qty = sum(1 for _ in range(inspected) if random.random() < rate)

                # 按权重分配不良原因
                reason = ""
                if defect_qty:
                    reason = random.choices(list(DEFECT_WEIGHT), weights=list(DEFECT_WEIGHT.values()))[0]

                rows.append([
                    day.isoformat(), line, shift, code, name, random.choice(INSPECTORS),
                    plan, actual, inspected, defect_qty, reason,
                ])

# ---------- 故意注入约 2% 的脏数据（清洗步骤的素材）----------
dirty = 0
for _ in range(int(len(rows) * 0.02)):
    r = random.choice(rows)
    kind = random.choice(["null_inspected", "defect_gt_inspected", "negative", "null_line", "bad_date"])
    if kind == "null_inspected":
        r[8] = ""
    elif kind == "defect_gt_inspected":
        r[9] = int(r[8]) + random.randint(5, 50)
    elif kind == "negative":
        r[7] = -abs(int(r[7])) if r[7] else -100
    elif kind == "null_line":
        r[1] = ""
    else:
        r[0] = "2027-0{}-15".format(random.randint(1, 9))    # 未来日期
    dirty += 1

with open(os.path.join(RAW, "production.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["生产日期", "产线", "班次", "产品编码", "产品名称", "检验员",
                "计划产量", "实际产量", "检验数", "不良数", "不良原因"])
    w.writerows(rows)

# ---------- 打印真实数字（一会儿要填进简历）----------
print("=" * 60)
print(f"生产记录：{len(rows)} 行")
print(f"日期范围：{START} ~ {START + timedelta(days=DAYS - 1)}（周日不排产）")
print(f"故意注入脏数据：{dirty} 行（约 {dirty / len(rows) * 100:.1f}%）")
print(f"产线 {len(LINES)} 条 × 产品 {len(PRODUCTS)} 个 × 班次 {len(SHIFTS)} 个")
print("=" * 60)