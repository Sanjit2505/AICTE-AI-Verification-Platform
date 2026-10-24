import pymysql
import pymysql.cursors
from contextlib import contextmanager
from app.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def fetch_all(query: str, args=None):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, args or ())
            return cursor.fetchall()

def fetch_one(query: str, args=None):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, args or ())
            return cursor.fetchone()

def execute(query: str, args=None) -> int:
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, args or ())
            return cursor.lastrowid
