import sqlite3

def to_dict_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is None:
            return {}
        if isinstance(result, list):
            return [dict(row) for row in result]
        return dict(result)
    return wrapper

# Database connection
def get_db_connection():
    conn = sqlite3.connect('hpi_modules.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    return conn

# Checks if a user for the given name exists
def user_exists(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user is not None

# Insert a new user
def insert_user(username, passwordHash):
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, passwordHash))
    conn.commit()
    conn.close()

# Retrieves user information by username
@to_dict_decorator
def get_user_info_by_name(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

# Retrieves user information by user_id
@to_dict_decorator
def get_user_info_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

# Updates the course abbreviation for the given user
def update_user_course(user_id, selected_course):
    conn = get_db_connection()
    conn.execute("UPDATE users SET course_abbreviation = ? WHERE id = ?", (selected_course, user_id))
    conn.commit()
    conn.close()

# Retrieves module groups for the given user
@to_dict_decorator
def get_module_groups_by_user_id(user_id):
    conn = get_db_connection()
    module_groups = conn.execute(
        """
        SELECT DISTINCT
            module_group 
        FROM
            course_modules 
        JOIN
            users ON course_modules.course_abbreviation = users.course_abbreviation
        WHERE
            users.id = ?
        ORDER BY
            module_group;
        """, (user_id,)
    ).fetchall()
    conn.close()
    return module_groups

# Retrieves all modules that match the given filters
@to_dict_decorator
def get_filtered_modules(request, user_id):
    query_parts = [
        """SELECT
            modules.*,
            GROUP_CONCAT(course_modules.module_group || '-' || course_modules.submodule_group) AS module_group_subgroup_combinations
        FROM
            modules
        JOIN
            course_modules ON modules.url_trimmed = course_modules.url_trimmed
        JOIN
            courses ON courses.course_abbreviation = course_modules.course_abbreviation"""
    ]
    query_params = []
    if request.form.get("module_group_checkboxes"):
        query_parts.append("AND (")
        query_parts.append(" OR ".join(["course_modules.module_group = ?" for _ in request.form.getlist("module_group_checkboxes")]))
        query_parts.append(")")
        query_params.extend(request.form.getlist("module_group_checkboxes"))
    if request.form.get("credits_checkboxes"):
        query_parts.append("AND (")
        query_parts.append(" OR ".join(["modules.credits = ?" for _ in request.form.getlist("credits_checkboxes")]))
        query_parts.append(")")
        query_params.extend(request.form.getlist("credits_checkboxes"))
    if request.form.get("evap_max_result"):
        query_parts.append("AND (")
        query_parts.append("modules.evap_grade <= ?")
        query_parts.append(")")
        query_params.append(request.form.get("evap_max_result"))
    # if exclude_taken, exclude modules that the user has already taken
    if request.form.get("exclude_taken"):
        query_parts.append("AND modules.url_trimmed NOT IN (")
        query_parts.append("SELECT url_trimmed FROM user_modules WHERE user_id = ?")
        query_parts.append(")")
        query_params.append(user_id)
    query_parts.append("GROUP BY modules.url_trimmed;")
    query = " ".join(query_parts)
    
    conn = get_db_connection()
    modules = conn.execute(query, query_params).fetchall()
    conn.close()
    return modules

# Retrieves module groups for the given user
@to_dict_decorator
def get_user_module_groups(user_id):
    conn = get_db_connection()
    module_groups = conn.execute(
        """
        SELECT DISTINCT
            module_group 
        FROM
            course_modules 
        JOIN
            users ON course_modules.course_abbreviation = users.course_abbreviation
        WHERE
            users.id = ?
        ORDER BY
            module_group;
        """, (user_id,)
    ).fetchall()
    conn.close()
    return module_groups

# Retrieves all module group and submodule group combinations for the given user
@to_dict_decorator
def get_module_submodule_combinations(user_id):
    conn = get_db_connection()
    combinations = conn.execute(
        """
        SELECT 
            module_group, 
            GROUP_CONCAT(DISTINCT module_group || '-' || submodule_group) AS module_group_subgroup_combinations, 
            COUNT(DISTINCT module_group || '-' || submodule_group) AS colspan
        FROM 
            course_modules
        JOIN
            users ON course_modules.course_abbreviation = users.course_abbreviation
        WHERE
            users.id = ?
        GROUP BY
            module_group;
        """, (user_id,)
    ).fetchall()
    conn.close()
    return combinations

# Retrieves all modules taken by the given user
@to_dict_decorator
def get_modules_taken(user_id):
    conn = get_db_connection()
    modules = conn.execute(
        """
        SELECT 
            m.title, 
            m.url_trimmed, 
            m.credits, 
            GROUP_CONCAT(cm.module_group || '-' || cm.submodule_group) AS module_group_subgroup_combinations
        FROM 
            modules m
        JOIN 
            user_modules um ON m.url_trimmed = um.url_trimmed
        JOIN 
            course_modules cm ON m.url_trimmed = cm.url_trimmed
        JOIN 
            users u ON cm.course_abbreviation = u.course_abbreviation AND um.user_id = u.id
        WHERE 
            um.user_id = ?
        GROUP BY 
            m.url_trimmed;
        """, (user_id,)
    ).fetchall()
    conn.close()
    return modules

# Retrieves detailed information for the given module
@to_dict_decorator
def get_module_info(user_id, url_trimmed):
    conn = get_db_connection()
    module_info = conn.execute(
        """
        SELECT
            modules.*, 
            GROUP_CONCAT(lecturers.lecturer_name, ', ') AS lecturers,
            CASE WHEN um.enrolled_count > 0
                THEN 1
                ELSE 0
            END AS is_enrolled
        FROM
            modules
        LEFT JOIN (
            SELECT
                url_trimmed,
                COUNT(user_id) AS enrolled_count
            FROM
                user_modules
            WHERE
                user_id = ?
            GROUP BY
                url_trimmed
        ) AS um ON modules.url_trimmed = um.url_trimmed
        JOIN module_lecturers ON modules.url_trimmed = module_lecturers.url_trimmed
        JOIN lecturers ON module_lecturers.lecturer_id = lecturers.lecturer_id
        WHERE
            modules.url_trimmed = ?
        GROUP BY
            modules.url_trimmed;
        """, (user_id, url_trimmed)
    ).fetchone()
    conn.close()
    return module_info

def update_module_enrollment(user_id, url_trimmed, checked):
    conn = get_db_connection()
    if checked:
        conn.execute("INSERT INTO user_modules (user_id, url_trimmed) VALUES (?, ?)", (user_id, url_trimmed))
    else:
        conn.execute("DELETE FROM user_modules WHERE user_id = ? AND url_trimmed = ?", (user_id, url_trimmed))
    conn.commit()
    conn.close()
