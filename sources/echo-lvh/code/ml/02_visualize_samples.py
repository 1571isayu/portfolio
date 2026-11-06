"""第 1 週：隨機抽 N 支影片，把醫師標註的 4 個點與 3 條線畫在畫面上，確認座標理解正確。"""
import argparse
from pathlib import Path

import cv2
import pandas as pd

from common import KEYPOINT_NAMES, avi_index, diastolic_table, load_measurements, open_zip, read_frame, imwrite

ap = argparse.ArgumentParser()
ap.add_argument("--zip", default="../EchoNet-LVH.zip")
ap.add_argument("--out", default="outputs/samples")
ap.add_argument("--n", type=int, default=10)
ap.add_argument("--seed", type=int, default=42)
args = ap.parse_args()
out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

zf = open_zip(args.zip)
t = diastolic_table(load_measurements(zf))
t = t[(t.gap1 <= 3) & (t.gap2 <= 3)]
videos = avi_index(zf)
sample = t.sample(args.n, random_state=args.seed)

# 線段顏色（BGR）：LVPW 綠、LVID 黃、IVS 洋紅
SEGMENTS = [("LVPWd", (80, 200, 80)), ("LVIDd", (0, 210, 255)), ("IVSd", (255, 80, 255))]
tiles = []
for vid, r in sample.iterrows():
    img = read_frame(zf, videos[vid], int(r.frame))
    if img is None:
        print("讀不到", vid); continue
    pts = [(int(r[f"{k}_x"]), int(r[f"{k}_y"])) for k in KEYPOINT_NAMES]
    for i, (name, color) in enumerate(SEGMENTS):
        cv2.line(img, pts[i], pts[i + 1], color, 2)
        mid = ((pts[i][0] + pts[i + 1][0]) // 2 + 12, (pts[i][1] + pts[i + 1][1]) // 2)
        cv2.putText(img, f"{name} {r[name]:.2f}cm", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    for p in pts:
        cv2.circle(img, p, 5, (0, 0, 255), -1)
    lvh = "LVH?" if max(r.IVSd, r.LVPWd) >= 1.1 else "normal"
    cv2.putText(img, f"{vid}  frame {int(r.frame)}  {r.split}  {lvh}", (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    imwrite(str(out / f"{vid}.png"), img)
    tiles.append(cv2.resize(img, (512, 384)))
    print("OK", vid, f"IVSd={r.IVSd:.2f} LVIDd={r.LVIDd:.2f} LVPWd={r.LVPWd:.2f}")

# 拼成一張總覽圖（每列 5 張）
if tiles:
    while len(tiles) % 5:
        tiles.append(tiles[0] * 0)
    rows = [cv2.hconcat(tiles[i:i + 5]) for i in range(0, len(tiles), 5)]
    imwrite(str(out.parent / "samples_overview.jpg"), cv2.vconcat(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("總覽圖：", out.parent / "samples_overview.jpg")
