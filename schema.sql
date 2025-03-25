-- Create database
CREATE DATABASE IF NOT EXISTS recsys;
USE recsys;

-- Create tables
CREATE TABLE IF NOT EXISTS user (
    uid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS FOLLOW (
    XID INT,
    YID INT,
    FOREIGN KEY (XID) REFERENCES user(uid),
    FOREIGN KEY (YID) REFERENCES user(uid),
    CONSTRAINT chk_XID_YID_diff CHECK (XID <> YID)
);

CREATE TABLE IF NOT EXISTS LANGUAGES (
    LID INT AUTO_INCREMENT PRIMARY KEY,
    LANGUAGE VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS GENRES (
    GID INT AUTO_INCREMENT PRIMARY KEY,
    GENRE VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS MOVIES (
    MID INT AUTO_INCREMENT PRIMARY KEY,
    MOVIE VARCHAR(255) NOT NULL UNIQUE,
    LID INT,
    FOREIGN KEY (LID) REFERENCES LANGUAGES(LID)
);

CREATE TABLE IF NOT EXISTS BOOKS (
    BID INT AUTO_INCREMENT PRIMARY KEY,
    BOOK VARCHAR(255) NOT NULL UNIQUE,
    LID INT,
    FOREIGN KEY (LID) REFERENCES LANGUAGES(LID)
);

CREATE TABLE IF NOT EXISTS TVSHOWS (
    TVID INT AUTO_INCREMENT PRIMARY KEY,
    TVSHOW VARCHAR(255) NOT NULL UNIQUE,
    LID INT,
    FOREIGN KEY (LID) REFERENCES LANGUAGES(LID)
);

CREATE TABLE IF NOT EXISTS MOVIES_GENRES (
    MID INT,
    GID INT,
    FOREIGN KEY (MID) REFERENCES MOVIES(MID),
    FOREIGN KEY (GID) REFERENCES GENRES(GID),
    PRIMARY KEY (MID, GID)
);

CREATE TABLE IF NOT EXISTS BOOKS_GENRES (
    BID INT,
    GID INT,
    FOREIGN KEY (BID) REFERENCES BOOKS(BID),
    FOREIGN KEY (GID) REFERENCES GENRES(GID),
    PRIMARY KEY (BID, GID)
);

CREATE TABLE IF NOT EXISTS TVSHOWS_GENRES (
    TVID INT,
    GID INT,
    FOREIGN KEY (TVID) REFERENCES TVSHOWS(TVID),
    FOREIGN KEY (GID) REFERENCES GENRES(GID),
    PRIMARY KEY (TVID, GID)
);

CREATE TABLE IF NOT EXISTS USER_MOVIE_LANG_PREF (
    UID INT,
    LID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (LID) REFERENCES LANGUAGES(LID),
    PRIMARY KEY (UID, LID)
);

CREATE TABLE IF NOT EXISTS USER_BOOK_LANG_PREF (
    UID INT,
    LID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (LID) REFERENCES LANGUAGES(LID),
    PRIMARY KEY (UID, LID)
);

CREATE TABLE IF NOT EXISTS USER_TVSHOW_LANG_PREF (
    UID INT,
    LID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (LID) REFERENCES LANGUAGES(LID),
    PRIMARY KEY (UID, LID)
);

CREATE TABLE IF NOT EXISTS USER_MOVIE_GEN_PREF (
    UID INT,
    GID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (GID) REFERENCES GENRES(GID),
    PRIMARY KEY (UID, GID)
);

CREATE TABLE IF NOT EXISTS USER_BOOK_GEN_PREF (
    UID INT,
    GID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (GID) REFERENCES GENRES(GID),
    PRIMARY KEY (UID, GID)
);

CREATE TABLE IF NOT EXISTS USER_TVSHOW_GEN_PREF (
    UID INT,
    GID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (GID) REFERENCES GENRES(GID),
    PRIMARY KEY (UID, GID)
);

CREATE TABLE IF NOT EXISTS USER_TVSHOW_WATCHED (
    UID INT,
    TVID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (TVID) REFERENCES TVSHOWS(TVID),
    PRIMARY KEY (UID, TVID)
);

CREATE TABLE IF NOT EXISTS USER_MOVIE_WATCHED (
    UID INT,
    MID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (MID) REFERENCES MOVIES(MID),
    PRIMARY KEY (UID, MID)
);

CREATE TABLE IF NOT EXISTS USER_BOOK_READ (
    UID INT,
    BID INT,
    FOREIGN KEY (UID) REFERENCES user(uid),
    FOREIGN KEY (BID) REFERENCES BOOKS(BID),
    PRIMARY KEY (UID, BID)
);



-- Table insertions
INSERT INTO GENRES (GENRE) VALUES
    ('Action'),
    ('Romance'),
    ('Thriller'),
    ('Horror'),
    ('Comedy'),
    ('Crime'),
    ('Fantasy'),
    ('Sci-Fi');


INSERT INTO LANGUAGES (LANGUAGE) VALUES
    ('English'),
    ('Hindi'),
    ('Tamil'),
    ('Telugu'),
    ('Malayalam'),
    ('Kannada'),
    ('Korean'),
    ('Chinese'),
    ('Japanese');

INSERT INTO MOVIES (MOVIE, LID) VALUES
    ('Inception', 1),     -- English (Sci-Fi, Thriller)
    ('Titanic', 1),       -- English (Romance, Drama)
    ('The Dark Knight', 1), -- English (Action, Crime)
    ('Dangal', 2),        -- Hindi (Drama, Action)
    ('3 Idiots', 2),      -- Hindi (Comedy, Drama)
    ('Baahubali', 4),     -- Telugu (Action, Fantasy)
    ('Super Deluxe', 3),  -- Tamil (Thriller, Drama)
    ('Drishyam', 5),      -- Malayalam (Thriller, Crime)
    ('K.G.F: Chapter 1', 6), -- Kannada (Action, Crime)
    ('Parasite', 7),      -- Korean (Thriller, Drama)
    ('Train to Busan', 7), -- Korean (Horror, Action)
    ('Crouching Tiger, Hidden Dragon', 8), -- Chinese (Action, Fantasy)
    ('Infernal Affairs', 8), -- Chinese (Crime, Thriller)
    ('Your Name', 9),     -- Japanese (Romance, Fantasy)
    ('Akira', 9),         -- Japanese (Sci-Fi, Action)
    ('Interstellar', 1),  -- English (Sci-Fi, Adventure)
    ('Joker', 1),         -- English (Crime, Drama)
    ('Zindagi Na Milegi Dobara', 2), -- Hindi (Comedy, Drama)
    ('Shershaah', 2),     -- Hindi (Action, War)
    ('Vikram Vedha', 3),  -- Tamil (Thriller, Action)
    ('Eega', 4),          -- Telugu (Fantasy, Action)
    ('Premam', 5),        -- Malayalam (Romance, Drama)
    ('U-Turn', 6),        -- Kannada (Thriller, Horror)
    ('Spirited Away', 9); -- Japanese (Fantasy, Adventure)

INSERT INTO MOVIES_GENRES (MID, GID) VALUES
    (1, 8), (1, 3),  -- Inception (Sci-Fi, Thriller)
    (2, 2),         -- Titanic (Romance)
    (3, 1), (3, 6),  -- The Dark Knight (Action, Crime)
    (4, 1),         -- Dangal (Action)
    (5, 5),         -- 3 Idiots (Comedy)
    (6, 1), (6, 7),  -- Baahubali (Action, Fantasy)
    (7, 3),         -- Super Deluxe (Thriller)
    (8, 3), (8, 6),  -- Drishyam (Thriller, Crime)
    (9, 1), (9, 6),  -- K.G.F: Chapter 1 (Action, Crime)
    (10, 3),        -- Parasite (Thriller)
    (11, 4), (11, 1), -- Train to Busan (Horror, Action)
    (12, 1), (12, 7), -- Crouching Tiger (Action, Fantasy)
    (13, 6), (13, 3), -- Infernal Affairs (Crime, Thriller)
    (14, 2), (14, 7), -- Your Name (Romance, Fantasy)
    (15, 8), (15, 1), -- Akira (Sci-Fi, Action)
    (16, 8),         -- Interstellar (Sci-Fi)
    (17, 6),         -- Joker (Crime)
    (18, 5),         -- Zindagi Na Milegi Dobara (Comedy)
    (19, 1),         -- Shershaah (Action)
    (20, 3), (20, 1), -- Vikram Vedha (Thriller, Action)
    (21, 7), (21, 1), -- Eega (Fantasy, Action)
    (22, 2),         -- Premam (Romance)
    (23, 3), (23, 4), -- U-Turn (Thriller, Horror)
    (24, 7);         -- Spirited Away (Fantasy)


INSERT INTO BOOKS (BOOK, LID) VALUES
    ('To Kill a Mockingbird', 1),  -- English
    ('1984', 1),                   -- English
    ('The Great Gatsby', 1),       -- English
    ('Pride and Prejudice', 1),    -- English
    ('Harry Potter and the Sorcerer''s Stone', 1), -- English
    ('The Alchemist', 1),          -- English
    ('The God of Small Things', 1), -- English
    ('Malgudi Days', 2),           -- Hindi
    ('Godan', 2),                  -- Hindi
    ('Gitanjali', 2),              -- Hindi
    ('Rashmirathi', 2),            -- Hindi
    ('Ponniyin Selvan', 3),        -- Tamil
    ('Sivagamiyin Sabatham', 3),   -- Tamil
    ('Parthiban Kanavu', 3),       -- Tamil
    ('Karisal', 3);                -- Tamil


INSERT INTO BOOKS_GENRES (BID, GID) VALUES
    (1, 6),  -- To Kill a Mockingbird (Crime)
    (2, 8),  -- 1984 (Sci-Fi)
    (3, 5),  -- The Great Gatsby (Comedy)
    (4, 2),  -- Pride and Prejudice (Romance)
    (5, 7),  -- Harry Potter (Fantasy)
    (6, 7),  -- The Alchemist (Fantasy)
    (7, 3),  -- The God of Small Things (Thriller)
    (8, 5),  -- Malgudi Days (Comedy)
    (9, 3),  -- Godan (Thriller)
    (10, 2), -- Gitanjali (Romance)
    (11, 1), -- Rashmirathi (Action)
    (12, 7), -- Ponniyin Selvan (Fantasy)
    (13, 7), -- Sivagamiyin Sabatham (Fantasy)
    (14, 7), -- Parthiban Kanavu (Fantasy)
    (15, 3); -- Karisal (Thriller)


INSERT INTO TVSHOWS (TVSHOW, LID) VALUES
    ('Breaking Bad', 1),       -- English
    ('Stranger Things', 1),    -- English
    ('Game of Thrones', 1),    -- English
    ('Sherlock', 1),           -- English
    ('Friends', 1),            -- English
    ('Sacred Games', 2),       -- Hindi
    ('Mirzapur', 2),           -- Hindi
    ('Paatal Lok', 2),         -- Hindi
    ('The Family Man', 2),     -- Hindi
    ('Queen', 3),              -- Tamil
    ('November Story', 3),     -- Tamil
    ('Suzhal: The Vortex', 3), -- Tamil
    ('Kota Factory', 4),       -- Telugu
    ('Loser', 4),              -- Telugu
    ('Karikku: Thera Para', 5),-- Malayalam
    ('Brochara', 6),           -- Kannada
    ('Squid Game', 7),         -- Korean
    ('Crash Landing on You', 7),-- Korean
    ('The Untamed', 8),        -- Chinese
    ('Death Note', 9);         -- Japanese


INSERT INTO TVSHOWS_GENRES (TVID, GID) VALUES
    (1, 6),  -- Breaking Bad (Crime)
    (2, 8),  -- Stranger Things (Sci-Fi)
    (3, 7),  -- Game of Thrones (Fantasy)
    (4, 6),  -- Sherlock (Crime)
    (5, 5),  -- Friends (Comedy)
    (6, 6),  -- Sacred Games (Crime)
    (7, 6),  -- Mirzapur (Crime)
    (8, 3),  -- Paatal Lok (Thriller)
    (9, 3),  -- The Family Man (Thriller)
    (10, 3), -- Queen (Thriller)
    (11, 3), -- November Story (Thriller)
    (12, 3), -- Suzhal: The Vortex (Thriller)
    (13, 5), -- Kota Factory (Comedy)
    (14, 5), -- Loser (Comedy)
    (15, 5), -- Karikku: Thera Para (Comedy)
    (16, 5), -- Brochara (Comedy)
    (17, 3), -- Squid Game (Thriller)
    (18, 2), -- Crash Landing on You (Romance)
    (19, 3), -- The Untamed (Thriller)
    (20, 8); -- Death Note (Sci-Fi)


