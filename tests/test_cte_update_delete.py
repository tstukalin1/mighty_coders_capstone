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
