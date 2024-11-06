import asyncio
import time
from contextlib import asynccontextmanager
from typing import Iterator

import anyio
from fastapi import FastAPI, WebSocket
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from shared.chat import html

# from shared.message_broker import message_broker
from shared.websocket import ws_manager
from user.async_api import router as user_async_router
from user.sync_api import router as user_sync_router


# 애플리케이션의 수명 주기를 관리하는 비동기 함수
@asynccontextmanager
async def lifespan(app: FastAPI) -> Iterator[None]:
    # 애플리케이션의 스레드 제한을 조정
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = 200  # 최대 200개의 스레드 생성 가능
    yield  # yield를 통해 수명 주기 관리에 필요한 설정을 적용


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="FastAPI Async", lifespan=lifespan)  # 초기화

# 동기 및 비동기 라우터를 각각 "/sync"와 "/async" 경로에 등록
app.include_router(router=user_sync_router, prefix="/sync")
app.include_router(router=user_async_router, prefix="/async")


# HTML 페이지를 반환하는 비동기 핸들러
@app.get("/chats", include_in_schema=False)
async def chats_handler():
    return HTMLResponse(html)  # html 문자열을 HTML 응답으로 반환


# WebSocket 통신을 위한 핸들러로, 클라이언트가 WebSocket으로 연결될 때 호출 됨
@app.websocket("/ws/{client_id}")
async def websocket_handler(websocket: WebSocket, client_id: int):
    await ws_manager.connect(
        websocket, client_id
    )  # 클라이언트를 연결하여 WebSocket 연결을 설정
    try:
        while True:
            message = await websocket.receive_text()  # 클라이언트로부터 메시지를 받으면
            await ws_manager.broadcast(
                sender_client_id=client_id, message=message
            )  # 모든 클라이언트에게 해당 메시지를 브로드캐스트
            # await message_broker.publish(client_id=client_id, message=message)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, client_id)  # 클라이언트 연결 해제


# 동기 Sleep 핸들러
@app.get("/sync/sleep", include_in_schema=False)
def get_sleep_handler():
    time.sleep(1)
    return True


# 비동기 Sleep 핸들러
@app.get("/async/sleep", include_in_schema=False)
async def get_async_sleep_handler():
    await asyncio.sleep(1)
    return True
