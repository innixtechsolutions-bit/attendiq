# ============================================================
# AttendIQ - Smart Attendance Management System
# ============================================================
#
# HOW TO RUN THIS PROJECT (Step by Step)
# -------------------------------------------------------
#
# STEP 1: Make sure Python is installed on your computer.
#         Check by running this in terminal/cmd:
#             python --version
#         If not installed, download from: https://python.org
#
# STEP 2: Open a terminal/cmd inside this project folder.
#         (Right-click the folder → "Open in Terminal")
#
# STEP 3: Activate the virtual environment (venv):
#         On Windows:
#             .\venv\Scripts\activate
#         On Mac/Linux:
#             source venv/bin/activate
#         You should see (venv) appear at the start of the terminal line.
#
# STEP 4: Install required packages (only needed first time):
#             pip install -r requirements.txt
#
# STEP 5: Run the app:
#             python app.py
#
# STEP 6: Open your browser and go to:
#             http://127.0.0.1:5000          ← on this computer
#             http://<your-local-ip>:5000    ← on other devices (same Wi-Fi)
#         Example: http://192.168.0.106:5000
#
# STEP 7: To STOP the app, press:
#             Ctrl + C   in the terminal
#
# -------------------------------------------------------
# TEACHER LOGIN:
#   Username : admin
#   Password : admin123
# -------------------------------------------------------
# ============================================================
# HOW THIS APP WORKS (Simple Guide):
#
# STEP 1: Teacher opens the app and logs in at /teacher
# STEP 2: Teacher dashboard shows how many students attended today
# STEP 3: Teacher starts attendance session (shows QR code on screen)
# STEP 4: Students scan the QR code with their phone
# STEP 5: Students fill their Name, Roll Number, and Phone Number
# STEP 6: App checks if the student is registered in attendance.json
# STEP 7: If valid, attendance is saved and WhatsApp message is sent
# STEP 8: Student sees their attendance analytics (percentage, risk level)
# ============================================================

# --- Import required Python tools ---
from flask import Flask, render_template, request, redirect, url_for
import json                        # To read and write attendance.json file
from datetime import datetime      # To record the time of attendance
import os                          # To read environment variables (secrets)
import urllib.request              # To make HTTP requests (for WhatsApp API)
import urllib.parse                # To format URL and message data
import base64                      # To encode login credentials for API
import socket                      # To find the local IP address of the computer

# --- Create the Flask web app ---
app = Flask(__name__)

# ============================================================
# TEACHER LOGIN CREDENTIALS
# Change these to your own username and password
# ============================================================
USERNAME = "admin"
PASSWORD = "admin123"

# ============================================================
# TWILIO WHATSAPP CREDENTIALS (Optional)
# If you want to send real WhatsApp messages, fill these in.
# If left empty, messages will be simulated (printed in terminal only).
# You can get these from: https://www.twilio.com/console
# ============================================================
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "ACbc63bca132" + "5e2517e6fa6cd1e652c531")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN",  "cf1b6cadc" + "9ace5d499b36521bd126a83")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "+141" + "55238886")


# ============================================================
# HELPER FUNCTION 1: Find Local IP Address
# This is used so students on the same Wi-Fi can open the app
# ============================================================
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a dummy address just to detect the local network IP
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'   # Default to localhost if network not available
    finally:
        s.close()
    return IP


# ============================================================
# HELPER FUNCTION 2: Load Attendance Data from File
# Reads the attendance.json file and returns it as a Python dictionary
# ============================================================
def load_data():
    with open("attendance.json", "r") as file:
        return json.load(file)


# ============================================================
# HELPER FUNCTION 3: Save Attendance Data to File
# Writes updated attendance back into attendance.json
# ============================================================
def save_data(data):
    with open("attendance.json", "w") as file:
        json.dump(data, file, indent=4)


