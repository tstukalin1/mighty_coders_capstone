-- Feature: INET4 / INET6 native IP address types (MariaDB 10.5+)

-- OLD WAY: store IPs as VARCHAR — wrong sort order, no built-in validation

CREATE TABLE IF NOT EXISTS connections_old (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    client_ip  VARCHAR(45) NOT NULL
);

INSERT INTO connections_old (client_ip) VALUES
    ('192.168.1.10'),
    ('10.0.0.5'),
    ('172.16.0.1'),
    ('8.8.8.8'),
    ('8.8.4.4');

-- VARCHAR sorts lexicographically: '10...' < '172...' < '192...' < '8...'
-- That is wrong — 8.8.8.8 should come before 10.0.0.5
SELECT id, client_ip
FROM connections_old
ORDER BY client_ip;

-- NEW WAY: INET4 — 4 bytes instead of up to 45, sorts numerically

CREATE TABLE IF NOT EXISTS connections_new (
    id         INT  AUTO_INCREMENT PRIMARY KEY,
    client_ip  INET4 NOT NULL
);

INSERT INTO connections_new (client_ip) VALUES
    ('192.168.1.10'),
    ('10.0.0.5'),
    ('172.16.0.1'),
    ('8.8.8.8'),
    ('8.8.4.4');

-- INET4 sorts numerically: 8.8.4.4 < 8.8.8.8 < 10.0.0.5 < 172.16.0.1 < 192.168.1.10
SELECT id, client_ip
FROM connections_new
ORDER BY client_ip;

-- Range comparison works correctly with INET4
SELECT id, client_ip
FROM connections_new
WHERE client_ip BETWEEN '10.0.0.0' AND '10.255.255.255'; -- 10.0.0.5 only

-- MariaDB rejects invalid addresses at INSERT time
-- INSERT INTO connections_new (client_ip) VALUES ('999.999.999.999');
-- ERROR 1292 (22007): Incorrect ipv4 value: '999.999.999.999'

-- INET6 stores both IPv4-mapped and full IPv6 addresses (16 bytes)
CREATE TABLE IF NOT EXISTS connections_v6 (
    id         INT  AUTO_INCREMENT PRIMARY KEY,
    client_ip  INET6 NOT NULL
);

INSERT INTO connections_v6 (client_ip) VALUES
    ('2001:db8::1'),
    ('2001:db8::ff'),
    ('::ffff:192.168.1.10'); -- IPv4-mapped IPv6

SELECT id, client_ip
FROM connections_v6
ORDER BY client_ip;
