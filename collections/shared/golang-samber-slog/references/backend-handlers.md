# Backend Handlers

All implement `slog.Handler`; constructor pattern `Option{}.NewXxxHandler()`.

## Table of Contents

- [Common Option Fields](#common-option-fields)
- [Cloud Backends](#cloud-backends)
  - [Datadog — `slog-datadog`](#datadog--slog-datadog)
  - [Sentry — `slog-sentry`](#sentry--slog-sentry)
  - [Loki — `slog-loki`](#loki--slog-loki)
  - [Graylog — `slog-graylog`](#graylog--slog-graylog)
- [Messaging Backends](#messaging-backends)
  - [Kafka — `slog-kafka`](#kafka--slog-kafka)
  - [Fluentd — `slog-fluentd`](#fluentd--slog-fluentd)
  - [Logstash — `slog-logstash`](#logstash--slog-logstash)
- [Notification Backends](#notification-backends)
  - [Slack — `slog-slack`](#slack--slog-slack)
  - [Telegram — `slog-telegram`](#telegram--slog-telegram)
  - [Webhook — `slog-webhook`](#webhook--slog-webhook)
- [Storage Backends](#storage-backends)
  - [Parquet — `slog-parquet`](#parquet--slog-parquet)
- [Logging Bridges](#logging-bridges)
  - [slog-zap](#slog-zap)
  - [slog-zerolog](#slog-zerolog)
  - [slog-logrus](#slog-logrus)
- [Graceful Shutdown Checklist](#graceful-shutdown-checklist)

## Common Option Fields

Every `Option` struct includes:

| Field | Purpose |
| --- | --- |
| `Level` | Minimum log level (default: `slog.LevelDebug`) |
| `AddSource` | Include source file/line in output |
| `ReplaceAttr` | Callback modifying attributes before emission |
| `Converter` | Custom payload builder for target format |
| `AttrFromContext` | Slice of functions extracting attributes from `context.Context` |

## Cloud Backends

### Datadog — `slog-datadog`

```go
import slogdatadog "github.com/samber/slog-datadog/v2"

handler := slogdatadog.Option{
    Level: slog.LevelInfo,
    // Service, Source, Hostname, Tags configured via Datadog client
}.NewDatadogHandler()
defer handler.(interface{ Stop(context.Context) error }).Stop(context.Background()) // REQUIRED: flush buffered logs
```

**Batch mode** default: logs buffered, sent periodically (default 5s):

- Call `Stop(ctx)` on shutdown, or buffered logs are lost.
- `Flush(ctx)` flushes mid-lifecycle.
- Synchronous delivery: check Option configuration.

### Sentry — `slog-sentry`

```go
import slogsentry "github.com/samber/slog-sentry/v2"

handler := slogsentry.Option{
    Level:   slog.LevelWarn,
    Hub:     sentry.CurrentHub(),
    AddSource: true,
}.NewSentryHandler()

// Flush on shutdown
defer sentry.Flush(2 * time.Second)
```

**Recognized attributes:** `error` (any error type), `request` (\*http.Request), `dist`, `environment`, `release`, `server_name`, `transaction`. `slog.Group("tags", ...)` for Sentry tags, `slog.Group("user", ...)` for user context.

**Error keys:** global `ErrorKeys = []string{"error", "err"}`; attributes with these keys treated as error objects.

### Loki — `slog-loki`

```go
import slogloki "github.com/samber/slog-loki/v3"

lokiClient, _ := loki.New(lokiCfg)
defer lokiClient.Stop() // REQUIRED: flush buffered logs

handler := slogloki.Option{
    Level:  slog.LevelDebug,
    Client: lokiClient,
}.NewLokiHandler()
```

**Labels vs metadata:** attributes go as Loki labels by default. High-cardinality data (request IDs, trace IDs): set `HandleRecordsWithMetadata: true` to send structured metadata instead. Avoids label explosion that degrades Loki performance.

### Graylog — `slog-graylog`

```go
import sloggraylog "github.com/samber/slog-graylog/v2"

gelfWriter, _ := gelf.NewWriter("localhost:12201")
handler := sloggraylog.Option{
    Level:  slog.LevelDebug,
    Writer: gelfWriter,
}.NewGraylogHandler()
```

GELF (Graylog Extended Log Format) over UDP.

## Messaging Backends

### Kafka — `slog-kafka`

```go
import slogkafka "github.com/samber/slog-kafka/v2"

writer := &kafka.Writer{
    Addr:  kafka.TCP("localhost:9092"),
    Topic: "logs",
    Async: true, // non-blocking writes
}
handler := slogkafka.Option{
    Level:       slog.LevelDebug,
    KafkaWriter: writer,
    Timeout:     60 * time.Second,
}.NewKafkaHandler()
defer writer.Close() // REQUIRED: flush pending messages
```

### Fluentd — `slog-fluentd`

```go
import slogfluentd "github.com/samber/slog-fluentd/v2"

client, _ := fluent.New(fluent.Config{
    FluentHost: "localhost", FluentPort: 24224,
})
handler := slogfluentd.Option{
    Level:  slog.LevelDebug,
    Client: client,
    Tag:    "api",
}.NewFluentdHandler()
defer client.Close()
```

### Logstash — `slog-logstash`

```go
import sloglogstash "github.com/samber/slog-logstash/v2"

conn, _ := net.Dial("tcp", "localhost:9999")
handler := sloglogstash.Option{
    Level: slog.LevelDebug,
    Conn:  conn,
}.NewLogstashHandler()
defer conn.Close()
```

Output: JSON with `@timestamp`, `level`, `message`, `error`, `extra` fields.

## Notification Backends

Webhook URLs and bot tokens are secrets: load from env or secret store; never hardcode, commit or log them.

### Slack — `slog-slack`

```go
import slogslack "github.com/samber/slog-slack/v2"

// Via webhook
handler := slogslack.Option{
    Level:      slog.LevelError,
    WebhookURL: os.Getenv("SLACK_WEBHOOK_URL"),
    Channel:    "alerts",
}.NewSlackHandler()

// Via bot token
handler := slogslack.Option{
    Level:    slog.LevelError,
    BotToken: os.Getenv("SLACK_BOT_TOKEN"),
    Channel:  "alerts",
}.NewSlackHandler()
```

### Telegram — `slog-telegram`

```go
import slogtelegram "github.com/samber/slog-telegram/v2"

handler := slogtelegram.Option{
    Level:    slog.LevelError,
    Token:    os.Getenv("TELEGRAM_BOT_TOKEN"),
    Username: "@your-channel",
}.NewTelegramHandler()
```

### Webhook — `slog-webhook`

```go
import slogwebhook "github.com/samber/slog-webhook/v2"

handler := slogwebhook.Option{
    Level:    slog.LevelError,
    Endpoint: os.Getenv("LOG_WEBHOOK_URL"),
    Timeout:  10 * time.Second,
}.NewWebhookHandler()
```

## Storage Backends

### Parquet — `slog-parquet`

```go
import slogparquet "github.com/samber/slog-parquet/v2"

buffer := slogparquet.NewParquetBuffer(bucket, "logs/", 10000, 5*time.Minute)
defer buffer.Flush(true) // REQUIRED: flush remaining records synchronously

handler := slogparquet.Option{
    Level:  slog.LevelDebug,
    Buffer: buffer,
}.NewParquetHandler()
```

Uses Thanos `objstore.Bucket` for cloud storage (S3, GCS, Azure). Buffers records; writes Parquet file when `maxRecords` or `maxInterval` is reached.

## Logging Bridges

Bridge `slog.Handler` to legacy logging frameworks, for incremental migration from Zap/Zerolog/Logrus to slog.

### slog-zap

```go
import slogzap "github.com/samber/slog-zap/v2"

zapLogger, _ := zap.NewProduction()
handler := slogzap.Option{
    Level:  slog.LevelDebug,
    Logger: zapLogger,
}.NewZapHandler()
slog.SetDefault(slog.New(handler))
// Now all slog.Info() calls route through Zap
```

### slog-zerolog

```go
import slogzerolog "github.com/samber/slog-zerolog/v2"

zerologLogger := zerolog.New(zerolog.ConsoleWriter{Out: os.Stderr})
handler := slogzerolog.Option{
    Level:  slog.LevelDebug,
    Logger: &zerologLogger,
}.NewZerologHandler()
```

### slog-logrus

```go
import sloglogrus "github.com/samber/slog-logrus/v2"

handler := sloglogrus.Option{
    Level:  slog.LevelDebug,
    Logger: logrus.StandardLogger(),
}.NewLogrusHandler()
```

## Graceful Shutdown Checklist

Handlers buffering records internally; each MUST close on shutdown:

| Handler | Shutdown method | What happens without it |
| --- | --- | --- |
| `slog-datadog` | `handler.Stop(ctx)` | Buffered logs lost (default 5s batch) |
| `slog-loki` | `lokiClient.Stop()` | Pending push requests dropped |
| `slog-kafka` | `writer.Close()` | Pending messages never sent |
| `slog-parquet` | `buffer.Flush(true)` | Partial Parquet file not flushed to storage |

Non-batched handlers (Sentry, Slack, Telegram, Webhook) send synchronously; no close required. `sentry.Flush(timeout)` still recommended.

```go
// Production shutdown pattern
func main() {
    lokiClient, _ := loki.New(lokiCfg)
    defer lokiClient.Stop() // flush buffered logs

    lokiHandler := slogloki.Option{
        Level: slog.LevelDebug, Client: lokiClient,
    }.NewLokiHandler()

    // Use signal handling for graceful shutdown
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
    defer stop()

    // ... start server ...
    <-ctx.Done()
    // deferred Stop() runs here, flushing buffered logs
}
```
