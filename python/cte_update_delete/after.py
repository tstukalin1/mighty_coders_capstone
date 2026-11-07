"""
after.py — UPDATE/DELETE with a derived-table JOIN (MariaDB)

MariaDB 11.4 does not support WITH ... UPDATE / WITH ... DELETE (error 1064).
The working way is UPDATE ... JOIN (SELECT ...) AS name: the derived table
names the filtering logic, so no double nesting is needed.
Source data: OpenFlights airports dataset (data/airports.csv, loaded into the airports table).

"""

import sys
import os

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

LIMIT = 50  #airports to load


def fetch_airports():
    #read (iata, name, country) from the airports table, in file order;
    #iata is '' when the airport has no code (NULL in the table)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(iata, ''), name, country FROM airports ORDER BY id LIMIT %s",
                (LIMIT,),
            )
            return list(cur.fetchall())
    finally:
        conn.close()

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
            try:  #the CTE form: needs MariaDB 12.3.1 (MDEV-37220)
                cur.execute(
                    "WITH registered AS (SELECT id FROM demo_airports WHERE iata != '')"
                    " UPDATE demo_airports SET status = 'active'"
                    " WHERE id IN (SELECT id FROM registered)"
                )
                print("[after.py] WITH ... UPDATE worked on this server")
            except pymysql.MySQLError as e:
                print(f"[after.py] WITH ... UPDATE failed: error {e.args[0]} (needs MariaDB 12.3.1)")
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
