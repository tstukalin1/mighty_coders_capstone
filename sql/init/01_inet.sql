CREATE DATABASE IF NOT EXISTS mighty_coders;

USE mighty_coders;

-- INET4 and INET6 
CREATE TABLE IF NOT EXISTS ip_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ipv4_address INET4,
    ipv6_address INET6
);

-- Insert IPv4
INSERT INTO ip_addresses (ipv4_address)
VALUES ('192.168.1.10');

-- Insert IPv6
INSERT INTO ip_addresses (ipv6_address)
VALUES ('2001:db8:85a3::8a2e:370:7334');

-- Another IPv4
INSERT INTO ip_addresses (ipv4_address)
VALUES ('122.168.133.103');

-- Validate IPv4
SELECT IS_IPV4('192.168.1.10') AS valid_ipv4;

SELECT IS_IPV4('999.999.999.999') AS valid_ipv4;

-- Validate IPv6
SELECT IS_IPV6('2001:db8:85a3::8a2e:370:7334') AS valid_ipv6;

-- Sort IPv4 addresses
SELECT id, ipv4_address
FROM ip_addresses
WHERE ipv4_address IS NOT NULL
ORDER BY ipv4_address;

-- Compare IPv4 addresses
SELECT id, ipv4_address
FROM ip_addresses
WHERE ipv4_address > '150.0.0.0';