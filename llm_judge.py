import json
import requests
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

def fallback_judgment(alert):
    rule = alert.get("rule", "unknown")
    severity = alert.get("severity", "low")
    tool = "block_ip" if rule in {"brute_force", "password_spraying"} else "watch"
    return {
        "severity": severity,
        "summary": alert.get("summary", f"{rule} 경보가 탐지되었습니다."),
        "tool": tool,
        "reason": "LLM 미사용 상태의 규칙 기반 기본 판단입니다.",
        "source": "fallback",
    }

def judge_alert(alert):
    if not LLM_API_KEY:
        return fallback_judgment(alert)

    url = f"{LLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = f"""당신은 Mini SOC의 보안 분석가입니다.
다음 경보를 분석하세요.

경보:
{json.dumps(alert, ensure_ascii=False)}

반드시 JSON만 반환하세요.
형식:
{{
  "severity": "high|medium|low",
  "summary": "한두 문장",
  "tool": "lock_account|block_ip|watch",
  "reason": "선택 이유"
}}"""

    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "보안 이벤트를 짧고 보수적으로 판단하세요."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        result = json.loads(text)
        if result.get("severity") not in {"high", "medium", "low"}:
            raise ValueError("invalid severity")
        if result.get("tool") not in {"lock_account", "block_ip", "watch"}:
            raise ValueError("invalid tool")
        result["source"] = "llm"
        return result
    except Exception as exc:
        result = fallback_judgment(alert)
        result["reason"] += f" (LLM 호출 실패: {type(exc).__name__})"
        return result
