from websocket import create_connection
import asyncio

LINK = "ws://localhost:8000/"
GAME_ID = "123"
GAME_ENDPOINT = "ws/game/" + GAME_ID + "/"
F_LINK = LINK + GAME_ENDPOINT
