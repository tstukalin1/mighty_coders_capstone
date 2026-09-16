-- SQL that saves you work
-- Features: CREATE OR REPLACE, RETURNING

USE mighty_coders;

-- Feature 1: CREATE OR REPLACE TABLE
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

-- Feature 2: RETURNING
INSERT INTO team_members (name, matriculation_number, age)
VALUES ('Anna', '30009999', 23)
RETURNING id, name, age;

DELETE FROM team_members
WHERE matriculation_number = '30009999'
RETURNING id, name;

SELECT * FROM team_members;