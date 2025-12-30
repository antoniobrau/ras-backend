BEGIN;

INSERT INTO employees (full_name, email, site, level, company)
VALUES
  ('Team Leader', 'tl@azienda.it', 'PI', 'B2', 'EXTRARED'),
  ('Mario Rossi', 'mario.rossi@azienda.it', 'PI', 'B1', 'EXTRARED'),
  ('Luigi Bianchi', 'luigi.bianchi@azienda.it', 'PI', 'B1', 'EXTRARED')
ON CONFLICT (email) DO NOTHING;

INSERT INTO teams (name, leader_id)
VALUES ('Team A', (SELECT id FROM employees WHERE email='tl@azienda.it'))
ON CONFLICT (name) DO NOTHING;

-- membri team
INSERT INTO team_members (team_id, employee_id, role)
SELECT t.id, e.id, CASE WHEN e.email='tl@azienda.it' THEN 'leader' ELSE 'member' END
FROM teams t
JOIN employees e ON e.email IN ('tl@azienda.it','mario.rossi@azienda.it','luigi.bianchi@azienda.it')
WHERE t.name='Team A'
ON CONFLICT DO NOTHING;

-- sheet dicembre 2025 per Mario
INSERT INTO ras_sheets (employee_id, year, month, sheet_status)
VALUES ((SELECT id FROM employees WHERE email='mario.rossi@azienda.it'), 2025, 12, 'draft')
ON CONFLICT (employee_id, year, month) DO NOTHING;

WITH s AS (
  SELECT rs.id AS sheet_id
  FROM ras_sheets rs
  JOIN employees e ON e.id = rs.employee_id
  WHERE e.email='mario.rossi@azienda.it' AND rs.year=2025 AND rs.month=12
)
INSERT INTO ras_lines (sheet_id, day, stato, loc, activity_desc, commessa_cdc, fase, ore_extra, tot_spese, pranzo_flag)
SELECT sheet_id, 2, 'ITA', 'PI', 'Analisi requisiti', 'EMO-1877', 'F1',  0,   0,    'R' FROM s
UNION ALL
SELECT sheet_id, 3, 'ITA', 'PI', 'Sviluppo',         'EMO-1877', NULL, 1.5, 12.30, 'R' FROM s;
COMMIT
