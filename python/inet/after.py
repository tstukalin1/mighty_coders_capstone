"""
after.py — IP addresses stored as INET4 (MariaDB 10.5+)

4 bytes instead of up to 45. Sorts numerically. Invalid addresses
are rejected by the engine at INSERT time.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

IPS = ["192.168.1.10", "10.0.0.5", "172.16.0.1", "8.8.8.8", "8.8.4.4"]


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_connections_new")
            cur.execute(
                "CREATE TABLE demo_connections_new (id INT AUTO_INCREMENT PRIMARY KEY, client_ip INET4 NOT NULL)"
            )
            for ip in IPS:
                cur.execute(
                    "INSERT INTO demo_connections_new (client_ip) VALUES (%s)", (ip,)
                )
            cur.execute(
                "SELECT client_ip FROM demo_connections_new ORDER BY client_ip"
            )
            rows = cur.fetchall()
        print("[after.py] INET4 sort order (numeric — correct):")
        for r in rows:
            print(f"  {r[0]}")
        print()
        print("Bytes per row: INET4=4 vs VARCHAR(45)=up to 46 (length prefix + data)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
