from collections import defaultdict
from datetime import datetime, timedelta


def _parse_event_time(value):
    """로그인 이벤트의 HH:MM 또는 HH:MM:SS 시각을 datetime으로 변환합니다."""
    if not isinstance(value, str):
        return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


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
    """동일 IP에서 지정 시간창 안에 로그인 실패가 threshold 이상이면 탐지합니다."""
    by_ip = defaultdict(list)
    for e in events:
        if e.get("type") == "login" and e.get("event") == "login_failed":
            timestamp = _parse_event_time(e.get("time"))
            if timestamp is not None and e.get("ip"):
                by_ip[e["ip"]].append((timestamp, e))

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
                    "users": sorted({x[1].get("user", "unknown") for x in window}),
                    "count": len(window),
                    "window_seconds": window_seconds,
                    "severity": "high",
                    "summary": f"{window_seconds}초 안에 로그인 실패 {len(window)}회가 탐지되었습니다.",
                })
                break
    return alerts


def detect_password_spraying(events, user_threshold=3, window_seconds=300):
    """동일 IP가 짧은 시간 안에 여러 계정을 시도하는 Password Spraying을 탐지합니다."""
    by_ip = defaultdict(list)
    for e in events:
        if e.get("type") == "login" and e.get("event") == "login_failed":
            timestamp = _parse_event_time(e.get("time"))
            if timestamp is not None and e.get("ip") and e.get("user"):
                by_ip[e["ip"]].append((timestamp, e))

    alerts = []
    for ip, items in by_ip.items():
        items.sort(key=lambda x: x[0])

        for i in range(len(items)):
            start = items[i][0]
            end = start + timedelta(seconds=window_seconds)
            window = [x for x in items[i:] if start <= x[0] <= end]
            users = sorted({x[1]["user"] for x in window})

            if len(users) >= user_threshold:
                alerts.append({
                    "rule": "password_spraying",
                    "ip": ip,
                    "users": users,
                    "count": len(users),
                    "window_seconds": window_seconds,
                    "severity": "high",
                    "summary": (
                        f"{window_seconds}초 안에 동일 IP가 "
                        f"{len(users)}개의 서로 다른 계정에 로그인 실패를 발생시켰습니다."
                    ),
                })
                break
    return alerts


def detect_night_login(events, start_hour=0, end_hour=6):
    alerts = []
    for e in events:
        if e.get("type") != "login" or e.get("event") != "login_success":
            continue

        timestamp = _parse_event_time(e.get("time"))
        if timestamp is None:
            continue

        hour = timestamp.hour
        if start_hour <= hour < end_hour:
            alerts.append({
                "rule": "night_login",
                "ip": e.get("ip"),
                "user": e.get("user"),
                "time": e.get("time"),
                "severity": "medium",
                "summary": f"심야 시간대 로그인 성공이 탐지되었습니다: {e.get('user')} {e.get('time')}",
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
