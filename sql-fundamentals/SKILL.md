---
name: sql-fundamentals
description: >
  SQL fundamentals for developers — schema design, indexing strategy, query
  optimization, JOINs, transactions, and common anti-patterns. Use this skill
  when designing a database schema, optimizing slow queries, or reviewing
  data access patterns. Dialect-agnostic with PostgreSQL examples.
category: data
tags: [sql, database, postgresql, schema, query-optimization]
related: [database-migrations, data-modeling, clean-ddd-go]
---

# SQL Fundamentals

> SQL is the most durable technology in software. Schemas outlive applications. Design them carefully.

## When to Use This Skill

- Designing a new database schema
- Optimizing slow queries
- Adding indexes
- Reviewing data access patterns
- Choosing between normalization and denormalization

---

## Schema Design

### Naming conventions

1. **Tables: plural, snake_case.** `orders`, `order_items`, `user_profiles`.
2. **Columns: singular, snake_case.** `created_at`, `order_id`, `total_amount`.
3. **Primary keys: `id` or `<table>_id`.** Be consistent across the schema.
4. **Foreign keys: `<referenced_table>_id`.** `user_id` references `users.id`.
5. **Booleans: `is_` or `has_` prefix.** `is_active`, `has_verified_email`.
6. **Timestamps: `_at` suffix.** `created_at`, `updated_at`, `deleted_at`.

### Data types (PostgreSQL)

| Use | Type | Not |
|-----|------|-----|
| IDs | `BIGINT` or `UUID` | `INT` (overflows at ~2B) |
| Money | `BIGINT` (cents) or `NUMERIC` | `FLOAT` / `DOUBLE` (rounding) |
| Timestamps | `TIMESTAMPTZ` | `TIMESTAMP` (no timezone) |
| Short strings | `VARCHAR(N)` or `TEXT` | `CHAR(N)` (padded) |
| Long text | `TEXT` | `VARCHAR(10000)` |
| Booleans | `BOOLEAN` | `INT` 0/1 |
| JSON | `JSONB` | `JSON` (no indexing) |

7. **Always use `TIMESTAMPTZ`** (timestamp with time zone). You will regret bare `TIMESTAMP`.

---

## Indexing

### When to index

8. **Columns in `WHERE` clauses.** If you filter by it, index it.
9. **Columns in `JOIN` conditions.** Foreign keys should be indexed.
10. **Columns in `ORDER BY`.** If sorting is slow.
11. **Unique constraints create indexes automatically.** No need to add separately.

### Index types

| Type | Use |
|------|-----|
| **B-tree (default)** | Equality, range, sorting — most queries |
| **GIN** | Full-text search, JSONB, array containment |
| **Partial** | Index only rows matching a condition: `WHERE is_active = true` |
| **Composite** | Multi-column: `(user_id, created_at)` for queries filtering on both |

### Rules

12. **Don't index everything.** Each index slows writes. Index what queries need.
13. **Composite index column order matters.** `(a, b)` serves `WHERE a = ?` and `WHERE a = ? AND b = ?`, but NOT `WHERE b = ?` alone.
14. **Use `EXPLAIN ANALYZE` to verify index usage.**

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = 42 AND status = 'active';
```

Look for `Index Scan` (good) vs `Seq Scan` (bad, unless table is tiny).

---

## Query Optimization

### The process

```
1. Identify slow query (application logs, pg_stat_statements)
2. Run EXPLAIN ANALYZE
3. Look for: Seq Scan on large tables, Nested Loop on large joins, Sort on disk
4. Fix: add index, rewrite query, or denormalize
5. Re-run EXPLAIN ANALYZE to confirm
```

### Common fixes

| Problem | Fix |
|---------|-----|
| Seq Scan on large table | Add index on filter column |
| `SELECT *` | Select only needed columns |
| N+1 queries (one query per row) | Use JOIN or batch query |
| Subquery in WHERE | Rewrite as JOIN |
| Sort on disk (external sort) | Add index matching ORDER BY |
| Missing LIMIT | Always LIMIT user-facing queries |

### N+1 Problem

```sql
-- BAD: 1 query for orders + N queries for items
SELECT * FROM orders WHERE user_id = 42;
-- then for each order:
SELECT * FROM order_items WHERE order_id = ?;

