from typing import Any

from fastapi import FastAPI, WebSocket

from .config import settings

app = FastAPI()


class WebSocketsClient:
    def __init__(self) -> None:
        self.sockets: list[WebSocket] = []

    async def connected(self, socket: WebSocket) -> None:
        await socket.accept()
        self.sockets.append(socket)

    async def disconnected(self, socket: WebSocket) -> None:
        self.sockets.remove(socket)

    async def notify_all(self, message: str) -> None:
        for socket in self.sockets:
            await socket.send_text(message)

    async def notify(self, socket: WebSocket, message: str) -> None:
        await socket.send_text(message)

    @property
    def connections(self) -> int:
        return len(self.sockets)


client = WebSocketsClient()


@app.get('/')
def main() -> dict[str, Any]:
    return {'message': 'Okay', 'settings': settings.model_dump()}


@app.websocket('/ws')
async def websocket_api(websocket: WebSocket) -> None:
    await client.connected(websocket)
    try:
        await client.notify_all(
            f'Someone new here. Now us {client.connections}'
        )
        while True:
            await websocket.receive()

    except Exception:
        await client.disconnected(websocket)
        await client.notify_all(f'Someone left us. {client.connections} left')
        return None
