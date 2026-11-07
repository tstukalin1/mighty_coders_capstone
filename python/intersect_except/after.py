"""
after.py — set operations via INTERSECT and EXCEPT (MariaDB 10.3+)

Intent is immediately clear from the operator name.
No JOIN boilerplate needed.
Source data: OpenFlights routes dataset (data/routes.csv, loaded into the routes table).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

SOURCE_A = "AMS"  #Amsterdam Schiphol
SOURCE_B = "FRA"  #Frankfurt Airport
LIMIT    = 50     #destinations per source airport


def fetch_routes():
    #read the first LIMIT distinct destinations of both airports from the routes table
    #(loaded from data/routes.csv by sql/init/12_flight_dataset.sql)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            result = []
            for source in (SOURCE_A, SOURCE_B):
                cur.execute(
                    "SELECT dest_airport FROM routes WHERE source_airport = %s"
                    " GROUP BY dest_airport ORDER BY MIN(id) LIMIT %s",
                    (source, LIMIT),
                )
                result.append([row[0] for row in cur.fetchall()])
            return result[0], result[1]
    finally:
        conn.close()

def setup(cur, dests_a, dests_b):
    cur.execute("DROP TABLE IF EXISTS demo_routes_ams")
    cur.execute("DROP TABLE IF EXISTS demo_routes_fra")
    cur.execute("CREATE TABLE demo_routes_ams (destination CHAR(3) NOT NULL)")
    cur.execute("CREATE TABLE demo_routes_fra (destination CHAR(3) NOT NULL)")
    for d in dests_a:
        cur.execute("INSERT INTO demo_routes_ams VALUES (%s)", (d,))
    for d in dests_b:
        cur.execute("INSERT INTO demo_routes_fra VALUES (%s)", (d,))


def main():
    dests_a, dests_b = fetch_routes()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            setup(cur, dests_a, dests_b)
            cur.execute(  #INTERSECT — destinations served from both airports
                "SELECT destination FROM demo_routes_ams"
                " INTERSECT"
                " SELECT destination FROM demo_routes_fra"
                " ORDER BY destination"
            )
            both = [r[0] for r in cur.fetchall()]
            cur.execute(  #EXCEPT — served from AMS but not FRA
                "SELECT destination FROM demo_routes_ams"
                " EXCEPT"
                " SELECT destination FROM demo_routes_fra"
                " ORDER BY destination"
            )
            only_ams = [r[0] for r in cur.fetchall()]
            cur.execute(  #EXCEPT reversed — served from FRA but not AMS
                "SELECT destination FROM demo_routes_fra"
                " EXCEPT"
                " SELECT destination FROM demo_routes_ams"
                " ORDER BY destination"
            )
            only_fra = [r[0] for r in cur.fetchall()]
        print(f"[after.py] INTERSECT  (both {SOURCE_A} and {SOURCE_B}):", both)
        print(f"[after.py] EXCEPT     ({SOURCE_A} only):", only_ams)
        print(f"[after.py] EXCEPT     ({SOURCE_B} only):", only_fra)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
