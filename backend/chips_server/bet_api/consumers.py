import json, time, random, math
from collections import defaultdict
from typing import List
from channels.generic.websocket import AsyncWebsocketConsumer
from bet_api.game import Game

''' TEMPORARY DEBUG VARIABLE '''
DEBUG = True

class GameConsumer(AsyncWebsocketConsumer):
    # Game State information
    player_games = defaultdict(str) # Each player is connected to a list of their games
    votes = defaultdict(list) # Keeps track of votes for each game
    games = defaultdict(Game)
    game_id = ''

    # Connect to websocket and join the game from your link
    async def connect(self):
        # Get the game id from the link
        try:
            self.game_id = self.scope['url_route']['kwargs']['game_id']
        except KeyError:
            await self.close()
            return

        # Get the game
        game = self.games[self.game_id]
        # If the game is empty, restart it (could also do this in disconnect... or just delete it)
        if game.table.total_players == 0:
            self.games[self.game_id] = Game()
            game = self.games[self.game_id]

        # Add player to game
        game.table.add_player(channel=self.channel_name)
        # Add player to channel layer
        await self.channel_layer.group_add(self.game_id, self.channel_name)

        # Accept connection
        await self.accept()
        return

    async def disconnect(self, close_code):
        # Remove player from the game
        game = self.games[self.game_id]
        if game.table.player_is_in_game(self.channel_name):
            game.table.remove_player(self.channel_name)
        return

    # Receive action from client and send it to the game
    async def receive(self, text_data:str):
        # Try to parse the received data // if its not json spit out the error
        try:
            action = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_fail_message("Can't accept non json messages")
            return

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
        # if action['type']=='CREATE':
            # settings = None
            # if self._has_params(action, ['settings']):
                # settings = action['settings']
            # await self.new_game(settings=settings)
        # ## Join existing game
        # elif action['type']=='JOIN':
            # if self._has_params(action, ['name', 'game_id']):
                # name = action['name']
                # game = action['game_id']
            # else:
                # await self._send_fail_message('Need a name to join a game')
                # return
            # await self.join_game(game, name)
        ## Get *full* game status
        # elif action['type']=='STATUS':
            # try:
                # game_id = action['game_id']
            # except Exception:
                # await self.send(json.dumps({'status':'fail','message':'Include game_id to get game state'}))
                # return
            # await self.game_status(game_id)
        ## Get order of players
        if action['type']=='ORDER':
            await self.order_players()
        ## Get Counted for the order
        elif action['type']=='COUNT':
            await self.count_me()
        ## Start voting process
        elif action['type']=='START_VOTE':
            if self._has_params(action, ['voting_param']):
                voting_param = action['voting_param']
            else:
                self._send_fail_message('Must include voting param to begin voting process')
                return
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type':'announce_voting_start',
                    'voting_param': voting_param,
                }
            )
        ## Place a vote
        elif action['type']=='VOTE':
            if self._has_params(action, ['vote']):
                vote = action['vote'] 
            else:
                await self._send_fail_message(f'Must include `vote` in the action')
                return
            await self.cast_bool_vote(vote)
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
        ## TEST
        elif action['type']=='GAME':
            if DEBUG:
                await self.send(repr(self.games[self.game_id]))
            else:
                await self.send('Must turn on DEBUG to receive these messages')
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
    # async def new_game(self, settings:dict[str and int]=None):
        # game_id:str = None
        # while (not game_id) or game_id in self.games:
            # # Generate game IDs
            # size = 8
            # options = [chr(x) for x in range(65,91)] + list(range(10))
            # game_id = ''.join(str(random.choice(options)) for _ in range(size))
        # # Create the new game
        # if settings:
            # self.games[game_id].update_settings(settings)
        # if DEBUG:
            # await self.send(json.dumps({'status':'ok', 'body':{'game_id':game_id}}))
        # return

    # JOIN GAME
    # async def join_game(self, name:str, game_id:str=''):
        # if game_id == '':
            # game_id = self.scope['url_path']['kwargs']['game_id']
# 
        # # Make sure game exists
        # if not self.games.__contains__(game_id):
            # await self._send_fail_message('The game ID you sent is not an active game')
            # return
        # 
        # # Get current game
        # game = self.games[game_id]
        # # Make sure they aren't already in the game
        # if game.player_is_in_game(self.channel_name):
            # await self._send_fail_message('You are already in this game')
            # return
        # # Make sure name is legit
        # if not name or type(name)!=str:
            # await self._send_fail_message('Improper name')
            # return
        # # Make sure name is unique
        # if not game.name_is_available(name):
            # await self._send_fail_message('The name you chose is taken')
            # return