-- GOOD: 2 queries total
SELECT * FROM orders WHERE user_id = 42;
SELECT * FROM order_items WHERE order_id IN (?, ?, ...);

-- OR: 1 query with JOIN
SELECT o.*, oi.*
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.user_id = 42;
```

15. **N+1 is the #1 performance killer** in application code. Detect via query count per request.

---

## Transactions

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

16. **Use transactions for multi-statement operations** that must be atomic.
17. **Keep transactions short.** Long transactions hold locks and block others.
18. **Set isolation level when needed.** Default `READ COMMITTED` is fine for most. Use `SERIALIZABLE` for strict consistency requirements.

### Isolation levels (simplified)

| Level | Prevents | Cost |
|-------|----------|------|
| `READ COMMITTED` (default) | Dirty reads | Low |
| `REPEATABLE READ` | + Non-repeatable reads | Medium |
| `SERIALIZABLE` | + Phantom reads | Highest (may abort transactions) |

---

## Normalization vs Denormalization

### Normalize by default

Separate entities into their own tables to avoid data duplication.

```
users (id, name, email)
orders (id, user_id, total, created_at)
order_items (id, order_id, product_id, quantity, price)
```

### Denormalize selectively

When:
- Read-heavy, write-rare data
- Expensive JOINs on hot paths
- Reporting/analytics tables

```sql
-- Denormalized: order includes user_name for fast display
orders (id, user_id, user_name, total, created_at)
```

19. **Start normalized. Denormalize when measured.** Premature denormalization creates data inconsistency.

---

## Common Patterns

### Soft delete

```sql
ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMPTZ;
CREATE INDEX idx_orders_active ON orders(id) WHERE deleted_at IS NULL;
```

20. **Soft delete = set `deleted_at`, don't actually delete.** Allows recovery. Use partial index for active rows.

### Pagination

```sql
-- Offset (simple but slow on deep pages)
SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 100;

-- Cursor (fast, stable)
SELECT * FROM products WHERE id > $last_id ORDER BY id LIMIT 20;
```

21. **Cursor pagination for large tables.** Offset re-scans skipped rows.

### Upsert

```sql
INSERT INTO settings (key, value)
VALUES ('theme', 'dark')
ON CONFLICT (key)
DO UPDATE SET value = EXCLUDED.value;
```

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `SELECT *` everywhere | Select needed columns only |
| No index on foreign keys | Index all FKs |
| `FLOAT` for money | `BIGINT` (cents) or `NUMERIC` |
| `TIMESTAMP` without timezone | `TIMESTAMPTZ` |
| N+1 queries | Batch or JOIN |
| Long-running transactions | Keep short; break into smaller units |
| No `EXPLAIN ANALYZE` on slow queries | Always explain before optimizing |
| Premature denormalization | Normalize first; denormalize when measured |

---

## Checklist

- [ ] Naming is consistent (plural tables, snake_case)
- [ ] All foreign keys have indexes
- [ ] `TIMESTAMPTZ` used (not `TIMESTAMP`)
- [ ] No `FLOAT` for monetary values
- [ ] Slow queries identified and `EXPLAIN ANALYZE`d
- [ ] N+1 queries eliminated from hot paths
- [ ] Transactions are short and use appropriate isolation
- [ ] Pagination uses cursor for large tables
- [ ] Schema changes go through migration tooling

---

## Related Skills

- [`database-migrations`](../database-migrations/SKILL.md) — evolving schemas safely
- [`data-modeling`](../data-modeling/SKILL.md) — entity-relationship design
- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — repository pattern on top of SQL
