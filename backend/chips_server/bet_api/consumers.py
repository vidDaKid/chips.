import json, time, random, math
from collections import defaultdict
from typing import List
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    # Game State information
    games = defaultdict(lambda: {
            'status': list([1,1]), # 0=busy,1=active // [ordering,voting]
            'to_play':'', # Who's turn it currently is to bet
            'round': {
                'betting_round':0, # Rounds 0,1,2,3 for pre-flop -> river
                'pot': 0, # total_pot_size:int
                'side_pots': defaultdict(int), # {(players_in_side_pot,):side_pot_size}
                'max_bet': 0, # Increase the max bet whenever someone bets
                'starting_player':0, # starting player
                'current_player':0, # current_playing_player
                'players':defaultdict(int), # {'player':curr_bet}
            },
            'players':defaultdict(lambda: {'chips':0,'position':-1}),
            'settings':dict()
    }) # {game_id: {'pot':pot_count,'order/chips':{'player1':chipcount}, 'settings': {x:user_input for x in settings}},}
    players = defaultdict(lambda: {'name':'', 'games':list()})
    settings = ['default_count', 'big_blind']
    count = defaultdict(int) # Keeps track of count to order players
    votes = defaultdict(list) # Keeps track of votes for each game

    async def connect(self):
        # Defautl accept the connection for now
        await self.accept()

        await self.send(self.channel_name)
        print('CONNECTED to new socket client')

        return

    async def disconnect(self, close_code):
        # Find all the games the player was in and eliminate the player
        # await self._send_fail_message(self.channel_name)
        p_games = self.players[self.channel_name]['games']
        for game_id in p_games:
            self.games[game_id]['players'].__delitem__(self.channel_name)
            # deactivate game if last person leaves
            if len(self.games[game_id]['players'])==0:
                self.games.__delitem__(game_id)
        return

    # Receive action from client and send it to the game
    async def receive(self, text_data:str):
        # Try to parse the received data // if its not json spit out the error
        try:
            action = json.loads(text_data)
        except Exception as e:
            await self._send_fail_message("Can't accept non json messages")
            return
        # User is the channel_name for now (change to self.user soon probably)
        user = self.channel_name
        # Get the action from the message // Spit out error otherwise
        # try:
            # action = text_data['action']
        # except Exception as e:
            # await self.send('DATA NEEDS AN ACTION')
            # return
        
        # ACTION SPACE
        ## Create new game
        if action['type']=='CREATE':
            settings, game_id = None, None
            if self._has_params(action, ['settings']):
                settings = action['settings']
            if self._has_params(action, ['game_id']):
                game_id = action['game_id']
            await self.new_game(game_id=game_id, settings=settings)
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
        ## Start voting process
        elif action['type']=='START_VOTE':
            if self._has_params(action, ['game_id','voting_param']):
                game_id = action['game_id']
                voting_param = action['voting_param']
            else:
                self._send_fail_message('Must include game ID to begin voting process')
                return
            await self.channel_layer.group_send(
                game_id,
                {
                    'type':'announce_voting_start',
                    'game_id':game_id,
                    'voting_param': voting_param,
                }
            )
        ## Place a vote
        elif action['type']=='VOTE':
            if self._has_params(action, ['game_id','vote']):
                game_id = action['game_id']
                vote = action['vote'] #Should be 0 or 1 (string is ok)
            else:
                self._send_fail_message(f'Must have all parameters: {["game_id","vote"]}')
                return
            await self.count_vote(game_id, vote)
        ## Play turn
        elif action['type']=='PLAY':
            # Action should have an attribute 'play' that denotes whether its a bet, check, or fold
            if self._has_params(action, ['play', 'game_id']):
                play = action['play']
                game_id = action['game_id']
            if play=='bet':
                self.play_bet(game_id)
            else:
                self.play(game_id, play)

        ## TEST
        elif action['type']=='GAMES':
            await self.send(json.dumps(self.games))
        return

    ''' FUNCTIONALITY '''
    ## CREATE GAME   
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


    # JOIN GAME
    async def join_game(self, game_id, name):
        # Make sure name is legit
        if not name or type(name)!=str:
            await self.send(json.dumps({'status':'fail', 'message':'Improper Name'}))
            return
        # Make sure they aren't already in the game
        if self.channel_name in self.games[game_id]['players']:
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

    # SEND CURRENT GAME STATE
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
        # Reset the ordering for every player
        for player in self.games[game_id]['players']:
            self.games[game_id]['players'][player]['position'] = -1
        # Update Game State
        self._set_game_busy(game_id, 0) # busy up game ordering
        # Update the game status to be in standby mode
        await self.channel_layer.group_send(
            game_id,
            {
                'type': 'announce_ordering_start',
            }
        )
        return

    # Each client is going to call this to be counted in the order
    async def count_me(self, game_id):
        # Make sure player is in game before being counted
        if not self._verify_player_in_game(self.channel_name, game_id):
            await self._send_fail_message('Must be in game to participate in count')
            return
        # Make sure ordering is active
        if not self._game_is_busy(game_id, 0):
            await self._send_fail_message('Ordering is not currently active')
            return
        position = self.count[game_id]
        self.count[game_id] += 1
        self.games[game_id]['players'][self.channel_name]['position'] = position
        # Announce position of recent player to that player
        await self.send(json.dumps({'status':'ok','body':{'position':position}}))
        # If this si the last player, spit out the order to everyone
        if position+1 == len(self.games[game_id]['players'].keys()):
            order = sorted(self.games[game_id]['players'].keys(), key=lambda x: self.games[game_id]['players'][x]['position'])
            order = [self.players[x]['name'] for x in order]
            await self.channel_layer.group_send(
                game_id,
                {
                    'type':'announce_order',
                    'game_id':game_id,
                    'order':order
                }
            )
            # Free up game space
            self._set_game_active(game_id, 0)
        return

    # ACCEPT EACH VOTE
    async def count_vote(self, game_id, vote):
        # Make sure player is voting in a game they're in
        if not self._verify_player_in_game(self.channel_name, game_id):
            await self._send_fail_message('Must be in the game to vote')
            return
        # Make sure voting is active by checking the status
        if not self.games[game_id]['status'][1]:
            await self._send_fail_message('No current voting process')
            return
        # Add vote to list // check if vote brings about a verdict
        self.votes[game_id].append(int(vote))
        await self.send(json.dumps({'votes':f'{self.votes[game_id]}'}))
        for i in range(2):
            if len([x for x in self.votes[game_id] if int(x)==i])>=math.ceil(len(self.games[game_id]['players'])/2):
                await self.channel_layer.group_send(
                    game_id,
                    {
                        'type':'announce_vote_result',
                        'game_id':game_id,
                        'vote': i,
                    }
                )

    ### BETTING ###
    ## Play a check or a fold
    async def play(self, game_id:str, play:str):
        betting_round, _, _, max_bet, starting_player, _, players = self.get_round_info(game_id)
        if max_bet!=0 and play=='check':
            await self._send_fail_message('Cannot check if bet is not 0')
            return
        if play=='fold':
            # self.g
            pass

    # Helper Functions
    ## Move forward 1 betting round (if betting_round==3 (river), start next round) 
    async def advance_betting_round(self, game_id):
        betting_round, _, _, max_bet, starting_player, _, players = self.get_round_info(game_id)
        if int(betting_round) == 3:
            # CALL ADVANCE ROUND FUNCTION
            return
        # Make sure every player has bet however much they needed to
        for player, bet in players.items():
            if bet < max_bet:
                await self._send_fail_message(f'{player} has not yet bet')
                return
        # Update the betting round and reset the player/bet info
        self.games[game_id]['round']['betting_round'] = betting_round+1
        self.games[game_id]['round']['max_bet'] = 0
        self.games[game_id]['round']['current_player'] = starting_player
        player_lst = list(players.keys())
        self.games[game_id]['round']['players'] = {x:0 for x in player_lst}
        # Use the current_player index to get the player chennel name to get the player name
        new_curr_player = self.players[player_lst[self.games[game_id]['round']['current_player']]]['name']
        await self.send(json.dumps({'status':'ok','body':{
                'current_player':new_curr_player
        }}))
            

    
    ## Get and send all round information
    def get_round_info(self, game_id:str):
        bet_round = self.games[game_id]['round']
        betting_round, pot, side_pots, max_bet, starting_player, current_player, players = bet_round.values()
        return betting_round, pot, side_pots, max_bet, starting_player, current_player, players

    ''' ANNOUNCEMENTS '''
    # Announces to all the clients that we are starting the ordering process
    async def announce_ordering_start(self, event):
        await self.send(json.dumps({'status':'ok','body':{'message':'Starting ordering process'}}))
    
    ## ANNOUNCE FINAL ORDER
    async def announce_order(self, event):
        if not self._has_params(event, ['game_id', 'order']):
            await self._send_fail_message('Need game ID to get order')
        game_id = event['game_id']
        order = event['order']
        # order = sorted(self.games[game_id]['players'].keys(), key=lambda x: self.games[game_id]['players'][x]['position'])
        # order = [self.players[x]['name'] for x in order]
        await self.send(json.dumps({'status':'ok','body':{'order':order}}))
        self._set_game_active(game_id, 0) # Free up game ordering
        return

    ## ANNOUNCE START OF VOTING PROCESS
    async def announce_voting_start(self, event):
        self._set_game_busy(event['game_id'], 1) # Busy up game voting
        self.votes[event['game_id']] = list()
        await self.send(json.dumps({'status':'action','body':{'action':'VOTE','voting_param':event['voting_param']}}))

    async def announce_vote_result(self, event):
        await self.send(json.dumps({'status':'ok','body':{'winner':event['vote']}}))
        self._set_game_active(event['game_id'], 1) # Turn off voting busy for the game

    ''' USEFUL FUNCTIONS '''
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

    # @param index // 0=ordering, 1=voting

    def _set_game_busy(self, game_id:str, index:int):
        self.games[game_id]['status'][index] = 0

    def _set_game_active(self, game_id:str, index:int):
        self.games[game_id]['status'][index] = 1

    # Returns whether the game is budy
    def _game_is_busy(self, game_id:str, index:int) -> bool:
        return not bool(self.games[game_id]['status'][index])

