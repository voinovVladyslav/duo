from fastapi import WebSocket


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
