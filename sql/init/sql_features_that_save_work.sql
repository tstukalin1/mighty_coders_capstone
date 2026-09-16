-- =============================================================
-- Area 1: "SQL that saves you work"
-- Features demonstrated: RETURNING, CREATE OR REPLACE
-- Team: Mighty Coders — Capstone Project I
-- =============================================================

CREATE OR REPLACE DATABASE mighty_coders;
USE mighty_coders;

-- -------------------------------------------------------------
-- Feature 1: CREATE OR REPLACE
-- Idempotent DDL — this table definition can be re-run any
-- number of times without manual cleanup.
-- -------------------------------------------------------------

-- WITHOUT CREATE OR REPLACE (the old, painful way):
--   DROP TABLE IF EXISTS team_members;
--   CREATE TABLE team_members ( ... );
-- Every migration script needs this two-line dance, and it is
-- easy to forget the DROP, which is exactly the error we hit
-- earlier this week: "ERROR 1007: Can't create database;
-- database exists."

-- WITH CREATE OR REPLACE (one statement, no dance):
CREATE OR REPLACE TABLE team_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    matriculation_number VARCHAR(20) NOT NULL,
    age INT
);

INSERT INTO team_members (name, matriculation_number, age) VALUES
    ('Yosief', '30009447', 26),
    ('Dinu', '30009445', 24),
    ('Timofey', '30009446', 22);

SELECT * FROM team_members;

-- Re-run this whole script right now. Notice: no error, no
-- manual DROP required, table is simply rebuilt clean.


-- -------------------------------------------------------------
-- Feature 2: RETURNING
-- INSERT and DELETE hand back the rows they touched, removing
-- the need for a second round-trip SELECT.
--
-- NOTE / finding: MariaDB's RETURNING clause is only supported
-- on INSERT, REPLACE, and DELETE — NOT on UPDATE. We confirmed
-- this ourselves: `UPDATE ... RETURNING ...` throws
-- ERROR 1064 (42000) on MariaDB 12.3.3. This matches MariaDB's
-- own documentation, which lists RETURNING as supported for
-- INSERT, REPLACE and DELETE only.
-- -------------------------------------------------------------

-- WITHOUT RETURNING (the old, two-round-trip way):
--   INSERT INTO team_members (name, matriculation_number, age)
--     VALUES ('Anna', '30009999', 23);
--   SELECT * FROM team_members WHERE matriculation_number = '30009999';
-- Two statements, two round trips to the server, and a second
-- query that has to guess which row you just inserted.

-- WITH RETURNING on INSERT (one round trip, no guessing):
INSERT INTO team_members (name, matriculation_number, age)
VALUES ('Anna', '30009999', 23)
RETURNING id, name, age;

-- WITHOUT RETURNING, confirming a delete the old way:
--   DELETE FROM team_members WHERE matriculation_number = '30009999';
--   -- no confirmation of what was removed unless you SELECT first

-- WITH RETURNING on DELETE (confirms exactly what was removed,
-- in one step, no prior SELECT needed):
DELETE FROM team_members
WHERE matriculation_number = '30009999'
RETURNING id, name;

-- -------------------------------------------------------------
-- Final state
-- -------------------------------------------------------------
SELECT * FROM team_members;