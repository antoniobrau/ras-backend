import random
import os
import calendar
from datetime import datetime
from faker import Faker
import psycopg

fake = Faker("it_IT")

DEFAULT_DSN = "postgresql://ras_user:ras_pass@localhost:5432/ras_db"
DSN = os.getenv("DATABASE_URL", DEFAULT_DSN)

CONFIG = {
    "company": "EXTRARED",
    "sites": ["PI", "MI", "RM"],
    "levels": ["B1", "B2", "C1", "C2"],
    "n_employees": 60,
    "n_teams": 6,
    "team_size_min": 6,
    "team_size_max": 12,
    "months": [(2025, 10), (2025, 11), (2025, 12)],

    # Probabilità per giorno lavorativo (lun-ven)
    "p_ferie": 0.06,
    "p_permesso": 0.05,
    "p_malattia": 0.02,

    # Per i giorni "WORK": quante righe (come ora)
    "lines_per_day_min": 1,
    "lines_per_day_max": 2,

    # Stima ore ordinarie (per query backend)
    "std_hours_per_workday": 8,
}

ACTIVITIES = ["Analisi requisiti", "Sviluppo", "Test", "Bugfix", "Meeting", "Documentazione"]
COMMESSE = ["EMO-1877", "EMO-1901", "INT-0001", "CUS-2044", "OPS-0100"]
FASI = ["F1", "F2", "F3", None]

ABSENCE_TYPES = ["FERIE", "PERMESSO", "MALATTIA"]

def upsert_employees(conn, company, n):
    emails, rows = [], []
    for i in range(n):
        full_name = fake.name()
        email = f"{full_name.lower().replace(' ','.')}{i}@azienda.it"
        site = random.choice(CONFIG["sites"])
        level = random.choice(CONFIG["levels"])
        rows.append((full_name, email, site, level, company))
        emails.append(email)

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO employees (full_name, email, site, level, company)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (email) DO NOTHING
            """,
            rows,
        )
    return emails

def ensure_team(conn, team_name, leader_email):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO teams (name, leader_id)
            VALUES (%s, (SELECT id FROM employees WHERE email=%s))
            ON CONFLICT (name) DO NOTHING
            """,
            (team_name, leader_email),
        )

