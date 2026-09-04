-- 게시판 데이터베이스 스키마
-- DB-SERVER(프라이빗 서브넷)의 MariaDB에서 실행한다.

CREATE DATABASE IF NOT EXISTS board_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE board_db;

CREATE TABLE IF NOT EXISTS posts (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  title         VARCHAR(200)  NOT NULL,
  author        VARCHAR(50)   NOT NULL,
  content       TEXT          NOT NULL,
  -- 비밀번호는 평문이 아닌 해시로 저장한다 (werkzeug scrypt 해시)
  password_hash VARCHAR(255)  NOT NULL,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 동작 확인용 샘플 글 (수정/삭제 비밀번호: test1234)
INSERT INTO posts (title, author, content, password_hash) VALUES (
  '첫 번째 글입니다',
  '관리자',
  'WEB-SERVER의 Flask가 프라이빗 서브넷의 MariaDB에서 이 글을 읽어왔다면 웹-DB 연결 성공입니다.',
  'scrypt:32768:8:1$xsaCr2392AIELtY6$98d2c2e7d54adfe27054e0b7906821365fba8a1c67bb9b8e2ca44225ea2c10e80b06113f68cb0b93545826bab74efc93f55fe8468ad91a1ea82498270ccf23fc'
);
