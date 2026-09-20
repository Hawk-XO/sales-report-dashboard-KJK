# app.py

from flask import Flask, render_template, request, redirect, session, jsonify, url_for, flash
from datetime import datetime, timedelta
from calendar import monthrange
import mysql.connector
import subprocess
import os

from config import TEXT_FILES

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only")
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
app.permanent_session_lifetime = timedelta(minutes=5)

# --- MySQL CONFIG ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.environ["DB_PASSWORD"],
    database="sales_report"
)
cursor = db.cursor()

# === Config File Loader ===
def load_config_data():
    regions, targets, last_month = [], {}, {}

    # Load regions
    if os.path.exists(TEXT_FILES['region_list']):
        with open(TEXT_FILES['region_list'], "r") as f:
            regions = [line.strip() for line in f if line.strip()]

    # Load monthly targets
    if os.path.exists(TEXT_FILES['monthly_targets']):
        with open(TEXT_FILES['monthly_targets'], "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=")
                    targets[k.strip()] = float(v.strip())

    # Load last month overrides (including international/export)
    if os.path.exists(TEXT_FILES['last_month_overrides']):
        with open(TEXT_FILES['last_month_overrides'], "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=")
                    last_month[k.strip()] = float(v.strip())

    return regions, targets, last_month

# === Admin Routes ===
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form["password"]
        if password == ADMIN_PASSWORD:
            session.permanent = True
            session["admin_logged_in"] = True
            return redirect("/admin_page")
        else:
            return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html")

@app.route("/admin_page")
def admin_page():
    if not session.get("admin_logged_in"):
        return redirect("/admin")
    override_enabled = session.get("override_enabled", False)
    return render_template("admin_page.html", override_enabled=override_enabled)

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin")

@app.before_request
def update_session_expiry():
    if session.get("admin_logged_in"):
        session.permanent = True

@app.route("/admin/edit/<filename>")
def edit_text_file(filename):
    if not session.get("admin_logged_in"):
        return redirect("/admin")
    if filename not in TEXT_FILES:
        flash("Invalid file requested.", "danger")
        return redirect(url_for('admin_page'))
    try:
        subprocess.Popen(['notepad.exe', TEXT_FILES[filename]])
        flash(f"Opening {filename.replace('_', ' ').title()}...", "info")
    except Exception as e:
        flash(f"Failed to open file: {e}", "danger")
    return redirect(url_for('admin_page'))

@app.route("/admin/open_target_file")
def open_target_file():
    if not session.get("admin_logged_in"):
        return redirect("/admin")
    try:
        subprocess.Popen(['notepad.exe', TEXT_FILES['monthly_targets']])
        flash("Monthly target file opened in Notepad.", "info")
    except Exception as e:
        flash(f"Failed to open monthly target file: {e}", "danger")
    return redirect("/admin_page")

@app.route('/admin/toggle_override_mode', methods=['POST'])
def toggle_override_mode():
    session['override_enabled'] = 'override_mode' in request.form
    return redirect(url_for('admin_page'))

# === Utility Loaders ===
def load_parties():
    with open(TEXT_FILES['party_list'], "r") as f:
        return [line.strip() for line in f if line.strip()]

def load_regions():
    with open(TEXT_FILES['region_list'], "r") as f:
        return [line.strip() for line in f if line.strip()]

def load_countries():
    with open(TEXT_FILES['sales_countries'], "r") as f:
        return [line.strip() for line in f if line.strip()]

def load_currencies():
    with open(TEXT_FILES['currency_names'], "r") as f:
        return [line.strip() for line in f if line.strip()]

# === Public Routes ===
@app.route("/")
@app.route("/start")
def start():
    return render_template("start.html")

@app.route("/entry")
def entry():
    return render_template("entry.html")

# === Domestic Entry ===
@app.route("/domestic", methods=["GET"])
def domestic_form():
    return render_template("domestic.html", regions=load_regions())

