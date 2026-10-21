-- Feature: UPDATE / DELETE with derived-table JOIN (MariaDB)
--
-- Task: make multi-step UPDATE/DELETE logic readable by naming the selection criteria.
-- Problem: MariaDB forbids UPDATE or DELETE from referencing the target table directly
-- in a subquery (e.g. UPDATE airports WHERE id IN (SELECT id FROM airports ...)).
-- The workaround is double-nesting — wrapping the subquery in another subquery just to
-- satisfy the parser. This compiles and runs, but the filtering logic is buried two levels
-- deep and the reason for the extra nesting is not obvious.
--
-- MariaDB-native solution: UPDATE ... JOIN / DELETE ... JOIN
-- Express the filter as a derived table (subquery with an alias) and JOIN it to the
-- target. No double nesting — intent is clear: match these rows, then update/delete them.
-- Note: WITH ... UPDATE / WITH ... DELETE (CTE + DML) is a PostgreSQL feature and is
-- not supported in MariaDB 11.4.

CREATE TABLE IF NOT EXISTS airports (
    id      INT          AUTO_INCREMENT PRIMARY KEY,
    iata    CHAR(3)      NOT NULL DEFAULT '',  -- 3-letter IATA code, empty if unassigned
    name    VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    status  VARCHAR(20)  NOT NULL DEFAULT 'unknown'
);

INSERT INTO airports (iata, name, country) VALUES
    ('LHR', 'Heathrow',               'United Kingdom'),
    ('CDG', 'Charles de Gaulle',      'France'),
    ('AMS', 'Amsterdam Schiphol',     'Netherlands'),
    ('FRA', 'Frankfurt Airport',      'Germany'),
    ('MAD', 'Adolfo Suárez Madrid',   'Spain'),
    ('FCO', 'Leonardo da Vinci',      'Italy'),
    ('',    'Enschede Helipad',        'Netherlands'),
    ('',    'Borkum Airfield',         'Germany');

-- OLD WAY: subquery
-- Double nesting required — MariaDB cannot reference the target table directly.
-- The inner SELECT id FROM (SELECT id FROM ...) AS sub exists only to satisfy the parser.
UPDATE airports
SET status = 'active'
WHERE id IN (
    SELECT id FROM (
        SELECT id FROM airports WHERE iata != ''
    ) AS sub
);

SELECT * FROM airports;

-- Reset
UPDATE airports SET status = 'unknown';

-- NEW WAY: UPDATE with JOIN
-- JOIN the derived table directly — no nesting, intent is clear at a glance.
UPDATE airports
JOIN (SELECT id FROM airports WHERE iata != '') AS registered ON airports.id = registered.id
SET airports.status = 'active';

SELECT * FROM airports;

-- DELETE with JOIN
-- Remove airports with no IATA code assigned.
DELETE airports FROM airports
JOIN (SELECT id FROM airports WHERE iata = '') AS no_iata ON airports.id = no_iata.id;

SELECT * FROM airports;

-- chained: two-step filter using nested derived tables
-- Filter to European airports, then narrow to inactive ones — joined in a single UPDATE.
UPDATE airports
JOIN (
    SELECT a.id
    FROM airports a
    JOIN (
        SELECT id FROM airports
        WHERE country IN ('France', 'Germany', 'Netherlands', 'Spain', 'Italy', 'United Kingdom')
    ) AS european ON a.id = european.id
    WHERE a.status = 'unknown'
) AS inactive_european ON airports.id = inactive_european.id
SET airports.status = 'pending';

SELECT * FROM airports;
