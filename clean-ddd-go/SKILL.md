# Clean Architecture + Domain-Driven Design for Go

## Description

This skill provides guidance for developing Go applications using **Clean Architecture** combined with **Domain-Driven Design (DDD)**. It covers layered architecture, bounded contexts, aggregate roots, repository patterns, usecase orchestration, and adapter separation. Use this skill when building or modifying Go projects that follow these architectural principles.

## Architecture Layers

The system is organized into four concentric layers, with dependencies pointing **inward only**:

```
┌─────────────────────────────────────────────────┐
│  Infrastructure (Frameworks & Drivers)          │
│  ┌─────────────────────────────────────────────┐│
│  │  Interface (Adapters)                       ││
│  │  ┌─────────────────────────────────────────┐││
│  │  │  Usecase (Application Business Rules)   │││
│  │  │  ┌─────────────────────────────────────┐│││
│  │  │  │  Domain (Enterprise Business Rules) ││││
│  │  │  └─────────────────────────────────────┘│││
│  │  └─────────────────────────────────────────┘││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### Layer Dependency Rule

- **Domain** → depends on nothing (pure Go, no external imports)
- **Usecase** → depends on Domain only
- **Interface** → depends on Usecase and Domain
- **Infrastructure** → depends on external libraries (DB drivers, frameworks)

## Directory Structure

```
cmd/
  ├── <app-name>/         # Application entry points

internal/
  ├── domain/             # [Core] Enterprise Business Rules
  │   └── <context>/      # One package per Bounded Context
  │       ├── entity.go        # Aggregate Root + Entities
  │       ├── value_object.go  # Value Objects
  │       └── repository.go    # Repository interface (output port)
  │
  ├── usecase/            # [Application] Application Business Rules
  │   ├── port/
  │   │   └── in/         # Input Ports (usecase interfaces)
  │   ├── dto/            # Data Transfer Objects
  │   └── <context>/      # Service implementations
  │       └── service.go
  │
  ├── interface/          # [Adapters] Interface Adapters
  │   ├── in/             # Input adapters (HTTP, CLI, gRPC)
  │   └── out/            # Output adapters (Repository implementations)
  │       └── persistence/
  │           └── <db>/
  │               ├── <context>/   # Per-context repository impl
  │               └── po/          # Persistence Objects & converters
  │
  └── infrastructure/     # [Frameworks] External Details
      ├── persistence/    # DB client/connection setup
      ├── memory/         # Cache setup
      └── logger/         # Logging setup
```

## Rules

### 1. Domain Layer Rules

- **Zero external dependencies**: Domain packages must only import Go standard library. No database drivers, HTTP libraries, or framework code.
- **Aggregate Root pattern**: Each bounded context has exactly one Aggregate Root that controls access to child entities.
- **Rich Domain Models**: Domain entities must contain business logic (validation, state transitions, calculations). Avoid anemic domain models where entities are just data holders.
- **Repository interfaces in Domain**: Define persistence interfaces within the domain package. The domain declares what it needs; infrastructure fulfills it.
- **Value Objects are immutable**: Value Objects should return new instances instead of mutating internal state. Use value receivers for Value Object methods.
- **Guard clauses**: Domain methods must validate preconditions before mutating state. Return early or no-op on invalid input.
- **No DTO references**: Domain types must never reference DTOs or any type from outer layers.

### 2. Usecase Layer Rules

- **Input Ports as interfaces**: Define usecase operations as Go interfaces in `port/in/`. Adapters depend on these interfaces, not concrete services.
- **DTO boundary**: All data entering or leaving the usecase layer must be wrapped in DTOs. Domain entities must never be returned directly to callers.
- **Constructor injection**: Services receive repository interfaces via constructor (`NewService(repo domain.Repository)`). Never instantiate repositories inside services.
- **Cross-context orchestration**: When a usecase needs entities from multiple bounded contexts, inject multiple repository interfaces. The usecase layer is the only place where cross-context coordination happens.
- **Error semantics**: Define domain-meaningful sentinel errors (e.g., `ErrPlayerNotFound`, `ErrInvestigationNotActive`) within the service package. Wrap infrastructure errors with `fmt.Errorf("context: %w", err)`.
- **No direct DB calls**: Usecase services must only call repository interface methods, never database drivers directly.

### 3. Interface Layer Rules

- **Input adapters**: Convert external input (HTTP request, CLI args) into usecase DTOs, call input port methods, and convert results to external output format.
- **Output adapters (repositories)**: Implement domain repository interfaces. Each bounded context has its own repository implementation package.
- **Persistence Objects (PO)**: Use dedicated structs for database documents/rows. Provide bidirectional converters (Domain ↔ PO) to decouple database schema from domain models.
- **Adapter isolation**: Each adapter package only implements one interface. Don't mix HTTP handler logic with persistence logic.

### 4. Infrastructure Layer Rules

- **Shared setup only**: Infrastructure provides connection clients, configuration, and logging setup. It does NOT implement business logic or repository methods.
- **Separation from adapters**: DB client creation (`NewClient`) lives in infrastructure; per-context repository implementations using that client live in `interface/out/`.

### 5. General Rules

- **Dependency direction**: Outer layers depend on inner layers, never the reverse. Use interfaces to invert dependencies at layer boundaries.
- **Package by context, not by type**: Organize packages by bounded context (`personnel/`, `intelligence/`), not by technical role (`models/`, `repositories/`).
- **Test at every layer**: Domain tests validate business rules with plain Go. Usecase tests use mock repositories. Integration tests cover adapters.
- **`context.Context` propagation**: All repository interface methods and usecase methods accept `context.Context` as the first parameter.

## Go Example

Below is a minimal example demonstrating the full Clean Architecture + DDD stack for a single bounded context.

### Domain Layer

```go
// internal/domain/catalog/product.go
package catalog

