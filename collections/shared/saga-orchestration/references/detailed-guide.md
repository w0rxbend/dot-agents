# Saga Orchestration - Detailed Guide


Code templates for the patterns summarized in `../SKILL.md`. The Python is illustrative (in-memory store and publisher interfaces); adapt persistence, messaging and error types to the target stack.


## Core Concepts

### 1. Saga Types

```
Choreography                    Orchestration
┌─────┐  ┌─────┐  ┌─────┐     ┌─────────────┐
│Svc A│─►│Svc B│─►│Svc C│     │ Orchestrator│
└─────┘  └─────┘  └─────┘     └──────┬──────┘
   │        │        │               │
   ▼        ▼        ▼         ┌─────┼─────┐
 Event    Event    Event       ▼     ▼     ▼
                            ┌────┐┌────┐┌────┐
                            │Svc1││Svc2││Svc3│
                            └────┘└────┘└────┘
```

### 2. Saga Execution States

| State            | Description                    |
| ---------------- | ------------------------------ |
| **Started**      | Saga initiated                 |
| **Pending**      | Waiting for step completion    |
| **Compensating** | Rolling back due to failure    |
| **Completed**    | All steps succeeded            |
| **Failed**       | Saga failed after compensation |


## Templates

### Template 1: Saga Orchestrator Base

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import UTC, datetime
import uuid


def utcnow() -> datetime:
    return datetime.now(UTC)  # datetime.utcnow() is deprecated since 3.12


class SagaState(Enum):
    STARTED = "started"
    PENDING = "pending"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SagaStep:
    name: str
    action: str
    compensation: str | None  # None for pivot/retriable steps (no compensation)
    status: str = "pending"
    result: dict | None = None
    error: str | None = None
    executed_at: datetime | None = None
    compensated_at: datetime | None = None
    timeout_at: datetime | None = None


@dataclass
class Saga:
    saga_id: str
    saga_type: str
    state: SagaState
    data: dict[str, Any]
    steps: list[SagaStep]
    current_step: int = 0
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class OutboxMessage:
    topic: str
    payload: dict


class SagaOrchestrator(ABC):
    """Base class for saga orchestrators.

    `saga_store.save(saga, outbox=[...])` must persist the saga row AND the
    outbox rows in ONE local database transaction. A separate relay (poller or
    CDC such as Debezium) publishes outbox rows to the broker. The orchestrator
    never calls the broker directly, so a crash can't lose or orphan a command.
    """

    def __init__(self, saga_store):
        self.saga_store = saga_store

    @abstractmethod
    def define_steps(self, data: dict) -> list[SagaStep]:
        """Define the saga steps."""

    @property
    @abstractmethod
    def saga_type(self) -> str:
        """Unique saga type identifier."""

    async def start(self, data: dict) -> Saga:
        """Start a new saga."""
        saga = Saga(
            saga_id=str(uuid.uuid4()),
            saga_type=self.saga_type,
            state=SagaState.STARTED,
            data=data,
            steps=self.define_steps(data),
        )
        await self.saga_store.save(saga, outbox=self._next_step_messages(saga))
        return saga

    async def handle_step_completed(self, saga_id: str, step_name: str, result: dict):
        """Handle successful step completion (idempotent: duplicates are ignored)."""
        saga = await self.saga_store.get(saga_id)
        step = saga.steps[saga.current_step] if saga.current_step < len(saga.steps) else None
        if saga.state not in (SagaState.STARTED, SagaState.PENDING) or step is None \
                or step.name != step_name or step.status != "executing":
            return  # duplicate or late message

        step.status = "completed"
        step.result = result
        step.executed_at = utcnow()
        saga.current_step += 1
        saga.updated_at = utcnow()

        if saga.current_step >= len(saga.steps):
            saga.state = SagaState.COMPLETED
            outbox = [OutboxMessage(f"{self.saga_type}Completed",
                                    {"saga_id": saga.saga_id, **saga.data})]
        else:
            saga.state = SagaState.PENDING
            outbox = self._next_step_messages(saga)
        await self.saga_store.save(saga, outbox=outbox)

    async def handle_step_failed(self, saga_id: str, step_name: str, error: str):
        """Handle step failure - start compensating completed steps, newest first."""
        saga = await self.saga_store.get(saga_id)
        step = next(s for s in saga.steps if s.name == step_name)
        if step.status != "executing":
            return  # duplicate or late message

        step.status = "failed"
        step.error = error
        saga.state = SagaState.COMPENSATING
        saga.updated_at = utcnow()
        await self.saga_store.save(saga, outbox=self._next_compensation_messages(saga))

    async def handle_compensation_completed(self, saga_id: str, step_name: str):
        """One compensation finished - trigger the next one in reverse order."""
        saga = await self.saga_store.get(saga_id)
        step = next(s for s in saga.steps if s.name == step_name)
        if step.status != "compensating":
            return  # duplicate or late message

        step.status = "compensated"
        step.compensated_at = utcnow()
        saga.updated_at = utcnow()
        await self.saga_store.save(saga, outbox=self._next_compensation_messages(saga))

    def _next_step_messages(self, saga: Saga) -> list[OutboxMessage]:
        """Mark the next step executing and return its command."""
        step = saga.steps[saga.current_step]
        step.status = "executing"
        return [OutboxMessage(step.action,
                              {"saga_id": saga.saga_id, "step_name": step.name, **saga.data})]

    def _next_compensation_messages(self, saga: Saga) -> list[OutboxMessage]:
        """Compensate ONE step: the most recently completed one.

        The next compensation is only sent after this one reports completion,
        so compensations run strictly in reverse order.
        """
        for step in reversed(saga.steps[: saga.current_step]):
            if step.status == "completed" and step.compensation:
                step.status = "compensating"
                return [OutboxMessage(step.compensation, {
                    "saga_id": saga.saga_id,
                    "step_name": step.name,
                    "original_result": step.result,
                    **saga.data,
                })]
        # Nothing left to compensate
        saga.state = SagaState.FAILED
        return [OutboxMessage(f"{self.saga_type}Failed",
                              {"saga_id": saga.saga_id, "error": "Saga failed", **saga.data})]
