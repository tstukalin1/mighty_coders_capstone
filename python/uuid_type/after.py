"""
after.py — API keys stored as UUID (MariaDB 10.7+)

16 bytes instead of 36. Invalid values rejected at INSERT time.
DEFAULT UUID() generates a valid v1 UUID automatically.
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
LIMIT = 20  #number of airports to use


def fetch_airports():
    #download airports.dat, return (iata, name) pairs with valid 3-letter IATA codes
    airports = []
    with urllib.request.urlopen(AIRPORTS_URL) as response:
        for row in csv.reader(io.TextIOWrapper(response, encoding="utf-8")):
            iata, name = row[4], row[1]
            if iata and iata != r"\N" and len(iata) == 3:
                airports.append((iata, name))
                if len(airports) >= LIMIT:
                    break
    return airports


def main():
    airports = fetch_airports()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_airport_keys_new")
            cur.execute(
                "CREATE TABLE demo_airport_keys_new ("
                "  iata    CHAR(3)      NOT NULL PRIMARY KEY,"
                "  name    VARCHAR(100) NOT NULL,"
                "  api_key UUID         NOT NULL DEFAULT UUID()"  #auto-generated, validated
                ")"
            )
            for iata, name in airports:
                cur.execute(  #UUID() called automatically — no uuid.uuid4() needed in Python
                    "INSERT INTO demo_airport_keys_new (iata, name) VALUES (%s, %s)",
                    (iata, name),
                )
            cur.execute("SELECT iata, name, api_key FROM demo_airport_keys_new")
            rows = cur.fetchall()
        print("[after.py] UUID — auto-generated, 16 bytes, validated:")
        for iata, name, key in rows:
            print(f"  {iata}  {key}  {name}")
        print()
        print("Storage: UUID=16 bytes vs CHAR(36)=36 bytes (2.25x smaller)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
