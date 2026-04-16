from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import psycopg2
import pandas as pd
import joblib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------
# LOAD MODEL
# -------------------------------
model = joblib.load("loan_model.pkl")
model_columns = joblib.load("model_columns.pkl")

# -------------------------------
# DB CONNECTION
# -------------------------------
conn = psycopg2.connect(
    host="localhost",
    database="LoanPridiction",
    user="postgres",
    password="shivam%8320"
)
cur = conn.cursor()

# -------------------------------
# LOGIN PAGE
# -------------------------------
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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
            conn.rollback()
            return f"Error: {e}"

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login_process():
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
# APPLY LOAN (FINAL)
# -------------------------------
@app.route("/apply-loan", methods=["POST"])
def apply_loan():

    bank = request.form.get("bank")

    try:
        # -------------------------------
        # INSERT USER
        # -------------------------------
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
        # INSERT LOAN
        # -------------------------------
        cur.execute("""
            INSERT INTO loantypes
            (user_id, loan_type, loan_amount, tenure, tenure_unit, loan_purpose,
             property_type, property_value, ownership, property_address,
             business_name, business_type, existing_loan, total_emi, bank)
            VALUES (%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,
                    %s,%s,%s,%s,%s)
            RETURNING loan_id
        """, (
            user_id,
            request.form.get("loan_type"),
            request.form.get("loan_amount"),
            request.form.get("tenure"),
            request.form.get("tenure_unit"),
            request.form.get("loan_purpose"),
            request.form.get("property_type"),
            request.form.get("property_value"),
            request.form.get("ownership"),
            request.form.get("property_address"),
            request.form.get("business_name"),
            request.form.get("business_type"),
            request.form.get("existing_loan"),
            request.form.get("total_emi"),
            bank
        ))

        loan_id = cur.fetchone()[0]

        # -------------------------------
        # INSERT DOCUMENT
        # -------------------------------
        cur.execute("""
            INSERT INTO documents
            (loan_id, document_type, file_path)
            VALUES (%s, %s, %s)
        """, (
            loan_id,
            request.form.get("document_type"),
            request.form.get("file_path")
        ))

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

        # -------------------------------
        # COMMIT + RESPONSE
        # -------------------------------
        conn.commit()

        return jsonify({
            "status": "SUCCESS",
            "bank": bank,
            "loan_decision": loan_decision,
            "probability": round(probability, 2)
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "ERROR", "message": str(e)})


# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)