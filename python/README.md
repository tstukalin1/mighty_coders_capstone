# IS JSON CHECK + INSERT RETURNING

Демонстрация двух фич MariaDB: валидации JSON через `CHECK` и возврата данных через `RETURNING`.

---

## 1. IS JSON CHECK constraint

**Файл:** `sql/init/02_isjson_check.sql`

```sql
CREATE TABLE products (
    id       INT          AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    metadata JSON         NOT NULL,
    CONSTRAINT chk_metadata_is_json CHECK (metadata IS JSON)
);
```

`CHECK (metadata IS JSON)` — это ограничение уровня таблицы. MariaDB отклонит
любой `INSERT` или `UPDATE`, если значение в колонке `metadata` не является
валидным JSON-документом.

**Пример ошибки:**
```sql
INSERT INTO products (name, metadata) VALUES ('Bad', 'not-json');
-- ERROR 4025 (23000): CONSTRAINT `chk_metadata_is_json` failed
```

> Требуется MariaDB 10.6+ для полной поддержки `IS JSON`.

---

## 2. INSERT + SELECT (before.py)

**Файл:** `python/before.py`

Классический подход: после `INSERT` делаем отдельный `SELECT` по `lastrowid`.

```python
cur.execute("INSERT INTO products (name, metadata) VALUES (%s, %s)", (...))
inserted_id = cur.lastrowid
cur.execute("SELECT id, name, metadata FROM products WHERE id = %s", (inserted_id,))
row = cur.fetchone()
```

**Недостатки:**
- Два round-trip к базе данных
- Возможна гонка данных в конкурентной среде (между INSERT и SELECT)

---

## 3. INSERT ... RETURNING (after.py)

**Файл:** `python/after.py`

`RETURNING` возвращает данные вставленной строки прямо в ответе на `INSERT`.

```python
cur.execute(
    "INSERT INTO products (name, metadata) VALUES (%s, %s) RETURNING id, name, metadata",
    (...)
)
row = cur.fetchone()
```

**Преимущества:**
- Один round-trip к базе данных
- Атомарно: нет гонки данных
- Можно возвращать любые колонки, включая вычисляемые

> Требуется MariaDB 10.5+. Поддерживается также `UPDATE ... RETURNING` и `DELETE ... RETURNING`.

---

## Запуск

```bash
# Убедитесь, что контейнер запущен
docker compose up -d

# Запуск примеров
python python/before.py
python python/after.py
```
