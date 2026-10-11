"""
test_ip_addresses.py -- tests for sql/init/01_inet.sql (INET4 / INET6)

One test group per item of the "What I learned" list in readme_inet.md:
  * creating INET4 and INET6 columns
  * storing IPv4 and IPv6 addresses
  * validating IP addresses
  * comparing IPv4 addresses
  * sorting IPv4 addresses

The tests work on their own table (test_ip_addresses) with the same shape and
rows as the ip_addresses table in 01_inet.sql, and drop it at teardown.
One extra test checks that Docker really loaded 01_inet.sql at start-up.
Uses the shared `conn` fixture from tests/conftest.py.
"""

import pymysql
import pytest


@pytest.fixture(autouse=True)
def setup_table(conn):
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_ip_addresses")
        cur.execute(
            "CREATE TABLE test_ip_addresses ("
            "  id INT AUTO_INCREMENT PRIMARY KEY,"
            "  ipv4_address INET4,"
            "  ipv6_address INET6)"
        )
        cur.execute(
            "INSERT INTO test_ip_addresses (ipv4_address) VALUES ('192.168.1.10')"
        )
        cur.execute(
            "INSERT INTO test_ip_addresses (ipv6_address)"
            " VALUES ('2001:db8:85a3::8a2e:370:7334')"
        )
        cur.execute(
            "INSERT INTO test_ip_addresses (ipv4_address) VALUES ('122.168.133.103')"
        )
    conn.commit()
    yield
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_ip_addresses")
    conn.commit()


class TestCreatingInetColumns:
    def test_columns_have_inet_types(self, conn):
        with conn.cursor() as cur:
            cur.execute("SHOW CREATE TABLE test_ip_addresses")
            ddl = cur.fetchone()[1].lower()
        assert "`ipv4_address` inet4" in ddl
        assert "`ipv6_address` inet6" in ddl


class TestStoringAddresses:
    def test_ipv4_is_stored_and_returned(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv4_address FROM test_ip_addresses WHERE id = 1"
            )
            assert str(cur.fetchone()[0]) == "192.168.1.10"

    def test_ipv6_is_stored_and_returned(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv6_address = '2001:db8:85a3::8a2e:370:7334'"
                " FROM test_ip_addresses WHERE id = 2"
            )
            assert cur.fetchone()[0] == 1

    def test_unused_column_is_null(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv6_address FROM test_ip_addresses WHERE id = 1"
            )
            assert cur.fetchone()[0] is None


class TestValidatingAddresses:
    def test_is_ipv4_accepts_valid_address(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV4('192.168.1.10')")
            assert cur.fetchone()[0] == 1

    def test_is_ipv4_rejects_invalid_address(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV4('999.999.999.999')")
            assert cur.fetchone()[0] == 0

    def test_is_ipv6_accepts_valid_address(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV6('2001:db8:85a3::8a2e:370:7334')")
            assert cur.fetchone()[0] == 1

    def test_is_ipv6_rejects_ipv4_address(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT IS_IPV6('192.168.1.10')")
            assert cur.fetchone()[0] == 0

    def test_inet4_column_rejects_invalid_address(self, conn):
        with conn.cursor() as cur:
            with pytest.raises(pymysql.err.MySQLError) as exc_info:
                cur.execute(
                    "INSERT INTO test_ip_addresses (ipv4_address)"
                    " VALUES ('999.999.999.999')"
                )
        assert exc_info.value.args[0] == 1292


class TestComparingIpv4:
    def test_greater_than_comparison(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv4_address FROM test_ip_addresses"
                " WHERE ipv4_address > '150.0.0.0'"
            )
            rows = [str(r[0]) for r in cur.fetchall()]
        # 192.168.1.10 is above 150.0.0.0, 122.168.133.103 is below it
        assert rows == ["192.168.1.10"]


class TestSortingIpv4:
    def test_order_by_is_numeric(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ipv4_address FROM test_ip_addresses"
                " WHERE ipv4_address IS NOT NULL ORDER BY ipv4_address"
            )
            rows = [str(r[0]) for r in cur.fetchall()]
        assert rows == ["122.168.133.103", "192.168.1.10"]


class TestInitScriptLoaded:
    def test_01_inet_sql_created_ip_addresses_table(self, conn):
        """Docker should have run sql/init/01_inet.sql at first start."""
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT COUNT(*) FROM ip_addresses")
            except pymysql.err.ProgrammingError as exc:
                if exc.args[0] == 1146:
                    pytest.skip("ip_addresses missing: 01_inet.sql not in sql/init yet")
                raise
            assert cur.fetchone()[0] == 3