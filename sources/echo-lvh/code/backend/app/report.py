"""模組 C/D：生成式 AI 報告 + 數字一致性檢查 + 離線備用模板。

流程：量測結果（JSON）→ Gemini 產生「專業版」與「白話版」→ 程式檢查報告裡的數字
都來自 JSON → 不一致就重試一次 → 仍失敗或沒有 API key → 使用固定模板。
"""
import json
import re
import time

from . import config

SYSTEM_PROMPT = """你是心臟超音波報告助理，協助把「AI 量測結果」寫成繁體中文報告。
規則：
1. 只能使用輸入 JSON 中的數字，不可自行計算新數字、不可編造數值；數字照抄（公分保留兩位小數）。
2. 判讀結論必須與 JSON 的 lvh_suspected、thick_walls、rwt_increased 一致。
3. 若 scale_source 為 "estimated"，要說明比例尺為估計值、公分數值僅供參考（RWT 是比值，不受影響）。
4. 若 low_confidence 為 true，要提醒影像可能不是胸骨旁長軸切面或品質不佳。
5. 1.1 cm 與 0.42 是「本系統設定的門檻」，不是醫學標準或正常範圍；請寫「超過本系統設定的門檻」，不要寫「超過標準」「高於正常範圍」。
6. 不做疾病診斷、不推測病因、不給治療建議；結尾固定加上：「本結果由 AI 自動產生，僅供學習參考，非醫療診斷。」
輸出 JSON：{"professional": "...", "plain": "..."}
- professional：給醫療人員的簡短報告，3–5 句，使用 IVSd、LVIDd、LVPWd、RWT 等術語。
- plain：給一般民眾的白話說明，4–6 句，解釋每個名詞是什麼（例如心室中隔是左右心室之間的牆；RWT 是「牆的厚度和心室腔大小的比例」，數值偏高代表牆相對於腔室比較厚）。"""

EXAMPLE_IN = {"measurements_cm": {"LVPWd": 1.18, "LVIDd": 4.6, "IVSd": 1.25}, "rwt": 0.51,
              "lvh_suspected": True, "thick_walls": ["IVSd", "LVPWd"], "rwt_increased": True,
              "thresholds": {"wall_cm": 1.1, "rwt": 0.42}, "scale_source": "dataset", "low_confidence": False}
EXAMPLE_OUT = {
    "professional": "舒張末期 IVSd 1.25 cm、LVPWd 1.18 cm，均達 1.1 cm 門檻；LVIDd 4.60 cm。RWT 0.51，高於 0.42。"
                    "整體符合左心室壁增厚之表現，建議由專業醫師結合臨床資料判讀。本結果由 AI 自動產生，僅供學習參考，非醫療診斷。",
    "plain": "這次分析量了心臟的三個地方。心室中隔（左右心室中間的那道牆）厚 1.25 公分，後壁厚 1.18 公分，"
             "都超過本系統設定的 1.1 公分，代表心臟的牆可能比一般人厚。左心室內徑 4.60 公分是心臟腔室的寬度。"
             "RWT 0.51 是牆厚度和腔室大小的比例，數值偏高。這只是 AI 的初步量測，請以醫師的判斷為準。"
             "本結果由 AI 自動產生，僅供學習參考，非醫療診斷。"}

