# SOURCE：TabiTabi

- 匯入日期：2026-11-06
- 來源：作者上傳的 `travel-app-main.zip`（GitHub 下載的 main 分支）

## 排除與遮蔽項目
- `firebaseConfig.ts`、`services/firebaseConfig.ts`：Firebase 專案設定值改成 `[已移除]`
- 字型檔（`.ttf`）、角色動畫（`.gif`）、`node_modules/`、`package-lock.json`
- `README.md` 是 Expo 範本的預設內容，不是專案說明

## 作者提供的背景
- 2026 年 5 月，行動應用創新賽，團隊作品
- 像素風格 React Native App；Firebase 身分驗證與即時資料同步；Google Maps 與定位；記帳與匯率換算
- 作者個人分工：大部分的程式（全端）；組員負責美術與一點點前端介面修改

## 作者提供的截圖（2026-11-06）
- `assets/images/tabi-tabi/`：選角色、行程、地圖、背包、交易紀錄、分帳畫面

## 先讀這些檔案
- `code/app.json`：App 名稱 Tabi-Tabi
- `code/app/home.tsx`：建立／加入冒險（旅程）
- `code/app/(tabs)/`：adventure（行程）、map（地圖）、backpack（背包清單）、wallet（記帳與分帳）、team（隊伍）
