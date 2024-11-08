import asyncio
import time
from contextlib import asynccontextmanager
from typing import Iterator

import anyio
import httpx  # 비동기 방식을 지원하는 HTTP 라이브러리
import requests
from fastapi import FastAPI, WebSocket
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from shared.chat import html

# from shared.message_broker import message_broker
from shared.websocket import ws_manager  # 웹소켓 요청 관리
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


# Chat 핸들러. HTML 페이지를 반환하는 비동기 핸들러
@app.get("/chats", include_in_schema=False)
async def chats_handler():
    return HTMLResponse(html)  # html 문자열을 HTML 응답으로 반환


# WebSocket 통신을 위한 핸들러로, 클라이언트가 WebSocket으로 연결될 때 호출 됨
# 각 사용자마다 부여(chat.py)된 client_id를 path를 통해 전달받음
@app.websocket("/ws/{client_id}")
async def websocket_handler(websocket: WebSocket, client_id: int):
    """
    - 클라이언트를 연결하여 WebSocket 연결을 설정
    - client_id는 WebSocket 요청과 함께 connections list(websocket.py)에 기록되었다가, 새로운 메세지가 들어오면 누가 보낸 메세지인지 식별할 때 사용
    """

    # 새로운 요청 connection list에 등록
    await ws_manager.connect(websocket, client_id)

    # conn이 종료될 때 까지 계속해서 client로 부터 새로운 메세지를 읽음
    try:
        while True:
            # 비동기로 실행 - 각 요청이 프로그램의 실행을 독점하지 않고, 새로운 이벤트 발생 전까지 대기상태 유지
            # 메세지 수신 메서드
            message = await websocket.receive_text()

            # 새로운 메세지가 들어오면 broadcast 메서드를 통해 모든 클라이언트에게 전달
            await ws_manager.broadcast(sender_client_id=client_id, message=message)
            # await message_broker.publish(client_id=client_id, message=message)

    except WebSocketDisconnect:  # 웹소켓 연결 종료
        # 클라이언트 연결 해제. 활성 연결 리스트(connections list)에서 제거
        ws_manager.disconnect(websocket, client_id)


# 동기식) 외부 API 요청
@app.get("/sync/posts")
def get_posts_sync_handler():
    start_time = time.perf_counter()

    urls = [
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
    ]
    responses = []

    for url in urls:
        responses.append(requests.get(url))

    end_time = time.perf_counter()
    return {"duration": end_time - start_time}  # API 동작 시간 측정
    # return [response.json() for response in responses]


# 비동기식) 외부 API 요청
@app.get("/async/posts")
async def get_posts_async_handler():
    start_time = time.perf_counter()

    urls = [
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
    ]

    async with httpx.AsyncClient() as client:  # client 객체 생성
        task = [client.get(url) for url in urls]

        # 동시에 다수의 요청을 해야하는 경우 (I/O 대기 발생)
        responses = await asyncio.gather(*task)

    end_time = time.perf_counter()
    return {"duration": end_time - start_time}  # API 동작 시간 측정
    # return [response.json() for response in responses]


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
