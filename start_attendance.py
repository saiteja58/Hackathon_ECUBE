import json
import datetime
import os

# Load students from JSON
with open("Students_DB.json", "r") as f:
    students = json.load(f)["students"]

# Ask course name
course = input("Enter course code/name: ")

# Get today’s date
today = datetime.date.today().strftime("%Y-%m-%d")

# Create new table (list of dicts)
attendance_table = []
for idx, student in enumerate(students, start=1):
    attendance_table.append({
        "S.No": idx,
        "Name": student["name"],
        "Roll No": student["roll_no"],
        "Attendance Status": "Absent"   # default
    })

# Prepare final structure
attendance_record = {
    "Date": today,
    "Course": course,
    "Records": attendance_table
}

# Save as JSON file
filename = f"Attendance/attendance_{today}_{course}.json"
with open(filename, "w") as f:
    json.dump(attendance_record, f, indent=4)

print(f"✅ Attendance table created: {filename}")
