"""設定：全部可以用環境變數或 backend/.env 覆蓋。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")

# 訓練好的模型（從 Google Drive 的 EchoLVH/checkpoints/ 下載）
MODEL_PATH = Path(os.getenv("MODEL_PATH", PROJECT_DIR / "checkpoints" / "best.pt"))
# 範例圖（test set，已知比例尺與醫師量測值）。不設定時自動用與模型解析度相同的資料夾（data/echolvh_256 或 echolvh_384）
SAMPLES_DIR_ENV = os.getenv("SAMPLES_DIR")
DATA_DIR = PROJECT_DIR / "data"

# TTA：推論時把圖平移/縮放 7 次再取中位數，較準但較慢（CPU 約 0.3–1 秒）。設成 0 可關閉
USE_TTA = os.getenv("USE_TTA", "1") == "1"

IMG_SIZE = 256   # 舊版 best.pt 沒有存解析度時的預設值
KEYPOINTS = ["lvpw_outer", "lvpw_lvid", "lvid_ivs", "ivs_outer"]   # 由下往上
SEGMENTS = [("LVPWd", 0, 1), ("LVIDd", 1, 2), ("IVSd", 2, 3)]

# 判讀門檻（專題設定，非臨床標準）
WALL_THRESHOLD_CM = float(os.getenv("WALL_THRESHOLD_CM", "1.1"))
RWT_THRESHOLD = float(os.getenv("RWT_THRESHOLD", "0.42"))

# 信心度門檻：4 個點的峰值機率最小值低於此值 → 標示低信心（雜訊圖約 0.000；拿到正式模型後可再校正）
LOW_CONF_THRESHOLD = float(os.getenv("LOW_CONF_THRESHOLD", "0.002"))

# 上傳的圖若沒有提供比例尺，使用資料集中位數（原始像素 1024 寬時約 0.0255 cm/px）
DEFAULT_CM_PER_PX_AT_1024 = float(os.getenv("DEFAULT_CM_PER_PX_AT_1024", "0.0255"))

# 生成式 AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")   # 最快、免費額度；想要更好的文筆可改 gemini-3.8-flash
GEMINI_TIMEOUT_S = int(os.getenv("GEMINI_TIMEOUT_S", "12"))          # 單次呼叫上限（秒）
GEMINI_TOTAL_BUDGET_S = int(os.getenv("GEMINI_TOTAL_BUDGET_S", "30"))  # 含換模型重試的總上限，超過改用模板
GEMINI_DISABLE_THINKING = os.getenv("GEMINI_DISABLE_THINKING", "0") == "1"   # 只有支援的模型才開
# 主模型忙碌（503/504）時依序改用的備用模型
GEMINI_FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "GEMINI_FALLBACK_MODELS", "gemini-3.1-flash-lite,gemini-2.5-flash-lite").split(",") if m.strip()]
