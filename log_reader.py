import re

NGINX_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) [^"]+" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)

LOGIN_RE = re.compile(
    r'(?P<time>\d{2}:\d{2}(?::\d{2})?)\s+'
    r'(?P<user>\S+)\s+'
    r'(?P<event>login_success|login_failed|logout)\s+'
    r'(?P<ip>\S+)'
)


def parse_nginx_log(line):
    m = NGINX_RE.search(line.strip())
    if not m:
        return None
    data = m.groupdict()
    data["status"] = int(data["status"])
    data["size"] = 0 if data["size"] == "-" else int(data["size"])
    data["type"] = "nginx"
    return data


def parse_login_log(line):
    m = LOGIN_RE.search(line.strip())
    if not m:
        return None
    data = m.groupdict()
    data["type"] = "login"
    return data


def parse_log(line):
    return parse_login_log(line) or parse_nginx_log(line)


def read_log_file(path):
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            event = parse_log(raw)
            if event:
                events.append(event)
    return events
