from collections import Counter
from flask import Flask, jsonify, render_template_string, request

from config import ALERT_SERVER_PORT
from utils import append_json, load_json_list, now_iso

app = Flask(__name__)

DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini SOC Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #1f2937; }
    main { max-width: 1100px; margin: 0 auto; padding: 28px 18px 48px; }
    h1 { margin-bottom: 6px; }
    .sub { color: #6b7280; margin-top: 0; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 22px 0; }
    .card { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; }
    .value { font-size: 28px; font-weight: 700; margin-top: 5px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }
    th, td { padding: 11px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; font-size: 14px; }
    th { background: #f9fafb; }
    .section { margin-top: 26px; }
    code { font-size: 12px; }
  </style>
</head>
<body>
<main>
  <h1>Mini SOC Dashboard</h1>
  <p class="sub">incidents.json 기준 현재 저장된 탐지/대응 결과입니다.</p>

  <div class="cards">
    <div class="card"><div>전체 사건</div><div class="value">{{ total }}</div></div>
    <div class="card"><div>HIGH</div><div class="value">{{ severity.get("high", 0) }}</div></div>
    <div class="card"><div>MEDIUM</div><div class="value">{{ severity.get("medium", 0) }}</div></div>
    <div class="card"><div>LOW</div><div class="value">{{ severity.get("low", 0) }}</div></div>
  </div>

  <div class="section">
    <h2>주요 공격 IP</h2>
    <table>
      <thead><tr><th>IP</th><th>사건 수</th></tr></thead>
      <tbody>
      {% for ip, count in top_ips %}
        <tr><td><code>{{ ip }}</code></td><td>{{ count }}</td></tr>
      {% else %}
        <tr><td colspan="2">아직 사건이 없습니다.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>최근 사건</h2>
    <table>
      <thead>
        <tr><th>시간</th><th>규칙</th><th>위험도</th><th>IP</th><th>대응</th><th>결과</th></tr>
      </thead>
      <tbody>
      {% for item in recent %}
        <tr>
          <td>{{ item.get("created_at", item.get("received_at", "-")) }}</td>
          <td>{{ item.get("alert", {}).get("rule", "-") }}</td>
          <td>{{ item.get("judgment", {}).get("severity", "-") }}</td>
          <td><code>{{ item.get("alert", {}).get("ip", "-") }}</code></td>
          <td>{{ item.get("judgment", {}).get("tool", "-") }}</td>
          <td>{{ item.get("result", {}).get("status", "-") }}</td>
        </tr>
      {% else %}
        <tr><td colspan="6">아직 사건이 없습니다.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</main>
</body>
</html>
"""


@app.get("/status")
def status():
    return jsonify({
        "ok": True,
        "service": "mini-soc-alert-server",
        "incident_count": len(load_json_list("incidents.json")),
        "dashboard": "/dashboard",
    })


@app.get("/help")
def help_page():
    return jsonify({
        "POST /alert": "경보/사건 수신",
        "GET /status": "서버 상태 확인",
        "GET /help": "API 도움말",
        "GET /dashboard": "Mini SOC 관제 대시보드",
        "GET /api/incidents": "저장된 사건 JSON 조회",
    })


@app.get("/api/incidents")
def incidents_api():
    incidents = load_json_list("incidents.json")
    return jsonify({"count": len(incidents), "incidents": incidents})


@app.get("/dashboard")
def dashboard():
    incidents = load_json_list("incidents.json")
    severity = Counter(
        item.get("judgment", {}).get("severity", "unknown")
        for item in incidents
    )
    ip_counts = Counter(
        item.get("alert", {}).get("ip")
        for item in incidents
        if item.get("alert", {}).get("ip")
    )
    return render_template_string(
        DASHBOARD_TEMPLATE,
        total=len(incidents),
        severity=severity,
        top_ips=ip_counts.most_common(10),
        recent=list(reversed(incidents[-20:])),
    )


@app.post("/alert")
def alert():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "JSON object required"}), 400
    payload.setdefault("received_at", now_iso())
    append_json("incidents.json", payload)
    return jsonify({
        "ok": True,
        "message": "incident stored",
        "received_at": payload["received_at"],
    }), 201


if __name__ == "__main__":
    print(f"[Mini SOC] Alert Server 시작: http://127.0.0.1:{ALERT_SERVER_PORT}")
    print(f"[Mini SOC] Dashboard: http://127.0.0.1:{ALERT_SERVER_PORT}/dashboard")
    app.run(host="127.0.0.1", port=ALERT_SERVER_PORT, debug=False)
