import random
import os
from datetime import date
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
    "days_per_month": 20,          # giorni lavorativi simulati
    "lines_per_day_min": 1,
    "lines_per_day_max": 2,
}

ACTIVITIES = ["Analisi requisiti", "Sviluppo", "Test", "Bugfix", "Meeting", "Documentazione"]
COMMESSE = ["EMO-1877", "EMO-1901", "INT-0001", "CUS-2044", "OPS-0100"]
FASI = ["F1", "F2", "F3", None]

def upsert_employees(conn, company, n):
    emails = []
    rows = []
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
        cur.execute("SELECT id, leader_id FROM teams WHERE name=%s", (team_name,))
        team_id, leader_id = cur.fetchone()

        # prendi id dipendenti
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
        rows = []
        for email in employee_emails:
            for (y, m) in months:
                rows.append((email, y, m))
        cur.executemany(
            """
            INSERT INTO ras_sheets (employee_id, year, month, sheet_status)
            VALUES ((SELECT id FROM employees WHERE email=%s), %s, %s, 'draft')
            ON CONFLICT (employee_id, year, month) DO NOTHING
            """,
            rows,
        )

def insert_lines(conn, employee_email, y, m, days, lines_per_day_min, lines_per_day_max):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rs.id
            FROM ras_sheets rs
            JOIN employees e ON e.id = rs.employee_id
            WHERE e.email=%s AND rs.year=%s AND rs.month=%s
            """,
            (employee_email, y, m),
        )
        sheet_id = cur.fetchone()[0]

        rows = []
        for day in range(1, days + 1):
            n_lines = random.randint(lines_per_day_min, lines_per_day_max)
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
    with psycopg.connect(DSN) as conn:
        conn.execute("BEGIN")

        # 1) dipendenti
        all_emails = upsert_employees(conn, CONFIG["company"], CONFIG["n_employees"])

        # 2) team + membri
        # scegli leader e membri senza sovrapposizioni pesanti
        random.shuffle(all_emails)
        team_leaders = all_emails[:CONFIG["n_teams"]]
        remaining = all_emails[CONFIG["n_teams"]:]

        teams = []
        for i in range(CONFIG["n_teams"]):
            team_name = f"Team {chr(ord('A') + i)}"
            leader = team_leaders[i]
            ensure_team(conn, team_name, leader)
            teams.append((team_name, leader))

        # assegna membri
        idx = 0
        for (team_name, leader) in teams:
            size = random.randint(CONFIG["team_size_min"], CONFIG["team_size_max"])
            members = [leader]
            members += remaining[idx: idx + (size - 1)]
            idx += (size - 1)
            add_team_members(conn, team_name, members, leader)

        # 3) sheets per un sottoinsieme (escludi i leader se vuoi)
        sheet_users = random.sample(all_emails, k=min(25, len(all_emails)))
        ensure_sheets(conn, sheet_users, CONFIG["months"])

        # 4) lines
        for email in sheet_users:
            for (y, m) in CONFIG["months"]:
                insert_lines(
                    conn, email, y, m,
                    CONFIG["days_per_month"],
                    CONFIG["lines_per_day_min"],
                    CONFIG["lines_per_day_max"]
                )

        conn.commit()
        print("Done: fake data inserted.")

if __name__ == "__main__":
    main()
