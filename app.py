from flask import Flask, render_template, request, redirect, session, jsonify
import json, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mikala-spending-secret-2026")

USERNAME = "CarolineJNovak"
PASSWORD = "crap"
DATA_FILE = "data.json"
ERRORS_FILE = "errors.json"

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_error(msg):
    errors = []
    if os.path.exists(ERRORS_FILE):
        with open(ERRORS_FILE) as f:
            errors = json.load(f)
    errors.insert(0, {"time": datetime.now().isoformat(), "error": msg})
    errors = errors[:100]
    with open(ERRORS_FILE, "w") as f:
        json.dump(errors, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
@login_required
def index():
    try:
        data = load_data()
        subs = data["subscriptions"]
        total = sum(s["amount"] for s in subs)
        annual = total * 12
        return render_template("index.html", subscriptions=subs, total=total, annual=annual,
                               month=datetime.now().strftime("%B %Y"))
    except Exception as e:
        log_error(str(e))
        return f"Error: {e}", 500

@app.route("/update-anthropic", methods=["POST"])
@login_required
def update_anthropic():
    try:
        amount = float(request.form.get("amount", 0))
        data = load_data()
        for s in data["subscriptions"]:
            if s["name"] == "Anthropic":
                s["amount"] = round(amount, 2)
                s["last_updated"] = datetime.now().strftime("%B %d, %Y")
        save_data(data)
        return redirect("/")
    except Exception as e:
        log_error(str(e))
        return redirect("/")

@app.route("/update-subscription", methods=["POST"])
@login_required
def update_subscription():
    try:
        name = request.form.get("name")
        amount = float(request.form.get("amount", 0))
        data = load_data()
        for s in data["subscriptions"]:
            if s["name"] == name:
                s["amount"] = round(amount, 2)
                s["last_updated"] = datetime.now().strftime("%B %d, %Y")
        save_data(data)
        return redirect("/")
    except Exception as e:
        log_error(str(e))
        return redirect("/")

@app.route("/errors")
@login_required
def errors():
    errs = []
    if os.path.exists(ERRORS_FILE):
        with open(ERRORS_FILE) as f:
            errs = json.load(f)
    return render_template("errors.html", errors=errs)

if __name__ == "__main__":
    app.run(debug=False)
