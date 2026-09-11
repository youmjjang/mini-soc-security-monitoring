from flask import Flask, jsonify, request
from config import ALERT_SERVER_PORT
from utils import append_json, load_json_list, now_iso

app = Flask(__name__)

@app.get("/status")
def status():
    return jsonify({
        "ok": True,
        "service": "mini-soc-alert-server",
        "incident_count": len(load_json_list("incidents.json")),
    })

@app.get("/help")
def help_page():
    return jsonify({
        "POST /alert": "경보/사건 수신",
        "GET /status": "서버 상태 확인",
        "GET /help": "API 도움말",
    })

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
    app.run(host="127.0.0.1", port=ALERT_SERVER_PORT, debug=False)
