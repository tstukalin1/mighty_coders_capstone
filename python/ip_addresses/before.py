"""
before.py -- IP addresses stored as VARCHAR (the old way)

Same data as sql/init/01_inet.sql, but in a plain text column:
  * invalid addresses are accepted without complaint
  * ORDER BY sorts as text, not as numbers
  * "> '150.0.0.0'" compares text, so the answer is wrong

Run after the database is up:  python python/ip_addresses/before.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

IPV4_ADDRESSES = ["192.168.1.10", "122.168.133.103", "9.9.9.9"]
IPV6_ADDRESS = "2001:db8:85a3::8a2e:370:7334"
INVALID_ADDRESS = "999.999.999.999"


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_ip_old")
            cur.execute(
                "CREATE TABLE demo_ip_old ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  ip_address VARCHAR(45) NOT NULL)"
            )
            for ip in IPV4_ADDRESSES + [IPV6_ADDRESS]:
                cur.execute("INSERT INTO demo_ip_old (ip_address) VALUES (%s)", (ip,))

            print("[before.py] IP addresses stored as VARCHAR(45)")
            print()

            # 1. validation: nothing stops an invalid address
            cur.execute(
                "INSERT INTO demo_ip_old (ip_address) VALUES (%s)", (INVALID_ADDRESS,)
            )
            print(f"Invalid address '{INVALID_ADDRESS}' was accepted without any error.")
            print()

            # 2. sorting: text order, not numeric order
            cur.execute(
                "SELECT ip_address FROM demo_ip_old"
                " WHERE ip_address LIKE '%%.%%.%%.%%' AND ip_address NOT LIKE '999.%%'"
                " ORDER BY ip_address"
            )
            print("Sorted as text (wrong, 9.9.9.9 should come first):")
            for (ip,) in cur.fetchall():
                print(f"  {ip}")
            print()

            # 3. comparison: text comparison gives the wrong answer
            cur.execute(
                "SELECT ip_address FROM demo_ip_old"
                " WHERE ip_address > '150.0.0.0'"
                " AND ip_address LIKE '%%.%%.%%.%%' AND ip_address NOT LIKE '999.%%'"
                " ORDER BY ip_address"
            )
            print("WHERE ip_address > '150.0.0.0' (text comparison):")
            for (ip,) in cur.fetchall():
                print(f"  {ip}")
            print("  -> 9.9.9.9 is included, but numerically it is below 150.0.0.0.")

            cur.execute("DROP TABLE IF EXISTS demo_ip_old")
    finally:
        conn.close()


if __name__ == "__main__":
    main()