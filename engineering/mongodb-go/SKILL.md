---
name: mongodb-go
description: >
  MongoDB with Go — mongo-go-driver usage, document schema design, indexing
  strategies, aggregation pipeline, transactions, and migration patterns.
  Use this skill when building Go services backed by MongoDB, designing
  document schemas, or optimizing query performance.
category: engineering
tags: [go, mongodb, database, nosql, document-db]
keywords: [MongoDB, mongo-go-driver, BSON, ObjectID, aggregation pipeline, $lookup]
related: [clean-ddd-go, data-modeling, go-testing, go-concurrency, auth-patterns, tw-payment-integration]
---

# MongoDB + Go

> MongoDB stores documents, not rows. Think in terms of "what does the application need in one read" — embed what's read together, reference what's read separately.

## When to Use This Skill

- Building a Go service with MongoDB as the primary datastore
- Designing document schemas (embed vs reference)
- Optimizing queries with indexes
- Using aggregation pipeline for complex queries
- Handling concurrent writes and transactions

---

## Setup (mongo-go-driver)

```go
import (
    "go.mongodb.org/mongo-driver/v2/mongo"
    "go.mongodb.org/mongo-driver/v2/mongo/options"
)

func NewMongoClient(ctx context.Context, uri string) (*mongo.Client, error) {
    client, err := mongo.Connect(options.Client().ApplyURI(uri))
    if err != nil {
        return nil, fmt.Errorf("connect mongo: %w", err)
    }
    if err := client.Ping(ctx, nil); err != nil {
        return nil, fmt.Errorf("ping mongo: %w", err)
    }
    return client, nil
}
```

### Collection access

```go
db := client.Database("booking")
groups := db.Collection("groups")
users := db.Collection("users")
```

---

## Document Schema Design

### The core question: Embed or Reference?

| Embed when | Reference when |
|------------|----------------|
| Data is always read together | Data is read independently |
| 1:1 or 1:few relationship | 1:many (unbounded) or many:many |
| Child doesn't exist without parent | Child has independent lifecycle |
| Updates are infrequent | Child is frequently updated independently |

### Example: Group Sports Booking

```go
// Group — aggregate root, embeds participants (bounded, read together)
type Group struct {
    ID          primitive.ObjectID   `bson:"_id,omitempty"`
    Sport       string               `bson:"sport"`
    Location    Location             `bson:"location"`      // embedded value object
    Schedule    Schedule             `bson:"schedule"`      // embedded
    MaxMembers  int                  `bson:"max_members"`
    Members     []Member             `bson:"members"`       // embedded array (bounded)
    Status      string               `bson:"status"`        // open, full, cancelled, completed
    CreatedBy   primitive.ObjectID   `bson:"created_by"`    // reference to user
    CreatedAt   time.Time            `bson:"created_at"`
    UpdatedAt   time.Time            `bson:"updated_at"`
}

type Location struct {
    Name    string  `bson:"name"`
    Address string  `bson:"address"`
    Lat     float64 `bson:"lat"`
    Lng     float64 `bson:"lng"`
}

type Schedule struct {
    Date      time.Time `bson:"date"`
    StartTime string    `bson:"start_time"` // "19:00"
    EndTime   string    `bson:"end_time"`   // "21:00"
}

type Member struct {
    UserID   primitive.ObjectID `bson:"user_id"`
    Name     string             `bson:"name"`      // denormalized for display
    JoinedAt time.Time          `bson:"joined_at"`
    Status   string             `bson:"status"`    // confirmed, cancelled
}

// User — separate collection (independent lifecycle)
type User struct {
    ID        primitive.ObjectID `bson:"_id,omitempty"`
    Name      string             `bson:"name"`
    Email     string             `bson:"email"`
    Phone     string             `bson:"phone"`
    AvatarURL string             `bson:"avatar_url"`
    Provider  string             `bson:"provider"`  // line, google
    CreatedAt time.Time          `bson:"created_at"`
}
```

### Schema design rules

