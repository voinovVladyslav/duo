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
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'Got: {data}')
    except WebSocketDisconnect:
        print('Disconnected')
        return None
