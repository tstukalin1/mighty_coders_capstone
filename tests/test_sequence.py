import os

import pymysql
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def conn():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=False,
    )
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture
def seq(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE OR REPLACE SEQUENCE test_seq START WITH 1 INCREMENT BY 1")
    conn.commit()
    yield "test_seq"
    with conn.cursor() as cur:
        cur.execute("DROP SEQUENCE IF EXISTS test_seq")
    conn.commit()


class TestSequenceBasics:
    def test_first_value_matches_start(self, conn, seq):
        with conn.cursor() as cur:
            cur.execute("SELECT NEXT VALUE FOR test_seq")
            row = cur.fetchone()
        assert row[0] == 1

    def test_value_increments(self, conn, seq):
        with conn.cursor() as cur:
            cur.execute("SELECT NEXT VALUE FOR test_seq")
            first = cur.fetchone()[0]
            cur.execute("SELECT NEXT VALUE FOR test_seq")
            second = cur.fetchone()[0]
        assert second == first + 1

    def test_value_is_integer(self, conn, seq):
        with conn.cursor() as cur:
            cur.execute("SELECT NEXT VALUE FOR test_seq")
            row = cur.fetchone()
        assert isinstance(row[0], int)


class TestSequenceSharedAcrossTables:
    def test_sequence_produces_unique_ids_across_two_tables(self, conn, seq):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE seq_test_a (id INT PRIMARY KEY, label VARCHAR(50))")
            cur.execute("CREATE OR REPLACE TABLE seq_test_b (id INT PRIMARY KEY, label VARCHAR(50))")

            cur.execute(
                "INSERT INTO seq_test_a (id, label) VALUES (NEXT VALUE FOR test_seq, %s)",
                ("A row",),
            )
            cur.execute(
                "INSERT INTO seq_test_b (id, label) VALUES (NEXT VALUE FOR test_seq, %s)",
                ("B row",),
            )

            cur.execute("SELECT id FROM seq_test_a")
            id_a = cur.fetchone()[0]
            cur.execute("SELECT id FROM seq_test_b")
            id_b = cur.fetchone()[0]

        assert id_b == id_a + 1  # consecutive, globally unique across both tables

    def test_auto_increment_does_not_share_across_tables(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "CREATE OR REPLACE TABLE auto_test_a (id INT AUTO_INCREMENT PRIMARY KEY, label VARCHAR(50))"
            )
            cur.execute(
                "CREATE OR REPLACE TABLE auto_test_b (id INT AUTO_INCREMENT PRIMARY KEY, label VARCHAR(50))"
            )

            cur.execute("INSERT INTO auto_test_a (label) VALUES (%s)", ("A row",))
            cur.execute("INSERT INTO auto_test_b (label) VALUES (%s)", ("B row",))

            cur.execute("SELECT id FROM auto_test_a")
            id_a = cur.fetchone()[0]
            cur.execute("SELECT id FROM auto_test_b")
            id_b = cur.fetchone()[0]

        # Each table starts its own counter at 1 independently --
        # this is the behavior CREATE SEQUENCE avoids.
        assert id_a == 1
        assert id_b == 1


class TestSequenceCycling:
    def test_cycle_wraps_at_maxvalue(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE OR REPLACE SEQUENCE cycle_test_seq
                START WITH 1
                INCREMENT BY 2
                MINVALUE 1
                MAXVALUE 5
                CYCLE
                """
            )
            values = []
            for _ in range(4):
                cur.execute("SELECT NEXT VALUE FOR cycle_test_seq")
                values.append(cur.fetchone()[0])
            cur.execute("DROP SEQUENCE cycle_test_seq")

        assert values == [1, 3, 5, 1]

    def test_nocycle_raises_when_exhausted(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE OR REPLACE SEQUENCE nocycle_test_seq
                START WITH 1
                INCREMENT BY 1
                MAXVALUE 2
                NOCYCLE
                """
            )
            cur.execute("SELECT NEXT VALUE FOR nocycle_test_seq")
            cur.execute("SELECT NEXT VALUE FOR nocycle_test_seq")

            with pytest.raises(pymysql.err.OperationalError):
                cur.execute("SELECT NEXT VALUE FOR nocycle_test_seq")

            cur.execute("DROP SEQUENCE IF EXISTS nocycle_test_seq")

class TestSequenceLimits:
    """What a sequence does NOT give you, and the tools to manage it."""

    @pytest.fixture
    def invoices(self, conn, seq):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE test_invoices (no INT PRIMARY KEY, item VARCHAR(50))")
        conn.commit()
        yield "test_invoices"
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS test_invoices")
        conn.commit()

    def test_rollback_does_not_return_the_value(self, conn, invoices):
        # A sequence is not transactional: a rolled-back INSERT leaves a gap.
        with conn.cursor() as cur:
            cur.execute("INSERT INTO test_invoices VALUES (NEXT VALUE FOR test_seq, 'cancelled')")
            conn.rollback()
            cur.execute("INSERT INTO test_invoices VALUES (NEXT VALUE FOR test_seq, 'kept')")
            conn.commit()
            cur.execute("SELECT no, item FROM test_invoices")
            rows = cur.fetchall()
        assert rows == ((2, "kept"),)   # number 1 is gone for good

    def test_setval_moves_the_counter(self, conn, seq):
        # After importing old data, SETVAL makes the sequence continue after it.
        with conn.cursor() as cur:
            cur.execute("SELECT SETVAL(test_seq, 500)")
            cur.execute("SELECT NEXT VALUE FOR test_seq")
            assert cur.fetchone()[0] == 501

    def test_previous_value_is_per_session(self, conn, seq):
        from db import get_connection
        with conn.cursor() as cur:
            cur.execute("SELECT NEXT VALUE FOR test_seq")
            cur.execute("SELECT PREVIOUS VALUE FOR test_seq")
            assert cur.fetchone()[0] == 1
        other = get_connection()
        try:
            with other.cursor() as cur:
                cur.execute("SELECT PREVIOUS VALUE FOR test_seq")
                assert cur.fetchone()[0] is None   # the other session has not used it
        finally:
            other.close()

    def test_default_next_value_fills_the_column(self, conn, seq):
        with conn.cursor() as cur:
            cur.execute("CREATE OR REPLACE TABLE test_seq_default"
                        " (no INT PRIMARY KEY DEFAULT (NEXT VALUE FOR test_seq), item VARCHAR(50))")
            cur.execute("INSERT INTO test_seq_default (item) VALUES ('a'), ('b')")
            cur.execute("SELECT no FROM test_seq_default ORDER BY no")
            numbers = [row[0] for row in cur.fetchall()]
            cur.execute("DROP TABLE test_seq_default")
        assert numbers == [1, 2]
