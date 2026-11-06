"""關鍵點模型：載入 best.pt，輸入一張超音波圖，輸出 4 個點（原圖座標）與信心度。
- 解析度（256/384）與骨幹（resnet18/34）會自動從 best.pt 裡的 config 讀取，換模型不用改程式
- 前處理與訓練時完全相同：灰階 → 右下補黑邊成正方形 → 縮成 IMG×IMG → 正規化 → 複製成 3 通道
- TTA（推論時資料增強）：平移/縮放 7 種版本各預測一次，座標換回原圖後取中位數
"""
from dataclasses import dataclass

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
import torch.nn.functional as F

from . import config

# 與訓練筆記本 06_train_v3 相同的 TTA 設定（平移以 256 為基準的像素，自動依解析度放大）
TTA = [(0, 0, 1.0), (4, 0, 1.0), (-4, 0, 1.0), (0, 4, 1.0), (0, -4, 1.0), (0, 0, 0.95), (0, 0, 1.05)]


@dataclass
class Prediction:
    points: np.ndarray        # (4, 2) 原圖座標 (x, y)
    points_model: np.ndarray  # (4, 2) 模型輸入（IMG×IMG）上的座標
    confidence: np.ndarray    # (4,) 每個點的峰值機率（0–1，越高越有把握）
    scale: float              # 原圖 → 模型輸入的縮放倍率


def decode(prob: torch.Tensor, win: int = 2) -> torch.Tensor:
    """prob: (B,K,H,W) 機率圖 → (B,K,2) 次像素座標（與訓練筆記本相同）"""
    B, K, H, W = prob.shape
    idx = prob.flatten(2).argmax(-1)
    cy, cx = (idx // W).float(), (idx % W).float()
    ys = torch.arange(H, device=prob.device).float()
    xs = torch.arange(W, device=prob.device).float()
    my = ((ys.view(1, 1, H) - cy[..., None]).abs() <= win).float()
    mx = ((xs.view(1, 1, W) - cx[..., None]).abs() <= win).float()
    w = prob.clamp(min=0) * my[..., :, None] * mx[..., None, :]
    s = w.sum((-1, -2)).clamp(min=1e-12)
    return torch.stack([(w.sum(-2) * xs).sum(-1) / s, (w.sum(-1) * ys).sum(-1) / s], -1)


def warp(x, dx, dy, s):
    B, C, H, W = x.shape
    tx, ty = 2 * dx / 256, 2 * dy / 256
    theta = torch.tensor([[1 / s, 0, -tx / s], [0, 1 / s, -ty / s]], dtype=x.dtype, device=x.device).expand(B, 2, 3)
    return F.grid_sample(x, F.affine_grid(theta, x.shape, align_corners=False), align_corners=False, padding_mode="zeros")


def unwarp_pts(p, dx, dy, s, H, W):
    tx, ty = 2 * dx / 256, 2 * dy / 256
    nx = ((2 * p[..., 0] + 1) / W - 1 - tx) / s
    ny = ((2 * p[..., 1] + 1) / H - 1 - ty) / s
    return torch.stack([((nx + 1) * W - 1) / 2, ((ny + 1) * H - 1) / 2], -1)


def to_prob(logits):
    B, K, H, W = logits.shape
    return logits.flatten(2).softmax(-1).view(B, K, H, W)


class KeypointModel:
    def __init__(self, path=config.MODEL_PATH, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.loaded = False
        self.info = {}
        cfg = {}
        ck = None
        if path and path.exists():
            ck = torch.load(path, map_location=self.device, weights_only=False)
            cfg = ck.get("config", {}) if isinstance(ck, dict) else {}
        self.img = int(cfg.get("img", config.IMG_SIZE))
        self.encoder = cfg.get("encoder", "resnet18")
        self.net = smp.Unet(self.encoder, encoder_weights=None, in_channels=3, classes=4)
        if ck is not None:
            self.net.load_state_dict(ck["model"] if "model" in ck else ck)
            self.info = {"run": cfg.get("run", "v1/v2"), "img": self.img, "encoder": self.encoder,
                         "epoch": ck.get("epoch"), "val_mae_mm": ck.get("val")}
            self.loaded = True
        self.net.to(self.device).eval()

    def preprocess(self, img: np.ndarray):
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = img.shape
        side = max(h, w)
        scale = self.img / side
        sq = cv2.copyMakeBorder(img, 0, side - h, 0, side - w, cv2.BORDER_CONSTANT, value=0)
        interp = cv2.INTER_AREA if side >= self.img else cv2.INTER_LINEAR
        small = cv2.resize(sq, (self.img, self.img), interpolation=interp)
        x = torch.from_numpy(small.astype(np.float32) / 255.0)
        x = ((x - 0.45) / 0.225)[None].repeat(3, 1, 1)
        return x, scale

    @torch.no_grad()
    def predict(self, img: np.ndarray, tta: bool | None = None) -> Prediction:
        tta = config.USE_TTA if tta is None else tta
        x, scale = self.preprocess(img)
        x = x[None].to(self.device)
        prob = to_prob(self.net(x).float())
        conf = prob.flatten(2).max(-1).values[0].cpu().numpy()
        if tta:
            H, W = x.shape[-2:]
            outs = [decode(prob)] + [unwarp_pts(decode(to_prob(self.net(warp(x, dx, dy, s)).float())), dx, dy, s, H, W)
                                     for dx, dy, s in TTA[1:]]
            pts = torch.stack(outs).median(0).values[0].cpu().numpy()
        else:
            pts = decode(prob)[0].cpu().numpy()
        return Prediction(points=pts / scale, points_model=pts, confidence=conf, scale=scale)
