"""規則檢查工具（見 CLAUDE.md）。用法：在專案根目錄執行 python scripts/check.py"""
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
TYPES = ["AI 應用", "網頁應用", "手機 App", "網站", "其他"]
STATUSES = ["進行中", "已完成"]
SECTIONS = ["overview", "my-role", "tech", "process", "result"]
NEED_SRC = ["overview", "tech", "process", "result"]
REQUIRED = ["slug", "title", "subtitle", "date", "type", "role", "team", "status", "tools", "cover"]
SOURCE_HEADINGS = ["來源", "排除", "作者提供的背景", "先讀這些檔案"]
SLUG_RE = re.compile(r"^[a-z]+(-[a-z]+){1,3}$")
DATE_RE = re.compile(r"^20\d\d-(0[1-9]|1[0-2])$")
SECRET_RE = re.compile(
    r"AIza[0-9A-Za-z_-]{30,}"          # Google / Firebase API key
    r"|sk-or-v1-[0-9a-f]{20,}"         # OpenRouter
    r"|sk-proj-[A-Za-z0-9_-]{20,}"     # OpenAI project key
    r"|sk-ant-[A-Za-z0-9_-]{20,}"      # Anthropic
    r"|gh[pousr]_[A-Za-z0-9]{30,}"     # GitHub token
)
MAX_BYTES = 2 * 1024 * 1024
SELF_SLUG = "this-portfolio"  # 本網站的原始資料就是 repo 本身

errors, warnings = [], []


def load_works():
    text = (ROOT / "data" / "works.js").read_text(encoding="utf-8")
    body = text[text.index("[") : text.rindex("]") + 1]
    body = re.sub(r"//.*", "", body)                    # 移除註解
    body = re.sub(r"(\b[a-z]+)\s*:", r'"\1":', body)      # key 加引號
    body = re.sub(r",\s*([}\]])", r"\1", body)            # 移除尾逗號
    return json.loads(body)


