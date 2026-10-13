# MariaDB Progress Reporting with Python

## Project Overview

This project explores progress reporting for long-running MariaDB operations, specifically `ALTER TABLE` and `CHECK TABLE`. It uses MariaDB running in Docker and Python to execute operations, monitor database activity, and automate verification with pytest.

## Technologies Used

- MariaDB 11.4
- Docker
- Python 3.14
- mysql-connector-python
- pytest
- VS Code

## Dataset

The project uses an airline dataset imported from `airlines.csv`.

- Database: `airlines_db`
- Original table: `airlines`
- Demo table: `airlines_progress_demo`
- Demo dataset: approximately 394,000 records

## Project Files

- `import_airlines.py` — imports CSV records into MariaDB.
- `setup_progress_demo.py` — creates and populates the demo table.
- `check_progress.py` — inspects the MariaDB version and process list.
- `check_table_engine.py` — verifies the table's storage engine and approximate row count.
- `run_alter.py` — executes an `ALTER TABLE` operation.
- `monitor_progress.py` — monitors active database operations through `information_schema.PROCESSLIST`.
- `run_check.py` — executes `CHECK TABLE`.
- `test_progress.py` — verifies indexes and table-check results.

## Setup

1. Start the existing MariaDB Docker container.
2. Install the Python dependency:

   ```bash
   python -m pip install mysql-connector-python pytest
   ```

3. Configure the database connection settings in the Python scripts.
4. Import the airline CSV if the database has not already been populated.

## Running the Experiments

### ALTER TABLE

Run the operation:

```bash
python run_alter.py
```

Monitor it from another terminal:

```bash
python monitor_progress.py
```

The monitor queries MariaDB's process list for matching active operations.

### CHECK TABLE

Run:

```bash
python run_check.py
```

The script prints the result and execution time.

## Automated Tests

Run the tests from the project root:

```bash
python -m pytest .\mariadb-row-project\test_progress.py -v
```

The completed test run reported:

- `test_country_index_exists` — PASSED
- `test_name_index_exists` — PASSED
- `test_check_table` — PASSED

**Result: 3 passed in 0.37 seconds.**

## Observations

- The `ALTER TABLE` operations completed successfully.
- The monitor detected an active table-altering operation.
- The sampled progress values were `STAGE=0/0` and `PROGRESS=0.00%`.
- `CHECK TABLE` returned `OK` in approximately 0.08 seconds.
- The short execution times made it difficult to capture intermediate progress values.

Progress reporting depends on the operation and its execution stage. Detecting an active operation does not guarantee that MariaDB will expose a meaningful percentage in every sample.

## Security Notes

- Do not commit database passwords to Git.
- Use environment variables for database credentials.
- Do not commit private data or unnecessary copies of the CSV dataset.
