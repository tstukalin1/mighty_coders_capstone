CREATE OR REPLACE TABLE employees (
    emp_id INT PRIMARY KEY,
    emp_name VARCHAR(100),
    salary DECIMAL(10,2),
    department VARCHAR(50)
);

INSERT INTO employees VALUES
(101, 'Rahul', 50000, 'QA'),
(102, 'John', 60000, 'Development');


DELIMITER //
CREATE PROCEDURE get_employee(IN p_id INT)
BEGIN
    DECLARE emp ROW TYPE OF employees;

    SELECT *
    INTO emp
    FROM employees
    WHERE emp_id = p_id;

    SELECT
        emp.emp_id AS Employee_ID,
        emp.emp_name AS Employee_Name,
        emp.salary AS Salary,
        emp.department AS Department;
END //
DELIMITER ;

CALL get_employee(101);
CALL get_employee(104);