1. **Embed for the read path.** If the API always returns group + members together, embed members.
2. **Denormalize display-only fields.** Store `member.Name` in the group so you don't need a JOIN. Accept staleness.
3. **Bound embedded arrays.** A group has max ~30 members — safe to embed. A user's activity history is unbounded — reference.
4. **Use `bson` tags explicitly.** Don't rely on default field name mapping.
5. **`_id` is `primitive.ObjectID`.** Use `omitempty` so MongoDB generates it on insert.

---

## CRUD Operations

### Insert

```go
group := Group{
    Sport:      "basketball",
    MaxMembers: 10,
    Status:     "open",
    Members:    []Member{},
    CreatedBy:  userID,
    CreatedAt:  time.Now(),
    UpdatedAt:  time.Now(),
}
result, err := groups.InsertOne(ctx, group)
// result.InsertedID is the generated _id
```

### Find

```go
var group Group
err := groups.FindOne(ctx, bson.M{"_id": groupID}).Decode(&group)
if errors.Is(err, mongo.ErrNoDocuments) {
    return nil, ErrGroupNotFound
}
```

### Find with filters

```go
filter := bson.M{
    "sport":         "basketball",
    "status":        "open",
    "schedule.date": bson.M{"$gte": time.Now()},
}
opts := options.Find().
    SetSort(bson.D{{"schedule.date", 1}}).
    SetLimit(20)

cursor, err := groups.Find(ctx, filter, opts)
var results []Group
err = cursor.All(ctx, &results)
```

### Update (add member to group)

```go
filter := bson.M{
    "_id":    groupID,
    "status": "open",
    "members": bson.M{
        "$not": bson.M{"$elemMatch": bson.M{"user_id": userID}},
    },
}
update := bson.M{
    "$push": bson.M{"members": newMember},
    "$set":  bson.M{"updated_at": time.Now()},
}
result, err := groups.UpdateOne(ctx, filter, update)
if result.MatchedCount == 0 {
    // group not found, already full, or user already joined
}
```

6. **Use atomic operators (`$push`, `$pull`, `$set`, `$inc`) instead of read-modify-write.** Avoids race conditions.
7. **Put preconditions in the filter, not in app code.** `"status": "open"` in the filter = atomic check-and-update.

### Delete (soft delete)

```go
update := bson.M{"$set": bson.M{"status": "cancelled", "updated_at": time.Now()}}
groups.UpdateOne(ctx, bson.M{"_id": groupID}, update)
```

8. **Prefer soft delete (status change) over hard delete.** Data recovery, audit trail.

---

## Indexing

### Common indexes for a booking service

```go
func EnsureIndexes(ctx context.Context, db *mongo.Database) error {
    groups := db.Collection("groups")

    indexes := []mongo.IndexModel{
        {Keys: bson.D{{"sport", 1}, {"status", 1}, {"schedule.date", 1}}},
        {Keys: bson.D{{"created_by", 1}}},
        {Keys: bson.D{{"members.user_id", 1}}},
        {Keys: bson.D{{"status", 1}, {"schedule.date", 1}}},
    }

    _, err := groups.Indexes().CreateMany(ctx, indexes)
    return err
}
```

### Rules

9. **Index fields you filter and sort on.** Compound index covers multi-field queries.
10. **Compound index field order matters.** Equality fields first, range/sort fields last.
11. **Index embedded array fields for `$elemMatch` queries.** `members.user_id` index enables "find groups a user joined".
12. **Use `Explain()` to verify index usage.** `cursor.Explain()` in tests.
13. **Unique index for constraints.** `email` on users, `(group_id, user_id)` to prevent double-join.

---

## Aggregation Pipeline

For complex queries — counts, grouping, joins.

```go
// Count open groups by sport
pipeline := mongo.Pipeline{
    {{"$match", bson.M{"status": "open"}}},
    {{"$group", bson.M{
        "_id":   "$sport",
        "count": bson.M{"$sum": 1},
    }}},
    {{"$sort", bson.M{"count": -1}}},
}
cursor, err := groups.Aggregate(ctx, pipeline)
```

### $lookup (JOIN equivalent)

