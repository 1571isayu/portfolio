# CLAUDE.md — 苡婕的作品紀錄簿

這份文件是給 AI（Claude、Codex、Copilot 等）看的專案規則。
**開始任何修改前，請完整讀過這份文件。** 規則和實際程式衝突時，以這份文件為準，並順手把程式修正回規則。

---

## 1. 專案目的

這是游苡婕（國立臺北教育大學 數位科技設計系，輔系資工）的個人作品集網站，部署在 GitHub Pages。

- 讀者：實習面試官、老師、同學。他們會花 1～3 分鐘看，想快速知道「她做了什麼、負責哪一塊、用了什麼技術」。
- 網站的工作：把每一件作品整理成**同一種格式**的紀錄頁，讓讀者能互相比較，也讓作品可以一件一件持續加上去。
- 運作方式像一個小型 LLM Wiki：
  - `sources/` 放每件作品的**原始資料**（程式碼、README、紀錄），是唯一的事實來源。
  - `works/` 是 AI 讀完原始資料後**整理出來的作品頁**。
  - 每個段落都要標出根據哪個原始檔案，讀者可以點進去查證。
- 最常見的任務是「匯入一件新作品」或「更新某件作品的進度」。

## 2. 技術限制（不要違反）

- 純靜態：HTML + CSS + 原生 JavaScript。**不使用** React、Vue、Tailwind、npm、建置工具。
- 必須能直接用瀏覽器打開 `index.html`（`file://`）正常顯示，也必須能在 GitHub Pages 上運作。
  - 因此作品資料放在 `data/works.js`（設定 `window.WORKS`），**不要**改成 `fetch()` 讀 JSON，`file://` 下會失敗。
- 所有路徑使用**相對路徑**（GitHub Pages 的網址會有 repo 名稱當子路徑，用 `/` 開頭的絕對路徑會壞掉）。
- 外部資源只允許 Google Fonts。不要加入追蹤碼、CDN 函式庫。
- 根目錄有 `.nojekyll`，讓 GitHub Pages 原樣提供 `sources/` 裡的檔案，不要刪除。

## 3. 資料夾結構

```
portfolio/
├── CLAUDE.md              ← 本文件（AI 規則）
├── AGENTS.md              ← 指向本文件，給其他 AI 工具
├── README.md              ← 給人看的簡介與部署方式
├── index.html             ← 首頁：簡介 + 作品目錄（目錄由 works.js 產生）
├── works/
│   └── <slug>.html        ← 每件作品一頁（由 AI 根據 sources/ 整理）
├── sources/
│   ├── README.md          ← 資料集總表
│   └── <slug>/
│       ├── SOURCE.md      ← 來源、排除項目、作者提供的背景、先讀哪些檔案
│       └── code/          ← 原始資料快照（不可修改）
├── data/
│   └── works.js           ← 所有作品的索引資料
├── templates/
│   └── work-template.html ← 新增作品頁時複製這個檔案
├── assets/
│   ├── css/style.css      ← 全站唯一樣式表
│   ├── js/site.js         ← 首頁目錄、篩選、作品頁資訊欄與上下篇導覽
│   └── images/<slug>/     ← 每件作品自己的圖片
└── scripts/
    └── check.py           ← 規則檢查工具，每次修改後執行
```

## 4. 命名規則

| 對象 | 規則 | 例子 |
|---|---|---|
| 作品代號 slug | 小寫英文 + 連字號，2～4 個字，不含年份 | `pin-deal`、`echo-lvh` |
| 作品頁 | `works/<slug>.html` | `works/pin-deal.html` |
| 原始資料 | `sources/<slug>/` | `sources/pin-deal/` |
| 圖片資料夾 | `assets/images/<slug>/` | `assets/images/pin-deal/` |
| 封面圖 | `cover.svg`、`cover.jpg` 或 `cover.png`，比例 16:10 | `assets/images/pin-deal/cover.jpg` |
| 其他圖片 | `01-說明.jpg`、`02-說明.svg`，依出現順序編號 | `01-yu-pay-map.jpg` |

slug 一旦決定就不要改（網址會變）。四個地方（作品頁、原始資料、圖片、works.js）用同一個 slug。

## 5. 作品資料格式（`data/works.js`）

每件作品在 `window.WORKS` 陣列中是一個物件，**依時間新到舊排列**：

