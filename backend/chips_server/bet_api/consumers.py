import json, time, random
from collections import defaultdict
from typing import List
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    # Game State information
    games = defaultdict(lambda: {
            'pot':0,
            'to_play':'', # Who's turn it currently is to bet
            'round': 0, # Rounds 0,1,2,3 for pre-flop -> river
            'players':defaultdict(lambda: {'chips':0,'position':-1}),
            'settings':dict()
    }) # {game_id: {'pot':pot_count,'order/chips':{'player1':chipcount}, 'settings': {x:user_input for x in settings}},}
    players = defaultdict(lambda: {'name':'', 'games':list()})
    settings = ['default_count', 'big_blind']
    count = defaultdict(int) # Keeps track of count to order players

    async def connect(self):
        # Defautl accept the connection for now
        await self.accept()

        await self.send(self.channel_name)
        print('CONNECTED to new socket client')

        self.num = self.channel_name
        return

    async def disconnect(self, close_code):
        # Find all the games the player was in and eliminate the player
        # await self._send_fail_message(self.channel_name)
        p_games = self.players[self.num]['games']
        for game_id in p_games:
            self.games[game_id]['players'].__delitem__(self.num)
            # deactivate game if last person leaves
            if len(self.games[game_id]['players'])==0:
                self.games.__delitem__(game_id)
        return

    # Receive action from client and send it to the game
    async def receive(self, text_data:str):
        # Try to parse the received data // if its not json spit out the error
        try:
            text_data = json.loads(text_data)
        except Exception as e:
            await self._send_fail_message("Can't accept non json messages")
            return
        # User is the channel_name for now (change to self.user soon probably)
        user = self.channel_name
        # Get the action from the message // Spit out error otherwise
        try:
            action = text_data['action']
        except Exception as e:
            await self.send('DATA NEEDS AN ACTION')
            return
        
        # ACTION SPACE
        ## Create new game
        if action['type']=='CREATE':
            if self._has_params(action, ['settings']):
                settings = action['settings']
            else:
                await self._send_fail_message('Settings are required to create a game')
                return
            await self.new_game(settings=settings)
        ## Join existing game
        elif action['type']=='JOIN':
            try:
                name = action['name']
                game = action['game_id']
            except Exception as e:
                await self.send('Need a name to join a game')
                return
            await self.join_game(game, name)
        ## Get *full* game status
        elif action['type']=='STATUS':
            try:
                game_id = action['game_id']
            except Exception:
                await self.send(json.dumps({'status':'fail','message':'Include game_id to get game state'}))
                return
            await self.game_status(game_id)
        ## Get order of players
        elif action['type']=='ORDER':
            if self._has_params(action, ['game_id']):
                game_id = action['game_id']
            else:
                self._send_fail_message('Please include game ID')
                return
            await self.order_players(game_id)
        ## Get Counted for the order
        elif action['type']=='COUNT':
            if self._has_params(action, ['game_id']):
                game_id = action['game_id']
            else:
                self._send_fail_message('Please include game ID')
                return
            await self.count_me(game_id)
        ## TEST
        # elif action['type']=='GAMES':
            # await self.send(json.dumps(self.games))
        return
        
    # Function to start a new game
    async def new_game(self, game_id:str=None, settings:dict=None):
        settings = settings or {'default_count':'200','big_blind':'4'}
        # Make sure all necessary data in the event
        if not self._has_params(settings, self.settings):
            await self._send_fail_message(f'Include All Settings: {self.settings}')
            return
        # Check if game ID is taken // return error if it is -- May remove in production
        if game_id and game_id in self.games:
            await self.send(json.dumps({'status':'fail','message':'Game ID is taken'}))
            return
        # Create a game ID and send it back to the client
        if not game_id:
            while (not game_id) or game_id in self.games:
                # Generate game IDs
                size = 8
                options = [chr(x) for x in range(65,91)] + list(range(10))
                game_id = ''.join(str(random.choice(options)) for _ in range(size))
        # Store new game info into the state
        self.games[game_id]['settings'] = settings
        await self.send(json.dumps({'status':'ok', 'body':{'game_id':game_id}}))
        # Finally, join the game you just created // OPTIONAL (or just get name & join after on client side
        # await self.join_game(game_id, k
        return


    # Join an existing game
    async def join_game(self, game_id, name):
        # Make sure name is legit
        if not name or type(name)!=str:
            await self.send(json.dumps({'status':'fail', 'message':'Improper Name'}))
            return
        # Make sure they aren't already in the game
        if game_id in self.players[self.channel_name]['games']:
            await self._send_fail_message('You are already in this game')
            return
        # Make sure game exists
        if not self.games.__contains__(game_id):
            await self._send_fail_message('The game ID you sent is not an active game')
            return
        # Add client to the channel
        await self.channel_layer.group_add(
            game_id,
            self.channel_name
        )
        # Add name to the names state
        self.players[self.channel_name]['name'] = name
        self.players[self.channel_name]['games'].append(game_id)
        # Add the player to the game state & give them the default number of chips
        self.games[game_id]['players'][self.channel_name]['chips'] = int(self.games[game_id]['settings']['default_count'])
        await self.send(json.dumps({'status':'ok', 'body':{'chip_count':self.games[game_id]['players'][self.channel_name]['chips'], 'name':name}}))
        return

    async def game_status(self, game_id):
        # Make sure person asking is in the game
        if self.channel_name not in self.games[game_id]['players']:
            await self.send(json.dumps({'status':'fail', 'message':'Can only get info on a game that you are in'}))
            return
        # Get and return all the information about the game
        ## Convert channel names to nicknames to keep private info private
        new_players = {self.players[x]['name']:y for x,y in self.games[game_id]['players'].items()}
        updated_game = dict(self.games[game_id])
        updated_game['players'] = new_players
        await self.send(json.dumps({'status':'ok','body':updated_game}))

    # Resets the ordering and gets ready for everyone to call 'count_me'
    async def order_players(self, game_id):
        # Make sure player is in the game
        if not self._verify_player_in_game(self.channel_name, game_id):
            await self.send(json.dumps({'status':'fail', 'message':'Ordering can only be called by players in the game'}))
            return
        for player in self.games[game_id]['players']:
            self.games[game_id]['players'][player]['position'] = -1
        await self.channel_layer.group_send(
            game_id,
            {
                'type': 'announce_ordering_start',
            }
        )
        return

    # Announces to all the clients that we are starting the ordering process
    async def announce_ordering_start(self, event):
        await self.send(json.dumps({'status':'ok','body':{'message':'Starting ordering process'}}))

    # Each client is going to call this to be counted in the order
    async def count_me(self, game_id):
        # Make sure player is in game before being counted
        if not self._verify_player_in_game(self.channel_name, game_id):
            self._send_fail_message('Must be in game to participate in count')
            return
        position = self.count[game_id]
        self.count[game_id] += 1
        self.games[game_id]['players'][self.channel_name]['position'] = position
        # If we counted everyone, end the count
        # if position+1 == len(self.games[game_id]['players'].keys()):
            # self.count[game_id] = 0
        order = sorted(self.games[game_id]['players'].keys(), key=lambda x: self.games[game_id]['players'][x]['position'])
        order = [self.players[x]['name'] for x in order]
        await self.send(json.dumps({'status':'ok','body':{'position':position}}))
        if position+1 == len(self.games[game_id]['players'].keys()):
            await self.channel_layer.group_send(
                game_id,
                {
                    'type':'announce_order',
                    'game_id':game_id,
                    'order':order
                }
            )
        return
    
    async def announce_order(self, event):
        if not self._has_params(event, ['game_id']):
            await self._send_fail_message('Need game ID to get order')
        game_id = event['game_id']
        order = event['order']
        # order = sorted(self.games[game_id]['players'].keys(), key=lambda x: self.games[game_id]['players'][x]['position'])
        # order = [self.players[x]['name'] for x in order]
        await self.send(json.dumps({'status':'ok','body':{'order':order}}))
        return

    ### USEFUL FUNCTIONS ###
    def _verify_player_in_game(self, player_id, game_id):
        if self.players[player_id]['games'] == []:
            return False
        if game_id not in self.players[player_id]['games']:
            return False
        return True

    def _has_params(self, data:dict, params:List) -> bool:
        for p in params:
            if not data.__contains__(p):
                return False
        else:
            return True

    async def _send_fail_message(self, msg:str) -> None:
        await self.send(json.dumps({'status':'fail','message':msg}))
        return

