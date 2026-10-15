-- CREATE SEQUENCE vs AUTO_INCREMENT

USE mighty_coders;


-- OLD WAY: AUTO_INCREMENT

-- AUTO_INCREMENT is tied to a single table.
-- Each table has its own independent counter
-- There is no way to share one counter across multiple tables.

CREATE OR REPLACE TABLE sequence_auto_a (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(50)
);

CREATE OR REPLACE TABLE sequence_auto_b (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(50)
);

INSERT INTO sequence_auto_a (label) VALUES
    ('Yosief'), ('Dinu'), ('Timofey');

INSERT INTO sequence_auto_b (label) VALUES
    ('Yosief'), ('Dinu'), ('Timofey');

SELECT * FROM sequence_auto_a;
SELECT * FROM sequence_auto_b;

-- Both tables independently count 1, 2, 3
-- the two counters know nothing about each other,




-- NEW WAY: CREATE SEQUENCE

-- A sequence is a standalone object, independent of any table.
-- One sequence can be shared across multiple tables.
-- Producing globally unique, continuously incrementing values.

CREATE OR REPLACE SEQUENCE member_id_seq
    START WITH 100
    INCREMENT BY 1;

CREATE OR REPLACE TABLE sequence_seq_a (
    id    INT PRIMARY KEY,
    label VARCHAR(50)
);

CREATE OR REPLACE TABLE sequence_seq_b (
    id    INT PRIMARY KEY,
    label VARCHAR(50)
);

-- Insert into A, then B, then A again, then B again -- alternating,

INSERT INTO sequence_seq_a (id, label) VALUES (NEXT VALUE FOR member_id_seq, 'Yosief');
INSERT INTO sequence_seq_b (id, label) VALUES (NEXT VALUE FOR member_id_seq, 'Yosief');
INSERT INTO sequence_seq_a (id, label) VALUES (NEXT VALUE FOR member_id_seq, 'Dinu');
INSERT INTO sequence_seq_b (id, label) VALUES (NEXT VALUE FOR member_id_seq, 'Dinu');
INSERT INTO sequence_seq_a (id, label) VALUES (NEXT VALUE FOR member_id_seq, 'Timofey');
INSERT INTO sequence_seq_b (id, label) VALUES (NEXT VALUE FOR member_id_seq, 'Timofey');

SELECT * FROM sequence_seq_a;
SELECT * FROM sequence_seq_b;

-- Table A ends up with ids 100, 102, 104 and table B with 101, 103, 105
-- AUTO_INCREMENT cannot produce this pattern.



-- Sequence configuration: step, start, cycling


CREATE OR REPLACE SEQUENCE cycling_seq
    START WITH 1
    INCREMENT BY 2
    MINVALUE 1
    MAXVALUE 5
    CYCLE;

SELECT NEXT VALUE FOR cycling_seq;  -- 1
SELECT NEXT VALUE FOR cycling_seq;  -- 3
SELECT NEXT VALUE FOR cycling_seq;  -- 5
SELECT NEXT VALUE FOR cycling_seq;  -- cycles back to 1



-- Cleanup


DROP TABLE sequence_auto_a;
DROP TABLE sequence_auto_b;
DROP TABLE sequence_seq_a;
DROP TABLE sequence_seq_b;
DROP SEQUENCE member_id_seq;
DROP SEQUENCE cycling_seq;