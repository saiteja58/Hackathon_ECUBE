import cv2
import face_recognition
import json
import datetime
import os

# ---- Load Students ----
with open("Students_DB.json", "r") as f:
    students_data = json.load(f)["students"]

known_faces = []
known_students = []  # store dicts with name + roll_no

for student in students_data:
    img = face_recognition.load_image_file(student["photo"])
    encoding = face_recognition.face_encodings(img)[0]
    known_faces.append(encoding)
    known_students.append(student)

# ---- Load today's attendance table ----
today = datetime.date.today().strftime("%Y-%m-%d")
course = input("Enter course code/name: ")

attendance_file = f"Attendance/attendance_{today}_{course}.json"

if not os.path.exists(attendance_file):
    print("⚠️ Attendance file not found! Run start_attendance.py first.")
    exit()

with open(attendance_file, "r") as f:
    attendance_data = json.load(f)

# Convert to dict for quick lookup
attendance_lookup = {record["Roll No"]: record for record in attendance_data["Records"]}

# ---- Start Webcam ----
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
            first_match_index = matches.index(True)
            student = known_students[first_match_index]
            roll_no = student["roll_no"]
            name = student["name"]
            label = f"{roll_no} - {name}"

            # ✅ Mark attendance as Present
            if attendance_lookup[roll_no]["Attendance Status"] == "Absent":
                attendance_lookup[roll_no]["Attendance Status"] = "Present"
                print(f"✅ Marked {name} ({roll_no}) as Present")

        # Draw box & label
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

    cv2.imshow("Face Recognition Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ---- Save updated attendance back to JSON ----
attendance_data["Records"] = list(attendance_lookup.values())

with open(attendance_file, "w") as f:
    json.dump(attendance_data, f, indent=4)

cap.release()
cv2.destroyAllWindows()
print(f"📁 Attendance saved to {attendance_file}")
