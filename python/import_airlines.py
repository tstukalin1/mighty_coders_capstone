
import csv
import mysql.connector

CSV_PATH = r"C:\Users\dinud\OneDrive\Desktop\New folder\mariadb-row-project\airlines.csv"

# Update these settings to match your Docker container.
conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="1234",
    database="airlines_db"
)

cursor = conn.cursor()

insert_sql = """
INSERT INTO airlines
(airline_id, name, alias, iata, icao, callsign, country, active)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
name = VALUES(name),
alias = VALUES(alias),
iata = VALUES(iata),
icao = VALUES(icao),
callsign = VALUES(callsign),
country = VALUES(country),
active = VALUES(active)
"""

def clean(value):
    if value == "" or value == r"\N":
        return None
    return value

rows = []

try:
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)

        # Skip the first line if it is a header.
        next(reader, None)

        for row in reader:
            if len(row) != 8:
                continue

            row = [clean(value) for value in row]
            row[0] = int(row[0])
            rows.append(tuple(row))

    cursor.executemany(insert_sql, rows)
    conn.commit()

    print(f"Imported {len(rows)} airline records.")

    cursor.execute("SELECT COUNT(*) FROM airlines")
    print("Total rows in database:", cursor.fetchone()[0])

except Exception as error:
    conn.rollback()
    print("Import failed:", error)
    raise

finally:
    cursor.close()
    conn.close()
