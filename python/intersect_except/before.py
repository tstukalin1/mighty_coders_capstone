"""
before.py — set operations via JOIN and subqueries

Finding common/unique destinations without INTERSECT/EXCEPT requires
JOIN constructs that obscure the intent.
Source data: OpenFlights routes dataset (routes.dat).
"""

import csv
import io
import sys
import os
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"
SOURCE_A = "AMS"  #Amsterdam Schiphol
SOURCE_B = "FRA"  #Frankfurt Airport
LIMIT    = 50     #destinations per source airport


def fetch_routes():
    #download routes.dat once, collect destinations for both airports
    result = {SOURCE_A: [], SOURCE_B: []}
    seen   = {SOURCE_A: set(), SOURCE_B: set()}
    with urllib.request.urlopen(ROUTES_URL) as response:
        for row in csv.reader(io.TextIOWrapper(response, encoding="utf-8")):
            src, dst = row[2], row[4]
            if src in result and dst != r"\N" and dst not in seen[src] and len(result[src]) < LIMIT:
                seen[src].add(dst)
                result[src].append(dst)
    return result[SOURCE_A], result[SOURCE_B]


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
            cur.execute(  #intersection via INNER JOIN
                "SELECT a.destination FROM demo_routes_ams a"
                " INNER JOIN demo_routes_fra f ON a.destination = f.destination"
                " ORDER BY a.destination"
            )
            both = [r[0] for r in cur.fetchall()]
            cur.execute(  #difference via LEFT JOIN + IS NULL
                "SELECT a.destination FROM demo_routes_ams a"
                " LEFT JOIN demo_routes_fra f ON a.destination = f.destination"
                " WHERE f.destination IS NULL ORDER BY a.destination"
            )
            only_ams = [r[0] for r in cur.fetchall()]
        print(f"[before.py] Reachable from both {SOURCE_A} and {SOURCE_B} (INNER JOIN):", both)
        print(f"[before.py] Only from {SOURCE_A} (LEFT JOIN+NULL):", only_ams)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
