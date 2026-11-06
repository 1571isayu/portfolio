# 苡婕的作品紀錄簿

游苡婕（國立臺北教育大學 數位科技設計系）的作品集網站。每件作品用同一套五個區塊紀錄：概要、我負責的部分、技術與工具、製作過程、目前成果。

這個專案的重點是 [`CLAUDE.md`](./CLAUDE.md)：一份給 AI 讀的規則文件。網站像一個小型 LLM Wiki：

- `sources/`：每件作品的原始程式碼與紀錄（資料集），匯入前已移除金鑰等機密
- `works/`：AI 依規則讀完原始資料後整理出的作品頁，每段都附來源連結

AI 讀完 `CLAUDE.md` 後，就能照同樣的格式持續匯入新作品。

## 本機瀏覽

直接用瀏覽器打開 `index.html` 即可，不需要安裝任何東西。

## 新增一件作品

對 AI 說：「依照 CLAUDE.md 匯入一件新作品」，並附上專案的程式碼 ZIP。
AI 會把原始資料放進 `sources/<slug>/`、清掉機密、寫 `SOURCE.md`，再複製 `templates/work-template.html` 整理成作品頁、在 `data/works.js` 加入資料，最後執行：

```bash
python scripts/check.py
```

## 部署

GitHub repo → Settings → Pages → Source 選 `Deploy from a branch`，Branch 選 `main`、資料夾 `/ (root)`。
