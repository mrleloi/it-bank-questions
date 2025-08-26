class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            headers = dict(scope['headers'])
            token = headers.get(b'authorization')
            if not token or token != b'Bearer mysecrettoken':
                response = {
                    'status': 401,
                    'body': b'Unauthorized',
                    'headers': [(b'content-type', b'text/plain')]
                }
                await send({
                    'type': 'http.response.start',
                    'status': response['status'],
                    'headers': response['headers']
                })
                await send({
                    'type': 'http.response.body',
                    'body': response['body']
                })
                return
        await self.app(scope, receive, send)