@app.route("/submit_domestic", methods=["POST"])
def submit_domestic():
    data = {
        "invoice_no": request.form.get("invoice_no"),
        "invoice_date": request.form.get("invoice_date"),
        "party_name": request.form.get("party_name"),
        "region_name": request.form.get("region_name"),
        "product_value": float(request.form.get("product_value")),
        "exchange_rate": 1.0,
        "product_value_inr": float(request.form.get("product_value")),
        "currency_name": "INR",
        "invoice_type": "domestic"
    }

    sql = """
        INSERT INTO sales_report 
        (invoice_no, invoice_date, party_name, region_name, product_value, exchange_rate, product_value_inr, currency_name, invoice_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, tuple(data.values()))
    db.commit()
    return "Domestic entry submitted successfully!"

# === Export Entry ===
@app.route("/export", methods=["GET"])
def export_form():
    return render_template("export.html", countries=load_countries(), currencies=load_currencies())

@app.route("/submit_export", methods=["POST"])
def submit_export():
    product_value = float(request.form.get("product_value"))
    exchange_rate = float(request.form.get("exchange_rate"))
    product_value_inr = product_value * exchange_rate

    data = {
        "invoice_no": request.form.get("invoice_no"),
        "invoice_date": request.form.get("invoice_date"),
        "party_name": request.form.get("party_name"),
        "region_name": request.form.get("region_name"),
        "product_value": product_value,
        "exchange_rate": exchange_rate,
        "product_value_inr": product_value_inr,
        "currency_name": request.form.get("currency_name"),
        "invoice_type": request.form.get("invoice_type")
    }

    sql = """
        INSERT INTO sales_report 
        (invoice_no, invoice_date, party_name, region_name, product_value, exchange_rate, product_value_inr, currency_name, invoice_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, tuple(data.values()))
    db.commit()
    return "Export entry submitted successfully!"

# === Autocomplete API ===
@app.route("/autocomplete_party")
def autocomplete_party():
    query = request.args.get("query", "").lower()
    matches = [p for p in load_parties() if p.lower().startswith(query)]
    return jsonify(matches)

# === Reports ===
@app.route("/sales_report", methods=["GET"])
def sales_report():
    return render_template(
        "sales_report.html",
        show_table=False,
        domestic_data=[],
        domestic_total=0.0,
        domestic_target_total=0.0,
        domestic_last_month_total=0.0,
        export_total=0.0,
        export_last_month_total=0.0,
        xlnt_data={  # ← Add this
            "value": 0.0,
            "value_inr": 0.0,
            "last_month_value": 0.0,
            "last_month_value_inr": 0.0
        },
        international_data=[]  # ← Add this
    )


