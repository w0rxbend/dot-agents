---
name: using-message-queues
description: Async communication patterns using message brokers and task queues. Use when building event-driven systems, background job processing, or service decoupling. Covers Kafka (event streaming), RabbitMQ (complex routing), NATS (cloud-native), Redis Streams, Celery (Python), BullMQ (TypeScript), Temporal (workflows), and event sourcing patterns.
---

# Message Queues

Implement asynchronous communication patterns for event-driven architectures, background job processing, and service decoupling.

## When to Use This Skill

Use message queues when:
- **Long-running operations** block HTTP requests (report generation, video processing)
- **Service decoupling** required (microservices, event-driven architecture)
- **Guaranteed delivery** needed (payment processing, order fulfillment)
- **Event streaming** for analytics (log aggregation, metrics pipelines)
- **Workflow orchestration** for complex processes (multi-step sagas, human-in-the-loop)
- **Background job processing** (email sending, image resizing)

## Broker Selection Decision Tree

Choose message broker based on primary need:

### Event Streaming / Log Aggregation
**→ Apache Kafka**
- Throughput: 500K-1M msg/s
- Replay events (event sourcing)
- Exactly-once semantics
- Long-term retention
- Use: Analytics pipelines, CQRS, event sourcing

### Simple Background Jobs
**→ Task Queues**
- **Python** → Celery + Redis
- **TypeScript** → BullMQ + Redis
- **Go** → Asynq + Redis
- Use: Email sending, report generation, webhooks

### Complex Workflows / Sagas
**→ Temporal**
- Durable execution (survives restarts)
- Saga pattern support
- Human-in-the-loop workflows
- Use: Order processing, AI agent orchestration

### Request-Reply / RPC Patterns
**→ NATS**
- Built-in request-reply
- Sub-millisecond latency
- Cloud-native, simple operations
- Use: Microservices RPC, IoT command/control

### Complex Message Routing
**→ RabbitMQ**
- Exchanges (direct, topic, fanout, headers)
- Dead letter exchanges
- Message TTL, priorities
- Use: Multi-consumer patterns, pub/sub

### Already Using Redis
**→ Redis Streams**
- No new infrastructure
- Simple consumer groups
- Moderate throughput (100K+ msg/s)
- Use: Notification queues, simple job queues

## Performance Comparison

| Broker | Throughput | Latency (p99) | Best For |
|--------|-----------|---------------|----------|
| **Kafka** | 500K-1M msg/s | 10-50ms | Event streaming |
| **NATS JetStream** | 200K-400K msg/s | Sub-ms to 5ms | Cloud-native microservices |
| **RabbitMQ** | 50K-100K msg/s | 5-20ms | Task queues, complex routing |
| **Redis Streams** | 100K+ msg/s | Sub-ms | Simple queues, caching |

## Quick Start Examples

### Kafka Producer/Consumer (Python)
See `examples/kafka-python/` for working code.

```python
from confluent_kafka import Producer, Consumer

# Producer
producer = Producer({'bootstrap.servers': 'localhost:9092'})
producer.produce('orders', key='order_123', value='{"status": "created"}')
producer.flush()

# Consumer
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'order-processors',
    'auto.offset.reset': 'earliest'
})
consumer.subscribe(['orders'])

while True:
    msg = consumer.poll(1.0)
    if msg is not None:
        process_order(msg.value())
```

### Celery Background Jobs (Python)
See `examples/celery-image-processing/` for full implementation.

```python
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task(bind=True, max_retries=3)
def process_image(self, image_url: str):
    try:
        result = expensive_image_processing(image_url)
        return result
    except RecoverableError as e:
        raise self.retry(exc=e, countdown=60)
```

### BullMQ Job Processing (TypeScript)
See `examples/bullmq-webhook-processor/` for full implementation.

