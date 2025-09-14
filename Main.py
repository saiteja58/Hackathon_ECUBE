import streamlit as st
import os
import json
from datetime import datetime, date
import cv2
import face_recognition
import pandas as pd
import smtplib
from email.message import EmailMessage

# -------------------- CONFIG --------------------
DATA_FILE = "users.json"
PROFILE_FOLDER = "profile_pics"
DB_FILE = "Students_DB.json"
ATTENDANCE_FOLDER = "Attendance"
STUDENT_PHOTOS = "student_photos"

EMAIL_ADDRESS = "saitejabairoju1@gmail.com"
EMAIL_PASSWORD = "vgqzxsjeqcgscsfd"

os.makedirs(PROFILE_FOLDER, exist_ok=True)
os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
os.makedirs(STUDENT_PHOTOS, exist_ok=True)

FACULTY_IDS = [f"{i:03d}" for i in range(1, 11)]

# -------------------- LOAD USERS --------------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        allowed_users = json.load(f)
else:
    allowed_users = {"students": {}, "faculty": {}}

# Normalize
for stu in allowed_users["students"].values():
    stu.setdefault("notifications", [])
    stu.setdefault("queries", [])
for fac in allowed_users["faculty"].values():
    fac.setdefault("notifications", [])
    fac.setdefault("queries", [])

# -------------------- SESSION STATE --------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "allowed_users" not in st.session_state:
    st.session_state.allowed_users = allowed_users
if "notifications_shown" not in st.session_state:
    st.session_state.notifications_shown = []
if "attendance_file" not in st.session_state:
    st.session_state.attendance_file = None
if "course_name" not in st.session_state:
    st.session_state.course_name = ""

st.set_page_config(page_title="Smart Attendance System", page_icon="🎓", layout="wide")

# -------------------- HELPER FUNCTIONS --------------------
def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.allowed_users, f, indent=4)

def faculty_id_exists(fid):
    return any(f.get("faculty_id") == fid for f in st.session_state.allowed_users["faculty"].values())

def roll_exists(roll):
    return any(u.get("roll") == roll for u in st.session_state.allowed_users["students"].values())

def save_profile_pic(uploaded_file, email):
    file_path = os.path.join(PROFILE_FOLDER, f"{email}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# -------------------- STUDENT DATABASE --------------------
def load_students():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"students": []}, f, indent=4)
    with open(DB_FILE, "r") as f:
        return json.load(f)["students"]

def save_students(students):
    with open(DB_FILE, "w") as f:
        json.dump({"students": students}, f, indent=4)

def add_student(roll_no, name, photo_file, email):
    students = load_students()
    for s in students:
        if s["roll_no"] == roll_no:
            st.warning(f"Student with roll no {roll_no} already exists!")
            return
    photo_path = os.path.join(STUDENT_PHOTOS, f"{roll_no}_{photo_file.name}")
    with open(photo_path, "wb") as f:
        f.write(photo_file.getbuffer())
    students.append({"roll_no": roll_no, "name": name, "photo": photo_path, "mail": email})
    save_students(students)
    st.success(f"Student {name} added successfully!")

def start_attendance(course):
    today = date.today().strftime("%Y-%m-%d")
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
    today = date.today().strftime("%Y-%m-%d")
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

# -------------------- HEADER --------------------
st.title("🎓 Smart Attendance System")
st.markdown("Face-recognition based automated attendance + Student/Faculty Portal")

