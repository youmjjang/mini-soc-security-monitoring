# Mini SOC Security Monitoring

Python과 Flask를 이용해 **로그 수집 → 파싱 → 탐지 → 위험도 판단 → 대응 → 알림 → 기록** 흐름을 구현한 미니 보안관제(SOC) 프로젝트입니다.

실제 보안관제의 기본 흐름을 개인 환경에서 직접 구현해보는 것을 목표로 했으며, Nginx 로그와 로그인 이벤트를 분석해 이상 행위를 탐지하고, AI 또는 규칙 기반 판단을 거쳐 대응 결과를 저장합니다.

---

## 1. 프로젝트 핵심 흐름

```text
로그
  ↓
log_reader.py
로그 파싱
  ↓
detector.py
규칙 기반 이상행위 탐지
  ↓
alerts.json
  ↓
llm_judge.py
AI 또는 fallback 규칙 기반 위험도 판단
  ↓
agent_desk.py
HIGH 경보 사용자 승인
  ↓
response_tools.py
lock_account / block_ip / watch
  ↓
Flask POST /alert
  ↓
incidents.json
  ↓
Slack 알림
  ↓
Markdown 일일 보고서
```

---

## 2. 주요 기능

### 로그 파싱
- Nginx access log 파싱
- 로그인 이벤트 로그 파싱
- IP, 시간, HTTP Method, Path, Status Code, Size 추출
- 로그인 성공/실패/로그아웃 이벤트 구조화

### 탐지 규칙
현재 다음 4가지 규칙을 구현했습니다.

| 탐지 규칙 | 기준 | 기본 위험도 |
|---|---|---|
| HTTP Error | HTTP Status Code 400 이상 | LOW |
| Brute Force | 동일 IP에서 60초 이내 로그인 실패 5회 이상 | HIGH |
| Password Spraying | 동일 IP에서 300초 이내 서로 다른 계정 3개 이상 로그인 실패 | HIGH |
| Night Login | 00:00~06:00 로그인 성공 | MEDIUM |

중복 탐지 결과는 `deduplicate_alerts()`에서 제거합니다. 로그인 이벤트 시간은 기존 `HH:MM` 형식과 `HH:MM:SS` 형식을 모두 지원하며, 60초/300초 시간창을 더 정확히 검증하려면 초 단위 로그 사용을 권장합니다.

### 위험도 판단
탐지된 경보는 `llm_judge.py`에서 판단합니다.

- LLM API Key가 있으면 LLM 기반 판단
- API Key가 없거나 호출에 실패하면 규칙 기반 fallback 사용
- 결과 형식
  - `severity`: high / medium / low
  - `summary`
  - `tool`: lock_account / block_ip / watch
  - `reason`

### Human-in-the-Loop
위험도가 `HIGH`인 경우 대응 전에 사용자 승인을 받습니다.

```text
[검토] 동일 IP에서 반복적인 로그인 실패가 탐지되었습니다.
block_ip 조치를 실행할까요? (y/n)
```

승인하지 않으면 해당 대응은 `held` 상태로 보류됩니다.

### 대응 도구
현재 대응은 **실제 시스템 변경이 아닌 포트폴리오용 시뮬레이션**입니다.

- `lock_account`: 계정 잠금 시뮬레이션
- `block_ip`: IP 차단 시뮬레이션
- `watch`: 관찰 대상 등록

### Alert Server
Flask 기반 Alert Server를 사용합니다.

| Method | Endpoint | 기능 |
|---|---|---|
| GET | `/status` | 서버 상태 및 사건 수 확인 |
| GET | `/help` | API 도움말 |
| GET | `/dashboard` | 사건 수·위험도·공격 IP·최근 사건 대시보드 |
| GET | `/api/incidents` | 저장된 사건 JSON 조회 |
| POST | `/alert` | 경보/사건 수신 및 저장 |

기본 포트는 `5001`입니다.

### Slack 알림
`SLACK_WEBHOOK_URL`이 설정되어 있으면 탐지 결과를 Slack으로 전송합니다.

Webhook이 설정되어 있지 않아도 기본 데모는 정상 실행되며, Slack 전송만 `skipped` 처리됩니다.

### 일일 보고서
처리된 사건을 날짜별 Markdown 보고서로 생성합니다.

