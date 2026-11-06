"""第 1 週：資料探勘。讀 MeasurementsList.csv，輸出統計報表與分布圖到 outputs/。"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import DIASTOLIC, avi_index, diastolic_table, load_measurements, open_zip

ap = argparse.ArgumentParser()
ap.add_argument("--zip", default="../EchoNet-LVH.zip")
ap.add_argument("--out", default="outputs")
args = ap.parse_args()
out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

zf = open_zip(args.zip)
df = load_measurements(zf)
videos = avi_index(zf)
t = diastolic_table(df)
t.to_csv(out / "keypoints_all.csv")

lines = ["# EchoNet-LVH 資料探勘結果", ""]
add = lines.append
add(f"- 標註筆數：{len(df):,}；影片數：{df.HashedFileName.nunique():,}；zip 內 avi：{len(videos):,}")
add(f"- 量測種類：{df.Calc.value_counts().to_dict()}")
vs = df.drop_duplicates("HashedFileName")
add(f"- 影片切分：{vs.split.value_counts().to_dict()}")
add(f"- 三個舒張期量測齊全且同一格的影片：{len(t):,}")
ok = t[(t.gap1 <= 3) & (t.gap2 <= 3)]
add(f"- 其中三條線首尾相接（誤差 ≤ 3 px）：{len(ok):,}（{len(ok)/len(t):.1%}）→ 可用 4 個關鍵點表示")
add(f"- 這些影片的切分：{ok.split.value_counts().to_dict()}")
add(f"- 解析度：{vs.groupby(['Width','Height']).size().sort_values(ascending=False).head(4).to_dict()}")
add(f"- 比例尺 cm/px：中位數 {t.cm_per_px.median():.4f}，範圍 {t.cm_per_px.min():.4f}–{t.cm_per_px.max():.4f}")
add("")
add("## 量測值（cm）")
add("| 項目 | 平均 | 標準差 | 中位數 | 最小 | 最大 |")
add("| --- | --- | --- | --- | --- | --- |")
for c in DIASTOLIC:
    s = t[c]
    add(f"| {c} | {s.mean():.2f} | {s.std():.2f} | {s.median():.2f} | {s.min():.2f} | {s.max():.2f} |")
add("")
for thr in (1.1, 1.2):
    lvh = (t.IVSd >= thr) | (t.LVPWd >= thr)
    add(f"- IVSd 或 LVPWd ≥ {thr} cm 的比例：{lvh.mean():.1%}（{lvh.sum():,} 支）")
rwt = 2 * t.LVPWd / t.LVIDd
add(f"- RWT > 0.42 的比例：{(rwt > 0.42).mean():.1%}")
(out / "explore_report.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))

fig, ax = plt.subplots(1, 3, figsize=(12, 3.2))
for a, c in zip(ax, DIASTOLIC):
    a.hist(t[c], bins=60, color="#3b6ea5")
    if c != "LVIDd":
        a.axvline(1.1, color="#d9534f", ls="--", lw=1, label="1.1 cm")
        a.legend(frameon=False)
    a.set_title(c); a.set_xlabel("cm")
fig.tight_layout(); fig.savefig(out / "measurement_hist.png", dpi=120)
print(f"\n已輸出：{out/'explore_report.md'}、{out/'measurement_hist.png'}、{out/'keypoints_all.csv'}")
