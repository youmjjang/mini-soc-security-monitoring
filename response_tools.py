from utils import now_iso

def lock_account(alert):
    user = alert.get("user") or (alert.get("users") or ["unknown"])[0]
    return {
        "status": "simulated",
        "action": "lock_account",
        "target": user,
        "message": f"{user} 계정 잠금 대응을 시뮬레이션했습니다.",
        "time": now_iso(),
    }

def block_ip(alert):
    ip = alert.get("ip", "unknown")
    return {
        "status": "simulated",
        "action": "block_ip",
        "target": ip,
        "message": f"{ip} IP 차단 대응을 시뮬레이션했습니다.",
        "time": now_iso(),
    }

def watch(alert):
    target = alert.get("ip") or alert.get("user") or "unknown"
    return {
        "status": "watching",
        "action": "watch",
        "target": target,
        "message": f"{target} 이벤트를 관찰 대상으로 등록했습니다.",
        "time": now_iso(),
    }

TOOLS = {
    "lock_account": lock_account,
    "block_ip": block_ip,
    "watch": watch,
}
