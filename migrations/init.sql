create table cards (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  phrase text,
  translate text,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

