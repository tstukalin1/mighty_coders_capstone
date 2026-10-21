USE mighty_coders;

-- Feature: CREATE OR REPLACE TABLE

-- OLD WAY: two statements

DROP TABLE IF EXISTS team_members;
CREATE TABLE team_members (
    id                    INT          AUTO_INCREMENT PRIMARY KEY,
    name                  VARCHAR(100) NOT NULL,
    matriculation_number  VARCHAR(20)  NOT NULL,
    age                   INT
);

-- NEW WAY: one statement
CREATE OR REPLACE TABLE team_members (
    id                    INT          AUTO_INCREMENT PRIMARY KEY,
    name                  VARCHAR(100) NOT NULL,
    matriculation_number  VARCHAR(20)  NOT NULL,
    age                   INT
);

INSERT INTO team_members (name, matriculation_number, age) VALUES
    ('Yosief', '30009447', 26),
    ('Dinu', '30009445', 24),
    ('Timofey', '30009446', 22);

SELECT * FROM team_members;

-- CREATE OR REPLACE also works on VIEW and PROCEDURE
-- Same idempotent benefit applies.

CREATE OR REPLACE VIEW active_members AS
SELECT id, name, age
FROM team_members
WHERE age < 30;

SELECT * FROM active_members;

-- Re-running this is safe and idempotent, unlike plain CREATE VIEW,


CREATE OR REPLACE VIEW active_members AS
SELECT id, name, age
FROM team_members
WHERE age < 25;

SELECT * FROM active_members;

-- Limit: CREATE OR REPLACE cannot replace a table that is
-- referenced by a foreign key constraint from another table.

CREATE OR REPLACE TABLE projects (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(100)
);

INSERT INTO projects (project_name) VALUES ('Capstone SQL Features');

CREATE OR REPLACE TABLE assignments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    member_id  INT,
    project_id INT,
    FOREIGN KEY (member_id) REFERENCES team_members(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

INSERT INTO assignments (member_id, project_id) VALUES
    (1, 1), -- Yosief on Capstone SQL Features
    (2, 1), -- Dinu on Capstone SQL Features
    (3, 1); -- Timofey on Capstone SQL Features

SELECT * FROM assignments;

-- Now that assignments references team_members.
-- Running CREATE OR REPLACE TABLE team_members will fail with an error.
--
-- CREATE OR REPLACE TABLE team_members (
--     id INT PRIMARY KEY,
--     name VARCHAR(100)
-- );
--
-- Actual error observed:
-- ERROR 1451 (23000): Cannot delete or update a parent row: a
-- foreign key constraint fails


-- Feature: RETURNING

-- INSERT and DELETE hand back the rows they touched,
-- removing the need for a separate SELECT round trip.

-- OLD WAY: insert, then a second round trip for the new row

INSERT INTO team_members (name, matriculation_number, age)
VALUES ('Anna', '30009999', 23);
SELECT * FROM team_members WHERE id = LAST_INSERT_ID();

-- NEW WAY: one round trip

INSERT INTO team_members (name, matriculation_number, age)
VALUES ('Anna2', '30009998', 23)
RETURNING id, name, age;

-- ------------------------------------------------------------
-- RETURNING can compute expressions on the returned row
-- RETURNING * returns every column without naming them.
-- ------------------------------------------------------------

INSERT INTO team_members (name, matriculation_number, age)
VALUES ('Anna3', '30009997', 23)
RETURNING id, name, age, age + 1 AS age_next_year;

INSERT INTO team_members (name, matriculation_number, age)
VALUES ('Anna4', '30009996', 23)
RETURNING *;

-- ------------------------------------------------------------
-- Limit: UPDATE ... RETURNING is NOT supported on this MariaDB
-- version. It was only added in MariaDB 13.0; this project runs
-- MariaDB 11.4, where RETURNING supports only INSERT and DELETE.
--
-- UPDATE team_members
-- SET age = age + 1
-- WHERE matriculation_number IN ('30009999', '30009998')
-- RETURNING id, name, age;
--
-- Actual error observed:
-- ERROR 1064 (42000): You have an error in your SQL syntax; check
-- the manual that corresponds to your MariaDB server version for
-- the right syntax to use near 'RETURNING id, name, age' at line 4
-- ------------------------------------------------------------

-- RETURNING also works on DELETE — clean up all demo rows
DELETE FROM team_members
WHERE matriculation_number IN ('30009999', '30009998', '30009997', '30009996')
RETURNING id, name;

SELECT * FROM team_members;