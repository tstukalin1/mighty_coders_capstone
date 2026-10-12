
import mysql.connector


def connect():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="1234",
        database="airlines_db"
    )


def test_country_index_exists():
    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SHOW INDEX FROM airlines_progress_demo
        """)
        indexes = [row[2] for row in cursor.fetchall()]

        assert "idx_country" in indexes
        print("PASS: idx_country exists")

    finally:
        cursor.close()
        conn.close()


def test_name_index_exists():
    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SHOW INDEX FROM airlines_progress_demo
        """)
        indexes = [row[2] for row in cursor.fetchall()]

        assert "idx_name" in indexes
        print("PASS: idx_name exists")

    finally:
        cursor.close()
        conn.close()


def test_check_table():
    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("CHECK TABLE airlines_progress_demo")
        results = cursor.fetchall()

        assert results, "CHECK TABLE returned no result"
        assert any(row[3] == "OK" for row in results), results
        print("PASS: CHECK TABLE returned OK")

    finally:
        cursor.close()
        conn.close()
