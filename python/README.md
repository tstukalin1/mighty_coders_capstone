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

## 2. INSERT + SELECT vs INSERT ... RETURNING

Python-примеры находятся в `python/returning/`:

- `before.py` — классический подход: `INSERT` + отдельный `SELECT` по `lastrowid`
- `after.py` — `INSERT ... RETURNING` возвращает строку за один round-trip

```python
#before: два запроса
cur.execute("INSERT INTO products (name, metadata) VALUES (%s, %s)", (...))
inserted_id = cur.lastrowid
cur.execute("SELECT id, name, metadata FROM products WHERE id = %s", (inserted_id,))

#after: один запрос
cur.execute("INSERT INTO products (name, metadata) VALUES (%s, %s) RETURNING id, name, metadata", (...))
row = cur.fetchone()
```

> Требуется MariaDB 10.5+. Поддерживается также `DELETE ... RETURNING`.

---

## Запуск

```bash
# Убедитесь, что контейнер запущен
docker compose up -d

# Запуск примеров
python python/returning/before.py
python python/returning/after.py
```
