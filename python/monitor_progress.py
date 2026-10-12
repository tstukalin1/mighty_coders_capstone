
import time
import mysql.connector

DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "airlines_db",
}

conn = mysql.connector.connect(**DB)
cursor = conn.cursor(dictionary=True)

query = """
SELECT ID, TIME, STATE, INFO, STAGE, MAX_STAGE, PROGRESS
FROM information_schema.PROCESSLIST
WHERE ID <> CONNECTION_ID()
  AND (
      INFO LIKE 'ALTER TABLE airlines_progress_demo%'
      OR INFO LIKE 'CHECK TABLE airlines_progress_demo%'
  )
"""

try:
    print("Monitoring MariaDB operations. Press Ctrl+C to stop.")

    while True:
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            print(
                f"ID={row['ID']} | "
                f"Time={row['TIME']}s | "
                f"Stage={row['STAGE']}/{row['MAX_STAGE']} | "
                f"Progress={row['PROGRESS']:.2f}% | "
                f"State={row['STATE']}"
            )

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nMonitoring stopped.")

finally:
    cursor.close()
    conn.close()
