---
name: data-modeling
description: >
  Data modeling fundamentals — entity-relationship design, normalization forms,
  modeling patterns (polymorphism, hierarchy, audit trails), and mapping domain
  models to database schemas. Use this skill when designing a new data model
  or refactoring an existing one.
category: data
tags: [data-modeling, database, schema, er-diagram, normalization]
related: [sql-fundamentals, database-migrations, clean-ddd-go]
---

# Data Modeling

> A data model is a contract between today's code and tomorrow's queries. Model for the questions you'll ask, not just the data you have.

## When to Use This Skill

- Designing a database schema for a new feature or system
- Refactoring a schema that's become painful (too many JOINs, duplicated data)
- Mapping DDD domain models to relational tables
- Choosing between normalization and denormalization
- Modeling common patterns (polymorphism, trees, audit)

---

## The Design Process

```
1. Identify entities and their relationships (from domain)
2. Define attributes (columns) for each entity
3. Normalize to reduce redundancy
4. Add indexes for known query patterns
5. Denormalize selectively for performance (only when measured)
```

---

## Entity-Relationship Basics

### Relationship types

| Relationship | Implementation |
|--------------|----------------|
| **One-to-one** | FK with UNIQUE constraint, or same table |
| **One-to-many** | FK on the "many" side |
| **Many-to-many** | Junction table (join table) |

### Example

```
users (id, name, email)
orders (id, user_id FK, total, created_at)        -- 1 user : N orders
order_items (id, order_id FK, product_id FK, qty)  -- N orders : N products via junction
products (id, name, price)
```

---

## Normalization

### Normal forms (practical subset)

| Form | Rule | Example violation |
|------|------|-------------------|
| **1NF** | No repeating groups; each cell holds one value | `tags: "go,python,rust"` → split into rows or separate table |
| **2NF** | Every non-key column depends on the whole PK | `order_items(order_id, product_id, product_name)` → `product_name` depends on `product_id` only |
| **3NF** | No transitive dependencies (A→B→C) | `orders(user_id, user_email)` → `user_email` depends on `user_id`, not on `order` |

1. **Normalize to 3NF by default.** Covers 90% of cases.
2. **Denormalize with intent.** When you denormalize, document why (read performance, reporting).

---

## Common Modeling Patterns

### Soft delete

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;
```
- Query active: `WHERE deleted_at IS NULL`
- Partial index: `CREATE INDEX ... WHERE deleted_at IS NULL`

### Audit trail (created/updated/by)

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    -- ... business columns ...
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by BIGINT REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);
```

3. **Every table gets `created_at` and `updated_at`.** Non-negotiable for debugging.

### Full audit log (event-based)

```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id BIGINT NOT NULL,
    action TEXT NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by BIGINT,
    changed_at TIMESTAMPTZ DEFAULT now()
);
```

For regulatory or compliance requirements.

### Polymorphism (single-table inheritance)

When multiple types share most columns:

```sql
CREATE TABLE notifications (
    id BIGINT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'email', 'sms', 'push'
    recipient TEXT NOT NULL,
    subject TEXT,        -- email only
    phone TEXT,          -- sms only
    device_token TEXT,   -- push only
    sent_at TIMESTAMPTZ
);
```

4. **Single-table works when types share 70%+ of columns.** Otherwise, use separate tables with a shared FK.

### Polymorphism (multiple tables)

```sql
CREATE TABLE notifications (id, type, recipient, sent_at)
CREATE TABLE email_details (notification_id FK, subject, body)
CREATE TABLE sms_details (notification_id FK, phone, message)
```

5. **Use separate tables when types have very different columns.** Avoids sparse NULLs.

### Tree / Hierarchy

| Pattern | Pros | Cons |
|---------|------|------|
| **Adjacency list** (`parent_id FK`) | Simple, easy insert | Recursive queries for full tree |
| **Materialized path** (`path: "/1/5/12"`) | Fast subtree queries | Path update on move |
| **Nested set** (`lft, rgt`) | Fast reads | Slow inserts/moves |
| **Closure table** | Fast reads + writes | Extra table, more storage |

6. **Default: adjacency list + recursive CTE.** PostgreSQL handles recursive CTEs well.

```sql
-- Adjacency list
CREATE TABLE categories (
    id BIGINT PRIMARY KEY,
    parent_id BIGINT REFERENCES categories(id),
    name TEXT NOT NULL
);

-- Recursive query for full subtree
WITH RECURSIVE tree AS (
    SELECT id, name, parent_id, 0 AS depth FROM categories WHERE id = 1
    UNION ALL
    SELECT c.id, c.name, c.parent_id, t.depth + 1
    FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree;
```

### Enum-like values

| Approach | When |
|----------|------|
| **CHECK constraint** | Small, stable set (`status IN ('active', 'closed')`) |
| **Lookup table** | Values change, need metadata, or are user-defined |
| **PostgreSQL ENUM type** | Caution: hard to modify (adding values requires migration) |

7. **Prefer CHECK constraints or lookup tables over PG ENUM.** ENUMs are hard to evolve.

### Tags / Labels

```sql
CREATE TABLE article_tags (
    article_id BIGINT REFERENCES articles(id),
    tag TEXT NOT NULL,
    PRIMARY KEY (article_id, tag)
);
CREATE INDEX idx_tags ON article_tags(tag);
```

Or with JSONB (simpler but less queryable):
```sql
ALTER TABLE articles ADD COLUMN tags JSONB DEFAULT '[]';
CREATE INDEX idx_articles_tags ON articles USING GIN(tags);
```

---

## Mapping DDD to SQL

| DDD concept | SQL mapping |
|-------------|-------------|
| **Aggregate root** | Main table; owns child tables |
| **Entity** | Table with its own `id` |
| **Value object** | Embedded columns, or separate table without independent identity |
| **Repository** | Data access layer (SELECT, INSERT, UPDATE per aggregate) |

8. **Load and save the whole aggregate.** Don't load child entities independently — that breaks aggregate consistency.
9. **Use persistence objects (POs) to decouple domain from schema.** Domain model ≠ database rows.

See [`clean-ddd-go`](../../engineering/clean-ddd-go/SKILL.md).

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| No primary key | Every table needs a PK |
| `VARCHAR(255)` everywhere | Use appropriate types and lengths |
| Storing comma-separated lists | Normalize into a separate table |
| No `created_at` / `updated_at` | Add to every table |
| Polymorphism with 80% NULL columns | Split into type-specific tables |
| Denormalized from day 1 | Normalize first; denormalize when measured |
| Using DB-level ENUM for mutable lists | CHECK constraint or lookup table |
| No indexes on foreign keys | Index all FKs |
| God table (50+ columns) | Decompose into related tables |

---

## Checklist

- [ ] Each entity has a primary key
- [ ] Relationships are explicit (FKs with indexes)
- [ ] Normalized to 3NF (denormalized only with documented reason)
- [ ] `created_at` and `updated_at` on every table
- [ ] Soft delete pattern if needed (with partial index)
- [ ] Hierarchy pattern chosen and documented
- [ ] Enum approach is evolvable (not PG ENUM for mutable values)
- [ ] DDD aggregates map to table groups with clear boundaries
- [ ] Schema reviewed for common anti-patterns

---

## Related Skills

- [`sql-fundamentals`](../sql-fundamentals/SKILL.md) — query and index the model
- [`database-migrations`](../database-migrations/SKILL.md) — evolve the model safely
- [`clean-ddd-go`](../../engineering/clean-ddd-go/SKILL.md) — domain model that maps to this data model
