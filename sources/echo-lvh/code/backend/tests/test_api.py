"""後端測試：在 backend 資料夾執行 `pytest -q`。
沒有 best.pt 時會用隨機權重的模型，只測試流程是否正確，不測準確度。
"""
import io
import os
from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("GOOGLE_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import config, main, measure, report  # noqa: E402

config.GEMINI_API_KEY = None
client = TestClient(main.app)

if not main.model.loaded:      # 沒有訓練好的模型 → 用隨機權重測流程
    main.model.loaded = True


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_measure_rules():
    pts = np.array([[100, 300], [100, 290], [100, 240], [100, 228]], float)   # 10 / 50 / 12 px
    r = measure.compute(pts, 0.1, "dataset")
    assert r["measurements_cm"] == {"LVPWd": 1.0, "LVIDd": 5.0, "IVSd": 1.2}
    assert r["lvh_suspected"] and r["thick_walls"] == ["IVSd"]
    assert r["rwt"] == 0.4 and not r["rwt_increased"]


def test_number_check():
    res = measure.compute(np.array([[0, 0], [0, 10], [0, 60], [0, 72]], float), 0.1, "dataset")
    assert report.check_numbers("IVSd 1.20 cm、LVPWd 1.00 cm、LVIDd 5.00 cm、RWT 0.40，門檻 1.1", res) == []
    assert report.check_numbers("IVSd 1.35 cm", res) == ["1.35"]
    t = report.template_report(res)
    assert report.check_numbers(t["professional"] + t["plain"], res) == []


def test_analyze_upload_and_report():
    img = (np.random.rand(600, 800) * 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", img)
    r = client.post("/analyze", files={"file": ("x.png", io.BytesIO(buf.tobytes()), "image/png")},
                    data={"with_report": "true"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert set(j["points"]) == set(config.KEYPOINTS)
    assert j["scale_source"] == "estimated" and j["image_size"] == {"width": 800, "height": 600}
    assert j["report"]["source"] == "template" and j["report"]["number_check"] == "pass"
    r2 = client.post("/report", json=j)
    assert r2.status_code == 200 and "非醫療診斷" in r2.json()["plain"]


def test_bad_image():
    r = client.post("/analyze", files={"file": ("x.png", io.BytesIO(b"not an image"), "image/png")})
    assert r.status_code == 400


@pytest.mark.skipif(len(main.samples) == 0, reason="沒有範例資料")
def test_samples():
    s = client.get("/samples?limit=3").json()
    assert len(s) == 3
    assert client.get(s[0]["image_url"]).status_code == 200
    j = client.post("/analyze", data={"sample_id": s[0]["id"]}).json()
    assert j["scale_source"] == "dataset" and j["ground_truth_cm"] is not None


def test_preprocess_matches_training():
    # 前處理需與訓練時一致：800×600 → 補成 800×800 → 256，倍率 0.32
    x, scale = main.model.preprocess(np.zeros((600, 800), np.uint8))
    assert x.shape == (3, 256, 256) and abs(scale - 0.32) < 1e-9


def test_loads_384_resnet34_from_checkpoint(tmp_path):
    """v3b/v3c：解析度與骨幹要從 best.pt 自動讀取"""
    import segmentation_models_pytorch as smp
    from app.model import KeypointModel
    net = smp.Unet("resnet34", encoder_weights=None, in_channels=3, classes=4)
    p = tmp_path / "best.pt"
    torch.save({"model": net.state_dict(), "epoch": 3, "config": {"img": 384, "encoder": "resnet34", "run": "v3c"}}, p)
    m = KeypointModel(p)
    assert m.loaded and m.img == 384 and m.encoder == "resnet34"
    x, scale = m.preprocess(np.zeros((768, 1024), np.uint8))
    assert x.shape == (3, 384, 384) and abs(scale - 0.375) < 1e-9
    img = (np.random.rand(600, 800) * 255).astype(np.uint8)
    a, b = m.predict(img, tta=False), m.predict(img, tta=True)
    assert a.points.shape == b.points.shape == (4, 2)
    assert (a.points >= -1).all() and (a.points[:, 0] <= 801).all()


def test_tta_unwarp_roundtrip():
    """TTA 的座標轉換：平移/縮放後再轉回來，要回到原位置"""
    from app.model import TTA, decode, unwarp_pts, warp
    for H in (256, 384):
        ys, xs = torch.meshgrid(torch.arange(H).float(), torch.arange(H).float(), indexing="ij")
        px, py = 0.4 * H, 0.6 * H
        img = torch.exp(-((xs - px) ** 2 + (ys - py) ** 2) / 8)[None, None]
        for dx, dy, s in TTA:
            w = warp(img, dx, dy, s)[0, 0]
            p = decode((w / w.sum())[None, None])
            back = unwarp_pts(p, dx, dy, s, H, H)[0, 0]
            assert ((back[0] - px) ** 2 + (back[1] - py) ** 2).sqrt() < 0.5
