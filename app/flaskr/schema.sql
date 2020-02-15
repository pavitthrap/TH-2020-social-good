-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS status;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
  user_type INTEGER NOT NULL,
  query_list TEXT 
);

CREATE TABLE query (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  subtitle TEXT NOT NULL,
  pic_filename TEXT NOT NULL, 
  category TEXT NOT NULL,
  top_answer TEXT, 
  answer_list TEXT, 
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE answer (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upvotes INTEGER DEFAULT 0, 
  downvotes INTEGER DEFAULT 0, 
  query_id INTEGER NOT NULL
)

CREATE TABLE status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  curr_state INTEGER NOT NULL
);