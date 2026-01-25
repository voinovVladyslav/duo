from typing import Any

from fastapi import FastAPI, WebSocket

from api.routers.auth import router as auth_router
from api.websockets import WebSocketsClient

app = FastAPI()
app.include_router(auth_router, prefix='/auth', tags=['auth'])


client = WebSocketsClient()


@app.get('/', tags=['status'])
def main() -> dict[str, Any]:
    return {'message': 'ok'}


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
