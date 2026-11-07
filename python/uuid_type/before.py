"""
before.py — API keys stored as CHAR(36)

No validation: any string is accepted. Sort order is lexicographic,
not time-based. Storage: 36 bytes per value.
Source data: OpenFlights airports dataset (data/airports.csv, loaded into the airports table).
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

LIMIT = 20  #number of airports to use


def fetch_airports():
    #read (iata, name) pairs with a 3-letter IATA code from the airports table
    #(loaded from data/airports.csv by sql/init/12_flight_dataset.sql)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT iata, name FROM airports"
                " WHERE CHAR_LENGTH(iata) = 3 ORDER BY id LIMIT %s",
                (LIMIT,),
            )
            return list(cur.fetchall())
    finally:
        conn.close()

def main():
    airports = fetch_airports()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_airport_keys_old")
            cur.execute(
                "CREATE TABLE demo_airport_keys_old ("
                "  iata    CHAR(3)      NOT NULL PRIMARY KEY,"
                "  name    VARCHAR(100) NOT NULL,"
                "  api_key CHAR(36)     NOT NULL"  #plain string, any value accepted
                ")"
            )
            for iata, name in airports:
                cur.execute(
                    "INSERT INTO demo_airport_keys_old (iata, name, api_key) VALUES (%s, %s, %s)",
                    (iata, name, str(uuid.uuid4())),
                )
            cur.execute(  #CHAR(36) silently accepts garbage — no validation
                "INSERT INTO demo_airport_keys_old (iata, name, api_key) VALUES (%s, %s, %s)",
                ("XXX", "Fake Airport", "not-a-uuid-at-all"),
            )
            cur.execute("SELECT iata, name, api_key FROM demo_airport_keys_old")
            rows = cur.fetchall()
        print("[before.py] CHAR(36) — invalid key accepted silently:")
        for iata, name, key in rows:
            valid = len(key) == 36 and key.count("-") == 4
            flag = "OK" if valid else "INVALID"
            print(f"  [{flag}] {iata}  {key}  {name}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
