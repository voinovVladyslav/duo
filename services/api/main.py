import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .config import settings

app = FastAPI()


@app.get('/')
def main() -> dict[str, Any]:
    return {'message': 'Okay', 'settings': settings.model_dump()}


@app.websocket('/ws')
async def websocket_api(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        counter = 0
        while True:
            await asyncio.sleep(1)
            counter += 1
            await websocket.send_text(str(counter))
    except WebSocketDisconnect:
        print('Disconnected')
        return None
