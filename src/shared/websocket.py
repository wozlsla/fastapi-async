from fastapi import WebSocket


# Global Instance, 웹소켓 요청 관리
class WebsocketConnectionManager:
    def __init__(self):
        # Conns List
        self.connections: list[tuple[WebSocket, int]] = []

    # 새로운 요청이 연결될 때 마다 connections에 새로운 요청 추가
    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept() # 서버에서 WebSocket 연결을 수락
        self.connections.append((websocket, client_id))

    # 요청이 끊어지면, connections에서 삭제하여 항상 활성화 된 요청만 남아있도록 관리
    def disconnect(self, websocket: WebSocket, client_id):
        self.connections.remove((websocket, client_id))

    async def broadcast(self, sender_client_id: int, message: str):
        for connection, client_id in self.connections:
            if client_id == sender_client_id:
                await connection.send_text(f"<Me>{message}")
            else:
                await connection.send_text(f"<Them>#{str(sender_client_id)[-4:]}: {message}")
                

ws_manager = WebsocketConnectionManager()
