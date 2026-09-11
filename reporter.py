from collections import Counter
from datetime import datetime
from pathlib import Path

def generate_daily_report(incidents):
    now = datetime.now().astimezone()
    month_dir = Path(__file__).resolve().parent / "reports" / now.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    path = month_dir / f"daily_report_{now.strftime('%Y-%m-%d')}.md"

    severities = Counter(i.get("judgment", {}).get("severity", "unknown") for i in incidents)
    rules = Counter(i.get("alert", {}).get("rule", "unknown") for i in incidents)

    lines = [
        f"# Mini SOC Daily Report — {now.strftime('%Y-%m-%d')}",
        "",
        f"- 총 사건 수: **{len(incidents)}**",
        f"- HIGH: **{severities.get('high', 0)}**",
        f"- MEDIUM: **{severities.get('medium', 0)}**",
        f"- LOW: **{severities.get('low', 0)}**",
        "",
        "## 탐지 규칙별 건수",
        "",
    ]

    for rule, count in rules.items():
        lines.append(f"- {rule}: {count}")
    if not rules:
        lines.append("- 사건 없음")

    lines += ["", "## 사건 상세", ""]
    for idx, incident in enumerate(incidents, 1):
        alert = incident.get("alert", {})
        judgment = incident.get("judgment", {})
        result = incident.get("result", {})
        lines += [
            f"### {idx}. {alert.get('rule', 'unknown')}",
            f"- 위험도: {judgment.get('severity', '-')}",
            f"- IP: {alert.get('ip', '-')}",
            f"- 요약: {judgment.get('summary', '-')}",
            f"- 대응: {judgment.get('tool', '-')}",
            f"- 실행 결과: {result.get('status', '-')}",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
