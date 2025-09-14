import json

DB_FILE = "Students_DB.json"

def add_student(roll_no, name, photo_path):
    # Load existing data
    with open(DB_FILE, "r") as f:
        data = json.load(f)

    # Check if roll_no already exists
    for student in data["students"]:
        if student["roll_no"] == roll_no:
            print(f"⚠️ Student with roll_no {roll_no} already exists.")
            return

    # Add new student
    new_student = {
        "roll_no": roll_no,
        "name": name,
        "photo": photo_path
    }
    data["students"].append(new_student)

    # Save back to JSON
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Student {name} ({roll_no}) added successfully!")


# Example usage (you can change these or wrap in input prompts)
if __name__ == "__main__":
    roll_no = input("Enter Roll Number: ")
    name = input("Enter Student Name: ")
    photo = input("Enter Path to Photo: ")

    add_student(roll_no, name, photo)
