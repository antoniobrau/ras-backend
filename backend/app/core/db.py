from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


@contextmanager
def get_conn():
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        # read-only per policy
        conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")
        yield conn
    finally:
        conn.close()