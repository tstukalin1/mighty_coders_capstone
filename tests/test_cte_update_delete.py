import pymysql
import pytest


@pytest.fixture(autouse=True)
def setup_table(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_orders")
        cur.execute(
            "CREATE TABLE test_orders ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  customer VARCHAR(100) NOT NULL,"
            "  amount DECIMAL(10,2) NOT NULL,"
            "  status VARCHAR(20) NOT NULL DEFAULT 'pending'"
            ")"
        )
        rows = [
            ("alice", 250.00),
            ("bob",   50.00),
            ("carol", 1500.00),
            ("dave",  30.00),
            ("eve",   900.00),
        ]
        for customer, amount in rows:
            cur.execute(
                "INSERT INTO test_orders (customer, amount) VALUES (%s, %s)",
                (customer, amount),
            )
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_orders")
    conn.commit()


class TestCTEUpdate:
    def test_cte_update_approves_high_value_orders(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE test_orders"
                " JOIN (SELECT id FROM test_orders WHERE amount >= 100.00) AS high_value"
                " ON test_orders.id = high_value.id"
                " SET test_orders.status = 'approved'"
            )
            cur.execute(
                "SELECT customer FROM test_orders WHERE status = 'approved' ORDER BY customer"
            )
            approved = [r[0] for r in cur.fetchall()]
        assert approved == ["alice", "carol", "eve"]

    def test_cte_update_leaves_small_orders_pending(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE test_orders"
                " JOIN (SELECT id FROM test_orders WHERE amount >= 100.00) AS high_value"
                " ON test_orders.id = high_value.id"
                " SET test_orders.status = 'approved'"
            )
            cur.execute(
                "SELECT customer FROM test_orders WHERE status = 'pending' ORDER BY customer"
            )
            pending = [r[0] for r in cur.fetchall()]
        assert pending == ["bob", "dave"]


class TestCTEDelete:
    def test_cte_delete_removes_small_orders(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "DELETE test_orders FROM test_orders"
                " JOIN (SELECT id FROM test_orders WHERE amount < 100.00) AS small_orders"
                " ON test_orders.id = small_orders.id"
            )
            cur.execute("SELECT customer FROM test_orders ORDER BY customer")
            remaining = [r[0] for r in cur.fetchall()]
        assert remaining == ["alice", "carol", "eve"]

    def test_cte_delete_count(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "DELETE test_orders FROM test_orders"
                " JOIN (SELECT id FROM test_orders WHERE amount < 100.00) AS small_orders"
                " ON test_orders.id = small_orders.id"
            )
            cur.execute("SELECT COUNT(*) FROM test_orders")
            count = cur.fetchone()[0]
        assert count == 3


CTE_DML_FROM = (12, 3, 1)


class TestWithClause:
    """WITH ... UPDATE / DELETE (feature 13), added in MariaDB 12.3.1 (MDEV-37220).
    On an older server the tests check that it is refused with error 1064."""

    def run_then_read(self, conn, version, sql, read_sql):
        """Run the WITH statement, then return the rows of read_sql; on a server before
        12.3.1 check that the statement fails with 1064 and return None."""
        with conn.cursor() as cur:
            if version < CTE_DML_FROM:
                with pytest.raises(pymysql.MySQLError) as exc:
                    cur.execute(sql)
                assert exc.value.args[0] == 1064
                return None
            cur.execute(sql)
            cur.execute(read_sql)
            return [r[0] for r in cur.fetchall()]

    def test_with_update(self, conn, version):
        approved = self.run_then_read(
            conn, version,
            "WITH high_value AS (SELECT id FROM test_orders WHERE amount >= 100.00)"
            " UPDATE test_orders SET status = 'approved' WHERE id IN (SELECT id FROM high_value)",
            "SELECT customer FROM test_orders WHERE status = 'approved' ORDER BY customer",
        )
        if approved is not None:
            assert approved == ["alice", "carol", "eve"]

    def test_with_delete(self, conn, version):
        remaining = self.run_then_read(
            conn, version,
            "WITH small_orders AS (SELECT id FROM test_orders WHERE amount < 100.00)"
            " DELETE FROM test_orders WHERE id IN (SELECT id FROM small_orders)",
            "SELECT customer FROM test_orders ORDER BY customer",
        )
        if remaining is not None:
            assert remaining == ["alice", "carol", "eve"]
