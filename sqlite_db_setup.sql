CREATE TABLE courses (
    course_abbreviation TEXT PRIMARY KEY,
    course_name TEXT NOT NULL
);

CREATE TABLE modules (
    url_trimmed TEXT PRIMARY KEY,
    full_url TEXT NOT NULL,
    website TEXT,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL,
    evap_grade INTEGER NOT NULL,
    evap_semester INTEGER NOT NULL,
    module_description TEXT,
    lecturers TEXT
);

CREATE TABLE course_modules (
    course_abbreviation TEXT NOT NULL,
    url_trimmed TEXT NOT NULL,
    module_group TEXT NOT NULL,
    submodule_group TEXT,
    PRIMARY KEY (course_abbreviation, url_trimmed, module_group, submodule_group),
    FOREIGN KEY (course_abbreviation) REFERENCES courses(course_abbreviation),
    FOREIGN KEY (url_trimmed) REFERENCES modules(url_trimmed)
);
CREATE INDEX idx_course_abbreviation ON course_modules(course_abbreviation);
CREATE INDEX idx_url_trimmed ON course_modules(url_trimmed);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    course_abbreviation TEXT DEFAULT 'dh_master',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_abbreviation) REFERENCES courses(course_abbreviation)
);

CREATE INDEX idx_username ON users(username);

CREATE TABLE user_modules (
    user_id INTEGER NOT NULL,
    url_trimmed TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, url_trimmed),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (url_trimmed) REFERENCES modules(url_trimmed)
);


CREATE INDEX idx_user_id ON user_modules(user_id);
CREATE INDEX idx_module_url_trimmed ON user_modules(url_trimmed);
