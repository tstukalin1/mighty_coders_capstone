"""
after.py -- IP addresses stored as INET4 / INET6 (MariaDB 10.5+)

Same data as before.py, now in native IP address columns:
  * invalid addresses are rejected at INSERT time (error 1292)
  * IS_IPV4() / IS_IPV6() validate values
  * ORDER BY sorts numerically
  * "> '150.0.0.0'" compares numerically

Run after the database is up:  python python/ip_addresses/after.py
"""

import os
import sys

import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection

IPV4_ADDRESSES = ["192.168.1.10", "122.168.133.103", "9.9.9.9"]
IPV6_ADDRESS = "2001:db8:85a3::8a2e:370:7334"
INVALID_ADDRESS = "999.999.999.999"


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS demo_ip_new")
            cur.execute(
                "CREATE TABLE demo_ip_new ("
                "  id INT AUTO_INCREMENT PRIMARY KEY,"
                "  ipv4_address INET4,"
                "  ipv6_address INET6)"
            )
            for ip in IPV4_ADDRESSES:
                cur.execute(
                    "INSERT INTO demo_ip_new (ipv4_address) VALUES (%s)", (ip,)
                )
            cur.execute(
                "INSERT INTO demo_ip_new (ipv6_address) VALUES (%s)", (IPV6_ADDRESS,)
            )

            print("[after.py] IP addresses stored as INET4 / INET6")
            print()

            # 1. validation: the engine rejects invalid addresses
            try:
                cur.execute(
                    "INSERT INTO demo_ip_new (ipv4_address) VALUES (%s)",
                    (INVALID_ADDRESS,),
                )
                print(f"Invalid address '{INVALID_ADDRESS}' was accepted (unexpected).")
            except pymysql.err.MySQLError as exc:
                print(f"Invalid address '{INVALID_ADDRESS}' rejected: {exc.args}")
            cur.execute("SELECT IS_IPV4(%s), IS_IPV6(%s)", (INVALID_ADDRESS, IPV6_ADDRESS))
            is_v4, is_v6 = cur.fetchone()
            print(f"IS_IPV4('{INVALID_ADDRESS}') = {is_v4}, IS_IPV6('{IPV6_ADDRESS}') = {is_v6}")
            print()

            # 2. sorting: numeric order
            cur.execute(
                "SELECT ipv4_address FROM demo_ip_new"
                " WHERE ipv4_address IS NOT NULL ORDER BY ipv4_address"
            )
            print("Sorted numerically (correct, 9.9.9.9 comes first):")
            for (ip,) in cur.fetchall():
                print(f"  {ip}")
            print()

            # 3. comparison: numeric comparison
            cur.execute(
                "SELECT ipv4_address FROM demo_ip_new"
                " WHERE ipv4_address > '150.0.0.0' ORDER BY ipv4_address"
            )
            print("WHERE ipv4_address > '150.0.0.0' (numeric comparison):")
            for (ip,) in cur.fetchall():
                print(f"  {ip}")
            print("  -> only 192.168.1.10, as expected.")

            cur.execute("DROP TABLE IF EXISTS demo_ip_new")
    finally:
        conn.close()


if __name__ == "__main__":
    main()