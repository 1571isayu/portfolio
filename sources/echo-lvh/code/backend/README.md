# 後端 API（FastAPI）

## 第一次設定
1. 把 Google Drive `EchoLVH/checkpoints/best.pt` 下載到 `EchoLVH/checkpoints/best.pt`
2. 在 `backend` 資料夾的終端機執行：`pip install -r requirements.txt`
3. （第 5 週）把 `.env.example` 複製一份改名為 `.env`，填入 Gemini API key

## 啟動
```
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
打開瀏覽器到 http://localhost:8000/docs ，可以直接在網頁上測試每個 API。

## API
| 方法 | 路徑 | 用途 |
| --- | --- | --- |
| GET | `/health` | 檢查模型與 Gemini 是否就緒 |
| GET | `/samples` | 範例圖清單（test set，附醫師量測值） |
| GET | `/samples/{id}/image` | 範例圖 |
| POST | `/analyze` | 上傳圖片或指定 `sample_id` → 4 個點、IVSd/LVIDd/LVPWd、RWT、是否疑似肥厚；`with_report=true` 同時產生報告 |
| POST | `/report` | 量測結果 → Gemini 專業版 + 白話版報告（含數字檢查；失敗時用模板） |
| POST | `/chat` | 針對結果追問（「問 AI」） |

## 比例尺（重要）
模型找到的是「像素」位置，換成公分需要比例尺：
- 範例圖：資料集已知比例尺（`scale_source = dataset`），最準
- 上傳圖可填 `cm_per_px`（`user`）；不填就用資料集中位數估計（`estimated`），公分值僅供參考
- RWT 是比值，不受比例尺影響

## 測試
`pytest -q`（沒有 best.pt 時用隨機權重測流程）
