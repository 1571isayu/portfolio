"""共用工具：從 zip 直接讀標註與影片，不需要解壓 73.8 GB。"""
import os
import tempfile
import zipfile

import cv2
import numpy as np
import pandas as pd

DIASTOLIC = ["IVSd", "LVIDd", "LVPWd"]
# 4 個關鍵點（由下往上）：LVPW 外緣、LVPW/LVID 交界、LVID/IVS 交界、IVS 上緣
# 資料中：LVPWd 的 P2 = LVIDd 的 P1；LVIDd 的 P2 = IVSd 的 P1
KEYPOINT_NAMES = ["lvpw_outer", "lvpw_lvid", "lvid_ivs", "ivs_outer"]


def open_zip(path):
    return zipfile.ZipFile(path)


def load_measurements(zf):
    df = pd.read_csv(zf.open("MeasurementsList.csv"), index_col=0)
    df["Frames"] = pd.to_numeric(df["Frames"], errors="coerce")
    return df


def avi_index(zf):
    """影片 ID -> zip 內路徑（例如 Batch1/0X....avi）"""
    return {n.rsplit("/", 1)[-1][:-4]: n for n in zf.namelist() if n.endswith(".avi")}


def diastolic_table(df):
    """每支影片一列，含三個量測的值、端點與畫面編號；只保留三個量測都在同一格的影片。"""
    d = df[df.Calc.isin(DIASTOLIC)].drop_duplicates(["HashedFileName", "Calc"])
    p = d.pivot(index="HashedFileName", columns="Calc",
                values=["CalcValue", "Frame", "X1", "Y1", "X2", "Y2"]).dropna()
    same_frame = (p["Frame", "IVSd"] == p["Frame", "LVIDd"]) & (p["Frame", "LVIDd"] == p["Frame", "LVPWd"])
    p = p[same_frame]
    out = pd.DataFrame(index=p.index)
    out["frame"] = p["Frame", "LVIDd"].astype(int)
    for c in DIASTOLIC:
        out[c] = p["CalcValue", c]
    # 4 個點（取相接處兩端點的平均，降低 1–2 px 誤差）
    out["lvpw_outer_x"], out["lvpw_outer_y"] = p["X1", "LVPWd"], p["Y1", "LVPWd"]
    out["lvpw_lvid_x"] = (p["X2", "LVPWd"] + p["X1", "LVIDd"]) / 2
    out["lvpw_lvid_y"] = (p["Y2", "LVPWd"] + p["Y1", "LVIDd"]) / 2
    out["lvid_ivs_x"] = (p["X2", "LVIDd"] + p["X1", "IVSd"]) / 2
    out["lvid_ivs_y"] = (p["Y2", "LVIDd"] + p["Y1", "IVSd"]) / 2
    out["ivs_outer_x"], out["ivs_outer_y"] = p["X2", "IVSd"], p["Y2", "IVSd"]
    # 相接誤差（px），太大的之後可以排除
    out["gap1"] = np.hypot(p["X2", "LVPWd"] - p["X1", "LVIDd"], p["Y2", "LVPWd"] - p["Y1", "LVIDd"])
    out["gap2"] = np.hypot(p["X2", "LVIDd"] - p["X1", "IVSd"], p["Y2", "LVIDd"] - p["Y1", "IVSd"])
    # 比例尺 cm/pixel
    out["cm_per_px"] = p["CalcValue", "LVIDd"] / np.hypot(p["X2", "LVIDd"] - p["X1", "LVIDd"],
                                                          p["Y2", "LVIDd"] - p["Y1", "LVIDd"])
    meta = df.drop_duplicates("HashedFileName").set_index("HashedFileName")
    out = out.join(meta[["split", "Width", "Height", "FPS", "Frames"]])
    return out


def read_frame(zf, zip_path, frame_idx):
    """從 zip 讀出一支影片的指定畫面（BGR）。"""
    data = zf.read(zip_path)
    fd, tmp = tempfile.mkstemp(suffix=".avi")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        cap = cv2.VideoCapture(tmp)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, img = cap.read()
        cap.release()
    finally:
        os.remove(tmp)
    return img if ok else None


def imwrite(path, img, params=None):
    """支援中文路徑的存圖（cv2.imwrite 在 Windows 寫不了含中文的路徑）"""
    ext = os.path.splitext(str(path))[1] or ".png"
    ok, buf = cv2.imencode(ext, img, params or [])
    if ok:
        buf.tofile(str(path))
    return ok
