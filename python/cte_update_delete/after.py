"""
after.py — UPDATE/DELETE with a derived-table JOIN (MariaDB)

MariaDB 11.4 does not support WITH ... UPDATE / WITH ... DELETE (error 1064).
The working way is UPDATE ... JOIN (SELECT ...) AS name: the derived table
names the filtering logic, so no double nesting is needed.
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
            cur.execute(  #the derived table names the filter, the JOIN applies it
                "UPDATE demo_airports"
                " JOIN (SELECT id FROM demo_airports WHERE iata != '') AS registered"
                "   ON demo_airports.id = registered.id"
                " SET demo_airports.status = 'active'"
            )
            cur.execute(  #same pattern for DELETE
                "DELETE demo_airports FROM demo_airports"
                " JOIN (SELECT id FROM demo_airports WHERE iata = '') AS no_iata"
                "   ON demo_airports.id = no_iata.id"
            )
            cur.execute("SELECT iata, name, country, status FROM demo_airports ORDER BY iata")
            rows = cur.fetchall()
        print("[after.py] Airports after UPDATE+DELETE via derived-table JOIN:")
        for iata, name, country, status in rows:
            print(f"  {iata}  {status}  {name} ({country})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