```text
reports/
└── YYYY-MM/
    └── daily_report_YYYY-MM-DD.md
```

보고서에는 총 사건 수, 위험도별 건수, 탐지 규칙별 건수, 사건 상세와 대응 결과가 포함됩니다.

---

## 3. 기술 스택

- Python
- Flask
- Requests
- python-dotenv
- Docker / Nginx
- JSON
- Markdown
- Slack Webhook
- Gemini OpenAI-compatible API

---

## 4. 프로젝트 구조

```text
mini-soc-security-monitoring/
├── .env.example
├── .gitignore
├── FINAL_DEMO.md
├── README.md
├── agent_desk.py
├── agent_result.json
├── alert_server.py
├── alerts.json
├── config.py
├── detector.py
├── docker-compose.yml
├── incidents.json
├── llm_judge.py
├── log_reader.py
├── live_monitor.py
├── logs/
├── notify.py
├── reporter.py
├── requirements.txt
├── response_tools.py
├── run_demo.py
├── run_live.py
├── sample_server.log
├── tests/
│   └── test_detector.py
└── utils.py
```

### 주요 파일 역할

| 파일 | 역할 |
|---|---|
| `log_reader.py` | Nginx / 로그인 로그 파싱 |
| `live_monitor.py` | 로그 파일에 새로 추가되는 이벤트 지속 감시 |
| `detector.py` | 이상행위 탐지 규칙 |
| `llm_judge.py` | AI 또는 fallback 위험도 판단 |
| `agent_desk.py` | 전체 탐지·판단·대응 흐름 제어 |
| `response_tools.py` | 대응 도구 시뮬레이션 |
| `alert_server.py` | Flask Alert Server |
| `notify.py` | Slack 알림 |
| `reporter.py` | 일일 Markdown 보고서 생성 |
| `run_demo.py` | 서버와 Agent를 한 번에 실행하는 샘플 데모 |
| `run_live.py` | Alert Server와 지속 감시기를 한 번에 실행 |
| `tests/test_detector.py` | 탐지 시간창·오탐 방지 회귀 테스트 |
| `FINAL_DEMO.md` | 최종 시연 순서와 샘플 결과 정리 |
| `alerts.json` | 탐지된 경보 저장 |
| `incidents.json` | Alert Server가 수신한 사건 저장 |
| `agent_result.json` | Agent 최종 처리 결과 저장 |

---

## 5. 실행 방법

### 1) 저장소 준비

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### 2) 기본 데모 실행

```powershell
python run_demo.py
```

`run_demo.py`가 다음 순서로 실행합니다.

```text
Alert Server 실행
→ 서버 상태 확인
→ sample_server.log 분석
→ 탐지
→ 판단
→ 대응
→ Alert Server 전달
→ Slack 알림
→ 보고서 생성
→ agent_result.json 저장
```

LLM API Key와 Slack Webhook이 없어도 fallback 판단을 이용해 기본 데모를 실행할 수 있습니다.


### 3) 실제 로그 지속 감시

Docker Nginx의 access log처럼 계속 추가되는 로그를 감시할 수 있습니다.

