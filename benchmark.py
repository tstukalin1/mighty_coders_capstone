"""
benchmark.py -- RETURNING vs. the old way (INSERT + SELECT), measured properly

Question: how much does INSERT ... RETURNING save over INSERT followed by a
separate SELECT to read the row back?

Method (so the numbers can be reproduced on another machine):
  * Table: the real OpenFlights `airlines` table (6,162 rows, see sql/init/12).
  * Each ROUNDS round does N inserts with the old way and N inserts with
    RETURNING. The order of the two approaches alternates every round, so
    neither one always runs first (cache warm-up affects both equally).
  * Rows from earlier rounds are deleted between rounds; ids never collide.
  * Same connection, same server, same data. Client and server run on one
    machine, so network latency is ~0 and the saving is a LOWER bound: on a
    real network each saved round trip costs more.
  * Reported: mean and standard deviation of per-operation time over ROUNDS
    rounds, plus the number of statements sent per operation.

Run after the database is up:  python benchmark.py
"""

import statistics
import time

from db import get_connection

N = 200       # operations per approach per round
ROUNDS = 5    # repeated rounds; variance is reported, not a single number


def old_way(cur, airline_id):
    cur.execute(
        "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)",
        (airline_id, f"OldBenchAirline{airline_id}", "BenchLand"),
    )
    cur.execute("SELECT * FROM airlines WHERE id = %s", (airline_id,))
    cur.fetchone()


def new_way(cur, airline_id):
    cur.execute(
        "INSERT INTO airlines (id, name, country) VALUES (%s, %s, %s)"
        " RETURNING id, name, country",
        (airline_id, f"NewBenchAirline{airline_id}", "BenchLand"),
    )
    cur.fetchone()


def run_round(fn, cur, first_id):
    start = time.perf_counter()
    for i in range(N):
        fn(cur, first_id + i)
    return (time.perf_counter() - start) / N * 1000  # ms per operation


def cleanup(cur):
    cur.execute("DELETE FROM airlines WHERE id >= 500000")


def summary(label, values, statements):
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    print(f"| {label:<28} | {statements} | {mean:7.3f} ms | {sd:6.3f} ms |")
    return mean


def main():
    conn = get_connection()
    old_times, new_times = [], []
    try:
        with conn.cursor() as cur:
            cleanup(cur)
            for r in range(ROUNDS):
                order = [("old", old_way, 500000), ("new", new_way, 600000)]
                if r % 2:
                    order.reverse()
                for name, fn, base in order:
                    t = run_round(fn, cur, base + r * 1000)
                    (old_times if name == "old" else new_times).append(t)
                cleanup(cur)

            print(f"\n{N} operations per approach, {ROUNDS} rounds, "
                  "order alternated each round\n")
            print("| Approach                     | Stmts/op | Mean/op   | Std dev  |")
            print("|------------------------------|----------|-----------|----------|")
            old_mean = summary("INSERT + SELECT (old way)", old_times, 2)
            new_mean = summary("INSERT ... RETURNING", new_times, 1)
            print(f"\nRETURNING is {(old_mean - new_mean) / old_mean * 100:.1f}% faster "
                  "per operation and sends half as many statements.")

            cur.execute("SELECT COUNT(*) FROM airlines")
            print(f"Airlines table back to: {cur.fetchone()[0]} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
