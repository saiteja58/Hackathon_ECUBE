# attendance_portal_app.py
import streamlit as st
import json
import os
import datetime
import cv2
import face_recognition
import smtplib
from email.message import EmailMessage
import pandas as pd

# -------------------- Dummy faculty login --------------------
DUMMY_CREDENTIALS = {
    "s": "1",
    "prof2@example.com": "abc123",
    "prof3@example.com": "xyz789",
    "prof4@example.com": "faculty456",
    "prof5@example.com": "mypassword",
}

# -------------------- Email Config --------------------
EMAIL_ADDRESS = "saitejabairoju1@gmail.com"
EMAIL_PASSWORD = "vgqzxsjeqcgscsfd"

# -------------------- Helper Functions --------------------
DB_FILE = "Students_DB.json"
ATTENDANCE_FOLDER = "Attendance"
os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
os.makedirs("student_photos", exist_ok=True)

def load_students():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"students": []}, f, indent=4)
    with open(DB_FILE, "r") as f:
        return json.load(f)["students"]

def save_students(students):
    with open(DB_FILE, "w") as f:
        json.dump({"students": students}, f, indent=4)

def add_student(roll_no, name, photo_file, email="dummy@example.com"):
    students = load_students()
    for s in students:
        if s["roll_no"] == roll_no:
            st.warning(f"Student with roll no {roll_no} already exists!")
            return
    photo_path = os.path.join("student_photos", f"{roll_no}_{photo_file.name}")
    with open(photo_path, "wb") as f:
        f.write(photo_file.getbuffer())
    students.append({"roll_no": roll_no, "name": name, "photo": photo_path, "mail": email})
    save_students(students)
    st.success(f"Student {name} added successfully!")

def start_attendance(course):
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"{ATTENDANCE_FOLDER}/attendance_{today}_{course}.json"
    students = load_students()
    attendance_records = [{"S.No": i+1, "Name": s["name"], "Roll No": s["roll_no"], "Attendance Status": "Absent"} 
                          for i, s in enumerate(students)]
    attendance_data = {"Date": today, "Course": course, "Records": attendance_records}
    with open(filename, "w") as f:
        json.dump(attendance_data, f, indent=4)
    st.success(f"Attendance initialized for course {course} ✅")
    return filename

def run_face_recognition(attendance_file):
    with open(attendance_file, "r") as f:
        attendance_data = json.load(f)
    students = load_students()
    known_faces = []
    known_students = []
    for student in students:
        img = face_recognition.load_image_file(student["photo"])
        encoding = face_recognition.face_encodings(img)[0]
        known_faces.append(encoding)
        known_students.append(student)
    attendance_lookup = {rec["Roll No"]: rec for rec in attendance_data["Records"]}
    st.info("Starting camera... Press 'q' in the window to stop.")
    cap = cv2.VideoCapture(1)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.5)
            label = "Unknown"
            if True in matches:
                idx = matches.index(True)
                student = known_students[idx]
                roll_no = student["roll_no"]
                name = student["name"]
                label = f"{roll_no} - {name}"
                if attendance_lookup[roll_no]["Attendance Status"] == "Absent":
                    attendance_lookup[roll_no]["Attendance Status"] = "Present"
                    st.success(f"Marked Present: {name} ({roll_no})")
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Face Recognition Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    attendance_data["Records"] = list(attendance_lookup.values())
    with open(attendance_file, "w") as f:
        json.dump(attendance_data, f, indent=4)
    st.success(f"Attendance saved to {attendance_file}")

def display_attendance(attendance_file):
    with open(attendance_file, "r") as f:
        attendance_data = json.load(f)
    df = pd.DataFrame(attendance_data["Records"])
    def color_rows(row):
        return ['background-color: lightgreen' if row['Attendance Status']=="Present" else 'background-color: salmon']*len(row)
    st.subheader("Attendance Table")
    st.dataframe(df.style.apply(color_rows, axis=1))
    return attendance_data["Records"]

