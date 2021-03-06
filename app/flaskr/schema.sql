-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS query;
DROP TABLE IF EXISTS answer;
DROP TABLE IF EXISTS status;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  user_type INTEGER NOT NULL,
  query_list TEXT,
  profile_pic_filename TEXT,
  global_rank INTEGER DEFAULT 4
);

CREATE TABLE query (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  subtitle TEXT NOT NULL,
  pic_filename TEXT,
  category TEXT NOT NULL,
  top_answer TEXT,
  answer_list TEXT,
  answer_state INTEGER DEFAULT 0,
  machine_answer_id INTEGER DEFAULT 0,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE answer (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upvotes INTEGER NOT NULL DEFAULT 0,
  downvotes INTEGER NOT NULL DEFAULT 0,
  query_id INTEGER NOT NULL,
  content TEXT NOT NULL, 
  username TEXT NOT NULL
);

CREATE TABLE status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  curr_state INTEGER NOT NULL
);
