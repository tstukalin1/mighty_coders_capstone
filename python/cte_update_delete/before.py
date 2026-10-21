"""
before.py — UPDATE/DELETE with nested subqueries

The filtering logic is buried inside WHERE IN (SELECT ...).
MariaDB requires double nesting for UPDATE/DELETE subqueries
that reference the same table being modified.
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
            cur.execute(  #double nesting required — MariaDB limitation with self-referencing subquery
                "UPDATE demo_airports SET status = 'active'"
                " WHERE id IN ("
                "   SELECT id FROM ("
                "     SELECT id FROM demo_airports WHERE iata != ''"
                "   ) AS sub"
                " )"
            )
            cur.execute(  #same double-nesting pattern for DELETE
                "DELETE FROM demo_airports"
                " WHERE id IN ("
                "   SELECT id FROM ("
                "     SELECT id FROM demo_airports WHERE iata = ''"
                "   ) AS sub"
                " )"
            )
            cur.execute("SELECT iata, name, country, status FROM demo_airports ORDER BY iata")
            rows = cur.fetchall()
        print("[before.py] Airports after UPDATE+DELETE via subquery:")
        for iata, name, country, status in rows:
            print(f"  {iata}  {status}  {name} ({country})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