def send_absent_emails(records, course):
    today = datetime.date.today().strftime("%Y-%m-%d")
    for rec in records:
        if rec["Attendance Status"] == "Absent":
            student_email = next((s["mail"] for s in load_students() if s["roll_no"] == rec["Roll No"]), None)
            if student_email:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = f"Attendance Notification - {course} ({today})"
                    msg['From'] = EMAIL_ADDRESS
                    msg['To'] = student_email
                    query_link = "https://forms.gle/AoaFAiFU6k7yhFXo8"
                    msg.set_content(f"Hello {rec['Name']},\n\nYou were marked absent today for {course} ({today}).\n\nIf this is a mistake, click below to raise a query:\n{query_link}\n\n- Attendance System")
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                        smtp.send_message(msg)
                    st.success(f"Email sent to {rec['Name']} ({student_email})")
                except Exception as e:
                    st.error(f"Failed to send email to {rec['Name']}: {e}")

# -------------------- Manual Attendance Page --------------------
def manual_attendance_page():
    course_name = st.session_state.course_name
    st.subheader(f"Manual Attendance for {course_name}")
    with open(st.session_state.attendance_file, "r") as f:
        attendance_data = json.load(f)
    if "manual_attendance" not in st.session_state:
        st.session_state.manual_attendance = {
            rec["Roll No"]: rec["Attendance Status"]=="Present" for rec in attendance_data["Records"]
        }
    st.write("Mark students as Present (unchecked = Absent)")
    for rec in attendance_data["Records"]:
        st.session_state.manual_attendance[rec["Roll No"]] = st.checkbox(
            f"{rec['Name']} ({rec['Roll No']})",
            value=st.session_state.manual_attendance[rec["Roll No"]],
            key=rec["Roll No"]
        )
    if st.button("Post Attendance"):
        for rec in attendance_data["Records"]:
            rec["Attendance Status"] = "Present" if st.session_state.manual_attendance[rec["Roll No"]] else "Absent"
        with open(st.session_state.attendance_file, "w") as f:
            json.dump(attendance_data, f, indent=4)
        st.success("Manual attendance finalized and saved ✅")
        del st.session_state.manual_attendance
        st.session_state.current_page = "dashboard"

# -------------------- MAIN APP --------------------
st.title("🎓 Faculty Attendance Portal")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"
if "course_name" not in st.session_state:
    st.session_state.course_name = ""
if "attendance_file" not in st.session_state:
    st.session_state.attendance_file = None

# --------- LOGIN PAGE ---------
if st.session_state.current_page=="login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in DUMMY_CREDENTIALS and DUMMY_CREDENTIALS[email]==password:
            st.session_state.logged_in = True
            st.session_state.current_page = "dashboard"
            st.success("Logged in successfully ✅")
        else:
            st.error("Invalid credentials ❌")

# --------- DASHBOARD PAGE ---------
elif st.session_state.current_page=="dashboard":
    st.subheader("Dashboard")
    st.session_state.course_name = st.text_input("Course Name / Code", value=st.session_state.course_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Attendance"):
            if st.session_state.course_name:
                st.session_state.attendance_file = start_attendance(st.session_state.course_name)
            else:
                st.warning("Enter course name first!")
    with col2:
        if st.button("Start Camera (Face Recognition)"):
            if st.session_state.attendance_file:
                run_face_recognition(st.session_state.attendance_file)
            else:
                st.warning("Start attendance first!")
    with col3:
        if st.button("Manual Attendance"):
            if st.session_state.attendance_file:
                st.session_state.current_page = "manual"
            else:
                st.warning("Start attendance first!")

    if st.session_state.attendance_file:
        records = display_attendance(st.session_state.attendance_file)
        if st.button("Send Emails to Absent Students"):
            send_absent_emails(records, st.session_state.course_name)

    st.markdown("---")
    st.subheader("Add New Student")
    new_roll = st.text_input("Roll Number")
    new_name = st.text_input("Student Name")
    new_photo = st.file_uploader("Student Photo", type=["jpg","jpeg","png"])
    if st.button("Add Student"):
        if new_roll and new_name and new_photo:
            add_student(new_roll,new_name,new_photo)
        else:
            st.warning("Fill all fields to add a student!")

# --------- MANUAL ATTENDANCE PAGE ---------
elif st.session_state.current_page=="manual":
    manual_attendance_page()
