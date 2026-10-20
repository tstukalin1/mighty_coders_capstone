-- Feature: INVISIBLE columns (MariaDB 10.3+)

USE mighty_coders;


-- OLD WAY: adding a column without INVISIBLE

-- Adding a new column to an existing table changes the result of SELECT *
-- Breaks any INSERT statement that doesn't list columns explicitly

CREATE OR REPLACE TABLE invisible_old (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100)
);

INSERT INTO invisible_old (name) VALUES ('Yosief'), ('Dinu'), ('Timofey');

SELECT * FROM invisible_old;

-- Now add a new column, without INVISIBLE
ALTER TABLE invisible_old ADD COLUMN added_column VARCHAR(100);

-- SELECT * now includes the new column

SELECT * FROM invisible_old;

-- An INSERT that used to work fine without naming columns now behaves differently
-- It must account for the new column or rely on it allowing NULL/default.

INSERT INTO invisible_old VALUES (NULL, 'Anna', 'added without a note');
SELECT * FROM invisible_old;



-- NEW WAY: INVISIBLE columns

-- A column marked INVISIBLE is excluded from SELECT * and from
-- INSERT statements that don't name columns explicitly.
-- but is still fully usable when named directly.
-- Adding an internal/technical column does not change the behavior of
-- existing SELECT * or column-less INSERT statements.


CREATE OR REPLACE TABLE invisible_new (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100)
);

INSERT INTO invisible_new (name) VALUES ('Yosief'), ('Dinu'), ('Timofey');

SELECT * FROM invisible_new;

-- Now add the column WITH INVISIBLE

ALTER TABLE invisible_new ADD COLUMN added_column VARCHAR(100) INVISIBLE;

-- SELECT * does NOT show added_column
-- Existing code relying on SELECT * sees no difference at all.

SELECT * FROM invisible_new;

-- Naming it explicitly DOES show it.

SELECT id, name, added_column FROM invisible_new;

-- A column-less INSERT still works fine
-- the invisible column is simply skipped and takes its default (NULL).


INSERT INTO invisible_new (name) VALUES ('Anna');
SELECT * FROM invisible_new;
SELECT id, name, added_column FROM invisible_new;

-- Inserting WITH the invisible column named explicitly also works.

INSERT INTO invisible_new (name, added_column) VALUES ('Frankfurt', 'city in Germany');
SELECT * FROM invisible_new;
SELECT id, name, added_column FROM invisible_new;



-- Cleanup


DROP TABLE invisible_old;
DROP TABLE invisible_new;