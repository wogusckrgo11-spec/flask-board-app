# flask-board-app

Flask + MariaDB로 만든 익명 게시판입니다. 회원가입 없이 글을 쓰고, 글마다 정한 비밀번호로만 수정·삭제할 수 있습니다.

![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-10.5-003545?logo=mariadb&logoColor=white)
![gunicorn](https://img.shields.io/badge/gunicorn-WSGI-499848?logo=gunicorn&logoColor=white)

프레임워크를 최소한으로만 써서, 게시판 한 개가 돌아가는 데 실제로 무엇이 필요한지 코드에서 그대로 보이도록 만들었습니다. ORM·빌드 도구·프론트엔드 프레임워크 없이 **Flask 라우트 + Jinja2 템플릿 + SQL** 세 가지로만 구성되어 있습니다.

---

## 기능

- **글 목록** — 최신 글이 위로 오는 단순 목록
- **글 작성** — 제목·작성자·내용·비밀번호
- **글 상세**
- **글 수정 / 삭제** — 작성 시 정한 비밀번호가 일치할 때만 허용
- **헬스체크** — `/health` 가 DB까지 실제로 왕복해 연결 상태를 JSON으로 반환

로그인·세션·권한 관리는 없습니다. 인증을 "글 단위 비밀번호" 하나로 대체한 구조입니다.

---

## 기술 스택

| 영역 | 사용 기술 | 이유 |
| --- | --- | --- |
| 웹 프레임워크 | Flask 3.0 | 라우트와 요청 처리만 필요해서 |
| 템플릿 | Jinja2 (Flask 내장) | 서버 사이드 렌더링, 별도 빌드 불필요 |
| DB 드라이버 | PyMySQL | 순수 파이썬이라 컴파일러 없이 설치됨 |
| 데이터베이스 | MariaDB 10.5 | MySQL 호환 |
| 스타일 | 템플릿 내장 CSS | 정적 파일 서빙 설정 없이 한 파일로 |
| WSGI 서버 | gunicorn | 운영 구동용 |

---

## 시작하기

### 1. 요구사항

- Python 3.8 이상
- MariaDB 또는 MySQL (로컬에 설치되어 있거나 접속 가능한 서버)

### 2. 데이터베이스 준비

`schema.sql` 이 데이터베이스·테이블·샘플 글을 한 번에 만듭니다.

```bash
mysql -u root -p < schema.sql
```

앱이 쓸 전용 계정을 만들고 권한을 줍니다.

```sql
CREATE USER 'board_user'@'%' IDENTIFIED BY '원하는_비밀번호';
GRANT ALL PRIVILEGES ON board_db.* TO 'board_user'@'%';
FLUSH PRIVILEGES;
```

### 3. 설치와 실행

```bash
git clone https://github.com/wogusckrgo11-spec/flask-board-app.git
cd flask-board-app

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env        # DB_HOST, DB_PASSWORD 등을 채웁니다
set -a && . ./.env && set +a

.venv/bin/python app.py     # http://localhost:8000
```

`schema.sql` 로 만들어진 샘플 글의 수정·삭제 비밀번호는 `test1234` 입니다.

---

## 환경변수

접속 정보는 코드에 하드코딩하지 않고 환경변수로만 받습니다.

| 변수 | 설명 | 기본값 |
| --- | --- | --- |
| `DB_HOST` | DB 서버 주소 | `127.0.0.1` |
| `DB_PORT` | DB 포트 | `3306` |
| `DB_USER` | 앱 전용 계정 | `board_user` |
| `DB_PASSWORD` | 계정 비밀번호 | (없음) |
| `DB_NAME` | 데이터베이스 이름 | `board_db` |
| `SECRET_KEY` | flash 메시지용 세션 키 | 매 기동 시 임의 생성 |

`.env` 와 실제 비밀번호가 담긴 파일은 커밋하지 않습니다(`.gitignore` 에 포함).

---

## 프로젝트 구조

```
app.py                    Flask 애플리케이션 — 라우트 전체 (약 180줄)
schema.sql                DB 스키마 + 샘플 데이터
requirements.txt          Flask, PyMySQL, gunicorn
templates/
  layout.html             공통 레이아웃 (헤더 · flash 메시지 · CSS)
  index.html              글 목록
  detail.html             글 상세 + 삭제 폼
  form.html               글 작성 / 수정 공용 폼
deploy/
  board-app.service       systemd 유닛 (gunicorn 상시 구동)
  nginx-board.conf        nginx 리버스 프록시 설정
.env.example              환경변수 예시
```

---

## 라우트

| 메서드 | 경로 | 함수 | 설명 |
| --- | --- | --- | --- |
| GET | `/` | `index` | 글 목록 (`ORDER BY id DESC`) |
| GET | `/posts/new` | `new_post_form` | 작성 폼 |
| POST | `/posts` | `create_post` | 글 저장 후 상세로 리다이렉트 |
| GET | `/posts/<id>` | `show_post` | 글 상세 |
| GET | `/posts/<id>/edit` | `edit_post_form` | 수정 폼 |
| POST | `/posts/<id>/edit` | `update_post` | 비밀번호 확인 후 수정 |
| POST | `/posts/<id>/delete` | `delete_post` | 비밀번호 확인 후 삭제 |
| GET | `/health` | `health` | DB 왕복 확인 (JSON) |

폼 전송 후에는 항상 리다이렉트합니다(PRG 패턴). 새로고침해도 같은 글이 다시 저장되지 않습니다.

---

## 데이터 모델

테이블은 `posts` 하나뿐입니다.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `id` | `INT AUTO_INCREMENT` | 기본키, 글 번호 |
| `title` | `VARCHAR(200)` | 제목 |
| `author` | `VARCHAR(50)` | 작성자 이름 |
| `content` | `TEXT` | 본문 |
| `password_hash` | `VARCHAR(255)` | 수정·삭제용 비밀번호 **해시** |
| `created_at` | `DATETIME` | 작성 시각 |
| `updated_at` | `DATETIME` | 수정 시각 (`ON UPDATE CURRENT_TIMESTAMP`) |

문자셋은 `utf8mb4` 라 한글과 이모지가 그대로 저장됩니다.

---

## 동작 방식

### 요청 흐름

```
브라우저 ──▶ Flask 라우트 ──▶ PyMySQL ──▶ MariaDB
              └──▶ Jinja2 템플릿 렌더링 ──▶ HTML 응답
```

### DB 연결

커넥션 풀 없이 요청마다 새 커넥션을 열고 `with` 블록으로 닫습니다. 규모가 작을 때는 이쪽이 코드가 훨씬 단순합니다.

```python
def get_connection():
  return pymysql.connect(**get_db_config())
```

DB가 응답하지 않을 때 요청이 무한정 매달리지 않도록 `connect_timeout=5` 를 둡니다. 결과는 `DictCursor` 로 받아 템플릿에서 `post.title` 처럼 이름으로 꺼냅니다.

### 비밀번호 처리

비밀번호는 평문으로 저장하지 않습니다. 저장할 때 `generate_password_hash()` 로 해시하고, 수정·삭제 시 `check_password_hash()` 로 대조만 합니다. DB가 통째로 노출되어도 원래 비밀번호는 복원되지 않습니다.

```python
# 저장
generate_password_hash(password)

# 확인
if not check_password_hash(post["password_hash"], request.form.get("password", "")):
    flash("비밀번호가 일치하지 않습니다.")
```

권한 확인은 **저장 시점**에만 합니다. 수정 폼은 누구나 열 수 있고, 실제로 반영되는 순간에 비밀번호를 대조합니다.

### SQL 인젝션 방어

모든 쿼리는 문자열 포매팅 대신 플레이스홀더(`%s`)로 값을 넘깁니다.

```python
cur.execute("SELECT ... FROM posts WHERE id = %s", (post_id,))
```

### 템플릿

`layout.html` 을 `{% extends %}` 로 상속해 헤더·flash 메시지·CSS를 공유합니다. 작성 폼과 수정 폼은 `form.html` 하나를 `post` 값이 있는지로 구분해 재사용합니다(`post=None` 이면 작성). CSS는 `layout.html` 안에 들어 있어 정적 파일 서빙 설정이 필요 없고, `prefers-color-scheme` 에 맞춰 다크 모드로 바뀝니다.

---

## 배포

운영에서는 Flask 내장 서버 대신 gunicorn으로 띄우고 앞단에 nginx를 둡니다.

```
브라우저 ──80──▶ nginx ──8000──▶ gunicorn ──▶ Flask ──3306──▶ MariaDB
                (외부 공개)      (127.0.0.1)
```

`deploy/` 의 두 파일을 그대로 쓰면 됩니다.

```bash
sudo cp deploy/board-app.service /etc/systemd/system/
sudo cp deploy/nginx-board.conf  /etc/nginx/conf.d/board.conf

sudo install -m 600 .env.example /etc/board-app.env   # 실제 값으로 수정
sudo systemctl enable --now board-app
sudo systemctl restart nginx

curl http://localhost/health
# {"db":"connected","status":"ok"}
```

gunicorn은 `127.0.0.1:8000` 에만 바인딩하므로 8000 포트를 외부에 열 필요가 없습니다. DB 비밀번호는 `/etc/board-app.env`(권한 600)에만 두고 systemd의 `EnvironmentFile` 로 주입합니다.

> 이 앱은 AWS 2-tier 인프라 실습(퍼블릭 서브넷 웹서버 + 프라이빗 서브넷 DB서버)에서 배포 대상으로 쓰였습니다. 인프라 구축 과정은 **[aws-2tier-web-db](https://github.com/wogusckrgo11-spec/aws-2tier-web-db)** 에 단계별로 정리되어 있습니다.
