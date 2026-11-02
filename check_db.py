# check_db.py
import sqlite3

conn = sqlite3.connect('placements.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())

cur.execute("SELECT * FROM students LIMIT 5")
print("\nStudents:", cur.fetchall())

cur.execute("PRAGMA table_info(students)")
print("\nStudents columns:", cur.fetchall())
# add these lines to check_db.py and run again
cur.execute("SELECT * FROM jobs")
print("\nJobs:", cur.fetchall())

cur.execute("PRAGMA table_info(jobs)")
print("\nJobs columns:", cur.fetchall())

conn.close()