```

### Template 2: Order Fulfillment Saga

```python
class OrderFulfillmentSaga(SagaOrchestrator):
    """Orchestrates order fulfillment across services."""

    @property
    def saga_type(self) -> str:
        return "OrderFulfillment"

    def define_steps(self, data: Dict) -> List[SagaStep]:
        return [
            SagaStep(
                name="reserve_inventory",
                action="InventoryService.ReserveItems",
                compensation="InventoryService.ReleaseReservation"
            ),
            SagaStep(
                name="process_payment",
                action="PaymentService.ProcessPayment",
                compensation="PaymentService.RefundPayment"
            ),
            SagaStep(
                name="create_shipment",
                action="ShippingService.CreateShipment",
                compensation="ShippingService.CancelShipment"
            ),
            SagaStep(
                name="send_confirmation",
                action="NotificationService.SendOrderConfirmation",
                compensation=None,  # retriable step after the pivot: retry, never compensate
            )
        ]


# Usage
async def create_order(order_data: Dict):
    saga = OrderFulfillmentSaga(saga_store)
    return await saga.start({
        "order_id": order_data["order_id"],
        "customer_id": order_data["customer_id"],
        "items": order_data["items"],
        "payment_method": order_data["payment_method"],
        "shipping_address": order_data["shipping_address"]
    })


# Event handlers in each service. Each handler should apply its effect, record
# the command's message id in an inbox/dedup table, and write the reply to its
# own outbox in ONE local transaction; `publish` below stands for that outbox write.
class InventoryService:
    async def handle_reserve_items(self, command: Dict):
        try:
            # Reserve inventory
            reservation = await self.reserve(
                command["items"],
                command["order_id"]
            )
            # Report success
            await self.event_publisher.publish(
                "SagaStepCompleted",
                {
                    "saga_id": command["saga_id"],
                    "step_name": "reserve_inventory",
                    "result": {"reservation_id": reservation.id}
                }
            )
        except InsufficientInventoryError as e:
            await self.event_publisher.publish(
                "SagaStepFailed",
                {
                    "saga_id": command["saga_id"],
                    "step_name": "reserve_inventory",
                    "error": str(e)
                }
            )

    async def handle_release_reservation(self, command: Dict):
        # Compensating action
        await self.release_reservation(
            command["original_result"]["reservation_id"]
        )
        await self.event_publisher.publish(
            "SagaCompensationCompleted",
            {
                "saga_id": command["saga_id"],
                "step_name": "reserve_inventory"
            }
        )
```

### Template 3: Choreography-Based Saga

```python
from dataclasses import dataclass
from typing import Dict, Any
import asyncio

@dataclass
class SagaContext:
    """Passed through choreographed saga events."""
    saga_id: str
    step: int
    data: Dict[str, Any]
    completed_steps: list


