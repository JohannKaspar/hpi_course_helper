from collections import defaultdict
import os

# TODO uninstall cs50 from pip
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import courses_dict

from helpers import apology, login_required, is_integer

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hpi_modules.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 0:
            return apology("please use a different username")

        # INSERT username into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", request.form.get("username"), generate_password_hash(request.form.get("password")))

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

@app.route("/")
@login_required
def index():
    """Show weekly planner"""
    user_id = session["user_id"]
    return render_template("index.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("buy.html")
    else:
        # Validate user input
        if not request.form.get("symbol"):
            return apology("must enter a stock")
        elif not request.form.get("shares"):
            return apology("must enter number of shares to buy")
        elif not is_integer(request.form.get("shares")):
            return apology("must enter a whole number of shares > 0")
        elif int(request.form.get("shares")) < 1:
            return apology("must enter a whole number of shares > 0")

        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        quote = lookup(request.form.get("symbol"))
        user_id = session["user_id"]
        if quote:
            price = quote["price"]
            total = price * shares
            cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
            if cash < total:
                return apology("You can't afford the selected amount of shares")
            else:
                db.execute("UPDATE users SET cash = ? WHERE id = ?;", cash - total, user_id)
                db.execute("INSERT INTO transactions (user_id, symbol, price, shares, time) \
                    VALUES (?, ?, ?, ?, ?);", user_id, symbol, price, shares, datetime.now())
            return redirect("/")
        else:
            return apology("Stock not found")
        

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Search for modules"""

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        # query for all available module groups
        module_groups_query_results = db.execute("SELECT DISTINCT module_group FROM course_modules;")
        module_groups = [row.get("module_group") for row in module_groups_query_results]
        return render_template("search.html", module_display_list=[], courses_dict=courses_dict, module_groups=module_groups)
    else:
        # Validate user input
        """ if not request.form.get("symbol"):
            return apology("must enter a stock")
        elif not request.form.get("shares"):
            return apology("must enter number of shares to buy")
        elif not is_integer(request.form.get("shares")):
            return apology("must enter a whole number of shares > 0")
        elif int(request.form.get("shares")) < 1:
            return apology("must enter a whole number of shares > 0") """

        user_id = session["user_id"]    
        
        
        query_parts = [
            """SELECT modules.*, GROUP_CONCAT(course_modules.module_group || '-' || course_modules.submodule_group) as module_group_subgroup_combinations
            FROM modules
            JOIN course_modules ON modules.url_trimmed = course_modules.url_trimmed
            JOIN courses ON courses.course_abbreviation = course_modules.course_abbreviation"""
        ]
        query_params = []
        if request.form.getlist("course_checkboxes"):
            query_parts.append("WHERE")
            query_parts.append(" OR ".join(["courses.course_abbreviation = ?" for _ in request.form.getlist("course_checkboxes")]))
            query_params.extend(request.form.getlist("course_checkboxes"))
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
        res = db.execute(query, *query_params)

        # query for all available module groups
        module_groups_query_results = db.execute("SELECT DISTINCT module_group FROM course_modules;")
        module_groups = [row.get("module_group") for row in module_groups_query_results]
        return render_template("search.html", module_display_list=res, courses_dict=courses_dict, module_groups=module_groups)


@app.route("/my_modules", methods=["GET"])
@login_required
def my_modules():
    """Show all modules taken"""

    # get all submodule groups of the user's course
    module_submodule_combinations = db.execute(
        """
        SELECT module_group, GROUP_CONCAT(DISTINCT submodule_group) AS submodule_groups, COUNT(DISTINCT submodule_group) AS colspan
        FROM course_modules
        WHERE course_abbreviation = 'dh_master'
        GROUP BY module_group;""")
    ''' # get all submodule groups of the user's course
    module_submodule_combinations = db.execute("""SELECT DISTINCT course_modules.module_group, course_modules.submodule_group
                     FROM course_modules
                     WHERE course_modules.course_abbreviation = 'dh_master';""") 
    # get the number of submodules per module group
    module_colspan = defaultdict(int)
    for row in module_submodule_combinations:
        module_colspan[row.get("module_group")] += 1'''
    
    module_colspan = {row.get("module_group"): row.get("colspan") for row in module_submodule_combinations}
    
    # get the submodule group names
    subheader = [item for row in module_submodule_combinations for item in row.get("submodule_groups").split(",")]

    # get the user's modules
    res = db.execute("""SELECT modules.title, modules.credits, course_modules.module_group, course_modules.submodule_group
                     FROM modules 
                     JOIN user_modules ON modules.url_trimmed = user_modules.url_trimmed
                     JOIN course_modules ON modules.url_trimmed = course_modules.url_trimmed
                     WHERE user_modules.user_id = ?
                     AND course_modules.course_abbreviation = 'dh_master';""", session["user_id"])

    modules_taken = [row.get("url_trimmed") for row in res]
    
    return render_template("my_modules.html", module_colspan=module_colspan, subheader=subheader, modules_taken=modules_taken)

@app.route("/module")
@login_required
def module():
    """Show detailed module information"""
    res = db.execute("SELECT * FROM modules WHERE url_trimmed = 'wise-23-24-3847-3d-computer-graphics-extending-the-threejs-framework.html';")
    if res:
        module_info = res[0]
    else:
        module_info = {}
    return render_template("module.html", module_info=module_info)
    

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user_id = session["user_id"]

    # holdings is a list of dicts with keys like "symbol", "shares"
    holdings = db.execute("SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ?", user_id)

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("sell.html", holdings=holdings)
    else:
        # Validate user input
        if not request.form.get("symbol"):
            return apology("must choose a stock to sell")
        elif not request.form.get("shares"):
            return apology("must enter number of shares to sell")
        elif not is_integer(request.form.get("shares")):
            return apology("must enter a whole number of shares > 0 to sell")
        if int(is_integer(request.form.get("shares"))) < 1:
            return apology("must enter a whole number of shares > 0 to sell")

        sell_shares = int(request.form.get("shares"))
        symbol = request.form.get("symbol")

        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        # Get the number of shares of the given stock that is in the user's possession
        for stock in holdings:
            if stock.get("symbol") == symbol:
                shares = stock.get("shares")

        if shares < sell_shares:
            return apology("You can't sell more shares than you own")
        else:
            quote = lookup(symbol)
            if quote:
                price = quote["price"]

            # Add transaction to database
            db.execute("INSERT INTO transactions (user_id, symbol, price, shares, time) \
                        VALUES (?, ?, ?, ?, ?);", user_id, symbol, price, -sell_shares, datetime.now())

            # Add cash from selling to database
            db.execute("UPDATE users SET cash = ? WHERE id = ?;", cash + price * sell_shares, user_id)

            return redirect("/")