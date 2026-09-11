import subprocess
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent

def wait_for_server(url="http://127.0.0.1:5001/status", seconds=8):
    for _ in range(seconds * 2):
        try:
            if requests.get(url, timeout=1).ok:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return False

def main():
    print("[1/2] Alert Server 실행")
    server = subprocess.Popen([sys.executable, str(ROOT / "alert_server.py")], cwd=ROOT)
    try:
        if not wait_for_server():
            print("Alert Server 시작 실패")
            return 1
        print("[2/2] Mini SOC Agent 실행")
        result = subprocess.run(
            [sys.executable, str(ROOT / "agent_desk.py"), "sample_server.log"],
            cwd=ROOT,
        )
        return result.returncode
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

if __name__ == "__main__":
    raise SystemExit(main())
