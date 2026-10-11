-- Feature: INTERSECT and EXCEPT set operators (MariaDB 10.3+)
--
-- Task: find the intersection and difference of two sets of rows without JOIN boilerplate.
-- Problem: without INTERSECT/EXCEPT, set logic must be expressed through INNER JOIN and
-- LEFT JOIN + IS NULL. These produce correct results but hide the intent — a reader sees
-- join syntax and has to mentally decode it as a set operation. The code is also fragile:
-- if the join key changes, the NULL trick silently breaks.
--
-- SQL set operators treat two SELECT results as mathematical sets and combine them.
-- UNION     — all rows from A and B (duplicates removed).
-- INTERSECT — only rows that appear in both A and B (A ∩ B).
-- EXCEPT    — rows from A that do not appear in B (A \ B).
-- Both SELECTs must return the same number of columns with compatible types.

CREATE TABLE IF NOT EXISTS routes_from_ams (
    destination CHAR(3) NOT NULL  -- IATA code of destination airport
);

CREATE TABLE IF NOT EXISTS routes_from_fra (
    destination CHAR(3) NOT NULL  -- IATA code of destination airport
);

-- sample of real destinations from Amsterdam Schiphol (AMS)
INSERT INTO routes_from_ams (destination) VALUES
    ('LHR'), ('CDG'), ('MAD'), ('FCO'), ('BCN'),
    ('VIE'), ('ZRH'), ('DXB'), ('JFK'), ('BKK');

-- sample of real destinations from Frankfurt Airport (FRA)
INSERT INTO routes_from_fra (destination) VALUES
    ('LHR'), ('CDG'), ('MAD'), ('FCO'), ('BCN'),
    ('MUC'), ('ORD'), ('JFK'), ('NRT'), ('SIN');

-- OLD WAY: INTERSECT via JOIN
-- INNER JOIN returns rows where both tables have a match on the join condition.
-- This produces the correct result, but the intent (set intersection) is not obvious
-- from reading the query — it looks like a regular join, not a set operation.
SELECT a.destination
FROM routes_from_ams a
INNER JOIN routes_from_fra f ON a.destination = f.destination;

-- OLD WAY: EXCEPT via LEFT JOIN + IS NULL
-- LEFT JOIN keeps every row from the left table, filling right-side columns with NULL
-- when there is no match. WHERE IS NULL isolates the unmatched left rows.
-- Again correct, but reads like a join trick rather than a set difference.
SELECT a.destination
FROM routes_from_ams a
LEFT JOIN routes_from_fra f ON a.destination = f.destination
WHERE f.destination IS NULL;

-- NEW WAY: INTERSECT
-- Destinations served from both AMS and FRA. Duplicates removed automatically.
SELECT destination FROM routes_from_ams
INTERSECT
SELECT destination FROM routes_from_fra;

-- NEW WAY: EXCEPT
-- Destinations from AMS not served from FRA (AMS \ FRA).
-- Order of operands matters: swap them to get the opposite difference.
SELECT destination FROM routes_from_ams
EXCEPT
SELECT destination FROM routes_from_fra;

-- EXCEPT: FRA \ AMS
-- Reversing operands gives destinations from FRA not served from AMS.
SELECT destination FROM routes_from_fra
EXCEPT
SELECT destination FROM routes_from_ams;

-- chained: AMS-only destinations, sorted
-- Operators can be chained; ORDER BY applies to the final combined result.
SELECT destination FROM routes_from_ams
EXCEPT
SELECT destination FROM routes_from_fra
ORDER BY destination;
