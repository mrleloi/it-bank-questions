# """WebSocket endpoints for real-time features."""
#
# from typing import Dict, Set
# from uuid import UUID
# import json
#
# from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
# from fastapi.websockets import WebSocketState
#
# from interfaces.api.dependencies import get_config
#
#
# class ConnectionManager:
#     """WebSocket connection manager."""
#
#     def __init__(self):
#         self.active_connections: Dict[UUID, Set[WebSocket]] = {}
#
#     async def connect(self, websocket: WebSocket, user_id: UUID):
#         """Accept and track connection."""
#         await websocket.accept()
#
#         if user_id not in self.active_connections:
#             self.active_connections[user_id] = set()
#
#         self.active_connections[user_id].add(websocket)
#
#     def disconnect(self, websocket: WebSocket, user_id: UUID):
#         """Remove connection."""
#         if user_id in self.active_connections:
#             self.active_connections[user_id].discard(websocket)
#
#             if not self.active_connections[user_id]:
#                 del self.active_connections[user_id]
#
#     async def send_personal_message(self, message: dict, user_id: UUID):
#         """Send message to specific user."""
#         if user_id in self.active_connections:
#             for connection in self.active_connections[user_id]:
#                 if connection.client_state == WebSocketState.CONNECTED:
#                     await connection.send_json(message)
#
#     async def broadcast(self, message: dict):
#         """Broadcast message to all connections."""
#         for connections in self.active_connections.values():
#             for connection in connections:
#                 if connection.client_state == WebSocketState.CONNECTED:
#                     await connection.send_json(message)
#
#
# manager = ConnectionManager()
#
#
# async def get_ws_user_id(
#         token: str = Query(...),
#         config=Depends(get_config)
# ) -> UUID:
#     """Verify WebSocket token and get user ID."""
#     import jwt
#
#     try:
#         payload = jwt.decode(
#             token,
#             config.auth.secret_key,
#             algorithms=[config.auth.algorithm]
#         )
#         return UUID(payload.get("sub"))
#     except Exception:
#         raise WebSocketDisconnect(code=4001, reason="Invalid token")
#
#
# @router.websocket("/ws")
# async def websocket_endpoint(
#         websocket: WebSocket,
#         user_id: UUID = Depends(get_ws_user_id)
# ):
#     """WebSocket endpoint for real-time updates."""
#     await manager.connect(websocket, user_id)
#
#     try:
#         while True:
#             # Receive message from client
#             data = await websocket.receive_json()
#
#             # Handle different message types
#             message_type = data.get("type")
#
#             if message_type == "ping":
#                 await websocket.send_json({"type": "pong"})
#
#             elif message_type == "subscribe":
#                 # Subscribe to specific events
#                 events = data.get("events", [])
#                 # Implementation for event subscription
#
#             elif message_type == "learning_update":
#                 # Real-time learning updates
#                 # Implementation for learning updates
#                 pass
#
#     except WebSocketDisconnect:
#         manager.disconnect(websocket, user_id)