# flask-board-app

AWS 2-tier 인프라(퍼블릭 서브넷 웹서버 + 프라이빗 서브넷 DB서버) 실습용 익명 게시판입니다.

- **웹**: Flask + gunicorn, 앞단에 nginx 리버스 프록시
- **DB**: MariaDB (프라이빗 서브넷의 별도 EC2)
- **기능**: 글 목록 / 작성 / 상세 / 수정 / 삭제 (글별 비밀번호로 수정·삭제 확인)

## 구조

```
app.py                    Flask 애플리케이션 (라우트 전체)
schema.sql                DB 스키마 + 샘플 데이터
requirements.txt          Flask, PyMySQL, gunicorn
templates/                Jinja2 템플릿
deploy/board-app.service  systemd 유닛 (gunicorn 상시 구동)
deploy/nginx-board.conf   nginx 리버스 프록시 설정
.env.example              환경변수 예시
```

## DB 접속 정보

비밀번호는 코드나 저장소에 두지 않습니다. 아래 환경변수로만 주입합니다.

| 변수 | 설명 | 기본값 |
| --- | --- | --- |
| `DB_HOST` | DB-SERVER 사설 IP | `127.0.0.1` |
| `DB_PORT` | MariaDB 포트 | `3306` |
| `DB_USER` | 앱 전용 계정 | `board_user` |
| `DB_PASSWORD` | 앱 전용 계정 비밀번호 | (없음) |
| `DB_NAME` | 데이터베이스 이름 | `board_db` |
| `SECRET_KEY` | flash 메시지용 세션 키 | 매 기동 시 임의 생성 |

서버에서는 `/etc/board-app.env`(권한 600)에 저장하고 systemd `EnvironmentFile`이 읽습니다.

## 로컬 실행

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && vi .env      # 값 채우기
set -a && . ./.env && set +a
.venv/bin/python app.py              # http://localhost:8000
```

## 서버 배포

`/health` 엔드포인트가 DB까지 실제로 왕복하므로 웹-DB 연결 검증에 사용할 수 있습니다.

```bash
curl http://localhost/health
# {"db":"connected","status":"ok"}
```

배포 절차 전체는 별도 구축 가이드 문서를 따릅니다.
