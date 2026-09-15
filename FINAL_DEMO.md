# Mini SOC Final Demo

최종 데모는 `sample_server.log`를 사용해 **수집 → 탐지 → 판단 → 승인 → 대응 → 서버 전달 → 알림 처리 → 보고서 생성** 흐름을 확인하는 방식으로 구성했습니다.

## 실행

```powershell
python run_demo.py
```

LLM API Key가 없으면 규칙 기반 fallback 판단을 사용하고, Slack Webhook이 없으면 Slack 단계만 `skipped` 처리됩니다.

## 데모 입력

샘플 로그는 다음 상황을 포함합니다.

- HTTP 404 요청
- 동일 IP의 짧은 시간 내 반복 로그인 실패
- 동일 IP의 다계정 로그인 실패
- 심야 시간대 로그인 성공

## 확인 결과

샘플 로그 11건을 기준으로 다음 6개 경보가 생성되도록 맞췄습니다.

| 규칙 | 건수 | 위험도 |
|---|---:|---|
| HTTP Error | 1 | LOW |
| Brute Force | 1 | HIGH |
| Password Spraying | 1 | HIGH |
| Night Login | 3 | MEDIUM |

위험도 합계:

- HIGH: 2
- MEDIUM: 3
- LOW: 1
- 총 경보: 6

HIGH 경보 2건은 사용자 승인 후 `block_ip` 대응을 **시뮬레이션**하고, 나머지 경보는 `watch`로 처리합니다.

## 생성되는 결과

- `alerts.json`: 탐지 엔진 경보
- `incidents.json`: Alert Server 수신 사건
- `agent_result.json`: 판단·승인·대응·전달 결과
- `reports/YYYY-MM/daily_report_YYYY-MM-DD.md`: 일일 보고서

## 시연에서 보여줄 순서

1. `python run_demo.py` 실행
2. 이벤트 수집 건수 확인
3. 4개 탐지 규칙 결과 확인
4. HIGH 경보 승인 질문에서 `y` 입력
5. `POST /alert` 응답 확인
6. Slack 설정이 없으면 `skipped` 확인
7. 보고서 경로와 `agent_result.json` 생성 확인
8. `http://127.0.0.1:5001/dashboard`에서 사건 수·위험도·공격 IP 확인

## 현재 범위

이 프로젝트의 `block_ip`와 `lock_account`는 실제 방화벽이나 계정을 변경하지 않는 **포트폴리오용 대응 시뮬레이션**입니다. 실제 보안 장비 연동은 현재 범위에 포함하지 않았습니다.

또한 Slack은 Webhook을 설정한 경우에만 실제 전송되며, Webhook이 없는 기본 공개 데모에서는 안전하게 생략됩니다.

## 추가 시연: 실제 로그 지속 감시

샘플 파일 1회 분석 외에 Docker Nginx access log를 계속 감시하는 흐름도 확인할 수 있습니다.

```powershell
docker compose up -d
python run_live.py logs/access.log
```

이 상태에서 브라우저로 `http://localhost:8081`에 접속하거나 존재하지 않는 경로를 요청하면 Nginx access log에 새 줄이 추가됩니다. Mini SOC는 실행 이후 새로 추가된 로그만 읽고 탐지 규칙을 적용합니다.

로그인 이벤트까지 라이브로 시연하려면 별도 `logs/login.log` 파일에 이벤트를 추가하고 두 파일을 함께 감시할 수 있습니다.

```powershell
python run_live.py logs/access.log logs/login.log
```

## 자동 테스트

탐지 시간창과 오탐 방지 조건은 다음 명령으로 확인합니다.

```powershell
python -m unittest discover -s tests -v
```

주요 검증 항목:
- 60초 안의 로그인 실패 5회는 Brute Force 탐지
- 60초 밖으로 분산된 실패는 Brute Force 미탐지
- 300초 안의 서로 다른 계정 3개 실패는 Password Spraying 탐지
- 긴 시간에 흩어진 다계정 실패는 Password Spraying 미탐지
- 06:00 이후 로그인은 Night Login 미탐지