def gemini_config(types, **kw):
    """關掉自動函式呼叫（AFC，會印警告）與「思考」（會變很慢）；短報告不需要。"""
    kw["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
    if config.GEMINI_DISABLE_THINKING:   # gemini-3.5-flash-lite 不接受此參數（會回 400），預設關閉
        kw["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    return types.GenerateContentConfig(**kw)


BUSY_CODES = ("503", "504", "429", "UNAVAILABLE", "DEADLINE_EXCEEDED", "RESOURCE_EXHAUSTED", "timed out", "Timeout")


def call_gemini(client, types, contents, cfg):
    """呼叫 Gemini，回傳 (response, 相容模式, 實際使用的模型)。
    - 遇到 400（參數不被接受）：逐步拿掉可能有問題的設定再試
    - 遇到 503/504/429（Google 伺服器忙碌、逾時、額度）：換下一個備用模型
    - 整體超過 GEMINI_TOTAL_BUDGET_S 秒就放棄（改用模板）"""
    import time as _t
    t_end = _t.time() + config.GEMINI_TOTAL_BUDGET_S
    modes = [("full", lambda c: c)]
    if cfg.thinking_config is not None:
        modes.append(("no_thinking_cfg", lambda c: c.model_copy(update={"thinking_config": None})))
    modes.append(("plain", lambda c: c.model_copy(update={"thinking_config": None, "response_mime_type": None})))
    last = None
    for model in [config.GEMINI_MODEL] + config.GEMINI_FALLBACK_MODELS:
        for name, fix in modes:
            if _t.time() > t_end:
                raise last or TimeoutError("Gemini 總等待時間超過上限")
            try:
                return client.models.generate_content(model=model, contents=contents, config=fix(cfg)), name, model
            except Exception as e:
                last = e
                msg = str(e)
                if "API_KEY" in msg or "PERMISSION_DENIED" in msg or "401" in msg or "403" in msg:
                    raise          # 金鑰問題 → 換模型也沒用，直接改用模板
                if any(c in msg for c in BUSY_CODES):
                    break          # 伺服器忙 → 換下一個模型
                if "400" not in msg and "INVALID_ARGUMENT" not in msg:
                    raise          # 金鑰、網路等其他問題 → 直接往外丟
    raise last


def parse_json(text):
    """解析模型回的 JSON（容忍 ```json 包起來的情況）"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(t[t.find("{"):t.rfind("}") + 1])

NUM_RE = re.compile(r"\d+\.\d+")


def allowed_numbers(result: dict) -> set[float]:
    vals = list(result["measurements_cm"].values()) + [result["rwt"]] + list(result["thresholds"].values())
    out = set()
    for v in vals:
        if v is None:
            continue
        out.add(round(float(v), 2))
        out.add(round(float(v) * 10, 1))   # 允許換算成 mm
    return out


def check_numbers(text: str, result: dict) -> list[str]:
    """回傳報告中「不在輸入 JSON 裡」的小數；空 list = 通過。"""
    ok = allowed_numbers(result)
    return [n for n in NUM_RE.findall(text) if round(float(n), 2) not in ok]


def template_report(r: dict) -> dict:
    m = r["measurements_cm"]
    thr = r["thresholds"]["wall_cm"]
    walls = {"IVSd": "心室中隔", "LVPWd": "左心室後壁"}
    if r["lvh_suspected"]:
        thick = "、".join(r["thick_walls"])
        concl = f"{thick} 達 {thr:.2f} cm 門檻，疑似左心室壁增厚。"
        plain_c = "、".join(walls[w] for w in r["thick_walls"]) + f"超過本系統設定的 {thr:.2f} 公分，心臟的牆可能比一般人厚。"
    else:
        concl = f"IVSd 與 LVPWd 均未達 {thr:.2f} cm 門檻。"
        plain_c = f"心室中隔和後壁都沒有超過本系統設定的 {thr:.2f} 公分。"
    rwt = f"RWT {r['rwt']:.2f}" + ("，高於 0.42。" if r["rwt_increased"] else "。")
    notes = []
    if r["scale_source"] == "estimated":
        notes.append("比例尺為估計值，公分數值僅供參考（RWT 不受影響）。")
    if r.get("low_confidence"):
        notes.append("模型信心度偏低，影像可能不是胸骨旁長軸切面或品質不佳。")
    tail = "本結果由 AI 自動產生，僅供學習參考，非醫療診斷。"
    pro = (f"舒張末期 IVSd {m['IVSd']:.2f} cm、LVIDd {m['LVIDd']:.2f} cm、LVPWd {m['LVPWd']:.2f} cm；{rwt}"
           f"{concl}{''.join(notes)}{tail}")
    plain = (f"心室中隔（左右心室中間的牆）厚 {m['IVSd']:.2f} 公分，左心室後壁厚 {m['LVPWd']:.2f} 公分，"
             f"左心室內徑（心臟腔室的寬度）是 {m['LVIDd']:.2f} 公分。{plain_c}{''.join(notes)}{tail}")
    return {"professional": pro, "plain": plain}


def generate_report(result: dict) -> dict:
    """回傳 {"professional", "plain", "source", "model", "seconds", "number_check"}"""
    t0 = time.time()
    payload = {k: result[k] for k in ("measurements_cm", "rwt", "lvh_suspected", "thick_walls",
                                      "rwt_increased", "thresholds", "scale_source") if k in result}
    payload["low_confidence"] = result.get("low_confidence", False)

    if config.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=config.GEMINI_API_KEY,
                                  http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_S * 1000))
            contents = [
                types.Content(role="user", parts=[types.Part(text=json.dumps(EXAMPLE_IN, ensure_ascii=False))]),
                types.Content(role="model", parts=[types.Part(text=json.dumps(EXAMPLE_OUT, ensure_ascii=False))]),
                types.Content(role="user", parts=[types.Part(text=json.dumps(payload, ensure_ascii=False))]),
            ]
            cfg = gemini_config(types, system_instruction=SYSTEM_PROMPT, temperature=0.3,
                                response_mime_type="application/json")
            for attempt in range(2):
                resp, mode, used_model = call_gemini(client, types, contents, cfg)
                out = parse_json(resp.text)
                bad = check_numbers(out.get("professional", "") + out.get("plain", ""), payload)
                if not bad:
                    return {**out, "source": "gemini", "model": used_model, "attempts": attempt + 1, "compat_mode": mode,
                            "seconds": round(time.time() - t0, 2), "number_check": "pass"}
            fallback_reason = f"數字檢查未通過：{bad}"
        except Exception as e:   # 斷網、額度用完、金鑰錯誤…
            fallback_reason = f"Gemini 呼叫失敗：{type(e).__name__}: {e}"[:300]
    else:
        fallback_reason = "未設定 GEMINI_API_KEY"

    out = template_report(payload)
    return {**out, "source": "template", "model": None, "fallback_reason": fallback_reason,
            "seconds": round(time.time() - t0, 2),
            "number_check": "pass" if not check_numbers(out["professional"] + out["plain"], payload) else "fail"}
