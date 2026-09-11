# Mini SOC Security Monitoring

Python 기반 미니 보안관제(SOC) 프로젝트입니다.

## 전체 흐름

```text
로그
→ 파싱
→ 탐지
→ alerts.json
→ AI/규칙 기반 판단
→ Human-in-the-loop
→ 대응
→ Flask /alert
→ incidents.json
→ Slack
→ Markdown 일일 보고서
```

## 주요 기능

- Nginx / 로그인 로그 파싱
- HTTP 오류 탐지
- Brute Force 탐지
- Password Spraying 탐지
- Night Login 탐지
- AI 또는 규칙 기반 위험도 판단
- lock_account / block_ip / watch 대응 선택
- HIGH 경보 사람 승인
- Flask Alert Server
- Slack Webhook 알림
- 일일 Markdown 보고서 생성

## 실행

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run_demo.py
```

LLM API Key와 Slack Webhook이 없어도 기본 데모는 실행됩니다.

## 주요 결과 파일

- `alerts.json`: 탐지된 경보
- `incidents.json`: Alert Server가 받은 사건
- `agent_result.json`: Agent 최종 처리 결과
- `reports/YYYY-MM/daily_report_YYYY-MM-DD.md`: 일일 보고서

## Docker Nginx

```powershell
docker compose up -d
```

브라우저에서 `http://localhost:8081` 접속 후 Nginx 로그를 생성할 수 있습니다.

## 보안

실제 API Key와 Slack Webhook은 `.env`에만 넣고 GitHub에는 올리지 않습니다.
`.gitignore`에 `.env`가 포함되어 있습니다.

## 주의

현재 `block_ip`, `lock_account`는 실제 시스템을 변경하지 않는 학습/포트폴리오용 시뮬레이션입니다.
