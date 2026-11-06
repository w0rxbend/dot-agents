# Top Go Libraries by Category

## Table of Contents

- [Web Frameworks](#web-frameworks)
- [HTTP Clients](#http-clients)
- [ORM & Database](#orm--database)
- [Database Drivers](#database-drivers)
- [Testing](#testing)
- [Command Line and Configuration](#command-line-and-configuration)
- [Logging](#logging)
- [Validation](#validation)
- [JSON Processing](#json-processing)
- [Authentication & Authorization](#authentication--authorization)
- [Caching](#caching)
- [Rate Limiting](#rate-limiting)
- [Concurrency & Goroutines](#concurrency--goroutines)
- [Messaging](#messaging)
- [Types and Data Structures](#types-and-data-structures)
- [Database Schema Migration](#database-schema-migration)
- [WebSockets](#websockets)
- [gRPC](#grpc)
- [GraphQL](#graphql)
- [File Watching](#file-watching)
- [Retry Logic](#retry-logic)
- [Error Handling](#error-handling)
- [Metrics & Monitoring](#metrics--monitoring)
- [API Documentation](#api-documentation)
- [Dependency Injection](#dependency-injection)
- [Functional Programming & Utilities](#functional-programming--utilities)
- [Excel & Spreadsheet](#excel--spreadsheet)

## Web Frameworks

**Gin** (<https://github.com/gin-gonic/gin>) High-performance HTTP web framework, minimalist API. Up to 40x faster than some alternatives. For REST APIs and microservices.

**Echo** (<https://github.com/labstack/echo>) Minimalist, extensible web framework. Clean middleware, excellent performance. REST APIs and traditional web apps.

**Fiber** (<https://github.com/gofiber/fiber>) Express.js-inspired, built on Fasthttp. Very fast; easy for Node.js developers moving to Go.

**Chi** (<https://github.com/go-chi/chi>) Lightweight, idiomatic router; composes with net/http. Minimal dependencies, good for smaller projects.

## HTTP Clients

**Resty** (<https://github.com/go-resty/resty>) Simple HTTP/REST client inspired by Ruby's rest-client. API consumption with retry support.

**Req** (<https://github.com/imroc/req>) Simple HTTP client with "black magic": less code, more efficiency. Clean API for common operations.

## ORM & Database

**GORM** (<https://github.com/go-gorm/gorm>) Feature-complete, developer-friendly ORM: associations, hooks, auto-migrations. Most popular Go ORM.

**SQLx** (<https://github.com/jmoiron/sqlx>) database/sql extensions: convenience without losing power. Type-safe, performant query helpers.

**Ent** (<https://github.com/ent/ent>) Entity framework. Code-generated, type-safe ORM; strong at complex queries and graph traversals.

**Sqlc** (<https://github.com/sqlc-dev/sqlc>) Generates type-safe Go code from SQL. No runtime reflection; compiler-checked queries.

## Database Drivers

**go-sql-driver/mysql** (<https://github.com/go-sql-driver/mysql>) MySQL driver for database/sql. Maintained by Go team; reliable, performant.

**lib/pq** (<https://github.com/lib/pq>) Pure Go PostgreSQL driver. Gold standard for PostgreSQL in Go.

**pgx** (<https://github.com/jackc/pgx>) PostgreSQL driver, advanced features. Faster than lib/pq; supports all PostgreSQL types.

**redis-go** (<https://github.com/redis/go-redis>) Redis client. Cluster support, modern Redis features, well-maintained.

**mongo-go-driver** (<https://github.com/mongodb/mongo-go-driver>) Official MongoDB driver. Async operations, transactions (newer versions).

## Testing

**Testify** (<https://github.com/stretchr/testify>) Sacred extension to testing package: assertions, mocking, suite testing. Essential for Go testing.

**gomock** (<https://github.com/uber-go/mock>) Mocking for Go interfaces. Widely used; integrates with testing package.

**go-sqlmock** (<https://github.com/DATA-DOG/go-sqlmock>) SQL mock driver. Tests database code without real database.

**testcontainers-go** (<https://golang.testcontainers.org>) Integration tests with real dependencies in Docker containers: databases, message queues, etc.

**httptest** (standard library) Tests HTTP servers/clients.

## Command Line and Configuration

**Cobra** (<https://github.com/spf13/cobra>) Commander for modern Go CLI apps. Subcommands, flags, auto-generated docs. Industry standard for CLIs.

**Viper** (<https://github.com/spf13/viper>) Go configuration with fangs. Works with Cobra; formats: JSON, YAML, TOML, env.

**urfave/cli** (<https://github.com/urfave/cli>) Simple, fast, fun command line apps. Cobra alternative.

**Koanf** (<https://github.com/knadh/koanf>) Lightweight, extensible config reader: JSON, YAML, TOML, env, command line.

**env** (from <https://github.com/caarlos0/env>) Parses environment variables into Go structs with defaults. Simple, type-safe, no struct tags.

## Logging

**Zap** (<https://github.com/uber-go/zap>) Fast, structured, leveled logging. Uber's production logger; zero-allocation hot paths.

**Zerolog** (<https://github.com/rs/zerolog>) Zero-allocation JSON logging. Very fast, simple API, leveled.

**Logrus** (<https://github.com/sirupsen/logrus>) Mature, widely used structured logger, plugin architecture. Note: deprecated in favor of structured logging.

## Validation

**validator** (<https://github.com/go-playground/validator>) Tag-based Go struct validation, extensive validators, cross-field validation.

**ozzo-validation** (<https://github.com/go-ozzo/ozzo-validation>) Fast validation library. Modern alternative for struct validation.

## JSON Processing

**jsoniter** (<https://github.com/json-iterator/go>) High-performance, 100% compatible drop-in replacement for encoding/json.

## Authentication & Authorization

**Casbin** (<https://github.com/casbin/casbin>) Policy-based authorization: ACL, RBAC, ABAC.

**JWT** (<https://github.com/golang-jwt/jwt>) Full-featured, widely used JSON Web Token implementation.

## Caching

**hot** (<https://github.com/samber/hot>) In-memory cache: 9 eviction algorithms (LRU, LFU, TinyLFU, W-TinyLFU, S3FIFO, ARC, TwoQueue, SIEVE, FIFO), TTL, loaders with singleflight deduplication, sharding, stale-while-revalidate.

**Ristretto** (<https://github.com/dgraph-io/ristretto>) High-performance memory-bound Go cache.

**BigCache** (<https://github.com/allegro/bigcache>) Efficient key/value cache for gigabytes of data. Sharded, high throughput.

**go-cache** (<https://github.com/patrickmn/go-cache>) In-memory key-value store with expiration. Thread-safe, simple API.

## Rate Limiting

**Tollbooth** (<https://github.com/ulule/limiter>) Simple, volume-based rate limiting HTTP middleware.

**golang.org/x/time/rate** (<https://golang.org/x/time/rate>) Standard library rate limiter. Token bucket algorithm, well-maintained.

## Concurrency & Goroutines

**Watermill** (<https://github.com/ThreeDotsLabs/watermill>) Event-driven framework: message streams, event sourcing, CQRS patterns.

**ro** (<https://github.com/samber/ro>) Reactive programming. Event-driven streams with operators transforming data flow.

## Messaging

**franz-go** (<https://github.com/twmb/franz-go>) Modern, high-performance, feature-complete Kafka client. Excellent docs and community support.

**amqp091-go** (<https://github.com/rabbitmq/amqp091-go>) Official RabbitMQ client, maintained by RabbitMQ team. Supports AMQP 0.9.1 protocol.

**NATS.go** (<https://github.com/nats-io/nats.go>) NATS messaging client. Simple, secure, performant.

**Temporal Go SDK** (<https://github.com/temporalio/sdk-go>) Durable execution framework for reliable async apps: workflows, activities, long-running processes.

**DBOS** (<https://github.com/dbos-inc/dbos-transact-golang>) Durable-execution backend framework for Go apps, built on PostgreSQL.

## Types and Data Structures

**gods** (<https://github.com/emirpasic/gods>) Go Data Structures: Sets, Lists, Stacks, Maps, Trees, Queues, much more

**bloom** (<https://github.com/bits-and-blooms/bloom>) Bloom filter. Memory-efficient set membership testing.

**hyperloglog** (<https://github.com/clarkduvall/hyperloglog>) HyperLogLog. Memory-efficient cardinality estimation for large datasets.

**Carbon** (<https://github.com/uniplaces/carbon>) Simple, semantic time library: parsing, formatting, manipulation.

**google/uuid** (<https://github.com/google/uuid>) Generates and parses UUIDs. Official Google library, RFC 4122 compliant. For new Go 1.27+ code, check stdlib `uuid` package first. This library still has broader RFC-variant coverage (v3/v5 namespaced UUIDs).

## Database Schema Migration

**golang-migrate** (<https://github.com/golang-migrate/migrate>) Database migration tool. Multiple databases, schema version control.

**goose** (<https://github.com/pressly/goose>) Database migration tool. SQL or Go migrations, multiple databases.

## WebSockets

**gorilla/websocket** (<https://github.com/gorilla/websocket>) Mature, widely used WebSocket package, part of Gorilla toolkit.

## gRPC

**grpc-go** (<https://github.com/grpc/grpc-go>) Go gRPC implementation. HTTP/2-based RPC framework by Google.

## GraphQL

**gqlgen** (<https://github.com/99designs/gqlgen>) Go generate based graphql server library. Type-safe, schema-first, code generation.

**graphql-go** (<https://github.com/graphql-go/graphql>) GraphQL for Go: query execution, schema parsing.

## File Watching

**fsnotify** (<https://github.com/fsnotify/fsnotify>) Cross-platform, efficient file system watcher.

## Retry Logic

**avast/retry-go** (<https://github.com/avast/retry-go>) Retry with exponential backoff. Simple, configurable.

## Error Handling

**pkg/errors** (<https://github.com/pkg/errors>) Legacy projects only. New code: prefer stdlib `errors`, `fmt.Errorf("%w")`, `errors.Join`. Use structured error library only when you need stack traces or rich context.

**oops** (<https://github.com/samber/oops>) Errors with stack traces, hints, context. Rich wrapping, type-safe error chains.

## Metrics & Monitoring

**prometheus/client_golang** (<https://github.com/prometheus/client_golang>) Prometheus instrumentation: metrics, histograms, counters, gauges.

**opentelemetry-go** (<https://github.com/open-telemetry/opentelemetry-go>) OpenTelemetry Go API and SDK: distributed tracing, metrics, logs.

## API Documentation

**swag** (<https://github.com/swaggo/swag>) Auto-generates OpenAPI/Swagger specs (`swagger.json`/`swagger.yaml`) from comment annotations (`@Summary`, `@Param`, `@Success`, `@Router`, etc.) on handler functions. Integrates with Gin (`gin-swagger`), Echo (`echo-swagger`), Fiber (`fiber-swagger`), Chi, net/http. Outputs Swagger 2.0 and OpenAPI 3.x.

## Dependency Injection

**do** (<https://github.com/samber/do>) Simple runtime dependency injection: service locator pattern, health checks.

**Wire** (<https://github.com/google/wire>) Code-generated, compile-time dependency injection without reflection.

**Dig** (<https://github.com/uber-go/dig>) Runtime dependency injection container with lifecycle management.

**Fx** (<https://github.com/uber-go/fx>) Application framework built on Dig: lifecycle management, dependency injection, observability.

## Functional Programming & Utilities

**lo** (<https://github.com/samber/lo>) Generics-based helpers: slice, map, tuple operations in functional style.

**mo** (<https://github.com/samber/mo>) Monads and functional helpers: Option, Either, Try, other functional patterns.

## Excel & Spreadsheet

**Excelize** (<https://github.com/qax-os/excelize>) Reads and writes Excel files (XLSX). Formatting, charts, complex spreadsheet operations.
