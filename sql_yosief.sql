-- SQL example
CREATE DATABASE mighty_coders;
USE mighty_coders;

CREATE TABLE team_members (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  matriculation_number VARCHAR(20),
  age INT
);

INSERT INTO team_members (name, matriculation_number, age) VALUES
('Yosief', '30009447', 26),
('Dinu', '30009445', 24),
('Timofey', '30009446', 22);

SELECT * FROM team_members;

SELECT name, age FROM team_members WHERE age > 24;

-- MariaDB-specific feature: System-versioned table
CREATE TABLE team_members_history (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  matriculation_number VARCHAR(20),
  age INT
) WITH SYSTEM VERSIONING;

INSERT INTO team_members_history VALUES (1, 'Jossy', '30009448', 27);

UPDATE team_members_history SET age = 25 WHERE id = 1;

-- history: old and new age
SELECT * FROM team_members_history FOR SYSTEM_TIME ALL;
