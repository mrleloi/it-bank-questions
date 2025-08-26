class RequestIdMiddleware:
    """Middleware to add a unique request ID to each request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            import uuid
            request_id = str(uuid.uuid4())
            scope['headers'].append((b'x-request-id', request_id.encode()))
        await self.app(scope, receive, send)
