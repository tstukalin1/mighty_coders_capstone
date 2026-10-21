"""
before.py — IP addresses stored as VARCHAR

Sorting is lexicographic, not numeric: '8.8.8.8' sorts after '192.168.1.10'
because '8' > '1' as a string. No built-in validation either.
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
            cur.execute("DROP TABLE IF EXISTS demo_connections_old")
            cur.execute(
                "CREATE TABLE demo_connections_old (id INT AUTO_INCREMENT PRIMARY KEY, client_ip VARCHAR(45) NOT NULL)"
            )
            for ip in IPS:
                cur.execute(
                    "INSERT INTO demo_connections_old (client_ip) VALUES (%s)", (ip,)
                )
            cur.execute(
                "SELECT client_ip FROM demo_connections_old ORDER BY client_ip"
            )
            rows = cur.fetchall()
        print("[before.py] VARCHAR sort order (lexicographic — wrong):")
        for r in rows:
            print(f"  {r[0]}")
        print()
        print("Expected numeric order: 8.8.4.4, 8.8.8.8, 10.0.0.5, 172.16.0.1, 192.168.1.10")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
