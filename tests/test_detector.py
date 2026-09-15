import unittest

from detector import (
    detect_brute_force,
    detect_http_errors,
    detect_night_login,
    detect_password_spraying,
)
from log_reader import parse_login_log


def login(time, user, event, ip="203.0.113.10"):
    return {
        "type": "login",
        "time": time,
        "user": user,
        "event": event,
        "ip": ip,
    }


class LogReaderTests(unittest.TestCase):
    def test_login_parser_accepts_seconds(self):
        event = parse_login_log("03:05:42 admin login_failed 203.0.113.10")
        self.assertIsNotNone(event)
        self.assertEqual(event["time"], "03:05:42")

    def test_login_parser_keeps_minute_format_compatibility(self):
        event = parse_login_log("03:05 admin login_failed 203.0.113.10")
        self.assertIsNotNone(event)
        self.assertEqual(event["time"], "03:05")


class DetectorTests(unittest.TestCase):
    def test_brute_force_detects_five_failures_within_60_seconds(self):
        events = [
            login("10:00:00", "admin", "login_failed"),
            login("10:00:10", "admin", "login_failed"),
            login("10:00:20", "admin", "login_failed"),
            login("10:00:30", "admin", "login_failed"),
            login("10:00:50", "admin", "login_failed"),
        ]
        alerts = detect_brute_force(events)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["rule"], "brute_force")

    def test_brute_force_ignores_failures_outside_60_seconds(self):
        events = [
            login("10:00:00", "admin", "login_failed"),
            login("10:00:20", "admin", "login_failed"),
            login("10:00:40", "admin", "login_failed"),
            login("10:01:20", "admin", "login_failed"),
            login("10:02:00", "admin", "login_failed"),
        ]
        self.assertEqual(detect_brute_force(events), [])

    def test_password_spraying_detects_three_users_within_five_minutes(self):
        events = [
            login("11:00:00", "user1", "login_failed"),
            login("11:01:00", "user2", "login_failed"),
            login("11:04:59", "user3", "login_failed"),
        ]
        alerts = detect_password_spraying(events)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["users"], ["user1", "user2", "user3"])

    def test_password_spraying_ignores_users_spread_over_long_period(self):
        events = [
            login("11:00:00", "user1", "login_failed"),
            login("11:06:00", "user2", "login_failed"),
            login("11:12:00", "user3", "login_failed"),
        ]
        self.assertEqual(detect_password_spraying(events), [])

    def test_night_login_only_detects_success_between_midnight_and_six(self):
        events = [
            login("05:59:59", "night", "login_success"),
            login("06:00:00", "day", "login_success"),
        ]
        alerts = detect_night_login(events)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["user"], "night")

    def test_http_error_detects_4xx(self):
        events = [{
            "type": "nginx",
            "ip": "203.0.113.20",
            "status": 404,
            "path": "/admin",
        }]
        alerts = detect_http_errors(events)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["rule"], "http_error")


if __name__ == "__main__":
    unittest.main()
