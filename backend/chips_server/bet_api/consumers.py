import json, time, random, math
from collections import defaultdict
from typing import List
from channels.generic.websocket import AsyncWebsocketConsumer
from bet_api.game import Game

''' TEMPORARY DEBUG VARIABLE '''
DEBUG = True

class GameConsumer(AsyncWebsocketConsumer):
    # Game State information
    # games = defaultdict(lambda: {
            # 'status': list([1,1]), # 0=busy,1=active // [ordering,voting]
            # 'round': {
                # 'betting_round':0, # Rounds 0,1,2,3 for pre-flop -> river
                # 'pot': 0, # total_pot_size:int
                # 'side_pots': defaultdict(int), # {(players_in_side_pot,):side_pot_size}
                # 'max_bet': 0, # Increase the max bet whenever someone bets
                # 'starting_player':0, # starting player
                # 'current_player':0, # current_playing_player
                # 'players':defaultdict(int), # {'player':curr_bet}
                # 'player_order': list(),
                # 'all_in': list(), # List of players who are all_in
            # },
            # 'players':defaultdict(lambda: {'chips':0,'position':-1}),
            # 'settings':dict()
    # }) # {game_id: {'pot':pot_count,'order/chips':{'player1':chipcount}, 'settings': {x:user_input for x in settings}},}
    player_games = defaultdict(str) # Each player is connected to a list of their games
    # settings = ['default_count', 'big_blind']
    # count = defaultdict(int) # Keeps track of count to order players
    votes = defaultdict(list) # Keeps track of votes for each game
    games = defaultdict(Game)
    game_id = ''

    async def connect(self):
        # Defautl accept the connection for now
        await self.accept()

        # await self.send(self.channel_name)
        # if DEBUG:
            # print('CONNECTED to new socket client')

        return

    async def disconnect(self, close_code):
        # Find all the games the player was in and eliminate the player
        # await self._send_fail_message(self.channel_name)

        game_id = self.player_games[self.channel_name]
        game = self.games[game_id]
        # Kick player out of game if they disconnect
            # do something w the game (like set them inactive) if u want

        # for game_id in p_games:
            # self.games[game_id]['players'].__delitem__(self.channel_name)
            # deactivate game if last person leaves
            # if len(self.games[game_id]['players'])==0:
                # self.games.__delitem__(game_id)
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

        # Make sure its a dictionary
        if type(action) is not dict:
            await self._send_fail_message("Can't accept non json messages")
            return

        # Make sure the action has a type
        if not action.__contains__('type'):
            await self._send_fail_message('A message must have a type')
            return

        
        # ACTION SPACE
        ## Create new game
        if action['type']=='CREATE':
            settings = None
            if self._has_params(action, ['settings']):
                settings = action['settings']
            await self.new_game(settings=settings)
        ## Join existing game
        elif action['type']=='JOIN':
            if self._has_params(action, ['name', 'game_id']):
                name = action['name']
                game = action['game_id']
            else:
                await self._send_fail_message('Need a name to join a game')
                return
            await self.join_game(game, name)
        ## Get *full* game status
        # elif action['type']=='STATUS':
            # try:
                # game_id = action['game_id']
            # except Exception:
                # await self.send(json.dumps({'status':'fail','message':'Include game_id to get game state'}))
                # return
            # await self.game_status(game_id)
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
                vote = action['vote'] # bool
            else:
                await self._send_fail_message(f'Must have all parameters: {["game_id","vote"]}')
                return
            await self.count_bool_vote(game_id, vote)
        ## Play turn
        elif action['type']=='PLAY':
            # Action should have an attribute 'play' that denotes whether its a bet or fold
            if not self._has_params(action, ['play', 'game_id']):
                await self._send_fail_message('Need a `play` action and a `game_id`')
                return
            play = action['play']
            game_id = action['game_id']
            amount = action['amount'] if action.__contains__('amount') else None
            await self.play(play=play, game_id=game_id, bet_size=amount)
            return

            # Make sure game_id exists
            # if not self._game_exists(game_id):
                # await self._send_fail_message('The game ID you provided does not exist')
            # # get the game if it exists
            # game = self.games[game_id]
            # if play=='bet':
                # if not self._has_params(action, ['amount']):
                    # await self._send_fail_message('Need to include amount with a bet')
                    # return
                # amount = action['amount']
                # # self.play_bet(game_id, amount)
                # game.place_bet(channel=self.channel_name, bet_size=amount)
                # ''' ADD ANNOUNCEMENT ABOUT WHAT JUST HAPPENED HERE AND FOR FOLD '''
                # await self.channel_layer.group_send(
                    # game_id,
                    # {
                        # 'type':'announce_bet',
                        # 'game_id':game_id,
                        # 'amount':amount,
                    # }
                # )
            # elif play == 'fold':
                # # self.play(game_id, play)
                # game.fold()
            # else:
                # await self._send_fail_message('Play can only be bet or fold')

        ## TEST
        # elif action['type']=='GAMES':
            # await self.send(json.dumps(self.games))
        else:
            await self._send_fail_message('The action type you sent does not exist')
        return

    ''' FUNCTIONALITY '''
    ## Betting
    async def play(self, play:str, game_id:str, bet_size:int=None):
        if not self._game_exists(game_id):
            await self._send_fail_message('The game ID you provided does not exist')
            return
        game = self.games[game_id]
        if play == 'bet':
            if bet_size is None:
                await self._send_fail_message('Bet must include a bet size')
                return
            try:
                new_pot = game.place_bet(channel=self.channel_name, bet_size=bet_size)
            except ValueError as e:
                await self._send_fail_message(e)
                return
            else:
                # await self.channel_layer.group_send(
                    # game_id,
                    # {
                        # 'type':'announce_bet',
                        # 'game_id':game_id,
                        # 'bet_size':bet_size,
                    # }
                # )
                await self.channel_layer.group_send(
                    game_id,
                    {
                        'type':'announce_pot',
                        'pot':new_pot,
                    }
                )
        elif play == 'fold':
            game.fold(channel=self.channel_name)
        else:
            await self._send_fail_message('`play` can only be bet or check')

    ## CREATE GAME   
    async def new_game(self, settings:dict[str and int]=None):
        # settings = settings or {'default_count':'200','big_blind':'4'}
        # Make sure all necessary data in the event
        # if not self._has_params(settings, self.settings):
            # await self._send_fail_message(f'Include All Settings: {self.settings}')
            # return
        # Check if game ID is taken // return error if it is -- May remove in production
        # if game_id and game_id in self.games:
            # await self.send(json.dumps({'status':'fail','message':'Game ID is taken'}))
            # return
        # Create a game ID and send it back to the client
        # if not game_id:
        game_id:str = None
        while (not game_id) or game_id in self.games:
            # Generate game IDs
            size = 8
            options = [chr(x) for x in range(65,91)] + list(range(10))
            game_id = ''.join(str(random.choice(options)) for _ in range(size))
        # Store new game info into the state
        # self.games[game_id]['settings'] = settings
        # Create the new game
        self.games[game_id] = Game()
        if settings:
            self.games[game_id].update_settings(settings)
        if DEBUG:
            await self.send(json.dumps({'status':'ok', 'body':{'game_id':game_id}}))
        # Finally, join the game you just created // OPTIONAL (or just get name & join after on client side
        # await self.join_game(game_id, k
        return


    # JOIN GAME
    async def join_game(self, name:str, game_id:str=''):
        # game_id = game_id or self.game_id
        # await self.send(self.game_id)
        # return

        # Set game_id as the game_id in the link if theres no game_id
        if game_id == '':
            game_id = self.scope['url_path']['kwargs']['game_id']

        # Make sure game exists
        if not self.games.__contains__(game_id):
            await self._send_fail_message('The game ID you sent is not an active game')
            return
        
        # Get current game
        game = self.games[game_id]
        # Make sure they aren't already in the game
        if game.player_is_in_game(self.channel_name):
            await self._send_fail_message('You are already in this game')
            return
        # Make sure name is legit
        if not name or type(name)!=str:
            await self._send_fail_message('Improper name')
            return
        # Make sure name is unique
        if not game.name_is_available(name):
            await self._send_fail_message('The name you chose is taken')
            return

        # Add game to player state
        self.player_games[self.channel_name] = game_id

        # Add client to the channel
        await self.channel_layer.group_add(
            game_id,
            self.channel_name
        )
        # Add name to the names state
        # self.players[self.channel_name]['name'] = name
        # self.players[self.channel_name]['games'].append(game_id)
        # Add the player to the game state & give them the default number of chips
        # self.games[game_id]['players'][self.channel_name]['chips'] = int(self.games[game_id]['settings']['default_count'])
        # await self.send(json.dumps({'status':'ok', 'body':{'chip_count':self.games[game_id]['players'][self.channel_name]['chips'], 'name':name}}))

        # Add player to game
        game.add_player(self.channel_name, name)
        # Get player info
        if DEBUG:
            info = game.get_player_info(self.channel_name)
            await self.send(str(info))
        return

    # SEND CURRENT GAME STATE
    # async def game_status(self, game_id):
        # # Make sure person asking is in the game
        # if self.channel_name not in self.games[game_id]['players']:
            # await self.send(json.dumps({'status':'fail', 'message':'Can only get info on a game that you are in'}))
            # return
        # # Get and return all the information about the game
        # ## Convert channel names to nicknames to keep private info private
        # new_players = {self.players[x]['name']:y for x,y in self.games[game_id]['players'].items()}
        # updated_game = dict(self.games[game_id])
        # updated_game['players'] = new_players
        # await self.send(json.dumps({'status':'ok','body':updated_game}))

    # Resets the ordering and gets ready for everyone to call 'count_me'
    async def order_players(self, game_id):
        # Make sure player is in the game
        if not self._verify_player_in_game(channel=self.channel_name, game_id=game_id):
            await self._send_fail_message('Ordering can only be called by players in the game')
            return
        # Get current game
        game = self.games[game_id]
        # Reset the ordering for every player
        game.reset_ordering()
        # Update Game State
        game.set_ordering_busy()
        # Update the game status to be in standby mode
        await self.channel_layer.group_send(
            game_id,
            {
                'type': 'announce_ordering_start',
            }
        )
        return

    # Each client is going to call this to be counted in the order
    async def count_me(self, game_id:str):
        # Make sure game is legit
        if not self.games.__contains__(game_id):
            await self._send_fail_message('That game ID is not an active game')
        # Make sure player is in game before being counted
        if not self._verify_player_in_game(self.channel_name, game_id):
            await self._send_fail_message('Must be in game to participate in count')
            return
        # Get current game
        game = self.games[game_id]
        # Make sure ordering is active
        if not game.ordering:
            await self._send_fail_message('Ordering is not currently active')
            return
        game.set_player_position(self.channel_name)
        ordering_completed = game.ordering_is_finished()
        if DEBUG:
            await self.send(str(game.get_player_info(self.channel_name)))
        if ordering_completed:
            game.order_players()
            game.set_ordering_free()
            await self.channel_layer.group_send(
                game_id,
                {
                    'type':'announce_order',
                    'game_id':game_id,
                }
            )
        return

        # Make sure ordering is active
        # if not self._game_is_busy(game_id, 0):
            # await self._send_fail_message('Ordering is not currently active')
            # return
        # position = self.count[game_id]
        # self.count[game_id] += 1
        # self.games[game_id]['players'][self.channel_name]['position'] = position
        # # Announce position of recent player to that player
        # await self.send(json.dumps({'status':'ok','body':{'position':position}}))
        # # If this is the last player, spit out the order to everyone
        # if position+1 == len(self.games[game_id]['players'].keys()):
            # order = sorted(self.games[game_id]['players'].keys(), key=lambda x: self.games[game_id]['players'][x]['position'])
            # name_order = [self.players[x]['name'] for x in order]
            # # Also update the current round players (put them in order)
            # for player in order:
                # self.games[game_id]['round']['players'][player] = 0
                # self.games[game_id]['round']['player_order'].append(player)
            # await self.channel_layer.group_send(
                # game_id,
                # {
                    # 'type':'announce_order',
                    # 'game_id':game_id,
                    # 'order':name_order
                # }
            # )
            # # Free up game space
            # self._set_game_active(game_id, 0)
        # return

    # ACCEPT EACH VOTE
    async def count_bool_vote(self, game_id:str, vote:bool):
        # Make sure game exists
        if not self._game_exists(game_id):
            await self._send_fail_message('The game ID you provided does not exist')
            return
        # Make sure player is voting in a game they're in
        if not self._verify_player_in_game(self.channel_name, game_id):
            await self._send_fail_message('Must be in the game to vote')
            return
        # Make sure vote is a boolean
        if not (type(vote) == bool):
            await self._send_fail_message('Vote must be a boolean value')
            return
        # Get current game
        game = self.games[game_id]
        # Make sure voting is active by checking the status
        if not game.voting:
            await self._send_fail_message('No current voting process')
            return
        # Add vote to game
        try:
            game.cast_bool_vote(channel=self.channel_name, vote=vote)
        except ValueError as e:
            await self._send_fail_message(e)
            return
        except TypeError as e:
            await self._send_fail_message(e)
            return
        # Check if that vote brought about a verdict
        if game.verdict_ready():
            # If there is a verdict, spit it out to the other players
            await self.channel_layer.group_send(
                game_id,
                {
                    'type':'announce_vote_result',
                    'game_id':game_id,
                    'vote':game.get_verdict(), # Use this result to do whatever else in the future
                }
            )

        # Add vote to list // check if vote brings about a verdict
        # self.votes[game_id].append(int(vote))
        # await self.send(json.dumps({'votes':f'{self.votes[game_id]}'}))
        # for i in range(2):
            # if len([x for x in self.votes[game_id] if int(x)==i])>=math.ceil(len(self.games[game_id]['players'])/2):
                # await self.channel_layer.group_send(
                    # game_id,
                    # {
                        # 'type':'announce_vote_result',
                        # 'game_id':game_id,
                        # 'vote': i,
                    # }
                # )

    ### BETTING ###
    ## Play a check or a fold
    # async def play(self, game_id:str, play:str):
        # betting_round, _, _, max_bet, _, current_player, players, player_order = self.get_round_info(game_id)
        # if max_bet!=0 and play=='check':
            # await self._send_fail_message('Cannot check if bet is not 0')
            # return
        # # Make sure betting player is who is supposed to play
        # if self.channel_name != player_order[current_player]:
            # await self._send_fail_message('It is not your turn to play')
            # return
        # # Handle fold
        # if play=='fold':
            # self.games[game_id]['round']['players'].__delitem__(self.channel_name)
            # pass
        # # Handle check
        # if play=='check':
            # self.advance_bet()

    ## Play a bet
    async def play_bet(self, game_id:str, amount:int):
        betting_round, pot, side_pots, max_bet, _, current_player, players, player_order, all_in = self.get_round_info(game_id)
        bet_amount = int(amount)
        # Make sure player is up to play
        if not (curr_p:=player_order[current_player]) == self.channel_name:
            await self._send_fail_message('It is not your turn to play')
            return
        # Make sure player has enough to bet
        if bet_amount > self.games[game_id]['players'][curr_p]['chips']:
            await self._send_fail_message('You do not have enough chips to bet that much')
            return
        # Make sure the bet is big enough (dont check for doubling on the raise for now)
        if bet_amount < max_bet:
            await self._send_fail_message(f'Bet must be at least equal to the max: {max_bet}')
            return
        # If the bet is over the max_bet, update it
        self.games[game_id]['round']['max_bet'] = max(max_bet,bet_amount)
        # Update game state
        ## Check if player is going all in
        if bet_amount == self.games[game_id]['players'][self.channel_name]['chips']:
            self.games[game_id]['round']['all_in'].append(self.channel_name)
            self.games[game_id]['round']['players'].__delitem__(self.channel_name)
        ## Add bet to pot if no one is all in
        if all_in == []:
            self.games[game_id]['round']['pot'] += bet_amount
            # Add bet amount to player dict
            self.games[game_id]['round']['players'][self.channel_name] += bet_amount
        else:
            # Hash a tuple of the players in order and add the pot amount
            self.games[game_id]['round']['side_pots'][tuple(players.keys())] += bet_amount
        # Take money out of personal chips
        self.games[game_id]['players'][self.channel_name]['chips'] -= bet_amount
        await self.advance_bet()

        
    # Helper Functions
    ## Move forward 1 betting round (if betting_round==3 (river), start next round) 
    async def advance_betting_round(self, game_id):
        betting_round, _, _, max_bet, starting_player, _, players, player_order,_ = self.get_round_info(game_id)
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
    
    ## Advance from current better to the next
    async def advance_bet(self, game_id:str):
        _,_,_,max_bet,starting_player,current_player,players,player_order,_ = self.get_round_info(game_id)
        # If current player is in round & hasn't bet enough throw an error
        if (curr_player:=player_order[current_player]) in players and (
                player[curr_player] < max_bet
        ):
            await self._send_fail_message('Current Player has not bet enough')
        # Otherwise update the game state
        if current_player == len(player_order)-1:
            # If ur the last player, check the starting player & if the best is good 
            # go to the next round
            if players[player_order[starting_player]]==max_bet:
                await self.advance_betting_round(game_id)
                return
            else:
                self.games[game_id]['round']['current_player'] = starting_player
        else:
            self.games[game_id]['round']['current_player'] = current_player+1
            
    
    ## Get and send all round information
    def get_round_info(self, game_id:str):
        bet_round = self.games[game_id]['round']
        betting_round, pot, side_pots, max_bet, starting_player, current_player, players, player_order, all_in = bet_round.values()
        return betting_round, pot, side_pots, max_bet, starting_player, current_player, players, player_order, all_in

    ''' ANNOUNCEMENTS '''
    # Announces to all the clients that we are starting the ordering process
    async def announce_ordering_start(self, event):
        await self.send(json.dumps({'status':'action','action':'ORDER'}))
    
    ## ANNOUNCE FINAL ORDER
    async def announce_order(self, event):
        if not self._has_params(event, ['game_id']):
            await self._send_fail_message('Need game ID to get order')
        game_id = event['game_id']
        game = self.games[game_id]
        # game.order_players()
        await self.send(json.dumps({'status':'update','update':game.get_ordered_players()}))
        # game.set_ordering_free()
        return

        # order = event['order']
        # order = sorted(self.games[game_id]['players'].keys(), key=lambda x: self.games[game_id]['players'][x]['position'])
        # order = [self.players[x]['name'] for x in order]
        # await self.send(json.dumps({'status':'ok','body':{'order':order}}))
        self._set_game_active(game_id, 0) # Free up game ordering
        return

    ## ANNOUNCE START OF VOTING PROCESS
    async def announce_voting_start(self, event):
        # self._set_game_busy(event['game_id'], 1) # Busy up game voting
        # self.votes[event['game_id']] = list()
        game_id = event['game_id']
        game = self.games[game_id]
        game.set_voting_busy() # set game state
        game.reset_voting() # Reset voting game state
        # Announce voting param
        agenda = event['voting_param']
        await self.send(json.dumps({'status':'action','action':'VOTE','agenda':agenda}))

    # This function gets the vote winner and announces it // resets game voting
    async def announce_vote_result(self, event):
        await self.send(json.dumps({'status':'result','result':event['vote']}))
        # self._set_game_active(event['game_id'], 1) # Turn off voting busy for the game
        game_id = event['game_id']
        game = self.games[game_id]
        game.reset_voting()
        game.set_voting_free()

    # Announce to everyone else when someone makes a bet so their clients update
    async def announce_bet(self, event):
        game_id, bet_size = event['game_id'], event['bet_size']

    async def announce_pot(self, pot):
        await self.send(pot)

    ''' USEFUL FUNCTIONS '''
    def _verify_player_in_game(self, channel:str, game_id:str):
        if self.games[game_id].player_is_in_game(channel):
            return True
        return False

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

    # def _set_game_busy(self, game_id:str, index:int):
        # self.games[game_id]['status'][index] = 0

    # def _set_game_active(self, game_id:str, index:int):
        # self.games[game_id]['status'][index] = 1

    # Returns whether the game is budy
    # def _game_is_busy(self, game_id:str) -> bool:
        # game = self.games[game_id]

    def _game_exists(self, game_id:str) -> bool:
        return self.games.__contains__(game_id)