```js
{
  slug: "pin-deal",                        // 必填，同檔名
  title: "PinDeal",                        // 必填，作品名
  subtitle: "讓 AI 代理人替乘客協商的共乘 demo", // 必填，一句話，30 字內
  date: "2026-09",                         // 必填，YYYY-MM，作品開始或參賽的月份
  event: "梅竹黑客松",                      // 選填，比賽或課程名稱
  type: "網頁應用",                         // 必填，只能用下方「類型」清單
  role: "待補",                            // 必填，我負責的部分，15 字內；不知道就寫「待補」
  team: "團隊作品",                         // 必填，「個人作品」或「團隊作品」或「N 人團隊」
  status: "已完成",                         // 必填，只能是「進行中」或「已完成」
  tools: ["React 19", "Leaflet"],          // 必填，2～6 個，只列 sources 裡看得到的
  cover: "assets/images/pin-deal/cover.jpg" // 必填，相對於網站根目錄
}
```

**類型（type）只能從這裡選**：`AI 應用`、`網頁應用`、`手機 App`、`網站`、`其他`。
要新增類型時，先在這份文件的清單加上去，再改 `scripts/check.py` 的 `TYPES`，最後才使用。首頁的篩選按鈕會自動依資料產生。

## 6. 原始資料規則（`sources/`）

- `sources/<slug>/code/` 是匯入時的快照，**AI 不可修改裡面的檔案**。要更新就整份重新匯入。
- `SOURCE.md` 必須包含四個小節：來源（含匯入日期）、排除項目、作者提供的背景、先讀這些檔案。
- 「作者提供的背景」只寫作者本人在對話中明確說過的事（比賽名稱、日期、分工），不可推測。
- **匯入前一定要清掉機密**：
  - 不收錄 `.env`、`node_modules/`、`.git/`、`package-lock.json`。
  - 找到 API key、Firebase 設定、密碼時，刪掉整個檔案或把值換成 `[已移除]`，並寫進「排除項目」。
  - 有使用授權限制的資料（例如醫療資料集的影像）不收錄，作品頁也不可放。
- 作者另外提供的截圖也算原始資料：縮小到寬度 1600 px 以內，放到 `assets/images/<slug>/`，並寫進 `SOURCE.md` 的「作者提供的截圖」小節。圖說只能描述截圖上看得到的內容。
- 單一檔案超過 2 MB 不收錄；截圖縮小後放到 `assets/images/<slug>/`。
- 截圖排版：寬的桌面截圖單張全寬；手機直式截圖用 `<div class="shots shots-phone">` 三張一列；小型對話框截圖用 `<div class="shots shots-narrow">`。

## 7. 作品頁格式（`works/<slug>.html`）

一律從 `templates/work-template.html` 複製。每頁的 `<main>` 裡必須依序包含以下六個區塊，用 `data-section` 標記：

| 順序 | `data-section` | 標題 | 要寫什麼 |
|---|---|---|---|
| 1 | `overview` | 作品概要 | 這是什麼、給誰用、解決什麼問題。2～4 句。 |
| 2 | `my-role` | 我負責的部分 | 團隊作品要說清楚分工，以及**自己**做了哪些事。 |
| 3 | `tech` | 技術與工具 | 用了什麼、為什麼選它。可用條列。 |
| 4 | `process` | 製作過程 | 依時間順序的關鍵決定與遇到的問題，用 `<ol class="timeline">`。 |
| 5 | `result` | 目前成果 | 做到哪裡、可以展示什麼。有圖放圖。 |
| 6 | `reflection` | 反思與下一步 | 學到什麼、下一步打算做什麼。 |

**引用來源**：除了 `my-role` 和 `reflection` 之外，每個區塊最後都要有一行來源，連到 `sources/` 裡的實際檔案：

```html
<p class="src">來源：<a href="../sources/pin-deal/code/AGENTS.md">AGENTS.md</a>、<a href="../sources/pin-deal/SOURCE.md">SOURCE.md</a></p>
```

作品頁左側的資訊欄（日期、比賽、類型、角色、團隊、狀態、工具）和頁尾的上下篇導覽，由 `site.js` 依 `works.js` 自動產生，**不要手寫在 HTML 裡**。`<body data-slug="...">` 必須和檔名相同，`<h1>` 必須和 `works.js` 的 `title` 相同。

## 8. 寫作規則

