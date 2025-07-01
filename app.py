import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

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


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    stocks = db.execute(
        "SELECT symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares>0", session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    grand_total = cash
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["name"] = quote["name"]
        stock["price"] = usd(round(quote["price"], 2))
        stock["total"] = usd(round(stock["total_shares"] * quote["price"], 2))
        grand_total += stock["total_shares"] * quote["price"]

    return render_template("index.html", stocks=stocks, cash=usd(round(cash, 2)), grand_total=usd(round(grand_total, 2)))


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        amount = request.form.get("amount")
        if amount:
            cash = float(db.execute("SELECT * FROM users WHERE id=?",
                         session["user_id"])[0]["cash"])
            db.execute("UPDATE users SET cash=? WHERE id=?",
                       float(amount) + cash, session["user_id"])
            return redirect("/")
        else:
            return apology("not a valid amount", 403)
    else:
        return render_template("deposit.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        result = lookup(request.form.get("symbol"))
        shares = request.form.get("shares")
        if not shares or not shares.isdigit():
            return apology("must provide a valid number of shares", 400)

        shares = int(shares)
        if result:
            if shares > 0:
                price = result["price"]
                symbol = result["symbol"]
                cash = db.execute("SELECT cash FROM users WHERE id = ?",
                                  session["user_id"])[0]["cash"]
                if (cash >= price*shares):
                    db.execute("INSERT INTO transactions(user_id, symbol, shares, price_per_share) VALUES(?,?,?,?)",
                               session["user_id"], symbol, shares, usd(price))
                    db.execute("UPDATE users SET cash = ? WHERE id=?",
                               cash - price*shares, session["user_id"])
                    return redirect("/")
                else:
                    return apology("not enough money", 400)

            else:
                return apology("must provide a positive number of shares", 400)
        else:
            return apology("must provide a valid symbol", 400)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    stocks = db.execute(
        "SELECT symbol, shares, price_per_share, timestamp, type FROM transactions WHERE user_id=?", session["user_id"])
    for stock in stocks:
        stock["name"] = lookup(stock["symbol"])["name"]

    return render_template("history.html", stocks=stocks)


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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        result = lookup(request.form.get("symbol"))

        if result:
            return render_template("quoted.html", name=result["name"], price=usd(result["price"]), symbol=result["symbol"])
        else:
            return apology("must provide a valid symbol", 400)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("must match password with confirmation", 400)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?,?)", request.form.get(
                "username"), generate_password_hash(request.form.get("password")))
        except ValueError:
            return apology("username already in use", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    SYMBOLS = []
    for share in db.execute("SELECT symbol FROM transactions WHERE user_id=? AND already_sold='0' AND type='BUY' GROUP BY symbol", session["user_id"]):
        SYMBOLS.append(share["symbol"])

    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol or symbol not in SYMBOLS:
            return apology("invalid stock", 400)
        else:
            shares = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id=? AND symbol=? GROUP BY symbol",
                                session["user_id"], symbol)[0]["SUM(shares)"]
            if not request.form.get("shares").isdigit():
                return apology("must provide a number", 400)
            share_input = int(request.form.get("shares"))
            if not share_input or share_input < 1 or share_input > shares:
                return apology("invalid number of shares", 400)
            else:
                price = lookup(symbol)["price"]
                db.execute("INSERT INTO transactions (user_id, symbol, shares, price_per_share, type) VALUES(?,?,?,?,'SELL')",
                           session["user_id"], symbol, -share_input, usd(price))
                cash = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]["cash"]
                while share_input != 0:
                    for share in db.execute("SELECT * FROM transactions WHERE user_id=? AND symbol=? AND type='BUY'", session["user_id"], symbol):
                        if share["already_sold"] < share["shares"]:
                            cash += price
                            share_input -= 1
                            db.execute("UPDATE transactions SET already_sold = ? WHERE id = ?",
                                       share["already_sold"]+1, share["id"])
                            break

                db.execute("UPDATE users SET cash=? WHERE id=?", cash, session["user_id"])
                return redirect("/")

    else:
        return render_template("sell.html", SYMBOLS=SYMBOLS)
