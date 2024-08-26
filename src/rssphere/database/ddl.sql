CREATE TABLE feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    last_checked DATETIME
);

CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER,
    title TEXT,
    content TEXT,
    url TEXT UNIQUE NOT NULL,
    published_at DATETIME,
    saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_content TEXT,
    is_read BOOLEAN DEFAULT 0,
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);

CREATE TABLE scraped_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    file_path TEXT,
    scrape_method TEXT,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

CREATE TABLE media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_page_id INTEGER,
    file_path TEXT,
    alt_text TEXT,
    FOREIGN KEY (scraped_page_id) REFERENCES scraped_pages(id) ON DELETE CASCADE
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE article_tags (
    article_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (article_id, tag_id),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE feed_tags (
    feed_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (feed_id, tag_id),
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE read_articles (
    feed_id INTEGER,
    article_url TEXT,
    PRIMARY KEY (feed_id, article_url),
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);
