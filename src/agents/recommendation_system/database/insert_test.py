"""
One-time test: inserts a single real resource into our resources table, to
confirm INSERT works before we build this into a reusable function.
"""

import os
import psycopg2

connection = psycopg2.connect(
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT"),
    dbname=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
)
cursor = connection.cursor()

cursor.execute(
    """
    INSERT INTO resources (title, url, description, topic, difficulty, format, duration)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """,
    (
        "Machine Learning for Absolute Beginners",
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "A short beginner-friendly video introduction to machine learning.",
        "machine learning",
        "beginner",
        "video",
        "short",
    ),
)

connection.commit()
print("Inserted successfully.")

cursor.execute("SELECT * FROM resources;")
rows = cursor.fetchall()

print("\nEverything currently in the table:")
for row in rows:
    print(row)

cursor.close()
connection.close()