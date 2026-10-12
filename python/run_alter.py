
import mysql.connector
import time

conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="1234",
    database="airlines_db"
)

cursor = conn.cursor()

try:
    start = time.time()

    cursor.execute("""
    ALTER TABLE airlines_progress_demo
    ADD INDEX idx_name (airline_name),
    ALGORITHM=INPLACE,
    LOCK=NONE
    """)

    print(f"ALTER TABLE completed in {time.time() - start:.2f} seconds")

finally:
    cursor.close()
    conn.close()
