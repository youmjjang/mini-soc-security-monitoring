import json
from pathlib import Path
import requests

from config import ALERT_SERVER_URL, ASK_HIGH_APPROVAL
from detector import detect_all
from llm_judge import judge_alert
from log_reader import read_log_file
from notify import send_slack
from reporter import generate_daily_report
from response_tools import TOOLS
from utils import save_json_list, now_iso

def approve_if_needed(judgment):
    if judgment.get("severity") != "high":
        return True
    if not ASK_HIGH_APPROVAL:
        return False
    print(f"\n[검토] {judgment.get('summary')}")
    answer = input(f"{judgment.get('tool')} 조치를 실행할까요? (y/n) ").strip().lower()
    return answer == "y"

def process_alert(alert):
    print(f"\n[탐지] {alert['rule']} / {alert.get('ip', '-')}")
    judgment = judge_alert(alert)
    print(f"[판단] severity={judgment.get('severity')} tool={judgment.get('tool')}")
    print(f"[이유] {judgment.get('reason')}")

    approved = approve_if_needed(judgment)
    if not approved:
        result = {
            "status": "held",
            "action": judgment.get("tool"),
            "message": "담당자 승인 없이 보류되었습니다.",
            "time": now_iso(),
        }
    else:
        tool = TOOLS.get(judgment.get("tool", "watch"), TOOLS["watch"])
        result = tool(alert)

    incident = {
        "created_at": now_iso(),
        "alert": alert,
        "judgment": judgment,
        "approved": approved,
        "result": result,
    }

    try:
        response = requests.post(ALERT_SERVER_URL, json=incident, timeout=10)
        incident["server_delivery"] = {"status": "sent", "http_status": response.status_code}
        print(f"[서버] POST /alert -> {response.status_code}")
    except requests.RequestException as exc:
        incident["server_delivery"] = {"status": "failed", "error": type(exc).__name__}
        print(f"[서버] 전송 실패: {type(exc).__name__}")

    try:
        slack = send_slack(incident)
        incident["slack"] = slack
        print(f"[Slack] {slack['status']}")
    except requests.RequestException as exc:
        incident["slack"] = {"status": "failed", "error": type(exc).__name__}
        print(f"[Slack] 전송 실패: {type(exc).__name__}")

    return incident

def run(log_path="sample_server.log"):
    print(f"[Mini SOC] 로그 읽기: {log_path}")
    events = read_log_file(log_path)
    print(f"[수집] 이벤트 {len(events)}건")

    alerts = detect_all(events)
    save_json_list("alerts.json", alerts)
    print(f"[탐지] 경보 {len(alerts)}건 → alerts.json 저장")

    incidents = [process_alert(alert) for alert in alerts]
    report_path = generate_daily_report(incidents)
    print(f"\n[보고서] {report_path}")

    (Path(__file__).resolve().parent / "agent_result.json").write_text(
        json.dumps(incidents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("[완료] agent_result.json 저장")
    return incidents

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_server.log"
    run(path)
