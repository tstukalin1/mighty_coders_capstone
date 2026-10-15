"""
benchmark.py — RETURNING vs. old-way (INSERT + SELECT) timing comparison

Run against the real OpenFlights 'airlines' dataset (6,162+ rows)
"""

import time
from db import get_connection

N = 200  # number of insert operations per approach


def old_way(cur, i):
    airline_id = 500000 + i
    cur.execute(
        "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)",
        (airline_id, f"OldBenchAirline{i}", "BenchLand"),
    )
    cur.execute("SELECT * FROM airlines WHERE id = %s", (airline_id,))
    cur.fetchone()


def new_way(cur, i):
    airline_id = 600000 + i
    cur.execute(
        """
        INSERT INTO airlines (id, name, country)
        VALUES (%s, %s, %s)
        RETURNING id, name, country
        """,
        (airline_id, f"NewBenchAirline{i}", "BenchLand"),
    )
    cur.fetchone()


def run_benchmark(fn, cur, label):
    start = time.perf_counter()
    for i in range(N):
        fn(cur, i)
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.4f}s total, {elapsed / N * 1000:.3f}ms per operation")
    return elapsed


def cleanup(cur):
    cur.execute("DELETE FROM airlines WHERE id >= 500000")


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            old_time = run_benchmark(old_way, cur, "OLD (INSERT + SELECT)")
            new_time = run_benchmark(new_way, cur, "NEW (INSERT ... RETURNING)")

            improvement = (old_time - new_time) / old_time * 100
            print(f"\nRETURNING is {improvement:.1f}% faster over {N} operations")

            cleanup(cur)
            cur.execute("SELECT COUNT(*) FROM airlines")
            print(f"Airlines table back to: {cur.fetchone()[0]} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()