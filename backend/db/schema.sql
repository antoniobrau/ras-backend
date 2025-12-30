BEGIN;

-- ====== anagrafiche ======

CREATE TABLE IF NOT EXISTS employees (
  id          BIGSERIAL PRIMARY KEY,
  full_name   TEXT NOT NULL,
  email       TEXT UNIQUE NOT NULL,
  fiscal_code TEXT,
  site        TEXT,          -- es. PI
  level       TEXT,          -- es. B1
  company     TEXT,          -- es. EXTRARED
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS teams (
  id          BIGSERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  leader_id   BIGINT NOT NULL REFERENCES employees(id),
  created_at  TIMESTAMP NOT NULL DEFAULT now(),
  UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS team_members (
  team_id     BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  employee_id BIGINT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
  role        TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('member','leader')),
  PRIMARY KEY(team_id, employee_id)
);

-- ====== sheet mensile (un “RAS” per mese per dipendente) ======

CREATE TABLE IF NOT EXISTS ras_sheets (
  id          BIGSERIAL PRIMARY KEY,
  employee_id BIGINT NOT NULL REFERENCES employees(id),
  year        INTEGER NOT NULL,
  month       INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),

  sheet_status TEXT NOT NULL DEFAULT 'draft'
    CHECK (sheet_status IN ('draft','submitted','approved','rejected')),

  submitted_at TIMESTAMP,
  approved_at  TIMESTAMP,
  approver_id  BIGINT REFERENCES employees(id),

  created_at   TIMESTAMP NOT NULL DEFAULT now(),
  updated_at   TIMESTAMP NOT NULL DEFAULT now(),

  UNIQUE(employee_id, year, month)
);

-- ====== righe giornaliere (una o più righe per giorno) ======

CREATE TABLE IF NOT EXISTS ras_lines (
  id            BIGSERIAL PRIMARY KEY,
  sheet_id      BIGINT NOT NULL REFERENCES ras_sheets(id) ON DELETE CASCADE,

  day           INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31),

  stato         TEXT,          -- es. ITA
  loc           TEXT,          -- es. PI

  activity_desc TEXT,          -- descrizione attività
  commessa_cdc  TEXT,          -- es. EMO-1877
  ss            TEXT,
  fase          TEXT,

  rip_percent   NUMERIC(5,2) NOT NULL DEFAULT 100.00 CHECK (rip_percent >= 0 AND rip_percent <= 100),

  ore_extra     NUMERIC(6,2) NOT NULL DEFAULT 0.00 CHECK (ore_extra >= 0),

  pranzo_flag   TEXT,          -- es. R / N
  cena_flag     TEXT,          -- es. R / N

  tot_spese     NUMERIC(10,2) NOT NULL DEFAULT 0.00 CHECK (tot_spese >= 0),
  rip_spesa     NUMERIC(5,2),
  rip_extra     TEXT,

  note          TEXT,

  created_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ras_lines_sheet_day ON ras_lines(sheet_id, day);
CREATE INDEX IF NOT EXISTS idx_ras_lines_commessa ON ras_lines(commessa_cdc);
CREATE INDEX IF NOT EXISTS idx_ras_sheets_emp_period ON ras_sheets(employee_id, year, month);
CREATE INDEX IF NOT EXISTS idx_team_members_employee ON team_members(employee_id);

COMMIT;
