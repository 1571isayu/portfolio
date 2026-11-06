"""第 2 週：擷取訓練資料。
從 zip 抽出每支影片被標註的那一格 → 灰階 → 補成正方形（右下補黑邊，不變形）→ 縮成 256×256。
輸出：
  data/echolvh_256/images/<影片ID>.png
  data/echolvh_256/labels.csv   （4 個點在 256×256 上的座標、三個量測值 cm、cm_per_px_256、split）
  data/echolvh_256.zip          （打包好，直接上傳 Google Drive 給 Colab 用）
可中斷重跑：已存在的圖片會跳過。
"""
import argparse
import os
import shutil
from pathlib import Path

import cv2
import pandas as pd
from tqdm import tqdm

from common import KEYPOINT_NAMES, avi_index, diastolic_table, load_measurements, open_zip, read_frame, imwrite

ap = argparse.ArgumentParser()
ap.add_argument("--zip", default="../EchoNet-LVH.zip")
ap.add_argument("--out", default="data/echolvh_256")
ap.add_argument("--size", type=int, default=256)
ap.add_argument("--n-train", type=int, default=2400)
ap.add_argument("--n-val", type=int, default=300)
ap.add_argument("--n-test", type=int, default=0, help="0 = 全部 test（約 325 支）")
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--shard", default="0/1", help="平行擷取：例如 0/3、1/3、2/3（只擷取圖，不寫 labels）")
ap.add_argument("--no-zip", action="store_true", help="只擷取不打包（分段跑時用）")
ap.add_argument("--zip-name", default=None, help="打包檔名（預設與 --out 相同）")
args = ap.parse_args()

out = Path(args.out); img_dir = out / "images"; img_dir.mkdir(parents=True, exist_ok=True)
zf = open_zip(args.zip)
videos = avi_index(zf)
t = diastolic_table(load_measurements(zf))
t = t[(t.gap1 <= 3) & (t.gap2 <= 3)]

parts = []
for split, n in [("train", args.n_train), ("val", args.n_val), ("test", args.n_test)]:
    s = t[t.split == split]
    parts.append(s if n == 0 or n >= len(s) else s.sample(n, random_state=args.seed))
sel = pd.concat(parts)
print("抽樣：", sel.split.value_counts().to_dict())
k, n = map(int, args.shard.split("/"))
if n > 1:
    sel = sel.iloc[k::n]

rows, failed = [], []
for vid, r in tqdm(sel.iterrows(), total=len(sel)):
    path = img_dir / f"{vid}.png"
    img = None
    if path.exists() and path.stat().st_size > 0:
        h, w = int(r.Height), int(r.Width)
    else:
        img = read_frame(zf, videos[vid], int(r.frame))
        if img is None:
            failed.append(vid); continue
        h, w = img.shape[:2]
    side = max(h, w); scale = args.size / side
    if img is not None:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sq = cv2.copyMakeBorder(g, 0, side - h, 0, side - w, cv2.BORDER_CONSTANT, value=0)
        tmp = path.with_suffix(".tmp.png")   # 先寫暫存檔，寫完才改名：中斷也不會留下壞檔
        imwrite(str(tmp), cv2.resize(sq, (args.size, args.size), interpolation=cv2.INTER_AREA))
        os.replace(tmp, path)
    row = {"id": vid, "split": r.split, "orig_w": w, "orig_h": h, "scale": scale,
           "IVSd": r.IVSd, "LVIDd": r.LVIDd, "LVPWd": r.LVPWd,
           "cm_per_px_256": r.cm_per_px / scale}
    for k in KEYPOINT_NAMES:
        row[f"{k}_x"] = r[f"{k}_x"] * scale
        row[f"{k}_y"] = r[f"{k}_y"] * scale
    rows.append(row)

if n > 1:
    print(f"分片 {k}/{n} 完成 {len(rows)} 張，失敗 {len(failed)}"); raise SystemExit
lab = pd.DataFrame(rows)
lab.to_csv(out / "labels.csv", index=False)
print(f"完成 {len(lab)} 張，失敗 {len(failed)} 支：{failed[:10]}")
print(lab.split.value_counts().to_dict())
if not args.no_zip:
    zname = str(out.parent / args.zip_name) if args.zip_name else str(out)
    shutil.make_archive(zname, "zip", root_dir=out.parent, base_dir=out.name)
    print("已打包：", zname + ".zip")
