-- Create database
CREATE DATABASE IF NOT EXISTS recommendation_system;
USE recommendation_system;

-- Create tables
CREATE TABLE IF NOT EXISTS user (
    uid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS follow (
    id INT AUTO_INCREMENT PRIMARY KEY,
    xid INT NOT NULL,  -- follower
    yid INT NOT NULL,  -- followed
    FOREIGN KEY (xid) REFERENCES user(uid),
    FOREIGN KEY (yid) REFERENCES user(uid)
);

CREATE TABLE IF NOT EXISTS languages (
    lid INT AUTO_INCREMENT PRIMARY KEY,
    language VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS genres (
    gid INT AUTO_INCREMENT PRIMARY KEY,
    genre VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS movies (
    mid INT AUTO_INCREMENT PRIMARY KEY,
    movie VARCHAR(100) NOT NULL,
    lid INT NOT NULL,
    FOREIGN KEY (lid) REFERENCES languages(lid)
);

CREATE TABLE IF NOT EXISTS movies_genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mid INT NOT NULL,
    gid INT NOT NULL,
    FOREIGN KEY (mid) REFERENCES movies(mid),
    FOREIGN KEY (gid) REFERENCES genres(gid)
);

CREATE TABLE IF NOT EXISTS books (
    bid INT AUTO_INCREMENT PRIMARY KEY,
    book VARCHAR(100) NOT NULL,
    lid INT NOT NULL,
    FOREIGN KEY (lid) REFERENCES languages(lid)
);

CREATE TABLE IF NOT EXISTS books_genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bid INT NOT NULL,
    gid INT NOT NULL,
    FOREIGN KEY (bid) REFERENCES books(bid),
    FOREIGN KEY (gid) REFERENCES genres(gid)
);

CREATE TABLE IF NOT EXISTS tvshows (
    tvid INT AUTO_INCREMENT PRIMARY KEY,
    tvshow VARCHAR(100) NOT NULL,
    lid INT NOT NULL,
    FOREIGN KEY (lid) REFERENCES languages(lid)
);

CREATE TABLE IF NOT EXISTS tvshows_genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tvid INT NOT NULL,
    gid INT NOT NULL,
    FOREIGN KEY (tvid) REFERENCES tvshows(tvid),
    FOREIGN KEY (gid) REFERENCES genres(gid)
);

-- User preferences tables
CREATE TABLE IF NOT EXISTS user_movie_lang_pref (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    lid INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (lid) REFERENCES languages(lid)
);

CREATE TABLE IF NOT EXISTS user_movie_gen_pref (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    gid INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (gid) REFERENCES genres(gid)
);

CREATE TABLE IF NOT EXISTS user_book_lang_pref (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    lid INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (lid) REFERENCES languages(lid)
);

CREATE TABLE IF NOT EXISTS user_book_gen_pref (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    gid INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (gid) REFERENCES genres(gid)
);

CREATE TABLE IF NOT EXISTS user_tvshow_lang_pref (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    lid INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (lid) REFERENCES languages(lid)
);

CREATE TABLE IF NOT EXISTS user_tvshow_gen_pref (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    gid INT NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (gid) REFERENCES genres(gid)
);

-- User history tables
CREATE TABLE IF NOT EXISTS user_movie_watched (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    mid INT NOT NULL,
    watch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (mid) REFERENCES movies(mid)
);

CREATE TABLE IF NOT EXISTS user_book_read (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    bid INT NOT NULL,
    read_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (bid) REFERENCES books(bid)
);

CREATE TABLE IF NOT EXISTS user_tvshow_watched (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL,
    tvid INT NOT NULL,
    watch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uid) REFERENCES user(uid),
    FOREIGN KEY (tvid) REFERENCES tvshows(tvid)
);