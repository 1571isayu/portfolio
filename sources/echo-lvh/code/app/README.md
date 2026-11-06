# EchoLVH 小助手 — 手機 App（Expo）

## 第一次
```
cd app
npm install
```

## 啟動（每次）
1. 先啟動後端（另一個終端機），**一定要加 `--host 0.0.0.0`**，手機才連得到：
   ```
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Windows 第一次會跳出防火牆視窗 → 勾「私人網路」→ 允許。
2. 啟動 App：
   ```
   cd app
   npx expo start
   ```
3. 手機打開 **Expo Go** 掃終端機上的 QR code（iPhone 用相機掃）。

手機和電腦要在同一個 Wi-Fi。App 會自動用「電腦的 IP:8000」連後端；連不到時到首頁「連線狀態 → 設定」手動輸入。
也可以在電腦瀏覽器預覽：在 `npx expo start` 的畫面按 `w`。

## 畫面
| 檔案 | 畫面 |
| --- | --- |
| `src/screens/HomeScreen.tsx` | 首頁：範例圖 / 相簿 / 拍照、連線狀態、最近紀錄 |
| `src/screens/SamplesScreen.tsx` | 範例圖清單（test set，附醫師量測值） |
| `src/screens/ResultScreen.tsx` | 量測結果：圖上畫點與線、三個數值、RWT、是否疑似增厚 |
| `src/screens/ReportScreen.tsx` | Gemini 報告：白話版 / 專業版、數字檢查 |
| `src/screens/ChatScreen.tsx` | 問 AI |
