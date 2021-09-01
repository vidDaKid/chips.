import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio


class GameConsumer(AsyncWebsocketConsumer):
    # Game State information
    player_stacks = dict()
    player_bets = dict() # {'player1': $curr_bet}
    player_order = list() # player_bets.keys() ?
    max_bet = 0
    pot = 0

    async def connect(self):
        # Get the game_id from the parameter in routing.py
        self.game_id = self.scope['url_route']['kwargs']['game_id']

        # Join the game
        # await self.channel_layer.group_add(
            # self.game_id,
            # self.channel_name
        # )

        # Once we join we can accept the connection
        await self.accept()

        await self.send(self.channel_name)
        print('CONNECTED to new socket client')

        return

    async def disconnect(self, close_code):
        # If the connection breaks, automatically leave the room (maybe change later to save info)
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

        return

    # Receive action from client and send it to the game
    async def receive(self, text_data:str):
        try:
            text_data = json.loads(text_data)
        except Exception as e:
            print("Can't accept non json messages")
            print(e)
            return
        user = text_data['user'] if text_data.__contains__('user') else self.channel_name
        try:
            action = text_data['action']
        except Exception as e:
            await self.send('DATA NEEDS AN ACTION')

        # await self.channel_layer.group_send(
            # self.game_id,
            # {
                # 'type': 'test',
                # 'user': user,
                # 'works': True,
            # }
        # )
        await self.send(action)

        return
        
    async def get_action(self, event):
        user = event['user']
        works = event['works']
        
        # Send info back to the client
        await self.send(json.dumps({'user':user, 'works':works}))

        return