# ---------- works.js 與作品頁 ----------
works = load_works()
seen = set()
dates = []
for i, w in enumerate(works):
    tag = w.get("slug", f"第 {i + 1} 筆")
    for k in REQUIRED:
        if k not in w or w[k] in ("", []):
            errors.append(f"[{tag}] works.js 缺少欄位 {k}")
    slug = w.get("slug", "")
    if not SLUG_RE.match(slug):
        errors.append(f"[{tag}] slug 不符合命名規則（小寫英文 + 連字號，2～4 個字）")
    if slug in seen:
        errors.append(f"[{tag}] slug 重複")
    seen.add(slug)
    if not DATE_RE.match(w.get("date", "")):
        errors.append(f"[{tag}] date 必須是 YYYY-MM")
    dates.append(w.get("date", ""))
    if w.get("type") not in TYPES:
        errors.append(f"[{tag}] type「{w.get('type')}」不在類型清單 {TYPES}")
    if w.get("status") not in STATUSES:
        errors.append(f"[{tag}] status 只能是 {STATUSES}")
    if not 2 <= len(w.get("tools", [])) <= 6:
        errors.append(f"[{tag}] tools 需要 2～6 個")
    if len(w.get("subtitle", "")) > 30:
        warnings.append(f"[{tag}] subtitle 超過 30 字")
    if len(w.get("role", "")) > 15:
        warnings.append(f"[{tag}] role 超過 15 字")
    if w.get("role") == "待補":
        warnings.append(f"[{tag}] role 待補")

    cover = ROOT / w.get("cover", "")
    if not cover.is_file():
        errors.append(f"[{tag}] 找不到封面 {w.get('cover')}")
    elif cover.parent.name != slug or cover.stem != "cover":
        errors.append(f"[{tag}] 封面應放在 assets/images/{slug}/cover.(svg|jpg|png)")

    if slug != SELF_SLUG and not (ROOT / "sources" / slug / "SOURCE.md").is_file():
        errors.append(f"[{tag}] 找不到 sources/{slug}/SOURCE.md")

    page = ROOT / "works" / f"{slug}.html"
    if not page.is_file():
        errors.append(f"[{tag}] 找不到作品頁 works/{slug}.html")
        continue
    html = page.read_text(encoding="utf-8")
    if f'data-slug="{slug}"' not in html:
        errors.append(f"[{tag}] <body data-slug> 和檔名不一致")
    h1 = re.search(r"<h1>(.*?)</h1>", html, re.S)
    if not h1 or h1.group(1).strip() != w.get("title"):
        errors.append(f"[{tag}] <h1> 和 works.js 的 title 不一致")
    found = re.findall(r'data-section="([^"]+)"', html)
    if found != SECTIONS:
        errors.append(f"[{tag}] 區塊順序應為 {SECTIONS}，目前是 {found}")
    for sec in NEED_SRC:
        m = re.search(r'<section data-section="%s">(.*?)</section>' % sec, html, re.S)
        if m and 'class="src"' not in m.group(1):
            errors.append(f"[{tag}] {sec} 區塊缺少來源 <p class=\"src\">")
        if m and slug != SELF_SLUG and f"../sources/{slug}/" not in m.group(1):
            errors.append(f"[{tag}] {sec} 區塊的來源沒有連到 sources/{slug}/")
    if "SLUG" in html or "作品名稱" in html:
        errors.append(f"[{tag}] 還有模板的佔位文字沒替換")
    if re.search(r"#[0-9a-fA-F]{3,6}\b", re.sub(r'href="[^"]*"', "", html)):
        errors.append(f"[{tag}] HTML 裡寫死了色碼，請改用 style.css 的變數")
    for ref in re.findall(r'(?:src|href)="(\.\./[^"#]+)"', html):
        if not (page.parent / ref).resolve().is_file():
            errors.append(f"[{tag}] 連結的檔案不存在：{ref}")
    todos = len(re.findall(r'class="todo"', html))
    if todos:
        warnings.append(f"[{tag}] 還有 {todos} 處待補")

if dates != sorted(dates, reverse=True):
    errors.append("works.js 沒有依 date 由新到舊排列")

for page in (ROOT / "works").glob("*.html"):
    if page.stem not in seen:
        errors.append(f"works/{page.name} 沒有登記在 data/works.js")

# ---------- sources/ ----------
src_root = ROOT / "sources"
for d in sorted(p for p in src_root.iterdir() if p.is_dir()):
    if d.name not in seen:
        errors.append(f"sources/{d.name}/ 沒有對應的作品")
    sm = d / "SOURCE.md"
    if sm.is_file():
        text = sm.read_text(encoding="utf-8")
        for h in SOURCE_HEADINGS:
            if h not in text:
                errors.append(f"sources/{d.name}/SOURCE.md 缺少「{h}」小節")
    if not (d / "code").is_dir():
        errors.append(f"sources/{d.name}/ 缺少 code/ 資料夾")

for f in src_root.rglob("*"):
    if not f.is_file():
        continue
    rel = f.relative_to(ROOT).as_posix()
    if f.name == ".env" or "/node_modules/" in rel or "/.git/" in rel:
        errors.append(f"不可收錄：{rel}")
    if f.stat().st_size > MAX_BYTES:
        errors.append(f"檔案超過 2 MB：{rel}")
    if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".ttf", ".zip", ".pt"}:
        continue
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    if SECRET_RE.search(text):
        errors.append(f"疑似 API key：{rel}（請刪除或換成 [已移除]）")

for w in warnings:
    print("提醒：" + w)
for e in errors:
    print("錯誤：" + e)
if errors:
    print(f"\n未通過：{len(errors)} 個錯誤")
    sys.exit(1)
print(f"\n通過：{len(works)} 件作品都符合 CLAUDE.md 規則")
