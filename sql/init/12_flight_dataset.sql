-- Flight Dataset (OpenFlights)

-- Source: https://github.com/jpatokal/openflights
-- CSV files included at: data/airports.csv, data/airlines.csv, data/routes.csv

-- CREATE OR REPLACE and RETURNING


USE mighty_coders;


-- Airports (~7,698 rows)

CREATE OR REPLACE TABLE airports (
    id          INT PRIMARY KEY,
    name        VARCHAR(200),
    city        VARCHAR(100),
    country     VARCHAR(100),
    iata        VARCHAR(10),
    icao        VARCHAR(10),
    latitude    DECIMAL(10,6),
    longitude   DECIMAL(10,6),
    altitude    INT,
    timezone    DECIMAL(4,1),
    dst         VARCHAR(5),
    tz_database VARCHAR(100),
    type        VARCHAR(20),
    source      VARCHAR(20)
);

LOAD DATA INFILE '/docker-entrypoint-initdb.d/data/airports.csv'
INTO TABLE airports
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n';


-- Airlines (~6,162 rows)


CREATE OR REPLACE TABLE airlines (
    id       INT PRIMARY KEY,
    name     VARCHAR(200),
    alias    VARCHAR(100),
    iata     VARCHAR(10),
    icao     VARCHAR(10),
    callsign VARCHAR(100),
    country  VARCHAR(100),
    active   VARCHAR(5)
);

LOAD DATA INFILE '/docker-entrypoint-initdb.d/data/airlines.csv'
INTO TABLE airlines
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n';


-- Routes (~66,316 valid rows out of 67,663 raw rows)

-- The raw OpenFlights routes file contains some rows with missing
-- or non-numeric airline/airport IDs, which would violate foreign
-- key constraints. These are filtered out via a staging table.


CREATE OR REPLACE TABLE routes_staging (
    airline_code      VARCHAR(10),
    airline_id        VARCHAR(10),
    source_airport    VARCHAR(10),
    source_airport_id VARCHAR(10),
    dest_airport      VARCHAR(10),
    dest_airport_id   VARCHAR(10),
    codeshare         VARCHAR(5),
    stops             INT,
    equipment         VARCHAR(50)
);

LOAD DATA INFILE '/docker-entrypoint-initdb.d/data/routes.csv'
INTO TABLE routes_staging
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n';

CREATE OR REPLACE TABLE routes (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    airline_code       VARCHAR(10),
    airline_id         INT,
    source_airport     VARCHAR(10),
    source_airport_id  INT,
    dest_airport       VARCHAR(10),
    dest_airport_id    INT,
    FOREIGN KEY (airline_id) REFERENCES airlines(id),
    FOREIGN KEY (source_airport_id) REFERENCES airports(id),
    FOREIGN KEY (dest_airport_id) REFERENCES airports(id)
);

INSERT INTO routes (airline_code, airline_id, source_airport, source_airport_id, dest_airport, dest_airport_id)
SELECT r.airline_code, r.airline_id, r.source_airport, r.source_airport_id, r.dest_airport, r.dest_airport_id
FROM routes_staging r
WHERE r.airline_id REGEXP '^[0-9]+$'
  AND r.source_airport_id REGEXP '^[0-9]+$'
  AND r.dest_airport_id REGEXP '^[0-9]+$'
  AND EXISTS (SELECT 1 FROM airlines a WHERE a.id = r.airline_id)
  AND EXISTS (SELECT 1 FROM airports ap1 WHERE ap1.id = r.source_airport_id)
  AND EXISTS (SELECT 1 FROM airports ap2 WHERE ap2.id = r.dest_airport_id);

DROP TABLE routes_staging;

SELECT COUNT(*) AS total_airports FROM airports;
SELECT COUNT(*) AS total_airlines FROM airlines;
SELECT COUNT(*) AS total_routes FROM routes;


-- CREATE OR REPLACE foreign key limit

-- With 66,316 routes referencing airlines and airports, attempting
-- to replace either parent table fails.

-- CREATE OR REPLACE TABLE airlines (id INT PRIMARY KEY, name VARCHAR(200));

-- Actual error observed:
-- ERROR 1451 (23000): Cannot delete or update a parent row: a
-- foreign key constraint fails


-- RETURNING


-- OLD WAY: insert, then a second round trip for the new row

INSERT INTO airlines (id, name, country)
VALUES (700001, 'Mekelle', 'Tigray');
SELECT * FROM airlines WHERE id = 700001;

-- NEW WAY: one round trip

INSERT INTO airlines (id, name, country)
VALUES (700002, 'Adwa', 'Tigray')
RETURNING id, name, country;

-- RETURNING: limitations

-- RETURNING only returns the rows touched by the statement it is
-- attached to. A second INSERT ... RETURNING does not return the
-- rows of the first one. To get earlier rows you need a SELECT, or
-- you insert all rows in a single statement:
--
-- INSERT INTO airlines (id, name, country)
-- VALUES (700003, 'A', 'Tigray'), (700004, 'B', 'Tigray')
-- RETURNING id, name;      -- returns both rows

-- DELETE ... RETURNING also works

DELETE FROM airlines
WHERE id IN (700001, 700002)
RETURNING id, name;

SELECT COUNT(*) AS airlines_count FROM airlines;


-- Note: a timed benchmark (200 operations each, old vs. new)
-- is available separately in benchmark.py:
--   python benchmark.py

-- Measured results across 6 runs:
--   OLD (INSERT + SELECT):      ~0.40-0.44ms per operation
--   NEW (INSERT ... RETURNING): ~0.18-0.22ms per operation
--   RETURNING is 49.0%-56.2% faster (average ~53%) over 200 operations