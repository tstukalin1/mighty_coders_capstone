"""
after.py — attempting CREATE GLOBAL TEMPORARY TABLE (MariaDB)

GLOBAL TEMPORARY TABLE is a SQL-standard feature (Oracle, PostgreSQL,
and others) where the table's DEFINITION is shared across all
sessions, while each session's DATA stays private. This would mean a
second session could simply use a scratch table another session
already defined, without recreating it.

MariaDB does not implement this syntax in any released version,
including the 11.4 image this project runs in Docker. This is
tracked in MariaDB's own issue tracker as MDEV-35915, targeting a
future 13.3 LTS release that has not shipped.

This script attempts the feature and captures the real failure,
rather than simulating a result that MariaDB cannot actually produce.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    CREATE GLOBAL TEMPORARY TABLE scratch_global (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        note VARCHAR(100)
                    ) ON COMMIT PRESERVE ROWS
                    """
                )
                print("[after.py] CREATE GLOBAL TEMPORARY TABLE succeeded (unexpected)")
            except Exception as e:
                print("[after.py] CREATE GLOBAL TEMPORARY TABLE failed, as expected:")
                print(f"  {e}")
                print()
                print("MariaDB does not implement this syntax yet (MDEV-35915).")
                print("See python/global_temp/before.py for the working alternative")
                print("(a plain TEMPORARY TABLE, which each session must create itself).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()