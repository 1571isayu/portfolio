# EchoLVH 小助手

上傳一張心臟超音波（PLAX 切面）圖片 → 自動量測 IVSd / LVIDd / LVPWd → 判斷是否疑似左心室肥厚 → 由 Gemini 生成醫師版與白話版報告。

TAICA 生成式 AI 期末專題。資料：EchoNet-LVH（Stanford，限研究與非商業用途）。**本系統非醫療診斷工具。**

## 資料夾
| 資料夾 | 內容 |
| --- | --- |
| `ml/` | 資料探勘、擷取畫面、模型訓練 |
| `backend/` | FastAPI 後端（第 4 週） |
| `app/` | Expo 手機 App（第 6 週） |
| `docs/` | 每週紀錄與發現 |
| `outputs/` | 程式產生的圖與報表（不進 git） |

## 第 1 週：怎麼跑
```bash
pip install -r requirements.txt
python ml/01_explore_measurements.py --zip "../EchoNet-LVH.zip"
python ml/02_visualize_samples.py --zip "../EchoNet-LVH.zip" --n 10
```