// Product is the Aggregate Root for the Catalog context.
type Product struct {
    ID    string
    Name  string
    Price Price
    Stock int
}

// NewProduct creates a product with validation.
func NewProduct(id, name string, price Price, stock int) *Product {
    if stock < 0 {
        stock = 0
    }
    return &Product{
        ID:    id,
        Name:  name,
        Price: price,
        Stock: stock,
    }
}

// Sell reduces stock by the given quantity. Returns false if insufficient stock.
func (p *Product) Sell(qty int) bool {
    if qty <= 0 || p.Stock < qty {
        return false
    }
    p.Stock -= qty
    return true
}

// Restock increases stock by the given quantity.
func (p *Product) Restock(qty int) {
    if qty <= 0 {
        return
    }
    p.Stock += qty
}
```

```go
// internal/domain/catalog/price.go
package catalog

// Price is a Value Object representing monetary amount.
type Price struct {
    Amount   int    // in cents
    Currency string
}

// Add returns a new Price with the sum of two prices.
// Panics if currencies don't match.
func (p Price) Add(other Price) Price {
    if p.Currency != other.Currency {
        panic("cannot add prices with different currencies")
    }
    return Price{Amount: p.Amount + other.Amount, Currency: p.Currency}
}
```

```go
// internal/domain/catalog/repository.go
package catalog

import "context"

// ProductRepository defines persistence operations for Product aggregates.
type ProductRepository interface {
    Save(ctx context.Context, product *Product) error
    FindByID(ctx context.Context, id string) (*Product, error)
    FindAll(ctx context.Context) ([]*Product, error)
}
```

### Usecase Layer

```go
// internal/usecase/port/in/catalog.go
package in

import (
    "context"
    "myapp/internal/usecase/dto"
)

// CatalogUsecase defines input port for catalog flows.
type CatalogUsecase interface {
    GetProduct(ctx context.Context, id string) (*dto.ProductSummary, error)
    SellProduct(ctx context.Context, id string, qty int) (*dto.SellResult, error)
}
```

```go
// internal/usecase/dto/catalog.go
package dto

// ProductSummary is used for product display.
type ProductSummary struct {
    ID       string
    Name     string
    Price    int
    Currency string
    Stock    int
}

// SellResult summarizes a sale outcome.
type SellResult struct {
    ProductID      string
    QuantitySold   int
    RemainingStock int
    Success        bool
}
```

```go
// internal/usecase/catalog/service.go
package catalog

import (
    "context"
    "errors"
    "fmt"

    "myapp/internal/domain/catalog"
    "myapp/internal/usecase/dto"
)

var (
    ErrProductNotFound    = errors.New("product not found")
    ErrInsufficientStock  = errors.New("insufficient stock")
)

// Service orchestrates catalog flows.
type Service struct {
    products catalog.ProductRepository
}

// NewService creates a new catalog service.
func NewService(products catalog.ProductRepository) *Service {
    return &Service{products: products}
}

// GetProduct retrieves a product by ID.
func (s *Service) GetProduct(ctx context.Context, id string) (*dto.ProductSummary, error) {
    product, err := s.products.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("find product: %w", err)
    }
    if product == nil {
        return nil, ErrProductNotFound
    }
    return &dto.ProductSummary{
        ID:       product.ID,
        Name:     product.Name,
        Price:    product.Price.Amount,
        Currency: product.Price.Currency,
        Stock:    product.Stock,
    }, nil
}

// SellProduct sells a quantity of a product.
func (s *Service) SellProduct(ctx context.Context, id string, qty int) (*dto.SellResult, error) {
    product, err := s.products.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("find product: %w", err)
    }
    if product == nil {
        return nil, ErrProductNotFound
    }
    if !product.Sell(qty) {
        return &dto.SellResult{
            ProductID: product.ID,
            Success:   false,
        }, ErrInsufficientStock
    }
    if err := s.products.Save(ctx, product); err != nil {
        return nil, fmt.Errorf("save product: %w", err)
    }
    return &dto.SellResult{
        ProductID:      product.ID,
        QuantitySold:   qty,
        RemainingStock: product.Stock,
        Success:        true,
    }, nil
}
```

### Domain Test

```go
// internal/domain/catalog/product_test.go
package catalog_test

import (
    "testing"

    "myapp/internal/domain/catalog"

    "github.com/stretchr/testify/assert"
)

func TestProduct_Sell(t *testing.T) {
    product := catalog.NewProduct("p1", "Widget", catalog.Price{Amount: 1000, Currency: "TWD"}, 5)

    // Successful sale
    assert.True(t, product.Sell(3))
    assert.Equal(t, 2, product.Stock)

    // Insufficient stock
    assert.False(t, product.Sell(10))
    assert.Equal(t, 2, product.Stock) // unchanged

    // Invalid quantity
    assert.False(t, product.Sell(0))
    assert.False(t, product.Sell(-1))
}
```
