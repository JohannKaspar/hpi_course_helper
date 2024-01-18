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
    module_url_trimmed TEXT NOT NULL,
    module_group TEXT NOT NULL,
    submodule_group TEXT,
    PRIMARY KEY (course_abbreviation, module_url_trimmed, module_group, submodule_group),
    FOREIGN KEY (course_abbreviation) REFERENCES courses(abbreviation),
    FOREIGN KEY (module_url_trimmed) REFERENCES modules(url_trimmed)
);