def add_team_members(conn, team_name, member_emails, leader_email):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM teams WHERE name=%s", (team_name,))
        team_id = cur.fetchone()[0]

        cur.execute(
            "SELECT id, email FROM employees WHERE email = ANY(%s)",
            (member_emails,),
        )
        emp_map = {email: emp_id for emp_id, email in cur.fetchall()}

        rows = []
        for email in member_emails:
            role = "leader" if email == leader_email else "member"
            rows.append((team_id, emp_map[email], role))

        cur.executemany(
            """
            INSERT INTO team_members (team_id, employee_id, role)
            VALUES (%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            rows,
        )

def ensure_sheets(conn, employee_emails, months):
    with conn.cursor() as cur:
        rows = [(email, y, m) for email in employee_emails for (y, m) in months]
        cur.executemany(
            """
            INSERT INTO ras_sheets (employee_id, year, month, sheet_status)
            VALUES ((SELECT id FROM employees WHERE email=%s), %s, %s, 'draft')
            ON CONFLICT (employee_id, year, month) DO NOTHING
            """,
            rows,
        )

def set_sheet_statuses(conn, employee_emails, months):
    # distribuzione realistica: molti salvati/draft, alcuni submitted, pochi approved
    def pick_status():
        r = random.random()
        if r < 0.60:
            return "draft"
        if r < 0.90:
            return "submitted"
        return "approved"

    now = datetime.now()
    with conn.cursor() as cur:
        rows = []
        for email in employee_emails:
            for (y, m) in months:
                status = pick_status()
                submitted_at = now if status in ("submitted", "approved") else None
                approved_at = now if status == "approved" else None
                rows.append((status, submitted_at, approved_at, email, y, m))

        cur.executemany(
            """
            UPDATE ras_sheets rs
            SET sheet_status = %s,
                submitted_at = %s,
                approved_at = %s,
                updated_at = now()
            WHERE rs.employee_id = (SELECT id FROM employees WHERE email=%s)
              AND rs.year=%s AND rs.month=%s
            """,
            rows,
        )

def get_sheet_id(cur, employee_email, y, m):
    cur.execute(
        """
        SELECT rs.id
        FROM ras_sheets rs
        JOIN employees e ON e.id = rs.employee_id
        WHERE e.email=%s AND rs.year=%s AND rs.month=%s
        """,
        (employee_email, y, m),
    )
    return cur.fetchone()[0]

def pick_day_kind():
    r = random.random()
    if r < CONFIG["p_malattia"]:
        return "MALATTIA"
    if r < CONFIG["p_malattia"] + CONFIG["p_permesso"]:
        return "PERMESSO"
    if r < CONFIG["p_malattia"] + CONFIG["p_permesso"] + CONFIG["p_ferie"]:
        return "FERIE"
    return "WORK"

def insert_lines_for_month(conn, employee_email, y, m):
    with conn.cursor() as cur:
        sheet_id = get_sheet_id(cur, employee_email, y, m)
        _, last_day = calendar.monthrange(y, m)

        rows = []
        for day in range(1, last_day + 1):
            weekday = datetime(y, m, day).weekday()  # 0=Mon ... 6=Sun
            is_weekend = weekday >= 5
            if is_weekend:
                continue  # nel RAS reale il weekend spesso resta vuoto

            kind = pick_day_kind()

            if kind != "WORK":
                # Riga "assenza": la codifichiamo in activity_desc (schema invariato)
                rows.append((
                    sheet_id, day,
                    "ITA", None,              # stato, loc (loc vuota)
                    kind, None, None,         # activity_desc = FERIE/PERMESSO/MALATTIA
                    0.00, 0.00, "N"           # ore_extra, spese, pranzo
                ))
                continue

            n_lines = random.randint(CONFIG["lines_per_day_min"], CONFIG["lines_per_day_max"])
            for _ in range(n_lines):
                stato = "ITA"
                loc = random.choice(CONFIG["sites"])
                activity = random.choice(ACTIVITIES)
                commessa = random.choice(COMMESSE)
                fase = random.choice(FASI)
                ore_extra = 0 if random.random() < 0.8 else round(random.choice([0.5, 1.0, 1.5, 2.0]), 2)
                spese = 0 if random.random() < 0.75 else round(random.uniform(5, 40), 2)
                pranzo = "R" if random.random() < 0.6 else "N"

                rows.append((sheet_id, day, stato, loc, activity, commessa, fase, ore_extra, spese, pranzo))

        # NB: per le assenze inseriamo 10 campi ma la query sotto ne accetta 10.
        # Per WORK abbiamo (sheet_id, day, stato, loc, activity_desc, commessa_cdc, fase, ore_extra, tot_spese, pranzo_flag)
        # Per assenze mettiamo activity_desc=kind e commessa/fase null.

        cur.executemany(
            """
            INSERT INTO ras_lines
              (sheet_id, day, stato, loc, activity_desc, commessa_cdc, fase, ore_extra, tot_spese, pranzo_flag)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            rows,
        )

def main():
    random.seed(42)
    # Se vuoi stessi NOMI ovunque:
    fake.seed_instance(42)

    with psycopg.connect(DSN) as conn:
        conn.execute("BEGIN")

        all_emails = upsert_employees(conn, CONFIG["company"], CONFIG["n_employees"])

        random.shuffle(all_emails)
        team_leaders = all_emails[:CONFIG["n_teams"]]
        remaining = all_emails[CONFIG["n_teams"]:]

        teams = []
        for i in range(CONFIG["n_teams"]):
            team_name = f"Team {chr(ord('A') + i)}"
            leader = team_leaders[i]
            ensure_team(conn, team_name, leader)
            teams.append((team_name, leader))

        idx = 0
        for (team_name, leader) in teams:
            size = random.randint(CONFIG["team_size_min"], CONFIG["team_size_max"])
            members = [leader] + remaining[idx: idx + (size - 1)]
            idx += (size - 1)
            add_team_members(conn, team_name, members, leader)

        sheet_users = random.sample(all_emails, k=min(25, len(all_emails)))
        ensure_sheets(conn, sheet_users, CONFIG["months"])
        set_sheet_statuses(conn, sheet_users, CONFIG["months"])

        for email in sheet_users:
            for (y, m) in CONFIG["months"]:
                insert_lines_for_month(conn, email, y, m)

        conn.commit()
        print("Done: fake data inserted (weekends empty, absences as activity_desc).")

if __name__ == "__main__":
    main()
