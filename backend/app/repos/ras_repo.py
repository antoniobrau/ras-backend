from app.core.db import get_conn

ABSENCE_TYPES = ("FERIE", "PERMESSO", "MALATTIA")


class RASRepo:
    """
    Repository RAS.
    Contiene SOLO query SQL e accesso ai dati.
    Nessuna logica di business.
    """

    # ---------- sheets ----------

    def get_sheets_by_user(self, email: str):
        """
        Tutti i RAS (stato per mese) di un utente.
        """
        sql = """
        SELECT rs.id, rs.year, rs.month,
               rs.sheet_status, rs.submitted_at, rs.approved_at
        FROM ras_sheets rs
        JOIN employees e ON e.id = rs.employee_id
        WHERE e.email = %(email)s
        ORDER BY rs.year, rs.month;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"email": email})
            return cur.fetchall()

    def get_sheet_id(self, email: str, year: int, month: int):
        """
        Ritorna l'id del RAS per (utente, anno, mese).
        """
        sql = """
        SELECT rs.id
        FROM ras_sheets rs
        JOIN employees e ON e.id = rs.employee_id
        WHERE e.email = %(email)s
          AND rs.year = %(year)s
          AND rs.month = %(month)s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"email": email, "year": year, "month": month})
            row = cur.fetchone()
            return row["id"] if row else None

    # ---------- absences ----------

    def count_absences(self, sheet_id: int):
        """
        Conta giorni distinti di ferie / permesso / malattia in un mese.
        """
        sql = """
        SELECT
          COUNT(DISTINCT day) FILTER (WHERE activity_desc = 'FERIE')    AS ferie_giorni,
          COUNT(DISTINCT day) FILTER (WHERE activity_desc = 'PERMESSO') AS permesso_giorni,
          COUNT(DISTINCT day) FILTER (WHERE activity_desc = 'MALATTIA') AS malattia_giorni
        FROM ras_lines
        WHERE sheet_id = %(sheet_id)s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"sheet_id": sheet_id})
            return cur.fetchone()

    def get_absence_days(self, sheet_id: int):
        """
        Giorni di assenza per tipo (FERIE / PERMESSO / MALATTIA).
        """
        sql = """
        SELECT activity_desc AS tipo,
               ARRAY_AGG(DISTINCT day ORDER BY day) AS giorni
        FROM ras_lines
        WHERE sheet_id = %(sheet_id)s
          AND activity_desc IN ('FERIE','PERMESSO','MALATTIA')
        GROUP BY activity_desc;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"sheet_id": sheet_id})
            return cur.fetchall()

    # ---------- work / hours ----------

    def count_work_days(self, sheet_id: int):
        """
        Giorni lavorati = almeno una riga con commessa valorizzata.
        """
        sql = """
        SELECT COUNT(*) AS work_days
        FROM (
          SELECT DISTINCT day
          FROM ras_lines
          WHERE sheet_id = %(sheet_id)s
            AND commessa_cdc IS NOT NULL
        ) d;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"sheet_id": sheet_id})
            return cur.fetchone()["work_days"]

    # ---------- extra / spese ----------

    def get_extra_and_expenses(self, sheet_id: int):
        """
        Totali ore extra e spese del mese.
        """
        sql = """
        SELECT
          COALESCE(SUM(ore_extra), 0)::double precision AS ore_extra_tot,
          COALESCE(SUM(tot_spese), 0)::double precision AS spese_tot
        FROM ras_lines
        WHERE sheet_id = %(sheet_id)s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"sheet_id": sheet_id})
            return cur.fetchone()

    # ---------- quality checks ----------

    def get_days_without_lines(self, sheet_id: int, days_in_month: int):
        """
        Giorni del mese senza nessuna riga.
        """
        sql = """
        WITH days AS (
          SELECT generate_series(1, %(days_in_month)s) AS day
        )
        SELECT d.day
        FROM days d
        LEFT JOIN ras_lines rl
          ON rl.sheet_id = %(sheet_id)s AND rl.day = d.day
        WHERE rl.id IS NULL
        ORDER BY d.day;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                sql,
                {"sheet_id": sheet_id, "days_in_month": days_in_month},
            )
            return [r["day"] for r in cur.fetchall()]

    def get_mixed_days(self, sheet_id: int):
        """
        Giorni con assenza + lavoro insieme (anomalia).
        """
        sql = """
        WITH per_day AS (
          SELECT day,
                 BOOL_OR(activity_desc IN ('FERIE','PERMESSO','MALATTIA')) AS has_absence,
                 BOOL_OR(commessa_cdc IS NOT NULL) AS has_work
          FROM ras_lines
          WHERE sheet_id = %(sheet_id)s
          GROUP BY day
        )
        SELECT day
        FROM per_day
        WHERE has_absence AND has_work
        ORDER BY day;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"sheet_id": sheet_id})
            return [r["day"] for r in cur.fetchall()]