# -------------------- LOGIN & SIGNUP --------------------
if st.session_state.role is None and not st.session_state.show_signup:
    st.subheader("🔐 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    role = st.selectbox("Login as", ["Student", "Faculty"], key="login_role")
    faculty_id_input = st.text_input("Faculty ID (for Faculty login)", key="login_faculty_id") if role=="Faculty" else ""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", key="login_btn"):
            if not email.endswith("@klh.edu.in"):
                st.error("❌ Only @klh.edu.in domain emails are allowed.")
            elif role == "Student":
                if email in st.session_state.allowed_users["students"] and st.session_state.allowed_users["students"][email]["password"] == password:
                    st.session_state.role = role
                    st.session_state.current_user = email
                    st.success("✅ Logged in as Student")
                else:
                    st.error("❌ Invalid Student credentials.")
            elif role == "Faculty":
                if email in st.session_state.allowed_users["faculty"]:
                    fac_data = st.session_state.allowed_users["faculty"][email]
                    if fac_data["password"] == password and fac_data["faculty_id"] == faculty_id_input:
                        st.session_state.role = role
                        st.session_state.current_user = email
                        st.success("✅ Logged in as Faculty")
                    else:
                        st.error("❌ Invalid Faculty credentials or Faculty ID.")
                else:
                    st.error("❌ Invalid Faculty credentials.")
    with col2:
        if st.button("📝 Sign Up", key="show_signup_btn"):
            st.session_state.show_signup = True

# -------------------- SIGNUP --------------------
elif st.session_state.show_signup:
    st.subheader("📝 Sign Up")
    name = st.text_input("Full Name *", key="signup_name")
    new_email = st.text_input("Institution Email *", key="signup_email")
    new_password = st.text_input("Password *", type="password", key="signup_password")
    new_role = st.selectbox("Register as", ["Student", "Faculty"], key="signup_role")
    profile_pic = st.file_uploader("Upload Profile Photo *", type=["jpg","jpeg","png"], key="signup_profile")
    faculty_id = st.text_input(f"Faculty ID (001-010) *", key="signup_faculty_id") if new_role=="Faculty" else ""
    roll_no = st.text_input("Roll No. *", key="signup_roll") if new_role=="Student" else ""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register", key="register_btn"):
            if not name or not new_email or not new_password or not profile_pic or (new_role=="Faculty" and not faculty_id) or (new_role=="Student" and not roll_no):
                st.error("⚠️ All fields are mandatory.")
            elif not new_email.endswith("@klh.edu.in"):
                st.error("❌ Only @klh.edu.in domain emails are allowed.")
            elif new_email in st.session_state.allowed_users["students"] or new_email in st.session_state.allowed_users["faculty"]:
                st.error("⚠️ Email already exists.")
            elif new_role=="Faculty" and faculty_id_exists(faculty_id):
                st.error("⚠️ Faculty ID already taken.")
            elif new_role=="Student" and roll_exists(roll_no):
                st.error("⚠️ Roll No. already exists.")
            else:
                pic_path = save_profile_pic(profile_pic, new_email)
                if new_role == "Faculty":
                    st.session_state.allowed_users["faculty"][new_email] = {
                        "password": new_password, "name": name, "faculty_id": faculty_id,
                        "email": new_email, "profile_pic": pic_path, "queries": [], "notifications": []
                    }
                else:
                    st.session_state.allowed_users["students"][new_email] = {
                        "password": new_password, "name": name, "roll": roll_no,
                        "email": new_email, "profile_pic": pic_path, "notifications": [], "queries": []
                    }
                save_users()
                st.success(f"✅ Registered successfully as {new_role}. Please login now.")
                st.session_state.show_signup = False
    with col2:
        if st.button("⬅️ Back to Login", key="back_login_btn"):
            st.session_state.show_signup = False

# -------------------- STUDENT PORTAL --------------------
elif st.session_state.role == "Student":
    user = st.session_state.allowed_users["students"][st.session_state.current_user]
    st.sidebar.title("🎓 Student Menu")
    if st.sidebar.button("Logout", key="student_logout_btn"):
        st.session_state.role = None
        st.session_state.current_user = None
        st.session_state.show_signup = False
        st.success("Logged out successfully. Refresh to login again.")
        st.stop()
    st.header(f"🎓 Student Portal - {user['name']} (Roll: {user['roll']})")
    if user.get("profile_pic"):
        st.image(user["profile_pic"], width=120, caption="Profile Picture")
    # Display dummy student info and notifications here
    st.subheader("📌 Your Queries & Notifications")
    if user.get("notifications"):
        for note in user["notifications"]:
            st.toast(note)
        user["notifications"] = []
        st.session_state.allowed_users["students"][user["email"]] = user
        save_users()

# -------------------- FACULTY PORTAL --------------------
elif st.session_state.role == "Faculty":
    user = st.session_state.allowed_users["faculty"][st.session_state.current_user]
    st.sidebar.title("📘 Faculty Menu")
    if st.sidebar.button("Logout", key="faculty_logout_btn"):
        st.session_state.role = None
        st.session_state.current_user = None
        st.session_state.show_signup = False
        st.success("Logged out successfully. Refresh to login again.")
        st.stop()
    st.header(f"📘 Faculty Portal - {user['name']} (ID: {user['faculty_id']})")
    if user.get("profile_pic"):
        st.image(user["profile_pic"], width=120, caption="Profile Picture")
    
    st.subheader("🎓 Attendance & Student Management")
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

    if st.session_state.attendance_file:
        records = display_attendance(st.session_state.attendance_file)
        if st.button("Send Emails to Absent Students"):
            send_absent_emails(records, st.session_state.course_name)

    st.markdown("---")
    st.subheader("Add New Student")
    new_roll = st.text_input("Roll Number")
    new_name = st.text_input("Student Name")
    new_mail = st.text_input("Student mail")
    new_photo = st.file_uploader("Student Photo", type=["jpg","jpeg","png"])
    if st.button("Add Student"):
        if new_roll and new_name and new_photo:
            add_student(new_roll,new_name,new_photo,new_mail)
        else:
            st.warning("Fill all fields to add a student!")

# -------------------- MANUAL ATTENDANCE --------------------
if st.session_state.get("current_page")=="manual":
    st.subheader(f"Manual Attendance for {st.session_state.course_name}")
    with open(st.session_state.attendance_file, "r") as f:
        attendance_data = json.load(f)
    if "manual_attendance" not in st.session_state:
        st.session_state.manual_attendance = {rec["Roll No"]: rec["Attendance Status"]=="Present" for rec in attendance_data["Records"]}
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
