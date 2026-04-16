from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import pandas as pd
import joblib
from werkzeug.security import generate_password_hash, check_password_hash

# Optional DB import (safe)
try:
    import psycopg2
except:
    psycopg2 = None

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------
# LOAD MODEL
# -------------------------------
model = joblib.load("loan_model.pkl")
model_columns = joblib.load("model_columns.pkl")

# -------------------------------
# SAFE DB CONNECTION
# -------------------------------
conn = None
cur = None

try:
    if psycopg2:
        conn = psycopg2.connect(
            host="localhost",
            database="LoanPridiction",
            user="postgres",
            password="shivam%8320"
        )
        cur = conn.cursor()
except:
    conn = None
    cur = None

# -------------------------------
# LOGIN PAGE
# -------------------------------
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST" and cur:
        try:
            full_name = request.form.get("full_name")
            username = request.form.get("username")
            email = request.form.get("email")
            mobile = request.form.get("mobile")
            password = request.form.get("password")
            city = request.form.get("city")

            hashed_password = generate_password_hash(password)

            cur.execute("""
                INSERT INTO Register_Users 
                (full_name, username, email, mobile, password, city)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, username, email, mobile, hashed_password, city))

            conn.commit()
            return redirect(url_for("login"))

        except Exception as e:
            if conn:
                conn.rollback()
            return f"Error: {e}"

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login_process():
    if not cur:
        return "Database not connected"

    username = request.form.get("username")
    password = request.form.get("password")

    cur.execute("SELECT password FROM Register_Users WHERE username = %s", (username,))
    user = cur.fetchone()

    if user and check_password_hash(user[0], password):
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", error="Invalid Username or Password")


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


# -------------------------------
# LOAN PAGES
# -------------------------------
@app.route("/personal")
def personal():
    return render_template("Personal_loan.html")

@app.route("/business")
def business():
    return render_template("Business_loan.html")

@app.route("/home-loan")
def home_loan():
    return render_template("Home_loan.html")

@app.route("/education")
def education():
    return render_template("Education_loan.html")

@app.route("/vehicle")
def vehicle():
    return render_template("Vehicle_loan.html")

@app.route("/agriculture")
def agriculture():
    return render_template("Agricultural_loan.html")

@app.route("/gold")
def gold():
    return render_template("Gold_loan.html")

@app.route("/property")
def property_loan():
    return render_template("Loan_Against_Property.html")

@app.route("/credit-card")
def credit_card():
    return render_template("Credit_Card_loan.html")


# -------------------------------
# APPLY LOAN (SAFE)
# -------------------------------
@app.route("/apply-loan", methods=["POST"])
def apply_loan():

    bank = request.form.get("bank")

    try:
        # DB insert only if connected
        if cur:
            cur.execute("""
                INSERT INTO users
                (full_name, dob, gender, mobile, email, marital_status, address,
                 pan, aadhaar, employment_type, company_name, experience, monthly_income)
                VALUES (%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s)
                RETURNING user_id
            """, (
                request.form.get("full_name"),
                request.form.get("dob"),
                request.form.get("gender"),
                request.form.get("mobile"),
                request.form.get("email"),
                request.form.get("marital_status"),
                request.form.get("address"),
                request.form.get("pan"),
                request.form.get("aadhaar"),
                request.form.get("employment_type"),
                request.form.get("company_name"),
                request.form.get("experience"),
                request.form.get("monthly_income")
            ))

            user_id = cur.fetchone()[0]

        # -------------------------------
        # ML PREDICTION
        # -------------------------------
        monthly_income = float(request.form.get("monthly_income", 0))
        loan_amount = float(request.form.get("loan_amount", 0))
        tenure = int(request.form.get("tenure", 0))
        employment_type = request.form.get("employment_type")
        cibil_score = int(request.form.get("cibil_score", 700))

        existing_value = request.form.get("existing_loan")
        existing_loans = 1 if existing_value in ["1", "Yes", "yes"] else 0

        new_user = pd.DataFrame({
            "monthly_income": [monthly_income],
            "loan_amount": [loan_amount],
            "tenure": [tenure],
            "cibil_score": [cibil_score],
            "employment_type": [employment_type],
            "existing_loans": [existing_loans]
        })

        new_user = pd.get_dummies(new_user)
        new_user = new_user.reindex(columns=model_columns, fill_value=0)

        prediction = model.predict(new_user)
        probability = model.predict_proba(new_user)[0][1] * 100

        loan_decision = "APPROVED" if prediction[0] == 1 else "REJECTED"

        if conn:
            conn.commit()

        return jsonify({
            "status": "SUCCESS",
            "bank": bank,
            "loan_decision": loan_decision,
            "probability": round(probability, 2)
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"status": "ERROR", "message": str(e)})


# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)