\`\`\`powershell
python run_live.py logs/access.log
\`\`\`

여러 로그를 함께 감시하려면 경로를 이어서 지정합니다.

\`\`\`powershell
python run_live.py logs/access.log logs/login.log
\`\`\`

기본 동작은 실행 이후 **새로 추가되는 줄부터** 읽습니다. 기존 내용까지 처음부터 분석하려면 Alert Server를 별도로 실행한 뒤 다음처럼 사용할 수 있습니다.

\`\`\`powershell
python live_monitor.py logs/access.log --from-start
\`\`\`

동일 규칙·대상에 대한 반복 알림은 라이브 세션에서 5분 쿨다운을 적용해 알림 폭주를 줄입니다.

### 4) 웹 대시보드

Alert Server가 실행 중일 때 브라우저에서 다음 주소를 열면 현재 사건 현황을 확인할 수 있습니다.

\`\`\`text
http://127.0.0.1:5001/dashboard
\`\`\`

대시보드는 전체 사건 수, HIGH/MEDIUM/LOW 건수, 주요 공격 IP, 최근 탐지 및 대응 결과를 표시합니다.

### 5) 자동 테스트

외부 테스트 프레임워크 없이 Python 표준 \`unittest\`로 탐지 규칙을 검증합니다.

\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

테스트에는 Brute Force 60초 시간창, Password Spraying 300초 시간창, 시간창 밖 오탐 방지, Night Login 경계값, HTTP Error 탐지가 포함됩니다.


### 샘플 최종 시연 결과

현재 `sample_server.log`는 4개 탐지 규칙이 모두 확인되도록 구성했습니다.

- 입력 이벤트: 11건
- 경보: 6건
- HIGH: 2건
- MEDIUM: 3건
- LOW: 1건
- 탐지 규칙: HTTP Error / Brute Force / Password Spraying / Night Login

자세한 시연 순서와 확인 항목은 [FINAL_DEMO.md](FINAL_DEMO.md)에 정리했습니다.

---

## 6. Docker Nginx 실행

실제 Nginx 로그를 생성하려면 Docker Desktop을 실행한 뒤 다음 명령을 사용합니다.

```powershell
docker compose up -d
```

브라우저에서 다음 주소에 접속하면 Nginx 요청 로그가 생성됩니다.

```text
http://localhost:8081
```

Docker Compose 설정은 호스트의 `./logs` 폴더와 Nginx의 `/var/log/nginx`를 연결합니다. 컨테이너 실행 후 `python run_live.py logs/access.log`를 실행하면 이후 생성되는 요청 로그를 지속 감시할 수 있습니다.

---

## 7. 환경 변수

실제 API Key와 Webhook URL은 코드에 직접 작성하지 않고 `.env`에서 관리합니다.

```env
ALERT_SERVER_URL=http://127.0.0.1:5001/alert
ALERT_SERVER_PORT=5001
SLACK_WEBHOOK_URL=
LLM_API_KEY=
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.5-flash-lite
ASK_HIGH_APPROVAL=true
```

실제 `.env` 파일은 GitHub에 올리지 않으며, 설정 예시는 `.env.example`로 제공합니다.

---

## 8. 결과 파일 구분

### alerts.json
탐지 엔진이 발견한 경보 목록입니다.

### incidents.json
Flask Alert Server가 실제로 수신한 사건 목록입니다.

### agent_result.json
탐지 → 판단 → 승인 → 대응 → 서버 전달 → Slack 처리 결과를 포함한 Agent 최종 결과입니다.

이렇게 각 단계의 결과를 분리하여 전체 처리 흐름을 확인할 수 있도록 구성했습니다.

---

## 9. 구현하면서 배운 점

이 프로젝트를 통해 다음 과정을 직접 연결해보았습니다.

- 웹 서버 로그의 구조 이해
- 문자열 로그를 구조화된 데이터로 변환
- 여러 이벤트를 기준으로 공격 패턴 탐지
- Flask REST API를 통한 서버 간 데이터 전달
- LLM 응답을 프로그램에서 사용할 수 있는 구조로 제한
- API 실패 시 fallback 로직 적용
- 자동 대응 과정에 사용자 승인을 추가하는 Human-in-the-Loop 설계
- 민감한 API Key와 Webhook을 환경 변수로 분리
- 탐지 결과를 JSON과 Markdown으로 기록
- 로그 파일의 증분 변화를 지속 감시하고 중복 알림을 제한
- 시간창 기반 탐지 규칙을 자동 테스트로 회귀 검증

---

## 10. 현재 한계 및 개선 계획

현재 `block_ip`와 `lock_account`는 실제 방화벽이나 계정 시스템을 변경하지 않는 시뮬레이션입니다.

향후에는 다음 기능을 추가할 수 있습니다.

- SQLite 또는 별도 DB 적용
- 탐지 이벤트 검색 및 조건별 필터링
- 장기간 IP별 / 시간대별 통계 저장
- SQLite 또는 별도 DB 기반 사건 저장소 고도화
- 실제 보안 장비 또는 방화벽 API 연동

---

## 한 줄 요약

> Python과 Flask를 활용해 로그를 수집·분석하고 이상 행위를 탐지한 뒤, AI/규칙 기반 판단과 사용자 승인, 대응 시뮬레이션, Slack 알림, 보고서 생성까지 연결한 Mini SOC 프로젝트입니다.
