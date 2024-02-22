# TODO uninstall cs50 from pip
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import courses_dict, apology, login_required
from utils.filters import unique_list
from db_queries import *
from helpers import store_data_in_session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.jinja_env.filters['unique_list'] = unique_list

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Ensure password and password confirmation match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        # QUERY database for username to prevent double entries
        if user_exists(request.form.get("username")):
            return apology("please use a different username")

        # INSERT username into database
        insert_user(request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Redirect user to login page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        user_info = get_user_info_by_name(request.form.get("username"))

        # Ensure username exists and password is correct
        if not user_info or not check_password_hash(user_info["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user_info["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    
    # Forget any user_id
    session.clear()
    
    # Redirect user to login form
    return redirect("/")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Change profile settings."""
    if request.method == "POST":
         # Validate user input
        if not request.form.get("course_checkboxes"):
            return apology("must select a course")
        else:
            selected_course = request.form.get("course_checkboxes")
        update_user_course(session["user_id"], selected_course)
    user_info = get_user_info_by_id(session["user_id"])  # TODO handle case when user does not exist
    selected_course = user_info.get("course_abbreviation")
    username = user_info["username"]
    return render_template("profile.html", courses_dict=courses_dict, username=username, selected_course=selected_course)


@app.route("/about", methods=["GET"])
def about():
    """Show information about the app"""
    return render_template("about.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search for modules"""
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        # query for all available module groups
        module_groups = [row["module_group"] for row in get_module_groups_by_user_id(session["user_id"])]
        return render_template("search.html", module_display_list=[], courses_dict=courses_dict, module_groups=module_groups, filter_settings=request.form) # TODO check behaviour of filter_settings
    else:
        # Filters all modules by the selected module groups, credits and evap grade
        filtered_modules = get_filtered_modules(request)
        # query for all available module groups
        user_module_groups = get_user_module_groups(session["user_id"])
        module_groups = [row["module_group"] for row in user_module_groups]
        return render_template("search.html", module_display_list=filtered_modules, courses_dict=courses_dict, module_groups=module_groups, filter_settings=request.form)


@app.route("/", methods=["GET"])
@login_required
def my_modules():
    """Show all modules taken"""
    # get all submodule groups of the user's course
    module_submodule_combinations = get_module_submodule_combinations(session["user_id"])
    
    module_colspan = {row["module_group"]: row["colspan"] for row in module_submodule_combinations}
    # get the submodule group names
    subheader = [item for row in module_submodule_combinations for item in row["module_group_subgroup_combinations"].split(",")]
    # get the user's modules
    modules_taken = get_modules_taken(session["user_id"])
    # TODO Handle case where a user enrolled in a module that is not offered for his/her course anymore, e.g. after changing the course
    # This currently results in a KeyError
    table_rows = []
    for module_taken in modules_taken:
        credit_cells = ["" for _ in range(len(subheader))]
        module_title = module_taken["title"]
        module_link = "module/" + module_taken["url_trimmed"]
        for module_group_subgroup_combination in module_taken["module_group_subgroup_combinations"].split(","):
            credit_cells[subheader.index(module_group_subgroup_combination)] = module_taken["credits"] or "X"
        table_rows.append((module_title, module_link, credit_cells))
    return render_template("my_modules.html", module_colspan=module_colspan, subheader=subheader, table_rows=table_rows)

@app.route("/module/<url_trimmed>")
@login_required
def module(url_trimmed):
    """Show detailed module information"""
    module_info = get_module_info(session["user_id"], url_trimmed)
    if not module_info:
        return apology("Module not found", 404)
    if module_info["is_enrolled"] == 1:
        module_info["checkbox_status"] = "checked"
    else:
        module_info["checkbox_status"] = None
    return render_template("module.html", module_info=module_info)
    

@app.route('/handle_checkbox', methods=['POST'])
@login_required
def handle_checkbox():
    data = request.json
    try:
        update_module_enrollment(session["user_id"], data["url_trimmed"], data["checked"])
    except ValueError as e:
        print(f"An error occurred: {e}")
    # Process the data
    return jsonify(success=True)