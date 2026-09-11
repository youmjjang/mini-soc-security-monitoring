from collections import defaultdict
from datetime import datetime, timedelta

def detect_http_errors(events):
    return [{
        "rule": "http_error",
        "ip": e.get("ip"),
        "status": e.get("status"),
        "path": e.get("path"),
        "severity": "low",
        "summary": f"HTTP {e.get('status')} 오류 요청이 탐지되었습니다.",
    } for e in events if e.get("type") == "nginx" and e.get("status", 0) >= 400]

def detect_brute_force(events, threshold=5, window_seconds=60):
    by_ip = defaultdict(list)
    for e in events:
        if e.get("type") == "login" and e.get("event") == "login_failed":
            try:
                by_ip[e["ip"]].append((datetime.strptime(e["time"], "%H:%M"), e))
            except ValueError:
                pass

    alerts = []
    for ip, items in by_ip.items():
        items.sort(key=lambda x: x[0])
        for i in range(len(items)):
            start = items[i][0]
            end = start + timedelta(seconds=window_seconds)
            window = [x for x in items[i:] if start <= x[0] <= end]
            if len(window) >= threshold:
                alerts.append({
                    "rule": "brute_force",
                    "ip": ip,
                    "users": sorted({x[1]["user"] for x in window}),
                    "count": len(window),
                    "severity": "high",
                    "summary": f"{window_seconds}초 안에 로그인 실패 {len(window)}회가 탐지되었습니다.",
                })
                break
    return alerts

def detect_password_spraying(events, user_threshold=3):
    by_ip = defaultdict(set)
    for e in events:
        if e.get("type") == "login" and e.get("event") == "login_failed":
            by_ip[e["ip"]].add(e["user"])

    return [{
        "rule": "password_spraying",
        "ip": ip,
        "users": sorted(users),
        "count": len(users),
        "severity": "high",
        "summary": f"동일 IP가 {len(users)}개의 서로 다른 계정에 로그인 실패를 발생시켰습니다.",
    } for ip, users in by_ip.items() if len(users) >= user_threshold]

def detect_night_login(events, start_hour=0, end_hour=6):
    alerts = []
    for e in events:
        if e.get("type") != "login" or e.get("event") != "login_success":
            continue
        try:
            hour = int(e["time"].split(":")[0])
        except (ValueError, KeyError):
            continue
        if start_hour <= hour < end_hour:
            alerts.append({
                "rule": "night_login",
                "ip": e["ip"],
                "user": e["user"],
                "time": e["time"],
                "severity": "medium",
                "summary": f"심야 시간대 로그인 성공이 탐지되었습니다: {e['user']} {e['time']}",
            })
    return alerts

def deduplicate_alerts(alerts):
    seen, result = set(), []
    for a in alerts:
        key = (a.get("rule"), a.get("ip"), a.get("user"), tuple(a.get("users", [])))
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result

def detect_all(events):
    return deduplicate_alerts(
        detect_http_errors(events)
        + detect_brute_force(events)
        + detect_password_spraying(events)
        + detect_night_login(events)
    )