```typescript
import { Queue, Worker } from 'bullmq'

const queue = new Queue('webhooks', {
  connection: { host: 'localhost', port: 6379 }
})

// Enqueue job
await queue.add('send-webhook', {
  url: 'https://example.com/webhook',
  payload: { event: 'order.created' }
})

// Process jobs
const worker = new Worker('webhooks', async job => {
  await fetch(job.data.url, {
    method: 'POST',
    body: JSON.stringify(job.data.payload)
  })
}, { connection: { host: 'localhost', port: 6379 } })
```

### Temporal Workflow Orchestration
See `examples/temporal-order-saga/` for saga pattern implementation.

```python
from temporalio import workflow, activity
from datetime import timedelta

@workflow.defn
class OrderSagaWorkflow:
    @workflow.run
    async def run(self, order_id: str) -> str:
        # Step 1: Reserve inventory
        inventory_id = await workflow.execute_activity(
            reserve_inventory,
            order_id,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Step 2: Charge payment
        payment_id = await workflow.execute_activity(
            charge_payment,
            order_id,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return f"Order {order_id} completed"
```

## Core Patterns

### Event Naming Convention
Use: `Domain.Entity.Action.Version`

Examples:
- `order.created.v1`
- `user.profile.updated.v2`
- `payment.failed.v1`

### Event Schema Structure
```json
{
  "event_type": "order.created.v2",
  "event_id": "uuid-here",
  "timestamp": "2025-12-02T10:00:00Z",
  "version": "2.0",
  "data": {
    "order_id": "ord_123",
    "customer_id": "cus_456"
  },
  "metadata": {
    "producer": "order-service",
    "trace_id": "abc123",
    "correlation_id": "xyz789"
  }
}
```

### Dead Letter Queue Pattern
Route failed messages to dead letter queue (DLQ) after max retries:

```python
@app.task(bind=True, max_retries=3)
def process_order(self, order_id: str):
    try:
        result = perform_processing(order_id)
        return result
    except UnrecoverableError as e:
        send_to_dlq(order_id, str(e))
        raise Reject(e, requeue=False)
```

### Idempotency (Effectively-Once Processing)
Claim the key atomically *before* doing the work. A `get` followed later by `setex`
is check-then-act: two concurrent duplicates both pass the check and both charge.
```python
import json

@app.post("/process")
async def process_payment(
    payment_data: dict,
    idempotency_key: str = Header(...)
):
    key = f"idempotency:{idempotency_key}"
    # SET NX EX: only one request wins the claim
    if not redis_client.set(key, "in_progress", nx=True, ex=86400):
        state = redis_client.get(key)
        return {"status": "in_progress" if state == b"in_progress" else "already_processed"}

    try:
        result = process_payment_logic(payment_data)
    except Exception:
        redis_client.delete(key)  # release so a retry can run
        raise
    redis_client.set(key, json.dumps(result), ex=86400)
    return {"status": "processed", "result": result}
```
For money movement, also enforce uniqueness in the database or at the payment
provider (its own idempotency key); Redis alone can lose the claim on failover.

## Frontend Integration

### Job Status Updates via SSE
```python
# FastAPI endpoint for real-time job status
@app.get("/status/{task_id}")
async def task_status_stream(task_id: str):
    async def event_generator():
        while True:
            task = celery_app.AsyncResult(task_id)

            if task.state == 'PROGRESS':
                yield {"event": "progress", "data": task.info.get('progress', 0)}
            elif task.state == 'SUCCESS':
                yield {"event": "complete", "data": task.result}
                break
            elif task.state in ('FAILURE', 'REVOKED'):
                yield {"event": "error", "data": str(task.result)}
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())
```

### React Component
```typescript
export function JobStatus({ jobId }: { jobId: string }) {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const eventSource = new EventSource(`/api/status/${jobId}`)

    eventSource.addEventListener('progress', (e) => {
      setProgress(JSON.parse(e.data))
    })

    eventSource.addEventListener('complete', (e) => {
      toast({ title: 'Job complete', description: JSON.parse(e.data) })
      eventSource.close()
    })

    return () => eventSource.close()
  }, [jobId])

  return <ProgressBar value={progress} />
}
```

