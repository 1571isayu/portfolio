"""第 7 週：評估 AI 報告品質（需要先啟動後端）

用法（在 EchoLVH 資料夾）：
    python ml/05_eval_reports.py --n 30

會對 n 張 test 範例圖呼叫後端 /analyze（含報告），自動計算：
  1. 數字一致率：報告中的數字是否都來自量測結果（後端 number_check）
  2. 結論一致率：報告寫「增厚 / 未增厚」是否與量測判讀一致
  3. 用語檢查：是否出現不該出現的字（診斷為、超過標準…），是否有免責聲明
  4. 速度：每份報告秒數；以及來源（gemini / template）
  5. 量測誤差：模型 vs 醫師（mm），以及肥厚判斷是否與醫師一致
並輸出給同學打分數的可讀性評分表。

輸出（outputs/）：report_eval.csv、report_eval_summary.md、readability_form.csv
"""
import argparse
import csv
import json
import random
import statistics as st
import time
import urllib.request
import uuid
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--server", default="http://127.0.0.1:8000")
ap.add_argument("--n", type=int, default=30)
ap.add_argument("--delay", type=float, default=4.0, help="每次呼叫間隔秒數（避免超過 Gemini 免費額度的每分鐘上限）")
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--out", default="outputs")
args = ap.parse_args()
out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

THR = 1.1
BANNED = ["診斷為", "確診", "罹患", "超過標準", "正常範圍", "高於標準", "建議服用", "藥物", "治療方式"]
DISCLAIMER = "非醫療診斷"
POS_WORDS = ["增厚", "肥厚", "偏厚", "超過本系統", "達"]
NEG_PHRASES = ["未達", "未超過", "沒有超過", "均未", "都沒有", "正常"]


def get(path):
    with urllib.request.urlopen(args.server + path, timeout=30) as r:
        return json.loads(r.read())