# 
        # # Add game to player state
        # self.player_games[self.channel_name] = game_id
# 
        # # Add client to the channel
        # await self.channel_layer.group_add(
            # game_id,
            # self.channel_name
        # )
        # # Add player to game
        # game.add_player(self.channel_name, name)
        # # Get player info
        # if DEBUG:
            # info = game.get_player_info(self.channel_name)
            # await self.send(str(info))
        # return

    # Resets the ordering and gets ready for everyone to call 'count_me'
    async def order_players(self):
        # Make sure player is in the game
        if not self._verify_player_in_game():
            await self._send_fail_message('Ordering can only be called by players in the game')
            return
        # Get current game
        game = self.games[self.game_id]
        # Reset the ordering for every player
        game.table.reset_ordering()
        # Update Game State
        game.set_ordering_busy()
        # Update the game status to be in standby mode
        await self.channel_layer.group_send( self.game_id, { 'type': 'announce_ordering_start' })
        return

    # Each client is going to call this to be counted in the order
    async def count_me(self):
        # Make sure game is legit
        if not self.games.__contains__(self.game_id):
            await self._send_fail_message('That game ID is not an active game')
        # Make sure player is in game before being counted
        if not self._verify_player_in_game():
            await self._send_fail_message('Must be in game to participate in count')
            return
        # Get current game
        game = self.games[self.game_id]
        # Make sure ordering is active
        if not game.ordering:
            await self._send_fail_message('Ordering is not currently active')
            return
        game.table.set_player_position(self.channel_name)
        ordering_completed = game.table.voting_is_finished()
        if DEBUG:
            await self.send(repr(game.table._get_player_by_channel(self.channel_name)))
        if ordering_completed:
            game.table.order_players()
            game.set_ordering_free()
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type':'announce_order'
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
    async def cast_bool_vote(self, vote:bool):
        # Make sure game exists
        if not self._game_exists(self.game_id):
            await self._send_fail_message('The game ID you provided does not exist')
            return
        # Make sure player is voting in a game they're in
        if not self._verify_player_in_game():
            await self._send_fail_message('Must be in the game to vote')
            return
        # Make sure vote is a boolean
        if not (type(vote) == bool):
            await self._send_fail_message('Vote must be a boolean value')
            return
        # Get current game
        game = self.games[self.game_id]
        # Make sure voting is active by checking the status
        if not game.voting:
            await self._send_fail_message('No current voting process')
            return
        # Add vote to game
        try:
            game.table.cast_bool_vote(channel=self.channel_name, vote=vote)
        except ValueError as e:
            await self._send_fail_message(e)
            return
        except TypeError as e:
            await self._send_fail_message(e)
            return
        # Check if that vote brought about a verdict
        if game.table.voting_is_finished():
            # If there is a verdict, spit it out to the other players
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type':'announce_vote_result',
                    'vote':game.table.get_verdict(), # Use this result to do whatever else in the future
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
        game = self.games[self.game_id]
        await self.send(repr(game))
        # game.order_players()
        # await self.send(json.dumps({'status':'update','update':game.get_ordered_players()}))
        # game.set_ordering_free()
        return

    ## ANNOUNCE START OF VOTING PROCESS
    async def announce_voting_start(self, event):
        # self._set_game_busy(event['game_id'], 1) # Busy up game voting
        # self.votes[event['game_id']] = list()
        game = self.games[self.game_id]
        game.set_voting_busy() # set game state
        game.table.reset_voting() # Reset voting game state
        # Announce voting param
        agenda = event['voting_param']
        await self.send(json.dumps({'status':'action','action':'VOTE','agenda':agenda}))

    # This function gets the vote winner and announces it // resets game voting
    async def announce_vote_result(self, event):
        await self.send(json.dumps({'status':'result','result':event['vote']}))
        # self._set_game_active(event['game_id'], 1) # Turn off voting busy for the game
        game = self.games[self.game_id]
        game.table.reset_voting()
        game.set_voting_free()

    # Announce to everyone else when someone makes a bet so their clients update
    async def announce_bet(self, event):
        game_id, bet_size = event['game_id'], event['bet_size']

    async def announce_pot(self, pot):
        await self.send(pot)

    ''' USEFUL FUNCTIONS '''
    def _verify_player_in_game(self):
        if self.games[self.game_id].player_is_in_game(self.channel_name):
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
