import sys
import os

import pymysql
import pytest
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


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


def server_version(connection):
    """The server version as a tuple, e.g. (12, 3, 3) for '12.3.3-MariaDB-ubu2404'."""
    with connection.cursor() as cur:
        cur.execute("SELECT VERSION()")
        number = cur.fetchone()[0].split("-")[0]
    return tuple(int(part) for part in number.split("."))


@pytest.fixture
def version(conn):
    return server_version(conn)
