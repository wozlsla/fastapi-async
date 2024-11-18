import asyncio
import json
from typing import ClassVar, TypedDict

from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.client import PubSub

from shared.config import settings
from shared.websocket import ws_manager


class MessagePayload(TypedDict):
    client_id: int
    message: str


class MessageBroker:
    CHANNEL_NAME: ClassVar[str] = "openchat"  # 채널 - 클래스변수?

    def __init__(self):
        # client 속성 정의
        self.client = AsyncRedis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
            decode_responses=True,
        )

    @classmethod
    def init(cls):
        broker = cls()  # message brocker 인스턴스 생성

        # _subscribe()를 ensure_future()를 통해 호출
        # ensure_future(): 작업 예약 후, 결과를 기다리지 않고 다른 작업 수행 가능
        asyncio.ensure_future(broker._subscribe())
        return broker

    async def publish(self, client_id: int, message: str):
        payload: MessagePayload = MessagePayload(client_id=client_id, message=message)
        await self.client.publish(
            channel=self.CHANNEL_NAME, message=json.dumps(payload)
        )

    async def _subscribe(self):
        pubsub: PubSub = self.client.pubsub()  # pubsub 객체 생성
        await pubsub.subscribe(self.CHANNEL_NAME)  # message 수신할 채널을 구독
        # _read_message()을 ensure_future()를 통해 호출
        asyncio.ensure_future(self._read_message(pubsub=pubsub))

    @staticmethod
    async def _read_message(pubsub: PubSub):
        while True:
            # 계속해서 pubsub로 부터 메시지 수신
            message = await pubsub.get_message(ignore_subscribe_messages=True)

            # 구독하고 있는 채널의 메시지가 수신되면
            if message is not None:
                payload: MessagePayload = json.loads(message["data"])
                # 해당 메시지를 자신의 서버에 있는 웹소켓 conn 메니저에 넘겨 전파함
                await ws_manager.broadcast(
                    sender_client_id=payload["client_id"],
                    message=payload["message"],
                )


# message_broker = MessageBroker.init()
