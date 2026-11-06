"""EchoLVH 小助手 — FastAPI 後端

啟動（在 backend 資料夾）：
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
API 文件（自動產生，可直接在網頁上測試）：http://localhost:8000/docs
"""
import json
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from . import config, measure, report
from .model import KeypointModel

app = FastAPI(title="EchoLVH 小助手 API", version="0.1.0",
              description="心臟超音波（PLAX）左心室壁量測 + 生成式 AI 報告。課程專題，非醫療診斷。")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

model = KeypointModel()


def imread_gray(path):
    """支援中文路徑的讀圖（cv2.imread 在 Windows 讀不了含中文的路徑）"""
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_GRAYSCALE) if data.size else None

# 範例圖資料夾：與模型解析度一致（384 的模型配 384 的範例圖，才不會先縮小又放大）
if config.SAMPLES_DIR_ENV:
    config.SAMPLES_DIR = Path(config.SAMPLES_DIR_ENV)
else:
    want = config.DATA_DIR / f"echolvh_{model.img}"
    config.SAMPLES_DIR = want if (want / "labels.csv").exists() else config.DATA_DIR / "echolvh_256"

samples = pd.DataFrame()
if (config.SAMPLES_DIR / "labels.csv").exists():
    lab = pd.read_csv(config.SAMPLES_DIR / "labels.csv")
    samples = lab[lab.split == "test"].set_index("id")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model.loaded, "model_path": str(config.MODEL_PATH),
            "model_info": model.info, "device": model.device, "tta": config.USE_TTA,
            "samples_dir": str(config.SAMPLES_DIR), "gemini_configured": bool(config.GEMINI_API_KEY),
            "gemini_model": config.GEMINI_MODEL, "n_samples": len(samples)}


@app.get("/samples")
def list_samples(limit: int = 30):
    """範例圖清單（test set，訓練時沒看過；附醫師量測值可對照）"""
    rows = samples.head(limit)
    return [{"id": i, "image_url": f"/samples/{i}/image",
             "ground_truth_cm": {k: round(float(r[k]), 2) for k in ("IVSd", "LVIDd", "LVPWd")}}
            for i, r in rows.iterrows()]


@app.get("/samples/{sample_id}/image")
def sample_image(sample_id: str):
    path = config.SAMPLES_DIR / "images" / f"{sample_id}.png"
    if sample_id not in samples.index or not path.exists():
        raise HTTPException(404, "找不到這張範例圖")
    return FileResponse(path, media_type="image/png")


def _analyze(img: np.ndarray, cm_per_px: float | None, scale_source: str) -> dict:
    t0 = time.time()
    pred = model.predict(img)
    h, w = img.shape[:2]
    if cm_per_px is None:
        cm_per_px = config.DEFAULT_CM_PER_PX_AT_1024 * 1024 / max(h, w)
        scale_source = "estimated"
    res = measure.compute(pred.points, cm_per_px, scale_source, pred.confidence)
    res.update({
        "points": {k: [round(float(x), 1), round(float(y), 1)] for k, (x, y) in zip(config.KEYPOINTS, pred.points)},
        "image_size": {"width": w, "height": h},
        "cm_per_px": round(cm_per_px, 5),
        "model_loaded": model.loaded,
        "inference_seconds": round(time.time() - t0, 3),
    })
    return res