```go
// Get group with full user details for created_by
pipeline := mongo.Pipeline{
    {{"$match", bson.M{"_id": groupID}}},
    {{"$lookup", bson.M{
        "from":         "users",
        "localField":   "created_by",
        "foreignField": "_id",
        "as":           "creator",
    }}},
    {{"$unwind", "$creator"}},
}
```

14. **Use aggregation for analytics and reports.** Don't use it for simple CRUD — regular Find is faster.
15. **`$lookup` is MongoDB's JOIN.** Use sparingly; if you need it every read, consider embedding instead.

---

## Transactions

MongoDB supports multi-document transactions (4.0+ for replica sets, 4.2+ for sharded):

```go
session, err := client.StartSession()
if err != nil { return err }
defer session.EndSession(ctx)

_, err = session.WithTransaction(ctx, func(sessCtx mongo.SessionContext) (any, error) {
    // atomic: join group + update user's group list
    _, err := groups.UpdateOne(sessCtx, groupFilter, groupUpdate)
    if err != nil { return nil, err }

    _, err = users.UpdateOne(sessCtx, userFilter, userUpdate)
    if err != nil { return nil, err }

    return nil, nil
})
```

16. **Transactions require a replica set** (even for local dev: use `rs.initiate()`).
17. **Keep transactions short.** Lock duration = transaction duration.
18. **Prefer atomic single-document operations where possible.** They don't need transactions.
19. **Retry on transient errors.** `WithTransaction` handles retries automatically.

---

## Migration Patterns

MongoDB has no rigid schema, but you still need to evolve documents.

### Lazy migration

Add new fields with default values; old documents get updated on next write:

```go
// New field: add default when reading
if group.Status == "" {
    group.Status = "open"
}
```

### Batch migration

```go
filter := bson.M{"new_field": bson.M{"$exists": false}}
update := bson.M{"$set": bson.M{"new_field": defaultValue}}
groups.UpdateMany(ctx, filter, update)
```

20. **Prefer lazy migration for non-critical fields.** Batch for fields needed in queries/indexes.
21. **Version your document schema.** Add a `schema_version` field; migration scripts check it.

---

## Clean Architecture Integration

```
internal/
  domain/group/
    entity.go          # Group, Member (domain types, no bson tags)
    repository.go      # GroupRepository interface
  usecase/group/
    service.go         # uses GroupRepository
  interface/out/mongodb/group/
    repository.go      # implements GroupRepository with mongo-go-driver
    po.go             # GroupPO (with bson tags) + converters
```

22. **Domain types don't have `bson` tags.** Persistence Objects (POs) do. Convert at the repository boundary.
23. **Repository interface is in domain.** Implementation with mongo-go-driver is in the adapter layer.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Unbounded embedded arrays | Reference; or cap array size |
| Read-modify-write for concurrent updates | Use atomic operators (`$push`, `$set`, `$inc`) |
| No indexes on query fields | Index what you filter/sort |
| `$lookup` on every read | Embed or denormalize |
| `bson` tags missing | Always explicit `bson:"field_name"` |
| Domain types with `bson` tags | Separate PO types in adapter layer |
| Hard delete | Soft delete (status change) |
| Transaction for single-document ops | Atomic ops don't need transactions |

---

## Checklist

- [ ] Document schema follows embed-vs-reference rules
- [ ] Bounded arrays only (no unbounded embedded arrays)
- [ ] `bson` tags explicit on all PO fields
- [ ] Indexes cover query and sort patterns
- [ ] Concurrent writes use atomic operators (not read-modify-write)
- [ ] Transactions only for multi-document atomicity
- [ ] PO types separate from domain types (Clean Architecture)
- [ ] Soft delete pattern for data recovery
- [ ] `EnsureIndexes` runs at app startup
- [ ] Connection has proper timeout and pooling config

---

## Related Skills

- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — architecture; repository pattern on top of MongoDB
- [`data-modeling`](../../data/data-modeling/SKILL.md) — modeling concepts (adapted for documents)
- [`go-testing`](../go-testing/SKILL.md) — testing with testcontainers for MongoDB
- [`go-concurrency`](../go-concurrency/SKILL.md) — concurrent access patterns
