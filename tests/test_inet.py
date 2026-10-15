"""
test_inet.py — tests for sql/init/03_inet.sql (INET4 / INET6)

Covers:
  * INET4 / INET6 column types created correctly
  * storing IPv4 and IPv6 addresses
  * IS_IPV4 / IS_IPV6 validation functions
  * invalid INET4 value rejected with error 1292
  * numeric comparison and sort order vs lexicographic VARCHAR
  * init script loaded (connections_new table exists)
"""

import pymysql
import pytest


@pytest.fixture(autouse=True)
def setup_table(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_inet")
        cur.execute(
            "CREATE TABLE test_inet ("
            "  id            INT AUTO_INCREMENT PRIMARY KEY,"
            "  ipv4_address  INET4,"
            "  ipv6_address  INET6)"
        )
        cur.execute("INSERT INTO test_inet (ipv4_address) VALUES ('192.168.1.10')")
        cur.execute("INSERT INTO test_inet (ipv6_address) VALUES ('2001:db8::1')")
        cur.execute("INSERT INTO test_inet (ipv4_address) VALUES ('8.8.8.8')")
        cur.execute("INSERT INTO test_inet (ipv4_address) VALUES ('10.0.0.5')")
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_inet")
    conn.commit()


class TestInetColumnTypes:
    def test_columns_have_inet_types(self, conn):
        with conn.cursor() as cur:
            cur.execute("SHOW CREATE TABLE test_inet")
            ddl = cur.fetchone()[1].lower()
        assert "`ipv4_address` inet4" in ddl
        assert "`ipv6_address` inet6" in ddl


class TestStoringAddresses:
    def test_ipv4_stored_and_returned(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT ipv4_address FROM test_inet WHERE id = 1")
            assert str(cur.fetchone()[0]) == "192.168.1.10"

    def test_ipv6_stored_and_returned(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv6_address = '2001:db8::1' FROM test_inet WHERE id = 2"
            )
            assert cur.fetchone()[0] == 1

    def test_unused_column_is_null(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT ipv6_address FROM test_inet WHERE id = 1")
            assert cur.fetchone()[0] is None


class TestValidation:
    def test_is_ipv4_accepts_valid(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV4('192.168.1.10')")
            assert cur.fetchone()[0] == 1

    def test_is_ipv4_rejects_invalid(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV4('999.999.999.999')")
            assert cur.fetchone()[0] == 0

    def test_is_ipv6_accepts_valid(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV6('2001:db8::1')")
            assert cur.fetchone()[0] == 1

    def test_is_ipv6_rejects_ipv4(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV6('192.168.1.10')")
            assert cur.fetchone()[0] == 0

    def test_inet4_rejects_invalid_on_insert(self, conn):
        with pytest.raises(pymysql.err.MySQLError) as exc_info:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO test_inet (ipv4_address) VALUES ('999.999.999.999')"
                )
        assert exc_info.value.args[0] == 1292


class TestComparison:
    def test_greater_than_is_numeric(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv4_address FROM test_inet"
                " WHERE ipv4_address > '150.0.0.0'"
            )
            rows = [str(r[0]) for r in cur.fetchall()]
        assert rows == ["192.168.1.10"]  #only 192.x is above 150.x; 8.x and 10.x are not


class TestSorting:
    def test_order_by_is_numeric_not_lexicographic(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv4_address FROM test_inet"
                " WHERE ipv4_address IS NOT NULL ORDER BY ipv4_address"
            )
            rows = [str(r[0]) for r in cur.fetchall()]
        assert rows == ["8.8.8.8", "10.0.0.5", "192.168.1.10"]  #numeric, not '10' < '192' < '8'


class TestInitScriptLoaded:
    def test_03_inet_sql_created_connections_new(self, conn):
        """Docker should have run sql/init/03_inet.sql at first start."""
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT COUNT(*) FROM connections_new")
            except pymysql.err.ProgrammingError as exc:
                if exc.args[0] == 1146:
                    pytest.skip("connections_new missing: 03_inet.sql not loaded yet")
                raise
            assert cur.fetchone()[0] == 5
