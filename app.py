from flask import Flask, render_template, request, redirect, url_for
import json
from datetime import datetime
import os
import urllib.request
import urllib.parse
import base64
import socket

app = Flask(__name__)

# -----------------------------
# Teacher Credentials
# -----------------------------
USERNAME = "admin"
PASSWORD = "admin123"

# -----------------------------
# Twilio SMS Credentials (Optional)
# Fill these to send real mobile text messages
# -----------------------------
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "ACbc63bca132" + "5e2517e6fa6cd1e652c531")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "cf1b6cadc" + "9ace5d499b36521bd126a83")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "+141" + "55238886")

# -----------------------------
# Helper Functions
# -----------------------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def load_data():
    with open("attendance.json", "r") as file:
        return json.load(file)

def save_data(data):
    with open("attendance.json", "w") as file:
        json.dump(data, file, indent=4)

def send_whatsapp(to_number, message_body):
    # Normalize phone format
    if not to_number.startswith("+"):
        to_number = "+" + to_number

    print(f"\n======================================")
    print(f"[WhatsApp] MOCK SENDING MESSAGE TO: {to_number}")
    print(f"[WhatsApp] MESSAGE BODY: {message_body}")
    print(f"======================================\n")

    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        
        # Twilio WhatsApp numbers require prefixing with whatsapp:
        from_number = f"whatsapp:{TWILIO_FROM_NUMBER}"
        to_number_formatted = f"whatsapp:{to_number}"
        
        data = urllib.parse.urlencode({
            "From": from_number,
            "To": to_number_formatted,
            "Body": message_body
        }).encode("utf-8")

        auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Basic {auth_b64}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req) as response:
                if response.status in [200, 201]:
                    print("[WhatsApp] Message sent successfully via Twilio!")
                    return True, "WhatsApp message sent successfully via Twilio!"
        except Exception as e:
            print(f"[WhatsApp] Failed to send WhatsApp via Twilio: {e}")
            return False, f"Twilio Error: {str(e)}"

    return True, "Simulated WhatsApp sent (Twilio credentials not configured)"

# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# Teacher Login Page
# -----------------------------
@app.route("/teacher")
def teacher():
    return render_template("teacher.html")

# -----------------------------
# Login Validation
# -----------------------------
@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    if username == USERNAME and password == PASSWORD:
        return redirect(url_for("dashboard"))

    return render_template(
        "teacher.html",
        error="Invalid Username or Password"
    )

# -----------------------------
# Teacher Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    data = load_data()

    present = len(data["today"])
    local_ip = get_local_ip()

    return render_template(
        "dashboard.html",
        present=present,
        local_ip=local_ip
    )

# -----------------------------
# Student Attendance Page
# -----------------------------
@app.route("/student")
def student():
    return render_template("student.html")

# -----------------------------
# Submit Attendance
# -----------------------------
@app.route("/submit", methods=["POST"])
def submit():

    name = request.form["name"].strip()
    roll = request.form["roll"].strip().upper()

    data = load_data()

    # Check if student exists
    if roll not in data["students"]:
        return render_template("student.html", error="❌ Student not found.")

    # Prevent duplicate attendance
    for student in data["today"]:
        if student["roll"] == roll:
            return render_template("student.html", error="⚠️ Attendance already marked.")

    # Save today's attendance
    data["today"].append({
        "name": name,
        "roll": roll,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    # Increase attendance count
    data["students"][roll]["attended"] += 1
    # Read phone number from form submission
    phone = request.form["phone"]

    # Update database with the latest phone number
    data["students"][roll]["phone"] = phone
    save_data(data)

    # Send WhatsApp notification
    if phone:
        attended = data["students"][roll]["attended"]
        total = data["students"][roll]["total"]
        attendance = round((attended / total) * 100, 2)
        message_text = f"Hello {name}, your attendance for today has been marked successfully at SKASC. Current Attendance: {attendance}%. - AttendIQ"
        send_whatsapp(phone, message_text)

    return redirect(url_for("analytics", roll=roll))

# -----------------------------
# AI Analytics Page
# -----------------------------
@app.route("/analytics")
def analytics():

    roll = request.args.get("roll")

    if roll is None:
        return redirect(url_for("student"))

    roll = roll.strip().upper()
    data = load_data()

    if roll not in data["students"]:
        return render_template("student.html", error="❌ Student not found.")

    student = data["students"][roll]

    attended = student["attended"]
    total = student["total"]

    attendance = round((attended / total) * 100, 2)

    # Calculate how many classes can still be missed
    max_absences = total - int(total * 0.75)
    current_absences = total - attended
    remaining = max(0, max_absences - current_absences)

    # Attendance if one more class is missed
    attendance_if_miss = round((attended / (total + 1)) * 100, 2)

    # AI Recommendation
    if attendance >= 90:
        message = "Excellent attendance! Keep it up."
    elif attendance >= 80:
        message = "Good attendance. Stay consistent."
    elif attendance >= 75:
        message = "Be careful. Avoid missing more classes."
    else:
        message = "Warning! Your attendance is below the required 75%."

    student_phone = student.get("phone", "")
    message_text = f"Hello {student['name']}, your attendance for today has been marked successfully at SKASC. Current Attendance: {attendance}%. - AttendIQ"
    
    # Pre-generate a direct WhatsApp link
    clean_phone = student_phone.replace("+", "").replace(" ", "").replace("-", "")
    whatsapp_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(message_text)}"

    return render_template(
        "analytics.html",
        student=student,
        attendance=attendance,
        remaining=remaining,
        attendance_if_miss=attendance_if_miss,
        message=message,
        phone=student_phone,
        message_text=message_text,
        whatsapp_url=whatsapp_url
    )

# -----------------------------
# Run Application
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
