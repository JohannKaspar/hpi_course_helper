CREATE TABLE courses (
    course_abbreviation TEXT PRIMARY KEY,
    course_name TEXT NOT NULL
);

CREATE TABLE modules (
    url_trimmed PRIMARY KEY,
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
    FOREIGN KEY (course_abbreviation) REFERENCES courses(abbreviation),
    FOREIGN KEY (url_trimmed) REFERENCES modules(url_trimmed)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    course_abbreviation TEXT
);

CREATE TABLE user_modules (
    user_id INTEGER NOT NULL,
    url_trimmed TEXT NOT NULL,
    PRIMARY KEY (user_id, url_trimmed),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (url_trimmed) REFERENCES modules(url_trimmed)
);