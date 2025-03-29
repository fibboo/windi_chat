import asyncio

from cachetools import LFUCache
from starlette.websockets import WebSocket, WebSocketDisconnect
from websockets import ConnectionClosedOK

from app.configs.logging_settings import get_logger
from app.schemas.message import Message

logger = get_logger(__name__)


class WebsocketManager:
    def __init__(self, max_connections: int = 1000):
        self.connections = LFUCache(maxsize=max_connections)
        self.chat_index: dict[int, set[tuple[int, str]]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int, device_id: str) -> None:
        await websocket.accept()
        key: tuple = (chat_id, user_id, device_id)
        self.connections[key] = websocket

        if chat_id not in self.chat_index:
            self.chat_index[chat_id] = set()
        self.chat_index[chat_id].add((user_id, device_id))

        logger.debug(f'User `{user_id}` connected to chat_id `{chat_id}` from device `{device_id}`')

    def disconnect(self, chat_id: int, user_id: int, device_id: str) -> None:
        key: tuple = (chat_id, user_id, device_id)
        websocket: WebSocket | None = self.connections.pop(key, None)
        if websocket is not None:
            logger.debug(f'User `{user_id}` with device `{device_id}` disconnected from chat_id `{chat_id}`')

        if chat_id in self.chat_index:
            self.chat_index[chat_id].discard((user_id, device_id))
            if len(self.chat_index[chat_id]) == 0:
                self.chat_index.pop(chat_id)

    @staticmethod
    async def _send(message: Message, websocket: WebSocket) -> bool:
        try:
            await websocket.send_json(message.model_dump(mode='json'))
            return True

        except (ConnectionClosedOK, RuntimeError, WebSocketDisconnect):
            return False

    async def send_message(self, message: Message, chat_id: int, chat_user_ids: set[int], device_id: str) -> None:
        keys: set[tuple[int, str]] = self.chat_index.get(chat_id, set())
        tasks: list[tuple] = []
        keys_to_remove: list[tuple] = []

        for connection_user_id, connection_device_id in keys:
            if connection_user_id in chat_user_ids and connection_device_id != device_id:
                key: tuple = (chat_id, connection_user_id, connection_device_id)
                websocket: WebSocket | None = self.connections.get(key, None)
                if websocket is not None:
                    tasks.append((key, websocket, self._send(message=message, websocket=websocket)))

        if len(tasks) > 0:
            results = await asyncio.gather(*(task for _, _, task in tasks))
            for (key, _, _), success in zip(tasks, results):
                if not success:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            chat_id_key, connection_user_id, connection_device_id = key
            self.disconnect(chat_id=chat_id_key, user_id=connection_user_id, device_id=connection_device_id)


websocket_manager = WebsocketManager(max_connections=1000)