## Detailed Guides

For comprehensive documentation, see reference files:

### Broker-Specific Guides
- **Kafka**: See `references/kafka.md` for partitioning, consumer groups, exactly-once semantics
- **RabbitMQ**: See `references/rabbitmq.md` for exchanges, bindings, routing patterns
- **NATS**: See `references/nats.md` for JetStream, request-reply patterns
- **Redis Streams**: See `references/redis-streams.md` for consumer groups, acknowledgments

### Task Queue Guides
- **Celery**: See `references/celery.md` for periodic tasks, canvas (workflows), monitoring
- **BullMQ**: See `references/bullmq.md` for job prioritization, flows, Bull Board monitoring
- **Temporal**: See `references/temporal-workflows.md` for saga patterns, signals, queries

### Pattern Guides
- **Event Patterns**: See `references/event-patterns.md` for event sourcing, CQRS, outbox pattern

## Common Anti-Patterns to Avoid

### 1. Synchronous API for Long Operations
```python
# ❌ BAD: Blocks request thread
@app.post("/generate-report")
def generate_report(user_id: str):
    report = expensive_computation(user_id)  # 5 minutes!
    return report

# ✅ GOOD: Enqueue background job
@app.post("/generate-report")
async def generate_report(user_id: str):
    task = generate_report_task.delay(user_id)
    return {"task_id": task.id}
```

### 2. Non-Idempotent Consumers
```python
# ❌ BAD: Processes duplicates
@app.task
def send_email(email: str):
    send_email_service(email)  # Sends twice if retried!

# ✅ GOOD: Idempotent - claim the key atomically before sending
@app.task
def send_email(email: str, idempotency_key: str):
    if not redis.set(f"sent:{idempotency_key}", "1", nx=True, ex=86400):
        return "already_sent"
    try:
        send_email_service(email)
    except Exception:
        redis.delete(f"sent:{idempotency_key}")  # allow the retry to send
        raise
```

### 3. Ignoring Dead Letter Queues
```python
# ❌ BAD: Failed messages lost forever
@app.task(max_retries=3)
def risky_task(data):
    process(data)  # If all retries fail, data disappears

# ✅ GOOD: retry with backoff, then DLQ for manual inspection
@app.task(bind=True, max_retries=3)
def risky_task(self, data):
    try:
        process(data)
    except Exception as e:
        if self.request.retries >= self.max_retries:
            send_to_dlq(data, str(e))
            raise
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

### 4. Using Kafka for Request-Reply
```python
# ❌ BAD: Kafka is not designed for RPC
def get_user_profile(user_id: str):
    kafka_producer.send("user_requests", {"user_id": user_id})
    # How to correlate response? Kafka is asynchronous!

# ✅ GOOD: Use NATS request-reply or HTTP/gRPC
response = await nats.request("user.profile", user_id.encode())
```

## Library Recommendations

- **confluent-kafka (Python):** production Kafka client built on librdkafka
- **Temporal:** workflow orchestration for durable execution

### Installation

**Python:**
```bash
pip install confluent-kafka celery[redis] temporalio aio-pika redis
```

**TypeScript/Node.js:**
```bash
npm install kafkajs bullmq @temporalio/client amqplib ioredis
```

**Rust:**
```bash
cargo add rdkafka lapin async-nats redis
```

**Go:**
```bash
go get github.com/confluentinc/confluent-kafka-go/v2
go get github.com/hibiken/asynq
go get go.temporal.io/sdk
```

## Utilities

Use scripts for setup automation:

- **Kafka setup**: Run `python scripts/kafka_producer_consumer.py` for test utilities
- **Schema validation**: Run `python scripts/validate_message_schema.py` to validate event schemas

## Related Skills

- **designing-apis**: API design for async job submission
- **realtime-sync**: WebSocket/SSE for job status updates
- **feedback**: Toast notifications for job completion
- **databases-***: Persistent storage for event logs
- **observability**: Tracing and metrics for queue operations