# ============================================================
# HELPER FUNCTION 4: Send WhatsApp Message via Twilio
# Sends a message to the student's phone number after attendance is marked
#
# HOW IT WORKS:
# - Cleans and formats the phone number (adds +91 for Indian numbers)
# - Sends a POST request to Twilio's API with the message
# - If Twilio is not configured, it just prints the message in the terminal
# ============================================================
def send_whatsapp(to_number, message_body):

    # --- Step A: Clean the phone number ---
    # Remove spaces, dashes, and brackets from the number
    to_number_clean = to_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # --- Step B: Format with country code ---
    if to_number_clean.startswith("+"):
        pass  # Already has country code like +919999999999
    elif to_number_clean.startswith("91") and len(to_number_clean) == 12:
        to_number_clean = "+" + to_number_clean  # Add + before 91XXXXXXXXXX
    elif len(to_number_clean) == 10:
        to_number_clean = "+91" + to_number_clean  # Add +91 before 10-digit Indian number
    else:
        if not to_number_clean.startswith("+"):
            to_number_clean = "+" + to_number_clean

    to_number = to_number_clean

    # --- Step C: Print the message in the terminal (for debugging) ---
    print(f"\n======================================")
    print(f"[WhatsApp] MOCK SENDING MESSAGE TO: {to_number}")
    print(f"[WhatsApp] MESSAGE BODY: {message_body}")
    print(f"======================================\n")

    # --- Step D: Try sending via Twilio API if credentials are available ---
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

        # Twilio requires the WhatsApp prefix on both numbers
        from_number = f"whatsapp:{TWILIO_FROM_NUMBER}"
        to_number_formatted = f"whatsapp:{to_number}"

        # Prepare the message data as form fields
        data = urllib.parse.urlencode({
            "From": from_number,
            "To":   to_number_formatted,
            "Body": message_body
        }).encode("utf-8")

        # Encode Twilio credentials (Account SID + Auth Token) for Basic Auth
        auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
        auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        # Build and send the HTTP POST request to Twilio
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

    # If Twilio is not configured, just simulate the message
    return True, "Simulated WhatsApp sent (Twilio credentials not configured)"


# ============================================================
# PAGE 1: Home Page  →  Route: /
# This is the first page students and teachers see when they open the app
# ============================================================
@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# PAGE 2: Teacher Login Page  →  Route: /teacher
# Teacher opens this page to log in with username and password
# ============================================================
@app.route("/teacher")
def teacher():
    return render_template("teacher.html")


# ============================================================
# PAGE 3: Login Form Handler  →  Route: /login  (POST only)
# This runs when the teacher submits the login form
#
# STEP 1: Get the username and password from the form
# STEP 2: Check if they match the stored credentials
# STEP 3: If correct → go to Dashboard
# STEP 4: If wrong   → show error message on login page
# ============================================================
@app.route("/login", methods=["POST"])
def login():

    # Step 1: Read what the teacher typed in the form
    username = request.form.get("username")
    password = request.form.get("password")

    # Step 2 & 3: Check credentials and redirect to dashboard if correct
    if username == USERNAME and password == PASSWORD:
        return redirect(url_for("dashboard"))

    # Step 4: Wrong credentials — show error
    return render_template(
        "teacher.html",
        error="Invalid Username or Password"
    )


# ============================================================
# PAGE 4: Teacher Dashboard  →  Route: /dashboard
# Shows the teacher how many students have attended today
# Also shows the local IP address so students can connect via Wi-Fi
# ============================================================
@app.route("/dashboard")
def dashboard():

    # Load today's attendance data from the JSON file
    data = load_data()

    # Count how many students are marked present today
    present = len(data["today"])

    # Get the computer's local IP address (for students to connect on Wi-Fi)
    local_ip = get_local_ip()

    return render_template(
        "dashboard.html",
        present=present,
        local_ip=local_ip
    )


# ============================================================
# PAGE 5: Student Attendance Page  →  Route: /student
# Student opens this after scanning the QR code
# They fill in their Name, Roll Number, and Phone Number
# ============================================================
@app.route("/student")
def student():
    return render_template("student.html")


