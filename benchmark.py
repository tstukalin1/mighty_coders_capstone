"""
benchmark.py -- RETURNING vs. the old way (INSERT + SELECT), measured properly

Two measurements:
  1. Statements and time saved: INSERT ... RETURNING vs INSERT + SELECT.
  2. Bytes saved: the same 100,000 values stored as VARCHAR(45) vs INET4 and as
     CHAR(36) vs UUID, each with a primary key and an index on the value
     (table size = data + index, from information_schema after ANALYZE TABLE).

Question 1: how much does INSERT ... RETURNING save over INSERT followed by a
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


STORAGE_ROWS = 100_000

# (table, CREATE, ANALYZE, DROP) written out as literal statements
STORAGE_TABLES = [
    ("bench_ip_text",
     "CREATE TABLE bench_ip_text (id INT AUTO_INCREMENT PRIMARY KEY,"
     " ip VARCHAR(45), KEY idx_value (ip))",
     "ANALYZE TABLE bench_ip_text", "DROP TABLE IF EXISTS bench_ip_text"),
    ("bench_ip_inet",
     "CREATE TABLE bench_ip_inet (id INT AUTO_INCREMENT PRIMARY KEY,"
     " ip INET4, KEY idx_value (ip))",
     "ANALYZE TABLE bench_ip_inet", "DROP TABLE IF EXISTS bench_ip_inet"),
    ("bench_uuid_text",
     "CREATE TABLE bench_uuid_text (id INT AUTO_INCREMENT PRIMARY KEY,"
     " u CHAR(36), KEY idx_value (u))",
     "ANALYZE TABLE bench_uuid_text", "DROP TABLE IF EXISTS bench_uuid_text"),
    ("bench_uuid_native",
     "CREATE TABLE bench_uuid_native (id INT AUTO_INCREMENT PRIMARY KEY,"
     " u UUID, KEY idx_value (u))",
     "ANALYZE TABLE bench_uuid_native", "DROP TABLE IF EXISTS bench_uuid_native"),
]


def storage_benchmark(cur):
    for _, create, _, drop in STORAGE_TABLES:
        cur.execute(drop)
        cur.execute(create)
    cur.execute(
        "INSERT INTO bench_ip_text (ip) SELECT CONCAT('10.', (seq DIV 65536) MOD 256,"
        " '.', (seq DIV 256) MOD 256, '.', seq MOD 256) FROM seq_1_to_100000")
    cur.execute("INSERT INTO bench_ip_inet (ip) SELECT ip FROM bench_ip_text")
    cur.execute("INSERT INTO bench_uuid_text (u) SELECT UUID() FROM seq_1_to_100000")
    cur.execute("INSERT INTO bench_uuid_native (u) SELECT u FROM bench_uuid_text")

    sizes = {}
    for name, _, analyze, drop in STORAGE_TABLES:
        cur.execute(analyze)
        cur.fetchall()
        cur.execute("SELECT data_length + index_length FROM information_schema.tables"
                    " WHERE table_schema = DATABASE() AND table_name = %s", (name,))
        sizes[name] = cur.fetchone()[0]
        cur.execute(drop)
    return sizes


def print_storage(sizes):
    print(f"\nStorage for {STORAGE_ROWS:,} rows (id + value + index on value)\n")
    print("| Stored as                 | Table size | Saved vs text |")
    print("|---------------------------|------------|---------------|")
    for text, native, label in (("bench_ip_text", "bench_ip_inet", "INET4"),
                                ("bench_uuid_text", "bench_uuid_native", "UUID")):
        t, n = sizes[text], sizes[native]
        text_label = "VARCHAR(45)" if "ip" in text else "CHAR(36)"
        print(f"| {text_label:<25} | {t / 1024 / 1024:7.2f} MB | -             |")
        print(f"| {label:<25} | {n / 1024 / 1024:7.2f} MB | {(t - n) / t * 100:5.1f}%        |")


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

            print_storage(storage_benchmark(cur))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