- 使用繁體中文、台灣用語。技術名詞保留英文（LangGraph、FastAPI、React Native）。
- 第一人稱「我」，語氣平實、具體，像實驗紀錄，不要寫成廣告文案。
  - ✗「打造顛覆性的智慧共乘體驗」
  - ✓「2～4 個乘客代理人加 1 個仲裁者，用兩輪方案（v1、v2）和多數決決定共乘方案」
- **只寫 `sources/` 裡查得到的事實。** 數字一定要能在來源檔案找到原文。
- 缺資料時寫成 `<p class="todo">待補：……</p>`，網頁會用虛線框標示，之後再補。不要自己編。
  - 團隊作品的個人分工、得獎名次、心得感想，來源裡通常沒有，一律先標待補。
- `reflection` 區塊的心得必須是作者本人說的；AI 只能整理來源裡已寫明的「下一步」或「限制」。
- 團隊作品必須避免把團隊成果寫成個人功勞：作者分工確認前，用「我們」描述功能。
- 每段不超過 4 句；長內容改用條列。

## 9. 視覺風格

概念是「作品紀錄簿」：每件作品是一頁紀錄。背景是乾淨的素色紙張，**不要加格線、條紋或其他重複花紋**（作者覺得眼睛很亂）。

- 顏色只使用 `style.css` 頂部 `:root` 定義的變數，**不要**在 HTML 或其他地方寫死色碼。
  - `--paper` 紙張底色、`--ink` 主文字、`--ink-soft` 次要文字、`--line` 分隔線與邊框、`--accent` 強調色（藍綠）、`--mark` 螢光筆底色
  - SVG 封面圖是獨立的圖檔，不受此限。
- 字體：標題用「霞鶩文楷 TC」(LXGW WenKai TC)，內文用 Noto Sans TC。
- 版面：內容寬度上限 `--measure`（約 40 個中文字），手機寬度要能正常閱讀。
- 首頁的作品目錄是「紀錄目錄」的列狀排版，不是卡片牆。不要改成卡片格狀。
- 動態效果只有首頁波形線的一次性繪製動畫，並且要尊重 `prefers-reduced-motion`。不要再加入捲動淡入等效果。
- 新增樣式時寫在 `style.css`，並用註解標明屬於哪個區塊。

## 10. 常見任務流程

### A. 匯入一件新作品
1. 決定 slug（見第 4 節）。
2. 把原始資料放進 `sources/<slug>/code/`，依第 6 節清掉機密與大型檔案。
3. 寫 `sources/<slug>/SOURCE.md`，並在 `sources/README.md` 的總表加一列。
4. 先讀 `SOURCE.md` 列出的檔案，再讀其他需要的檔案。
5. 準備封面：有截圖就用截圖或 App icon 合成 `cover.jpg`；沒有就畫一張抽象的 `cover.svg`。
6. 複製 `templates/work-template.html` 為 `works/<slug>.html`，填入六個區塊，每區塊附上來源。
7. 在 `data/works.js` 依時間順序加入資料物件。
8. 執行 `python scripts/check.py`，全部通過才算完成。
9. 用瀏覽器打開 `index.html`，確認目錄、篩選、上下篇導覽和來源連結都正常。

### B. 更新作品進度
- 重新匯入 `sources/<slug>/code/`，更新 `SOURCE.md` 的匯入日期。
- 修改該頁的 `process`（新增 timeline 項目）、`result`、`reflection`。
- 狀態、工具等資訊改變時，只要改 `works.js`，資訊欄會自動更新。
- 作者補上資料後，刪掉對應的 `.todo` 段落。

### C. 修改全站外觀
- 只改 `assets/css/style.css`。改完要檢查首頁和至少一個作品頁。

## 11. AI 修改時必須遵守

1. 先讀本文件，再讀要改的檔案，再動手。
2. 不要刪除或重新命名已存在的作品頁。
3. 不要修改 `sources/*/code/` 裡的檔案。
4. 不要改動與任務無關的檔案。
5. 不要新增框架、套件或建置步驟。
6. 每次修改後執行 `python scripts/check.py`。
7. 規則本身需要改變時（例如新增類型、新增區塊），先更新本文件，再改程式，並在完成回報中說明改了哪條規則。
8. 完成時簡短回報：改了哪些檔案、`check.py` 結果、還有哪些 `.todo` 待補。
