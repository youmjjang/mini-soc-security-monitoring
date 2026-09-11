import requests
from config import SLACK_WEBHOOK_URL

def format_slack_message(incident):
    alert = incident.get("alert", {})
    judgment = incident.get("judgment", {})
    result = incident.get("result", {})
    return (
        "Mini SOC Alert\n"
        f"Rule: {alert.get('rule')}\n"
        f"Severity: {judgment.get('severity')}\n"
        f"IP: {alert.get('ip', '-')}\n"
        f"Summary: {judgment.get('summary', '-')}\n"
        f"Action: {result.get('action', judgment.get('tool', '-'))}\n"
        f"Result: {result.get('status', '-')}"
    )

def send_slack(incident):
    if not SLACK_WEBHOOK_URL:
        return {"status": "skipped", "reason": "SLACK_WEBHOOK_URL not configured"}
    response = requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": format_slack_message(incident)},
        timeout=10,
    )
    response.raise_for_status()
    return {"status": "sent", "http_status": response.status_code}
