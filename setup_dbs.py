import sqlite3
from pymongo import MongoClient

# --- 1. SQL Setup (SQLite) ---
def setup_sql():
    # This creates a file named 'placements.db' in your folder
    conn = sqlite3.connect('placements.db')
    cursor = conn.cursor()
    
    # Create our strict tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (student_id INTEGER PRIMARY KEY, name TEXT, department TEXT, gpa REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs 
                      (job_id INTEGER PRIMARY KEY, company TEXT, role TEXT, package INTEGER)''')
    
    # Clear old data so we don't get duplicates if we run this twice
    cursor.execute("DELETE FROM students")
    cursor.execute("DELETE FROM jobs")
    
    # Add mock data
    students = [
        (1, 'Alice Smith', 'Computer Science', 3.8),
        (2, 'Bob Jones', 'Data Science', 3.6),
        (3, 'Charlie Brown', 'Electrical', 3.2)
    ]
    jobs = [
        (101, 'Axcentra', 'Python Developer', 80000),
        (102, 'IRA Labs', 'AI Engineer', 95000),
        (103, 'Global Tech', 'Data Analyst', 70000)
    ]
    
    cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?)", students)
    cursor.executemany("INSERT INTO jobs VALUES (?, ?, ?, ?)", jobs)
    conn.commit()
    conn.close()
    print("SQL database initialized.")

# --- 2. NoSQL Setup (MongoDB) ---
def setup_nosql():
    # Connects to your local MongoDB server
    client = MongoClient('mongodb://localhost:27017/')
    db = client['placement_db']
    feedbacks = db['interview_feedbacks']
    
    # Clear old data
    feedbacks.delete_many({})
    
    # Add mock flexible document data
    mock_feedbacks = [
        {
            "student_id": 1,
            "job_id": 101,
            "rounds": [
                {"type": "Technical", "score": 85, "notes": "Strong in Python and SQL backend logic."},
                {"type": "HR", "status": "Passed", "notes": "Good communication, ready to join."}
            ]
        },
        {
            "student_id": 2,
            "job_id": 102,
            "rounds": [
                {"type": "Technical", "score": 92, "notes": "Excellent algorithmic thinking. Good with machine learning concepts."}
            ]
        }
    ]
    
    feedbacks.insert_many(mock_feedbacks)
    print("MongoDB initialized.")

if __name__ == "__main__":
    setup_sql()
    setup_nosql()