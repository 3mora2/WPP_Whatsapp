"""Authenticated local HTTP template. Importing creates neither app nor browser.

Install .[web], set WPP_API_TOKEN, then run:
uvicorn examples.fastapi_app:create_app --factory --host 127.0.0.1
"""

from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from WPP_Whatsapp import AsyncClient
from WPP_Whatsapp.core.errors import OperationConflictError, WPPError


class SendRequest(BaseModel):
    chat_id: str = Field(min_length=1, max_length=512)
    text: str = Field(min_length=1, max_length=65536)
    operation_id: str = Field(min_length=1, max_length=128)


def create_app(client: Optional[AsyncClient] = None, *, token: Optional[str] = None) -> FastAPI:
    secret = token or os.environ.get("WPP_API_TOKEN")
    if not secret:
        raise RuntimeError("Set WPP_API_TOKEN before starting the example")
    active = client or AsyncClient(
        "http-example",
        wait_for_login=False,
        autoClose=0,
        logQR=False,
        deliveryStore="tokens/.deliveries/http-example.sqlite3",
        reconnectAttempts=3,
    )

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            if client is None:
                await active.close()

    bearer = HTTPBearer(auto_error=False)
    bearer_dependency = Depends(bearer)

    async def authorize(credentials: Optional[HTTPAuthorizationCredentials] = bearer_dependency):
        if credentials is None or not secrets.compare_digest(
            credentials.credentials.encode(), secret.encode()
        ):
            raise HTTPException(
                401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}
            )

    app = FastAPI(lifespan=lifespan, dependencies=[Depends(authorize)])

    @app.exception_handler(WPPError)
    async def operation_error(request, error):
        if isinstance(error, OperationConflictError):
            return JSONResponse(
                status_code=409, content={"detail": "Operation ID belongs to another request"}
            )
        return JSONResponse(
            status_code=503,
            content={"detail": "Inspect session state and the operation receipt before retrying"},
        )

    @app.get("/health")
    async def health():
        return active.diagnostics()

    @app.post("/session/connect")
    async def connect():
        await active.connect()
        return active.diagnostics()

    @app.get("/messages")
    async def messages(chat_id: str, count: int = 50):
        if not 1 <= count <= 200:
            raise HTTPException(422, "Count must be between 1 and 200")
        return await active.messages.get_messages(chat_id, {"count": count})

    @app.post("/messages")
    async def send(request: SendRequest):
        return await active.messages.send_text(
            request.chat_id,
            request.text,
            operation_id=request.operation_id,
        )

    return app