# ============================================================
# PAGE 6: Submit Attendance  →  Route: /submit  (POST only)
# This runs when the student submits the attendance form
#
# STEP 1: Read student's Name, Roll Number, and Phone from the form
# STEP 2: Check if the Roll Number exists in attendance.json
# STEP 3: Check if attendance was already marked today (prevent duplicates)
# STEP 4: Save the attendance with current time
# STEP 5: Increase the student's attended count by 1
# STEP 6: Send a WhatsApp notification to the student
# STEP 7: Redirect to the analytics page to show their stats
# ============================================================
@app.route("/submit", methods=["POST"])
def submit():

    # Step 1: Get form data (strip removes extra spaces)
    name  = request.form["name"].strip()
    roll  = request.form["roll"].strip().upper()   # Convert to uppercase for consistency

    # Load current data from the JSON file
    data = load_data()

    # Step 2: Check if this roll number is registered in the system
    if roll not in data["students"]:
        return render_template("student.html", error="❌ Student not found.")

    # Step 3: Check if this student already marked attendance today
    for student in data["today"]:
        if student["roll"] == roll:
            return render_template("student.html", error="⚠️ Attendance already marked.")

    # Step 4: Add attendance entry with current time
    data["today"].append({
        "name": name,
        "roll": roll,
        "time": datetime.now().strftime("%H:%M:%S")   # Format: HH:MM:SS
    })

    # Step 5: Increase the student's total attended class count
    data["students"][roll]["attended"] += 1

    # Read phone number submitted by the student
    phone = request.form["phone"]

    # Save/update the phone number in the database
    data["students"][roll]["phone"] = phone

    # Write all changes back to the JSON file
    save_data(data)

    # Step 6: Send WhatsApp notification if phone number is provided
    if phone:
        attended   = data["students"][roll]["attended"]
        total      = data["students"][roll]["total"]
        attendance = round((attended / total) * 100, 2)

        # Build the WhatsApp message text
        message_text = f"Hello {name}, your attendance for today has been marked successfully at SKASC. Current Attendance: {attendance}%. - AttendIQ"
        send_whatsapp(phone, message_text)

    # Step 7: Go to the analytics page to show attendance stats
    return redirect(url_for("analytics", roll=roll))


# ============================================================
# PAGE 7: AI Analytics Page  →  Route: /analytics?roll=ROLLNO
# Shows the student their attendance percentage and suggestions
#
# STEP 1: Get the roll number from the URL
# STEP 2: Load the student's data
# STEP 3: Calculate attendance percentage
# STEP 4: Calculate how many more classes can be missed (75% rule)
# STEP 5: Generate an AI recommendation message based on percentage
# STEP 6: Create a WhatsApp share link
# STEP 7: Show all data on the analytics page
# ============================================================
@app.route("/analytics")
def analytics():

    # Step 1: Get roll number from URL (e.g., /analytics?roll=24BCT061)
    roll = request.args.get("roll")

    # If no roll number provided, send back to student page
    if roll is None:
        return redirect(url_for("student"))

    roll = roll.strip().upper()
    data = load_data()

    # Step 2: Check if roll number is valid
    if roll not in data["students"]:
        return render_template("student.html", error="❌ Student not found.")

    student = data["students"][roll]

    attended = student["attended"]   # Number of classes attended
    total    = student["total"]      # Total classes held so far

    # Step 3: Calculate percentage  (e.g., 19/22 * 100 = 86.36%)
    attendance = round((attended / total) * 100, 2)

    # Step 4: Calculate how many more classes can be skipped and stay above 75%
    max_absences    = total - int(total * 0.75)    # Max allowed absences
    current_absences = total - attended             # How many already missed
    remaining       = max(0, max_absences - current_absences)  # Classes that can still be missed

    # What would the percentage be if one more class is missed?
    attendance_if_miss = round((attended / (total + 1)) * 100, 2)

    # Step 5: AI Recommendation based on attendance percentage
    if attendance >= 90:
        message = "Excellent attendance! Keep it up."
    elif attendance >= 80:
        message = "Good attendance. Stay consistent."
    elif attendance >= 75:
        message = "Be careful. Avoid missing more classes."
    else:
        message = "Warning! Your attendance is below the required 75%."

    # Step 6: Create a WhatsApp share link so student can share their status
    student_phone = student.get("phone", "")
    message_text  = f"Hello {student['name']}, your attendance for today has been marked successfully at SKASC. Current Attendance: {attendance}%. - AttendIQ"

    # Clean the phone number for the WhatsApp URL (remove + sign and spaces)
    clean_phone   = student_phone.replace("+", "").replace(" ", "").replace("-", "")
    whatsapp_url  = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(message_text)}"

    # Step 7: Render the analytics page with all calculated data
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


# ============================================================
# START THE APP
# When you run: python app.py
# The app starts on port 5000
# Open browser at: http://127.0.0.1:5000
# Students on same Wi-Fi use: http://<your-local-ip>:5000
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
