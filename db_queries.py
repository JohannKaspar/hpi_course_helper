from cs50 import SQL
import requests

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hpi_modules.db")

# Checks if a user for the given name exists
def user_exists(username):
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    return len(rows) > 0

# Insert a new user to the 
def insert_user(username, passwordHash):
    db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", username, passwordHash)
    
# Retrieves user information by user_name
def get_user_info_by_name(username):
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    if len(rows) != 1:
        return None
    return rows[0]
    
# Retrieves user information by user_id
def get_user_info_by_id(user_id):
    return db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]

# Retrieves the course abbreviation for the given user
def update_user_course(user_id, selected_course):
    db.execute("UPDATE users SET course_abbreviation = ? WHERE id = ?;", selected_course, user_id)
    
# Retrieves module groups abbreviation for the given user
def get_module_groups_by_user_id(user_id):
    return db.execute(
        """
        SELECT DISTINCT module_group 
        FROM course_modules 
        JOIN users
            ON course_modules.course_abbreviation = users.course_abbreviation
        WHERE users.id = ?
        ORDER BY module_group;""",
        user_id
        )
    
def get_filtered_modules(request):
    # query_parts contains the SQL query parts that are concatenated at the end
    query_parts = [
        """SELECT modules.*, GROUP_CONCAT(course_modules.module_group || '-' || course_modules.submodule_group) as module_group_subgroup_combinations
        FROM modules
        JOIN course_modules ON modules.url_trimmed = course_modules.url_trimmed
        JOIN courses ON courses.course_abbreviation = course_modules.course_abbreviation"""
        ]
    query_params = [] # contains the parameters for the query
    if request.form.get("module_group_checkboxes"):
        query_parts.append("AND")
        query_parts.append(" OR ".join(["course_modules.module_group = ?" for _ in request.form.getlist("module_group_checkboxes")]))
        query_params.extend(request.form.getlist("module_group_checkboxes"))
    if request.form.get("credits_checkboxes"):
        query_parts.append("AND")
        query_parts.append(" OR ".join(["modules.credits = ?" for _ in request.form.getlist("credits_checkboxes")]))
        query_params.extend(request.form.getlist("credits_checkboxes"))
    if request.form.get("evap_max_result"):
        query_parts.append("AND")
        query_parts.append("modules.evap_grade <= ?")
        query_params.append(request.form.get("evap_max_result"))

    # TODO implement already taken module filter and necessary modules filter
    query_parts.append("GROUP BY modules.url_trimmed;")
    query = " ".join(query_parts)
    return db.execute(query, *query_params)

# Retrieves the module groups for the given user
def get_user_module_groups(user_id):
    return db.execute(
        """
        SELECT DISTINCT module_group 
        FROM course_modules 
        JOIN users
            ON course_modules.course_abbreviation = users.course_abbreviation
        WHERE users.id = ?
        ORDER BY module_group;""",
        user_id
        )
    
    
# Retrieves the module group and submodule group combinations for the given user
def get_module_submodule_combinations(user_id):
    return db.execute(
        """
        SELECT 
            module_group, 
            GROUP_CONCAT(DISTINCT module_group || '-' || submodule_group) AS module_group_subgroup_combinations, 
            COUNT(DISTINCT module_group || '-' || submodule_group) AS colspan
        FROM 
            course_modules
        JOIN users
            ON course_modules.course_abbreviation = users.course_abbreviation
        WHERE users.id = ?
        GROUP BY 
            module_group;
        """,
        user_id
        )
    
# Retrieves the modules taken by the given user
def get_modules_taken(user_id):
    return db.execute(
        """
        SELECT 
            m.title, 
            m.url_trimmed, 
            m.credits, 
            GROUP_CONCAT(DISTINCT cm.module_group || '-' || cm.submodule_group ORDER BY cm.module_group, cm.submodule_group) AS module_group_subgroup_combinations
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
        """,
        user_id
        )

def get_module_info(user_id, url_trimmed):
    res = db.execute(
        """
        SELECT modules.*, 
            CASE WHEN um.enrolled_count > 0 THEN 1 ELSE 0 END AS is_enrolled
        FROM modules
        LEFT JOIN (
            SELECT url_trimmed, COUNT(user_id) AS enrolled_count
            FROM user_modules
            WHERE user_id = ?
            GROUP BY url_trimmed
        ) AS um ON modules.url_trimmed = um.url_trimmed
        WHERE modules.url_trimmed = ?;
        """,
        user_id,
        url_trimmed
        )
    if res:
        return res[0]
    return {}

def update_module_enrollment(user_id, url_trimmed, checked):
    if checked:
        db.execute("INSERT INTO user_modules (user_id, url_trimmed) VALUES (?, ?);", user_id, url_trimmed)
    else:
        db.execute("DELETE FROM user_modules WHERE user_id = ? AND url_trimmed = ?;", user_id, url_trimmed)