from typing import Any

from fastapi import FastAPI

from .config import settings

app = FastAPI()


@app.get('/')
def main() -> dict[str, Any]:
    return {'message': 'Okay', 'settings': settings.model_dump()}
