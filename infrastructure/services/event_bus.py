"""Event bus implementation."""

import logging
from typing import List, Dict, Any, Callable, Optional
from collections import defaultdict
import asyncio

from domain.events import DomainEvent
from application.services import EventBus

logger = logging.getLogger(__name__)


class DjangoEventBus(EventBus):
    """Django implementation of EventBus with async support."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._middleware: List[Callable] = []

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to event {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe handler from event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed handler {handler.__name__} from event {event_type}")

    def add_middleware(self, middleware: Callable):
        """Add middleware to process events."""
        self._middleware.append(middleware)

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event."""
        try:
            # Apply middleware
            for middleware in self._middleware:
                event = await self._apply_middleware(middleware, event)
                if event is None:
                    logger.info(f"Event {event.__class__.__name__} blocked by middleware")
                    return

            # Get event type
            event_type = event.__class__.__name__

            # Log event
            logger.info(f"Publishing event: {event_type}")

            # Get handlers for this event type
            handlers = self._handlers.get(event_type, [])
            
            if not handlers:
                logger.debug(f"No handlers registered for event {event_type}")
                return

            # Execute handlers concurrently
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._execute_handler(handler, event))
                tasks.append(task)

            # Wait for all handlers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log handler results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Handler {handlers[i].__name__} failed for event {event_type}: {result}",
                        exc_info=result
                    )
                else:
                    logger.debug(f"Handler {handlers[i].__name__} completed for event {event_type}")

        except Exception as e:
            logger.error(f"Failed to publish event {event.__class__.__name__}: {e}", exc_info=True)
            raise

    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        try:
            logger.info(f"Publishing batch of {len(events)} events")
            
            # Publish all events concurrently
            tasks = [self.publish(event) for event in events]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"Completed publishing batch of {len(events)} events")

        except Exception as e:
            logger.error(f"Failed to publish event batch: {e}", exc_info=True)
            raise

    async def _apply_middleware(self, middleware: Callable, event: DomainEvent) -> Optional[DomainEvent]:
        """Apply middleware to event."""
        try:
            if asyncio.iscoroutinefunction(middleware):
                return await middleware(event)
            else:
                return middleware(event)
        except Exception as e:
            logger.error(f"Middleware {middleware.__name__} failed: {e}", exc_info=True)
            return event  # Continue with original event on middleware failure

    async def _execute_handler(self, handler: Callable, event: DomainEvent) -> Any:
        """Execute event handler safely."""
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(event)
            else:
                # Run sync handler in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, handler, event)
        except Exception as e:
            logger.error(f"Event handler {handler.__name__} failed: {e}", exc_info=True)
            raise


class CeleryEventBus(EventBus):
    """Celery-based event bus for distributed processing."""

    def __init__(self):
        self._local_handlers: Dict[str, List[Callable]] = defaultdict(list)

    async def publish(self, event: DomainEvent) -> None:
        """Publish event via Celery."""
        try:
            from infrastructure.celery.tasks.event_tasks import process_domain_event
            
            # Serialize event data
            event_data = {
                'event_type': event.__class__.__name__,
                'event_id': str(getattr(event, 'event_id', 'unknown')),
                'aggregate_id': str(getattr(event, 'aggregate_id', 'unknown')),
                'data': event.to_dict() if hasattr(event, 'to_dict') else {},
                'occurred_at': event.occurred_at.isoformat() if hasattr(event, 'occurred_at') else None
            }

            # Send to Celery
            process_domain_event.delay(event_data)
            
            logger.info(f"Published event {event.__class__.__name__} to Celery")

        except ImportError:
            logger.warning("Celery not available, falling back to local processing")
            # Fallback to local processing
            await self._process_locally(event)
        except Exception as e:
            logger.error(f"Failed to publish event via Celery: {e}", exc_info=True)
            raise

    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish batch of events via Celery."""
        try:
            from infrastructure.celery.tasks.event_tasks import process_domain_event_batch
            
            # Serialize all events
            events_data = []
            for event in events:
                event_data = {
                    'event_type': event.__class__.__name__,
                    'event_id': str(getattr(event, 'event_id', 'unknown')),
                    'aggregate_id': str(getattr(event, 'aggregate_id', 'unknown')),
                    'data': event.to_dict() if hasattr(event, 'to_dict') else {},
                    'occurred_at': event.occurred_at.isoformat() if hasattr(event, 'occurred_at') else None
                }
                events_data.append(event_data)

            # Send batch to Celery
            process_domain_event_batch.delay(events_data)
            
            logger.info(f"Published batch of {len(events)} events to Celery")

        except ImportError:
            logger.warning("Celery not available, falling back to local processing")
            # Fallback to local processing
            tasks = [self._process_locally(event) for event in events]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Failed to publish event batch via Celery: {e}", exc_info=True)
            raise

    async def _process_locally(self, event: DomainEvent):
        """Process event locally without Celery."""
        event_type = event.__class__.__name__
        handlers = self._local_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Local handler {handler.__name__} failed: {e}", exc_info=True)

    def subscribe_local(self, event_type: str, handler: Callable):
        """Subscribe local handler (for fallback processing)."""
        self._local_handlers[event_type].append(handler)


# Event middleware examples
class LoggingMiddleware:
    """Middleware to log all events."""

    async def __call__(self, event: DomainEvent) -> DomainEvent:
        logger.info(
            f"Event: {event.__class__.__name__} "
            f"AggregateId: {getattr(event, 'aggregate_id', 'N/A')} "
            f"Data: {getattr(event, 'data', {})}"
        )
        return event


class AuditMiddleware:
    """Middleware to create audit trail."""

    def __init__(self, audit_repository):
        self.audit_repository = audit_repository

    async def __call__(self, event: DomainEvent) -> DomainEvent:
        try:
            # Create audit record
            await self.audit_repository.create_audit_record(
                event_type=event.__class__.__name__,
                aggregate_id=getattr(event, 'aggregate_id', None),
                user_id=getattr(event, 'user_id', None),
                data=getattr(event, 'data', {}),
                occurred_at=getattr(event, 'occurred_at', None)
            )
        except Exception as e:
            logger.error(f"Audit middleware failed: {e}")
            # Don't block event processing on audit failure
        
        return event


class FilterMiddleware:
    """Middleware to filter events based on conditions."""

    def __init__(self, filter_func: Callable[[DomainEvent], bool]):
        self.filter_func = filter_func

    async def __call__(self, event: DomainEvent) -> Optional[DomainEvent]:
        if self.filter_func(event):
            return event
        else:
            logger.debug(f"Event {event.__class__.__name__} filtered out")
            return None


def create_event_bus(use_celery: bool = False) -> EventBus:
    """Factory function to create appropriate event bus."""
    if use_celery:
        try:
            return CeleryEventBus()
        except ImportError:
            logger.warning("Celery not available, using Django event bus")
            return DjangoEventBus()
    else:
        return DjangoEventBus()