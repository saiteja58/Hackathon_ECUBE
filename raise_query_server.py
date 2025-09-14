from flask import Flask, request
import json
import os

app = Flask(__name__)
QUERIES_FILE = "attendance_queries.json"

# create queries file if it doesn't exist
if not os.path.exists(QUERIES_FILE):
    with open(QUERIES_FILE, "w") as f:
        json.dump({"queries": []}, f, indent=4)

@app.route("/raise_query")
def raise_query():
    roll_no = request.args.get("roll_no")
    course = request.args.get("course")
    date = request.args.get("date")

    if not roll_no or not course or not date:
        return "❌ Missing parameters", 400

    with open(QUERIES_FILE, "r") as f:
        queries_data = json.load(f)

    if roll_no not in queries_data["queries"]:
        queries_data["queries"].append(roll_no)
        with open(QUERIES_FILE, "w") as f:
            json.dump(queries_data, f, indent=4)
        return f"✅ Query raised for roll number {roll_no} for {course} on {date}"
    else:
        return f"ℹ️ Query already exists for roll number {roll_no}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