class OrderChoreographySaga:
    """Choreography-based saga using events."""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._register_handlers()

    def _register_handlers(self):
        self.event_bus.subscribe("OrderCreated", self._on_order_created)
        self.event_bus.subscribe("InventoryReserved", self._on_inventory_reserved)
        self.event_bus.subscribe("PaymentProcessed", self._on_payment_processed)
        self.event_bus.subscribe("ShipmentCreated", self._on_shipment_created)

        # Compensation handlers
        self.event_bus.subscribe("PaymentFailed", self._on_payment_failed)
        self.event_bus.subscribe("ShipmentFailed", self._on_shipment_failed)

    async def _on_order_created(self, event: Dict):
        """Step 1: Order created, reserve inventory."""
        await self.event_bus.publish("ReserveInventory", {
            "saga_id": event["order_id"],
            "order_id": event["order_id"],
            "items": event["items"]
        })

    async def _on_inventory_reserved(self, event: Dict):
        """Step 2: Inventory reserved, process payment."""
        await self.event_bus.publish("ProcessPayment", {
            "saga_id": event["saga_id"],
            "order_id": event["order_id"],
            "amount": event["total_amount"],
            "reservation_id": event["reservation_id"]
        })

    async def _on_payment_processed(self, event: Dict):
        """Step 3: Payment done, create shipment."""
        await self.event_bus.publish("CreateShipment", {
            "saga_id": event["saga_id"],
            "order_id": event["order_id"],
            "payment_id": event["payment_id"]
        })

    async def _on_shipment_created(self, event: Dict):
        """Step 4: Complete - send confirmation."""
        await self.event_bus.publish("OrderFulfilled", {
            "saga_id": event["saga_id"],
            "order_id": event["order_id"],
            "tracking_number": event["tracking_number"]
        })

    # Compensation handlers
    async def _on_payment_failed(self, event: Dict):
        """Payment failed - release inventory."""
        await self.event_bus.publish("ReleaseInventory", {
            "saga_id": event["saga_id"],
            "reservation_id": event["reservation_id"]
        })
        await self.event_bus.publish("OrderFailed", {
            "order_id": event["order_id"],
            "reason": "Payment failed"
        })

    async def _on_shipment_failed(self, event: Dict):
        """Shipment failed - refund payment and release inventory."""
        await self.event_bus.publish("RefundPayment", {
            "saga_id": event["saga_id"],
            "payment_id": event["payment_id"]
        })
        await self.event_bus.publish("ReleaseInventory", {
            "saga_id": event["saga_id"],
            "reservation_id": event["reservation_id"]
        })
```

### Template 4: Saga with Timeouts

```python
from datetime import timedelta


class TimeoutSagaOrchestrator(SagaOrchestrator):
    """Saga orchestrator with step timeouts.

    The timeout request goes into the same outbox transaction as the step
    command; a scheduler consumes `ScheduleSagaTimeout` and later calls
    `check_timeout`.
    """

    step_timeout = timedelta(minutes=5)

    def _next_step_messages(self, saga: Saga) -> list[OutboxMessage]:
        messages = super()._next_step_messages(saga)
        step = saga.steps[saga.current_step]
        step.timeout_at = utcnow() + self.step_timeout
        messages.append(OutboxMessage("ScheduleSagaTimeout", {
            "saga_id": saga.saga_id,
            "step_name": step.name,
            "run_at": step.timeout_at.isoformat(),
        }))
        return messages

    async def check_timeout(self, saga_id: str, step_name: str):
        """Called by the scheduler at run_at; a no-op if the step already finished."""
        saga = await self.saga_store.get(saga_id)
        step = next(s for s in saga.steps if s.name == step_name)
        if step.status == "executing":
            # Step timed out - fail it (handle_step_failed ignores late duplicates)
            await self.handle_step_failed(saga_id, step_name, "Step timed out")
```


## Durable Execution Alternative

The templates above build saga infrastructure from scratch — saga stores, event publishers, compensation tracking. **Durable execution frameworks** (Temporal, AWS Step Functions, Azure Durable Functions, DBOS, Restate and similar) eliminate much of this boilerplate: the workflow runtime automatically persists state to a database, retries failed steps, and resumes from the last checkpoint after crashes. Instead of building a `SagaOrchestrator` base class, you write a workflow function with steps — the framework handles persistence, crash recovery and deterministic replay of the workflow logic. Individual steps (activities) are still retried at-least-once, so they must stay idempotent. Consider durable execution when you want saga-like reliability without managing the coordination infrastructure yourself.


## Best Practices

### Do's

- **Make steps idempotent** - Safe to retry
- **Design compensations carefully** - They must work
- **Use correlation IDs** - For tracing across services
- **Implement timeouts** - Don't wait forever
- **Log everything** - For debugging failures

### Don'ts

- **Don't assume instant completion** - Sagas take time
- **Don't skip compensation testing** - Most critical part
- **Don't couple services** - Use async messaging
- **Don't ignore partial failures** - Handle gracefully


## Related Skills

Works well with: `using-message-queues` (brokers, Temporal example), `architecture-patterns` (domain events, outbox).


## Resources

- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Designing Data-Intensive Applications](https://dataintensive.net/)
