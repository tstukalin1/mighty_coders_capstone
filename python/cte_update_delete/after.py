"""
after.py — UPDATE/DELETE with CTEs (MariaDB 10.2+)

The WITH clause names and isolates the filtering logic.
No double nesting needed. Complex conditions stay readable.
Source data: OpenFlights airports dataset (airports.dat).

"""

import csv
import io
import sys
import os
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
LIMIT = 50  #airports to load


def fetch_airports():
    #download airports.dat, return (iata, name, country) — iata may be empty
    airports = []
    with urllib.request.urlopen(AIRPORTS_URL) as response:
        for row in csv.reader(io.TextIOWrapper(response, encoding="utf-8")):
            iata    = row[4].strip()
            name    = row[1].strip()
            country = row[3].strip()
            airports.append((iata if iata != r"\N" else "", name, country))
            if len(airports) >= LIMIT:
                break
    return airports


def setup(cur, airports):
    cur.execute("DROP TABLE IF EXISTS demo_airports")
    cur.execute(
        "CREATE TABLE demo_airports ("
        "  id      INT AUTO_INCREMENT PRIMARY KEY,"
        "  iata    CHAR(3)      NOT NULL DEFAULT '',"
        "  name    VARCHAR(100) NOT NULL,"
        "  country VARCHAR(100) NOT NULL,"
        "  status  VARCHAR(20)  NOT NULL DEFAULT 'unknown'"
        ")"
    )
    for iata, name, country in airports:
        cur.execute(
            "INSERT INTO demo_airports (iata, name, country) VALUES (%s, %s, %s)",
            (iata, name, country),
        )


def main():
    airports = fetch_airports()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            setup(cur, airports)
            cur.execute(  #CTE names the filter — intent is clear before the UPDATE
                "WITH registered AS ("
                "  SELECT id FROM demo_airports WHERE iata != ''"
                ")"
                " UPDATE demo_airports SET status = 'active'"
                " WHERE id IN (SELECT id FROM registered)"
            )
            cur.execute(  #CTE makes the DELETE condition self-documenting
                "WITH no_iata AS ("
                "  SELECT id FROM demo_airports WHERE iata = ''"
                ")"
                " DELETE FROM demo_airports"
                " WHERE id IN (SELECT id FROM no_iata)"
            )
            cur.execute("SELECT iata, name, country, status FROM demo_airports ORDER BY iata")
            rows = cur.fetchall()
        print("[after.py] Airports after UPDATE+DELETE via CTE:")
        for iata, name, country, status in rows:
            print(f"  {iata}  {status}  {name} ({country})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