@app.route("/generate_report", methods=["POST"])
def generate_report():
    from datetime import datetime, timedelta
    import decimal

    def safe_float(val):
        return float(val) if isinstance(val, (int, float, decimal.Decimal)) else 0.0

    start_date_raw = request.form.get("start_date")
    end_date_raw = request.form.get("end_date")
    start_dt = datetime.strptime(start_date_raw, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date_raw, "%Y-%m-%d")
    start_date = start_dt.strftime("%d-%m-%Y")
    end_date = end_dt.strftime("%d-%m-%Y")

    # One-month previous range
    prev_start_dt = (start_dt - timedelta(days=30)).replace(day=1)
    prev_end_dt = start_dt - timedelta(days=1)
    prev_start_raw = prev_start_dt.strftime("%Y-%m-%d")
    prev_end_raw = prev_end_dt.strftime("%Y-%m-%d")

    regions, targets, last_month = load_config_data()
    override_mode = session.get("override_enabled", False)

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ["DB_PASSWORD"],
        database="sales_report"
    )
    cursor = db.cursor(dictionary=True)

    # === Domestic Region Totals ===
    cursor.execute("""
        SELECT region_name, SUM(product_value_inr) AS total_inr
        FROM sales_report
        WHERE invoice_type = 'domestic' AND invoice_date BETWEEN %s AND %s
        GROUP BY region_name
    """, (start_date_raw, end_date_raw))
    current_rows = cursor.fetchall()
    current_totals = {row['region_name']: safe_float(row['total_inr']) for row in current_rows}

    if not override_mode:
        cursor.execute("""
            SELECT region_name, SUM(product_value_inr) AS total_inr
            FROM sales_report
            WHERE invoice_type = 'domestic' AND invoice_date BETWEEN %s AND %s
            GROUP BY region_name
        """, (prev_start_raw, prev_end_raw))
        last_rows = cursor.fetchall()
        last_month = {row['region_name']: safe_float(row['total_inr']) / 100000 for row in last_rows}

    domestic_data = []
    domestic_total = domestic_target_total = domestic_last_month_total = 0.0

    for region in regions:
        today_val = current_totals.get(region, 0.0) / 100000
        target = targets.get(region, 0.0)
        last = last_month.get(region, 0.0)

        domestic_data.append({
            "name": region,
            "as_on_today": today_val,
            "target": target,
            "last_month": last
        })
        domestic_total += today_val
        domestic_target_total += target
        domestic_last_month_total += last

    # === XLNT Export ===
    cursor.execute("""
        SELECT SUM(product_value) AS value, SUM(product_value_inr) AS value_inr
        FROM sales_report
        WHERE invoice_type = 'export_xlnt' AND invoice_date BETWEEN %s AND %s
    """, (start_date_raw, end_date_raw))
    xlnt = cursor.fetchone() or {}

    if not override_mode:
        cursor.execute("""
            SELECT SUM(product_value) AS value, SUM(product_value_inr) AS value_inr
            FROM sales_report
            WHERE invoice_type = 'export_xlnt' AND invoice_date BETWEEN %s AND %s
        """, (prev_start_raw, prev_end_raw))
        xlnt_last = cursor.fetchone() or {}
        xlnt_last_value = safe_float(xlnt_last.get("value"))
        xlnt_last_inr = safe_float(xlnt_last.get("value_inr")) / 100000
    else:
        xlnt_last_value = last_month.get("XLNT-EURO", 0.0)
        xlnt_last_inr = last_month.get("XLNT-INR", 0.0)

    xlnt_data = {
        "value": safe_float(xlnt.get("value")),
        "value_inr": safe_float(xlnt.get("value_inr")) / 100000,
        "last_month_value": xlnt_last_value,
        "last_month_value_inr": xlnt_last_inr
    }

    # === International Export ===
    with open(TEXT_FILES["currency_names"], "r") as f:
        currency_list = [line.strip() for line in f if line.strip()]

    international_data = []
    for currency in currency_list:
        cursor.execute("""
            SELECT SUM(product_value) AS value, SUM(product_value_inr) AS value_inr
            FROM sales_report
            WHERE invoice_type = 'international' AND currency_name = %s AND invoice_date BETWEEN %s AND %s
        """, (currency, start_date_raw, end_date_raw))
        current = cursor.fetchone() or {}

        if not override_mode:
            cursor.execute("""
                SELECT SUM(product_value) AS value, SUM(product_value_inr) AS value_inr
                FROM sales_report
                WHERE invoice_type = 'international' AND currency_name = %s AND invoice_date BETWEEN %s AND %s
            """, (currency, prev_start_raw, prev_end_raw))
            last = cursor.fetchone() or {}
            last_value = safe_float(last.get("value"))
            last_inr = safe_float(last.get("value_inr")) / 100000
        else:
            last_value = last_month.get(f"INTL-{currency}", 0.0)
            last_inr = last_month.get(f"INTL-{currency}-INR", 0.0)

        international_data.append({
            "name": currency,
            "value": safe_float(current.get("value")),
            "value_inr": safe_float(current.get("value_inr")) / 100000,
            "last_month_value": last_value,
            "last_month_value_inr": last_inr
        })

    export_total = safe_float(xlnt_data["value_inr"])
    export_last_month_total = safe_float(xlnt_data["last_month_value_inr"])
    for row in international_data:
        export_total += safe_float(row["value_inr"])
        export_last_month_total += safe_float(row["last_month_value_inr"])

    db.close()

    return render_template("sales_report.html",
        show_table=True,
        start_date=start_date,
        end_date=end_date,
        domestic_data=domestic_data,
        domestic_total=domestic_total,
        domestic_target_total=domestic_target_total,
        domestic_last_month_total=domestic_last_month_total,
        xlnt_data=xlnt_data,
        international_data=international_data,
        export_total=export_total,
        export_last_month_total=export_last_month_total
    )

if __name__ == "__main__":
    app.run(debug=True)
