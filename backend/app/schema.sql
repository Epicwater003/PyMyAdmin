-- noinspection SqlNoDataSourceInspectionForFile

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS database;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  access_level TEXT NOT NULL
);

CREATE TABLE database (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  dbname TEXT NOT NULL,
  host TEXT NOT NULL,
  port TEXT NOT NULL
);

