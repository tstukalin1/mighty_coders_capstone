
import mysql.connector

def test_airline(airline_id):
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="1234",
        database="airlines_db"
    )

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("CALL get_airline_row(%s)", (airline_id,))
        result = cursor.fetchone()

        # Consume any remaining procedure result sets.
        while cursor.nextset():
            pass

        print(f"\nTesting airline ID: {airline_id}")
        print("Result:", result)

        if result and "message" in result:
            assert result["message"] == "Airline not found"
            print("PASS: Negative scenario")

        else:
            assert result is not None
            assert result["airline_id"] == airline_id
            assert "name" in result
            assert "country" in result
            assert "active" in result
            print("PASS: Positive scenario")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    test_airline(2)
    test_airline(-999)
