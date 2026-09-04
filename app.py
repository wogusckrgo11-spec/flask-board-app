"""
게시판 애플리케이션 (Flask)

WEB-SERVER(퍼블릭 서브넷)에서 실행되며,
프라이빗 서브넷의 DB-SERVER에 설치된 MariaDB에 접속한다.

DB 접속 정보는 코드에 하드코딩하지 않고 환경변수로만 받는다.
운영 서버에서는 systemd 유닛의 EnvironmentFile(/etc/board-app.env)이 주입한다.
"""

import os

import pymysql
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# flash 메시지용 세션 키. 실습용이라 없으면 임의값을 사용한다.
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())


def get_db_config():
  """환경변수에서 DB 접속 정보를 읽어온다."""
  return {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "board_user"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "board_db"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    # 프라이빗 서브넷의 DB가 응답하지 않을 때 무한 대기하지 않도록 제한
    "connect_timeout": 5,
  }


def get_connection():
  """요청마다 새 커넥션을 연다. (실습 규모라 커넥션 풀은 쓰지 않는다)"""
  return pymysql.connect(**get_db_config())


@app.route("/health")
def health():
  """
  로드밸런서 없이도 쓸 수 있는 헬스체크.
  DB까지 실제로 왕복해 보므로 웹-DB 연결 검증에 그대로 쓸 수 있다.
  """
  try:
    conn = get_connection()
    with conn:
      with conn.cursor() as cur:
        cur.execute("SELECT 1 AS ok")
        cur.fetchone()
    return {"status": "ok", "db": "connected"}, 200
  except Exception as exc:  # 검증 목적이므로 원인을 그대로 노출한다
    return {"status": "error", "db": "disconnected", "detail": str(exc)}, 500


@app.route("/")
def index():
  """글 목록. 최신 글이 위로 오도록 정렬한다."""
  conn = get_connection()
  with conn:
    with conn.cursor() as cur:
      cur.execute(
        "SELECT id, title, author, created_at FROM posts ORDER BY id DESC"
      )
      posts = cur.fetchall()
  return render_template("index.html", posts=posts)


@app.route("/posts/new")
def new_post_form():
  """글 작성 폼"""
  return render_template("form.html", post=None, action=url_for("create_post"))


@app.route("/posts", methods=["POST"])
def create_post():
  """글 저장. 비밀번호는 해시로만 보관한다."""
  title = request.form.get("title", "").strip()
  author = request.form.get("author", "").strip()
  content = request.form.get("content", "").strip()
  password = request.form.get("password", "")

  if not (title and author and content and password):
    flash("제목, 작성자, 내용, 비밀번호를 모두 입력하세요.")
    return redirect(url_for("new_post_form"))

  conn = get_connection()
  with conn:
    with conn.cursor() as cur:
      cur.execute(
        "INSERT INTO posts (title, author, content, password_hash)"
        " VALUES (%s, %s, %s, %s)",
        (title, author, content, generate_password_hash(password)),
      )
      post_id = cur.lastrowid
    conn.commit()
  return redirect(url_for("show_post", post_id=post_id))


@app.route("/posts/<int:post_id>")
def show_post(post_id):
  """글 상세"""
  post = fetch_post(post_id)
  return render_template("detail.html", post=post)


@app.route("/posts/<int:post_id>/edit")
def edit_post_form(post_id):
  """글 수정 폼. 실제 권한 확인은 저장 시점의 비밀번호 대조로 한다."""
  post = fetch_post(post_id)
  return render_template(
    "form.html", post=post, action=url_for("update_post", post_id=post_id)
  )


@app.route("/posts/<int:post_id>/edit", methods=["POST"])
def update_post(post_id):
  """비밀번호가 일치할 때만 글을 수정한다."""
  post = fetch_post(post_id, with_password=True)
  if not check_password_hash(post["password_hash"], request.form.get("password", "")):
    flash("비밀번호가 일치하지 않습니다.")
    return redirect(url_for("edit_post_form", post_id=post_id))

  title = request.form.get("title", "").strip()
  content = request.form.get("content", "").strip()
  if not (title and content):
    flash("제목과 내용을 모두 입력하세요.")
    return redirect(url_for("edit_post_form", post_id=post_id))

  conn = get_connection()
  with conn:
    with conn.cursor() as cur:
      cur.execute(
        "UPDATE posts SET title = %s, content = %s WHERE id = %s",
        (title, content, post_id),
      )
    conn.commit()
  return redirect(url_for("show_post", post_id=post_id))


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
  """비밀번호가 일치할 때만 글을 삭제한다."""
  post = fetch_post(post_id, with_password=True)
  if not check_password_hash(post["password_hash"], request.form.get("password", "")):
    flash("비밀번호가 일치하지 않습니다.")
    return redirect(url_for("show_post", post_id=post_id))

  conn = get_connection()
  with conn:
    with conn.cursor() as cur:
      cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    conn.commit()
  return redirect(url_for("index"))


def fetch_post(post_id, with_password=False):
  """글 한 건을 조회한다. 없으면 404."""
  columns = "id, title, author, content, created_at, updated_at"
  if with_password:
    columns += ", password_hash"

  conn = get_connection()
  with conn:
    with conn.cursor() as cur:
      cur.execute(f"SELECT {columns} FROM posts WHERE id = %s", (post_id,))
      post = cur.fetchone()
  if post is None:
    abort(404)
  return post


if __name__ == "__main__":
  # 로컬 확인용. 서버에서는 gunicorn이 app 객체를 직접 띄운다.
  app.run(host="0.0.0.0", port=8000, debug=True)
