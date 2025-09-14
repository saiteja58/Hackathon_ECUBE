import json
import os
import smtplib
from email.message import EmailMessage
import datetime

# ----- Ask Course Name -----
course = input("Enter course name/code: ")
today = datetime.date.today().strftime("%Y-%m-%d")
ATTENDANCE_FILE = f"Attendance/attendance_{today}_{course}.json"

if not os.path.exists(ATTENDANCE_FILE):
    print(f"⚠️ Attendance file for {course} on {today} not found! Run start_attendance.py first.")
    exit()

STUDENTS_FILE = "Students_DB.json"
QUERIES_FILE = "attendance_queries.json"

# Create queries file if it doesn't exist
if not os.path.exists(QUERIES_FILE):
    with open(QUERIES_FILE, "w") as f:
        json.dump({"queries": []}, f, indent=4)

# ----- Load Attendance -----
with open(ATTENDANCE_FILE, "r") as f:
    attendance_data = json.load(f)

# ----- Load Students -----
with open(STUDENTS_FILE, "r") as f:
    students_data = {s["roll_no"]: s for s in json.load(f)["students"]}

# ----- Email Config -----
EMAIL_ADDRESS = "saitejabairoju1@gmail.com"      # Replace with your Gmail
EMAIL_PASSWORD = "vgqzxsjeqcgscsfd"        # Replace with your 16-character App Password

def send_email(to_email, student_name, roll_no):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Attendance Notification - {course} ({today})"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email

        # URL for raising query
        query_link = f"https://forms.gle/AoaFAiFU6k7yhFXo8"


        msg.set_content(f"""
Hello {student_name},

You were marked absent today for {course} ({today}).

If you think this is a mistake, click the link below to raise a query automatically:

{query_link}

- Attendance System
""")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Email sent to {student_name} ({to_email})")
    except Exception as e:
        print(f"❌ Failed to send email to {student_name}: {e}")

# ----- Functions -----
def start_attendance():
    print("\n📊 Current Attendance Status:\n")
    for rec in attendance_data["Records"]:
        print(f"{rec['S.No']}. {rec['Name']} ({rec['Roll No']}): {rec['Attendance Status']}")

    # Automatically send email to all absent students
    print("\n📩 Sending email notifications to absent students...")
    for rec in attendance_data["Records"]:
        if rec["Attendance Status"] == "Absent":
            student_info = students_data[rec["Roll No"]]
            send_email(student_info["mail"], student_info["name"],student_info["roll_no"])

def manual_attendance():
    # Load queries
    with open(QUERIES_FILE, "r") as f:
        queries_data = json.load(f)

    queries = queries_data["queries"]
    if not queries:
        print("\nNo pending queries for manual attendance.")
        return

    print("\n📝 Manual Attendance for Query Students:")
    for roll_no in queries:
        student = next((s for s in attendance_data["Records"] if s["Roll No"] == roll_no), None)
        if student:
            print(f"{student['S.No']}. {student['Name']} ({roll_no})")
            mark = input("Mark Present? (y/n): ").lower()
            if mark == "y":
                student["Attendance Status"] = "Present"

    # Clear queries after manual marking
    queries_data["queries"] = []
    with open(QUERIES_FILE, "w") as f:
        json.dump(queries_data, f, indent=4)

def post_attendance():
    print("\n📌 Posting final attendance...")
    # Save attendance permanently
    with open(ATTENDANCE_FILE, "w") as f:
        json.dump(attendance_data, f, indent=4)

    # Lock JSON by renaming (optional)
    locked_file = ATTENDANCE_FILE.replace(".json", "_FINAL.json")
    os.rename(ATTENDANCE_FILE, locked_file)
    print(f"✅ Attendance posted permanently. File locked as {locked_file}")

def raise_query(roll_no):
    """Simulate a student raising a query"""
    with open(QUERIES_FILE, "r") as f:
        queries_data = json.load(f)

    if roll_no not in queries_data["queries"]:
        queries_data["queries"].append(roll_no)

    with open(QUERIES_FILE, "w") as f:
        json.dump(queries_data, f, indent=4)
    print(f"Query raised for {roll_no}")

# ----- Professor Menu -----
while True:
    print("\n=== Professor Attendance Portal ===")
    print("1. Start Attendance (emails absent students)")
    print("2. Manual Attendance (mark query students present)")
    print("3. Post Attendance (lock JSON)")
    print("4. Exit")

    choice = input("Enter choice: ")

    if choice == "1":
        start_attendance()
    elif choice == "2":
        manual_attendance()
    elif choice == "3":
        post_attendance()
        break
    elif choice == "4":
        break
    else:
        print("❌ Invalid choice")
