"""模組 B：由 4 個點算出三個量測值、RWT，並以規則判斷是否疑似左心室肥厚。"""
import numpy as np

from . import config


def compute(points: np.ndarray, cm_per_px: float, scale_source: str, confidence=None) -> dict:
    """points: (4,2) 原圖座標；cm_per_px: 原圖每像素幾公分。"""
    m = {}
    for name, a, b in config.SEGMENTS:
        m[name] = round(float(np.linalg.norm(points[b] - points[a]) * cm_per_px), 2)
    rwt = round(2 * m["LVPWd"] / m["LVIDd"], 2) if m["LVIDd"] > 0 else None
    thr = config.WALL_THRESHOLD_CM
    thick = [k for k in ("IVSd", "LVPWd") if m[k] >= thr]
    result = {
        "measurements_cm": m,
        "rwt": rwt,
        "lvh_suspected": bool(thick),
        "thick_walls": thick,
        "rwt_increased": rwt is not None and rwt > config.RWT_THRESHOLD,
        "thresholds": {"wall_cm": thr, "rwt": config.RWT_THRESHOLD},
        "scale_source": scale_source,     # dataset / user / estimated
    }
    if confidence is not None:
        c = [round(float(v), 3) for v in confidence]
        result["confidence"] = dict(zip(config.KEYPOINTS, c))
        result["low_confidence"] = min(c) < config.LOW_CONF_THRESHOLD   # 太低 → 可能不是 PLAX 切面或影像品質差
    return result
