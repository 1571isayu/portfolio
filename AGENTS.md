# AGENTS.md

本專案的完整 AI 規則寫在 [`CLAUDE.md`](./CLAUDE.md)。任何 AI 工具（Codex、Copilot、Cursor 等）開始工作前請先完整閱讀該文件，並遵守其中所有規則。

最重要的四件事：
1. 純靜態 HTML/CSS/JS，不使用框架與建置工具。
2. 作品資料只放在 `data/works.js`，作品頁從 `templates/work-template.html` 複製。
3. 只寫作者實際提供的事實，缺資料就標 `<p class="todo">待補：……</p>`。
4. 修改後執行 `python scripts/check.py`，全部通過才算完成。
