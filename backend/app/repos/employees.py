from typing import Any, Mapping, Optional
from app.core.db import get_conn


def get_employee_by_email(email: str) -> Optional[Mapping[str, Any]]:
    sql = """
    SELECT id, full_name, email, site, level, company, active, created_at
    FROM employees
    WHERE email = %s
    LIMIT 1;
    """
    with get_conn() as conn:
        row = conn.execute(sql, (email,)).fetchone()
        return row