import os
import psycopg2

try:
    connection = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        dbname=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
    )
    cursor = connection.cursor()

    cursor.execute("SELECT version();")
    result = cursor.fetchone()

    print("Connected successfully!")
    print("Server says:", result)

    cursor.close()
    connection.close()
except Exception as error:
    print("Connection failed:", error)