@app.post("/analyze")
async def analyze(file: UploadFile | None = File(None, description="超音波圖片（PNG/JPG），胸骨旁長軸切面"),
                  sample_id: str | None = Form(None, description="或改用範例圖 ID"),
                  cm_per_px: float | None = Form(None, description="比例尺：原圖每像素幾公分（不填則估計）"),
                  with_report: bool = Form(False, description="是否同時產生 AI 報告")):
    """上傳圖片（或指定範例圖）→ 4 個點、IVSd/LVIDd/LVPWd、RWT、是否疑似肥厚。"""
    if not model.loaded:
        raise HTTPException(503, f"模型尚未載入：請把 best.pt 放到 {config.MODEL_PATH}")
    gt = None
    if sample_id:
        if sample_id not in samples.index:
            raise HTTPException(404, "找不到這張範例圖")
        r = samples.loc[sample_id]
        img = imread_gray(config.SAMPLES_DIR / "images" / f"{sample_id}.png")
        if img is None:
            raise HTTPException(500, "範例圖讀取失敗")
        res = _analyze(img, float(r.cm_per_px_256), "dataset")
        # 範例圖下方是補成正方形的黑邊；告訴 App 實際影像範圍，顯示時可裁掉
        res["content_size"] = {"width": int(round(r.orig_w * r.scale)), "height": int(round(r.orig_h * r.scale))}
        gt = {k: round(float(r[k]), 2) for k in ("IVSd", "LVIDd", "LVPWd")}
    elif file is not None:
        data = await file.read()
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise HTTPException(400, "無法讀取圖片，請上傳 PNG 或 JPG")
        res = _analyze(img, cm_per_px if cm_per_px and cm_per_px > 0 else None, "user")
    else:
        raise HTTPException(400, "請上傳圖片或提供 sample_id")
    res["ground_truth_cm"] = gt
    if with_report:
        res["report"] = await run_in_threadpool(report.generate_report, res)   # 等 Gemini 時不卡住整個後端
    return res


@app.post("/report")
def make_report(result: dict = Body(..., description="/analyze 的回傳結果")):
    """把量測結果交給 Gemini 寫成專業版與白話版報告（失敗時使用固定模板）。"""
    for k in ("measurements_cm", "rwt", "lvh_suspected", "thick_walls", "rwt_increased", "thresholds", "scale_source"):
        if k not in result:
            raise HTTPException(422, f"缺少欄位：{k}")
    return report.generate_report(result)


@app.post("/chat")
def chat(question: str = Body(..., embed=True), result: dict | None = Body(None, embed=True)):
    """「問 AI」：針對這份量測結果回答使用者的追問。"""
    if not config.GEMINI_API_KEY:
        return {"answer": "目前沒有設定 Gemini API key，暫時無法回答問題。", "source": "none"}
    from google import genai
    from google.genai import types
    sys = ("你是心臟超音波衛教助理，用繁體中文、簡單易懂地回答（150 字以內）。只能引用提供的量測數字；"
           "不做診斷、不給用藥或治療建議；涉及個人健康決定時請對方諮詢醫師。")
    ctx = json.dumps({k: result[k] for k in ("measurements_cm", "rwt", "lvh_suspected") if result and k in result},
                     ensure_ascii=False)
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY,
                              http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_S * 1000))
        resp, *_ = report.call_gemini(client, types, f"量測結果：{ctx}\n問題：{question}",
                                  report.gemini_config(types, system_instruction=sys, temperature=0.4))
        return {"answer": resp.text, "source": "gemini"}
    except Exception as e:
        return {"answer": "AI 暫時無法回應，請稍後再試。", "source": "error", "error": f"{type(e).__name__}"}


@app.get("/gemini/test")
def gemini_test():
    """Gemini 診斷：用最簡單的方式呼叫一次，並列出這把金鑰可用的 Flash 模型。"""
    if not config.GEMINI_API_KEY:
        return {"ok": False, "step": "key", "error": "未設定 GEMINI_API_KEY（backend/.env）"}
    key = config.GEMINI_API_KEY
    info = {"model": config.GEMINI_MODEL, "key_prefix": key[:4] + "…", "key_length": len(key)}
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_S * 1000))
    try:
        names = [m.name.replace("models/", "") for m in client.models.list()]
        info["available_flash_models"] = sorted(n for n in names if "flash" in n)[:30]
        info["model_in_list"] = config.GEMINI_MODEL in names
    except Exception as e:
        info["list_error"] = f"{type(e).__name__}: {e}"[:300]
    try:
        t0 = time.time()
        r = client.models.generate_content(model=config.GEMINI_MODEL, contents="用一句繁體中文打招呼")
        return {"ok": True, **info, "reply": r.text, "seconds": round(time.time() - t0, 2)}
    except Exception as e:
        return {"ok": False, "step": "generate", **info, "error": f"{type(e).__name__}: {e}"[:500]}
