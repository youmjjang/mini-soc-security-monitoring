import argparse
import time
from pathlib import Path

from agent_desk import process_alert
from detector import detect_all
from log_reader import parse_log
from reporter import generate_daily_report
from utils import save_json_list


def alert_key(alert):
    return (
        alert.get("rule"),
        alert.get("ip"),
        alert.get("user"),
        tuple(alert.get("users", [])),
    )


class LiveMonitor:
    """로그 파일에 새로 추가되는 줄만 읽어 누적 이벤트 기준으로 탐지합니다."""

    def __init__(self, paths, from_start=False, poll_seconds=1.0, max_events=2000):
        self.paths = [Path(path) for path in paths]
        self.from_start = from_start
        self.poll_seconds = poll_seconds
        self.max_events = max_events
        self.positions = {}
        self.events = []
        self.alerts = []
        self.incidents = []
        self.last_alerted_at = {}
        self.cooldown_seconds = 300

    def _read_new_lines(self, path):
        if not path.exists():
            return []

        position = self.positions.get(path)
        with path.open("r", encoding="utf-8", errors="replace") as f:
            if position is None:
                if self.from_start:
                    f.seek(0)
                else:
                    f.seek(0, 2)
                self.positions[path] = f.tell()
                return []

            size = path.stat().st_size
            if size < position:
                position = 0

            f.seek(position)
            lines = f.readlines()
            self.positions[path] = f.tell()
            return lines

    def scan_once(self):
        new_event_count = 0
        for path in self.paths:
            for raw in self._read_new_lines(path):
                event = parse_log(raw)
                if event:
                    self.events.append(event)
                    new_event_count += 1

        if not new_event_count:
            return []

        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        detected = detect_all(self.events)
        new_alerts = []
        now = time.monotonic()
        for alert in detected:
            key = alert_key(alert)
            last_alerted = self.last_alerted_at.get(key)
            if last_alerted is not None and now - last_alerted < self.cooldown_seconds:
                continue
            self.last_alerted_at[key] = now
            self.alerts.append(alert)
            new_alerts.append(alert)

        if new_alerts:
            save_json_list("alerts.json", self.alerts)
            for alert in new_alerts:
                self.incidents.append(process_alert(alert))
            generate_daily_report(self.incidents)

        return new_alerts

    def run_forever(self):
        paths = ", ".join(str(path) for path in self.paths)
        mode = "처음부터" if self.from_start else "새로 추가되는 줄부터"
        print(f"[Live Monitor] 감시 시작: {paths}")
        print(f"[Live Monitor] 읽기 기준: {mode}")
        print("[Live Monitor] 종료: Ctrl+C")

        for path in self.paths:
            self._read_new_lines(path)

        try:
            while True:
                alerts = self.scan_once()
                if alerts:
                    print(f"[Live Monitor] 신규 경보 {len(alerts)}건")
                time.sleep(self.poll_seconds)
        except KeyboardInterrupt:
            print("\n[Live Monitor] 종료")


def main():
    parser = argparse.ArgumentParser(description="Mini SOC 로그 지속 감시")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["logs/access.log"],
        help="감시할 로그 파일. 여러 개 지정 가능 (기본: logs/access.log)",
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="실행 시 기존 로그도 처음부터 분석",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=1.0,
        help="파일 확인 주기(초), 기본 1.0",
    )
    args = parser.parse_args()

    monitor = LiveMonitor(
        args.paths,
        from_start=args.from_start,
        poll_seconds=max(args.poll, 0.2),
    )
    monitor.run_forever()


if __name__ == "__main__":
    main()