def post_form(path, fields):
    boundary = uuid.uuid4().hex
    body = b"".join(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()
    ) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(args.server + path, data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def conclusion_ok(text, lvh):
    """報告的結論是否與量測判讀一致（簡單規則）"""
    has_pos = any(w in text for w in POS_WORDS)
    has_neg = any(w in text for w in NEG_PHRASES)
    return has_pos if lvh else (has_neg and "疑似左心室壁增厚" not in text and "疑似左心室肥厚" not in text)


try:
    h = get("/health")
except Exception as e:
    raise SystemExit(f"連不到後端 {args.server}：請先在另一個終端機啟動後端（cd backend → uvicorn app.main:app --port 8000）\n（{e}）")
print(f"後端：模型 {'✓' if h['model_loaded'] else '✗'}　Gemini {'✓ ' + h['gemini_model'] if h['gemini_configured'] else '✗（會用模板）'}")
samples = get("/samples?limit=1000")
# 分層抽樣：醫師判讀「增厚」與「未增厚」各一半，讓兩種情況都有被測到
thick = [s for s in samples if max(s["ground_truth_cm"]["IVSd"], s["ground_truth_cm"]["LVPWd"]) >= THR]
thin = [s for s in samples if s not in thick]
rng = random.Random(args.seed)
pick = rng.sample(thick, min(len(thick), args.n // 2)) + rng.sample(thin, min(len(thin), args.n - args.n // 2))
rng.shuffle(pick)

rows = []
for i, s in enumerate(pick, 1):
    t0 = time.time()
    try:
        r = post_form("/analyze", {"sample_id": s["id"], "with_report": "true"})
    except Exception as e:
        print(f"[{i}/{len(pick)}] {s['id']} 失敗：{e}")
        continue
    rep = r["report"]
    text = rep["professional"] + "\n" + rep["plain"]
    gt, m = r["ground_truth_cm"], r["measurements_cm"]
    gt_lvh = max(gt["IVSd"], gt["LVPWd"]) >= THR
    row = {
        "case": i, "id": s["id"], "source": rep["source"], "model": rep.get("model") or "template",
        "report_seconds": rep["seconds"], "total_seconds": round(time.time() - t0, 2),
        "number_check": rep["number_check"],
        "conclusion_ok": conclusion_ok(text, r["lvh_suspected"]),
        "banned_words": "、".join(w for w in BANNED if w in text),
        "has_disclaimer": DISCLAIMER in rep["professional"] and DISCLAIMER in rep["plain"],
        "model_lvh": r["lvh_suspected"], "doctor_lvh": gt_lvh, "lvh_agree": r["lvh_suspected"] == gt_lvh,
        **{f"err_{k}_mm": round(abs(m[k] - gt[k]) * 10, 2) for k in ("IVSd", "LVIDd", "LVPWd")},
        "plain": rep["plain"], "professional": rep["professional"],
        "fallback_reason": rep.get("fallback_reason", ""),
    }
    rows.append(row)
    flag = "✓" if row["number_check"] == "pass" and row["conclusion_ok"] and not row["banned_words"] and row["has_disclaimer"] else "⚠"
    print(f"[{i}/{len(pick)}] {flag} {rep['source']:8s} {rep['seconds']:.1f}s 數字:{row['number_check']} 結論:{'OK' if row['conclusion_ok'] else '不一致'}"
          f"{' 用語:' + row['banned_words'] if row['banned_words'] else ''}")
    time.sleep(args.delay)

if not rows:
    raise SystemExit("沒有任何成功的案例，請確認後端有啟動。")

with open(out / "report_eval.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

with open(out / "readability_form.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["案例", "白話版報告", "同學A（1-5）", "同學B（1-5）", "同學C（1-5）", "意見"])
    for r in rows:
        w.writerow([r["case"], r["plain"], "", "", "", ""])

n = len(rows)
pct = lambda k: sum(1 for r in rows if r[k]) / n
gem = [r for r in rows if r["source"] == "gemini"]
secs = [r["report_seconds"] for r in gem] or [r["report_seconds"] for r in rows]
summary = f"""# AI 報告品質評估（{time.strftime('%Y-%m-%d')}）

- 案例數：{n}（醫師判讀增厚 {sum(r['doctor_lvh'] for r in rows)}、未增厚 {sum(not r['doctor_lvh'] for r in rows)}；分層抽樣，seed={args.seed}）
- 報告來源：Gemini {len(gem)} 份、模板 {n - len(gem)} 份（模型：{h['gemini_model'] if h['gemini_configured'] else '未設定'}）

| 指標 | 結果 |
| --- | --- |
| 數字一致率（報告數字皆來自量測結果） | {sum(r['number_check'] == 'pass' for r in rows) / n:.0%} |
| 結論一致率（報告結論與量測判讀一致） | {pct('conclusion_ok'):.0%} |
| 無不當用語（診斷為、超過標準…） | {sum(not r['banned_words'] for r in rows) / n:.0%} |
| 附免責聲明（兩個版本都有） | {pct('has_disclaimer'):.0%} |
| 報告生成時間（平均 / 最長） | {st.mean(secs):.1f} 秒 / {max(secs):.1f} 秒 |

## 量測（同一批案例）
| 量測 | 平均誤差 (mm) |
| --- | --- |
""" + "\n".join(f"| {k} | {st.mean(r[f'err_{k}_mm'] for r in rows):.2f} |" for k in ("IVSd", "LVIDd", "LVPWd")) + f"""

- 肥厚判斷與醫師一致：{pct('lvh_agree'):.0%}

## 需要人工看的案例
""" + ("\n".join(f"- 案例 {r['case']}：" + "、".join(x for x in [
    "數字不一致" if r["number_check"] != "pass" else "",
    "結論不一致" if not r["conclusion_ok"] else "",
    f"用語：{r['banned_words']}" if r["banned_words"] else "",
    "缺免責聲明" if not r["has_disclaimer"] else "",
    f"改用模板（{r['fallback_reason'][:60]}）" if r["source"] != "gemini" and h['gemini_configured'] else "",
] if x) for r in rows if not (r["number_check"] == "pass" and r["conclusion_ok"] and not r["banned_words"] and r["has_disclaimer"]))
   or "- 無") + """

可讀性：請 2–3 位同學填 `readability_form.csv`（1 = 看不懂，5 = 非常清楚），再算平均。
"""
(out / "report_eval_summary.md").write_text(summary, encoding="utf-8")
print("\n" + summary)
print(f"已輸出：{out/'report_eval.csv'}、{out/'report_eval_summary.md'}、{out/'readability_form.csv'}")
