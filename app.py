import os

# TODO uninstall cs50 from pip
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd, is_integer

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    # holdings is a list of dicts with keys like "symbol", "shares"
    holdings = db.execute("SELECT symbol, shares FROM (SELECT symbol, SUM(shares) as shares FROM transactions WHERE user_id = ? GROUP BY symbol) WHERE shares != 0;", user_id)
    grand_value = 0
    if not holdings == []:
        for stock in holdings:
            quote = lookup(stock.get("symbol"))
            if quote:
                stock["price"] = quote.get("price")
                stock["value"] = stock["price"] * stock["shares"]
                grand_value += stock["value"]
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    grand_value += cash
    return render_template("index.html", holdings=holdings, cash=cash, grand_value=grand_value)


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
        return render_template("search.html", module_display_list=[])
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


@app.route("/taken", methods=["GET"])
@login_required
def taken():
    """Show all modules taken"""

    #modules_taken = db.execute("SELECT * FROM transactions WHERE user_id = ?;", session["user_id"])
    
    return render_template("taken.html")

@app.route("/module")
@login_required
def show_module_details():
    """Show detailed module information"""
    example_module_dict = {
        '_url': 'https://hpi.de//studium/im-studium/lehrveranstaltungen/it-systems-engineering-ba/lehrveranstaltung/wise-23-24-3847-3d-computer-graphics-extending-the-threejs-framework.html',
        '_url_trimmed': 'wise-23-24-3847-3d-computer-graphics-extending-the-threejs-framework.html',
        '_title': '3D Computer Graphics: Extending the Three.js Framework (Wintersemester 2023/2024)',
        '_description': 'Im Bereich der 3D-Computergrafik ist die Open Source Bbliothek THREE.js ein langjährig etabliertes Projekt, welches als Computergrafik-Middleware in der Demo-Szene und auch in der Industrie eine oft genutzte Software-Komponente für die Darstellung von 3D Szenen ist. Diese zentrale Rolle verdankt die Blibliothek der effektiven Abstraktion der Konzepte, Verfahren und Techniken der 3D-Computergrafik, sowie einer großen Bandbreite an Beispielen und einer großen, aktiven Community.\nIm Rahmen des Seminars werden in Kleinst- und Kleingruppen (1-2 Studierende) verschiedene Themen im Kontext der Bibliothek THREE.js bearbeitet.\nZiel ist es, sich ein computergrafisches Thematheoretisch zu erschließen und softwaretechnisch mit THREE.js als ein Prototyp umzusetzen. Über die Ergebnisse wird im Rahmen eines Vortrags und einem Demonstrator (Live-Demo, Webseite, Video) berichtet.\nBeispiele für Themenbereiche:\n- Mesh-freie Geometrierepräsentationen, wie z.B. Signed Distance Fields für 3D Font Rendering und 3D Punktwolken\n- Parametrisierte Geometrien, wie z.B. Blobs und Superquadriken\n- Algorithmische Geometrie, wie z.B. Triangulierung, Hüllkörper, Skeletons oder progressive Meshes\n- Navigationstechniken, wie z.B. eine World-in-Hand Navigation\n- 3D Glyphen für z.B. Informationsvisualisierung',
        '_dates': None,
        '_rooms': None,
        '_lecturers': ['Prof. Dr. Jürgen Döllner', 'Willy Scheibel', 'Daniel Atzberger'],
        '_evaluation_metrics': None,
        '_general_info': '- Semesterwochenstunden: 4\n- ECTS: 6\n- Benotet: Ja\n- Einschreibefrist: 01.10.2023 - 03.11.2023\n- Lehrform: Seminar / Projekt\n- Belegungsart: Wahlpflichtmodul\n- Lehrsprache: Deutsch\n- Maximale Teilnehmerzahl: 12',
        '_prerequisites': 'Das Seminar richtet sich an Studierende ab dem 5. Fachsemester. Es werden grundlegende Programmierkenntnisse und -techniken, sowie Grundlagen der 3D-Computergrafik vorausgesetzt, wie sie unter anderem in den Lehrveranstaltungen Programmiertechnik I, Programmiertechnik II, Softwarearchitekturen, Softwaretechnik I und 3D-Computergrafik I vermittelt werden.\nDurch die Orientierung aller Themen an die 3D-Computergrafik-Bibliothek THREE.js sind auch Grundkenntnisse in JavaScript bzw. TypeScript, CSS und HTML gefordert, wobei diese Grundkenntnisse auch im Rahmen des Seminars erarbeitet werden können.',
        '_literature': 'Literatur wird themenspezifisch ausgegeben.',
        '_grading': 'Für eine erfolgreiche Bearbeitung des Seminars müssen sowohl ein technischer Prototyp erarbeitet werden als auch die Fortschritte und Ergebnisse in Form von einem Vortrag, einer Webseite und einem Video dokumentiert und präsentiert werden.\nDie Endnote setzt sich wie folgt zusammen:\n- 70% Prototyp und Projektbearbeitung\n- 20% Endvortrag (25 Minuten)\n- 10% Projektwebseite und -video',
        '_website_url': None
    }
    return render_template("module.html", module_dict=example_module_dict)

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