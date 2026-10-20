-- Feature: GLOBAL TEMPORARY TABLES — NOT YET AVAILABLE IN MARIADB
--
-- The project brief lists "Global temporary tables (12.3)" as a feature
-- to demonstrate: one shared table definition, contents private to each
-- session (SQL-standard behaviour, similar to Oracle/MSSQL/PostgreSQL).
--
-- After investigating, this feature is NOT actually implemented in any
-- released version of MariaDB, including 12.3 and the 11.4 image this
-- project runs in Docker. The work is tracked publicly in MariaDB's own
-- issue tracker:
--
--   MDEV-35915 — https://jira.mariadb.org/browse/MDEV-35915
--
-- As of this writing, MDEV-35915's status is "Stalled" and it targets
-- MariaDB 13.3 LTS, a release that has not shipped yet. We confirmed
-- this is not shipped in 12.3 by checking the official release notes
-- for 12.3.1 and 12.3.3, neither of which mentions this feature.
--
-- The proposed syntax (per the Jira ticket) is:
--
--   CREATE GLOBAL TEMPORARY TABLE table_name (
--       ...
--   ) ON COMMIT [DELETE | PRESERVE] ROWS;
--
-- Run separately (not as part of this script) to reproduce the actual
-- failure, confirming the feature is genuinely unavailable rather than a mistake:
--
-- CREATE GLOBAL TEMPORARY TABLE scratch_new (
--     id   INT AUTO_INCREMENT PRIMARY KEY,
--     note VARCHAR(100)
-- ) ON COMMIT PRESERVE ROWS;
--
-- Actual error reproduced on MariaDB 12.3.3 (Homebrew, local) and
-- MariaDB 11.4 (Docker, project's shared environment):
--
--   ERROR 1064 (42000): You have an error in your SQL syntax; check the
--   manual that corresponds to your MariaDB server version for the
--   right syntax to use near 'GLOBAL TEMPORARY TABLE scratch_new (
--       id   INT AUTO_INCREMENT PRIMARY KEY,...' at line 1
--
-- This is a plain parser error (unrecognised keyword), not a privilege
-- or configuration issue -- the GLOBAL TEMPORARY TABLE syntax simply
-- does not exist in the parser yet.

USE mighty_coders;

-- What IS available today: a regular TEMPORARY TABLE, which is private
-- to the session that creates it -- both its structure AND its data
-- disappear when that session ends, and every session that needs it
-- has to CREATE it again itself.


CREATE TEMPORARY TABLE scratch_old (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    note VARCHAR(100)
);

INSERT INTO scratch_old (note) VALUES ('from this session');

SELECT * FROM scratch_old;

-- Cleanup
DROP TEMPORARY TABLE IF EXISTS scratch_old;