import json, time, random, math
from typing import List
from bet_api.bet import RoundBets
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer
from bet_api.game import Game
from bet_api.tasks import bet_timer, pay_winners_timer

''' TEMPORARY DEBUG VARIABLE '''
DEBUG = False

class GameConsumer(AsyncWebsocketConsumer):
    # Game State information
    # player_games = defaultdict(str) # Each player is connected to a list of their games
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

        # Get name from query parameters if sent
        # query_string = self.scope['query_string']
        ## For some really stupid reason the string is formatted as
            ## "b'query_params'" where the b'' is part of the string
            ## So we gotta strip that part
        # query_string = str(query_string)[1:].replace("'","")
        # set a default name for the player (handled in table consumer)
        # name=''
        # queries = query_string.split('&')
        # Get the name query only
        # for query in queries:
            # if query.startswith('name'):
                # # Get just the name
                # name = query.split('=')[1]
                # break

        # Get the game
        game = self.games[self.game_id]
        # If the game is empty, restart it (could also do this in disconnect... or just delete it)
        if game.table.total_players == 0:
            self.games[self.game_id] = Game()
            game = self.games[self.game_id]

        if game.table.player_is_in_game(self.channel_name):
            return

        # Add player to game
        # game.table.add_player(channel=self.channel_name)
        # Add player to channel layer
        await self.channel_layer.group_add(self.game_id, self.channel_name)

        # Accept connection
        await self.accept()

        # Send them the players that are already in the group
        if len(game.table.players) > 0:
            await self.send(json.dumps({
                'type':'PLAYERS',
                'players':[{'player':x.name,'c_count':x.c_count,'position':x.position} for x in game.table.players]
            }))

        # save the session
        # self.scope['session'].save()
        return

    async def disconnect(self, close_code):
        # Remove player from the game
        game = self.games[self.game_id]
        if not game.table.player_is_in_game(self.channel_name):
            return
        player = game.table._get_player_by_channel(self.channel_name)
        name = player.name
        if game.table.curr_player == player:
            _, new_bet_round, new_round = game.table.fold(self.channel_name)
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'announce_fold',
                    'player': name
                }
            )
            if not new_round:
                if new_bet_round:
                    await self.channel_layer.group_send(
                        self.game_id,
                        {
                            'type':'announce_new_bet_round', 
                            'bet_round':game.table.bet_round
                        }
                    )
                await self.send_curr_player_announcement()
            else:
                await self.decide_winners()
        game.table.remove_player(self.channel_name)
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type':'announce_player_leave',
                'player':name,
            }
        )
        await self.channel_layer.group_discard(self.game_id, self.channel_name)
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
        ## Join a game
        if action['type']=='JOIN':
            name = ''
            if self._has_params(action, ['name', 'position']):
                name = action['name']
                position = action['position']
            await self.join_game(name=name, position=position)
        ## Get ur player back w the secret
        elif action['type']=='SECRET_JOIN':
            if self._has_params(action, ['secret']):
                secret = action['secret']
            else:
                await self._send_fail_message('Cannot find your old player without a secret')
                return
            await self.join_with_player_secret(secret)
        ## Change sears
        elif action['type'] == 'MOVE':
            if not self._has_params(action, ['position']): return
            position = action['position']
            game = self.games[self.game_id]
            player = game.table._get_player_by_channel(self.channel_name)
            player.position = position
        ## Get order of players
        elif action['type']=='ORDER':
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
        ## Vote for a winner
        elif action['type']=='VOTE_WINNERS':
            if not self._has_params(action, ['winners']):
                await self._send_fail_message('Must include the winner you are voting for')
                return
            winners = action['winners']
            game = self.games[self.game_id]
            game.table.vote_winners[frozenset(winners)] += 1
        ## Play turn
        elif action['type'] == 'BET':
            if not self._has_params(action, ['bet_size']):
                await self._send_fail_message('Must include a bet size')
                return
            bet_size = action['bet_size'] if action.__contains__('bet_size') else 0
            await self.play_bet(int(bet_size))
        elif action['type'] == 'FOLD':
            await self.play_fold()
        # elif action['type']=='PLAY':
            # # Action should have an attribute 'play' that denotes whether its a bet or fold
            # if not self._has_params(action, ['play']):
                # await self._send_fail_message('Need a `play` action')
                # return
            # play = action['play']
            # if play == 'fold':
                # await self.play_fold()
            # else:
                # bet_size = action['bet_size'] if action.__contains__('bet_size') else 0
                # await self.play_bet(int(bet_size))
            # return
        ## Start a new game--gets everything set up for u (might make this automatic instead)
        elif action['type'] == 'START':
            await self.start_game()
        elif action['type']=='CLAIM_WIN':
            game = self.games[self.game_id]
            if not self._has_params(action, ['pot_id']):
                await self._send_fail_message('Need pot Id with win claim')
                return
            # check if they've already claimed it
            if self.channel_name in game.table.winners[action['pot_id']]:
                return
            game.table.claim_win(self.channel_name, action['pot_id'])
            player = game.table._get_player_by_channel(self.channel_name)
            await self.channel_layer.group_send(self.game_id, {
                'type':'announce_claimed_win',
                'pot_id':action['pot_id'],
                'player':player.name
            })
        elif action['type']=='PAY_WINNERS':
            await self.pay_winners()
        elif action['type']=='START_CLAIMS':
            if not self._has_params(action, ['pot_id']):
                await self._send_fail_message('Must have pot_id to start claim process')
                return
            pot_id = action['pot_id']
            await self.start_claims(pot_id)
        ## TEMP DEGBUG SERVER CALLS
        # elif action['type']=='GAME':
            # if DEBUG:
                # await self.send(repr(self.games[self.game_id]))
            # else:
                # await self.send('Must turn on DEBUG to receive these messages')
        # elif action['type']=='POTS':
            # if DEBUG:
                # game = self.games[self.game_id]
                # await self._send_debug_message(str(game.table.pot))
        # elif action['type']=='TEST_COUNTDOWN':
            # await bet_timer.apply_async((game_id=self.game_id,), countdown=10)
            # self.bet_timer.apply_async((self.game_id,), countdown=5)
            # self.start_timer()
        # elif action['type']=='END_TIMER':
            # await self.end_timer()
        else:
            await self._send_fail_message('The action type you sent does not exist')
        return

    ''' FUNCTIONALITY '''
    ## GAME
    async def join_game(self, name:str, position:int) -> None:
        if name == 'null' or not name:
            await self._send_fail_message('Name must only have characters, symbols, and numbers')
            return
        game = self.games[self.game_id]
        try:
            name, c_count, position, secret = game.table.add_player(channel=self.channel_name, name=name, position=position)
        except ValueError as e:
            await self._send_fail_message(e)
            return
        # if is_in_game:
            # await self._send_fail_message('Player already in game')
            # return
        # Send the secret to the client
        await self.send(json.dumps({'type':'SECRET','secret':secret}))
        # announce to everyone that u joined the game
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type':'announce_new_player',
                'player':name,
                'c_count':c_count,
                'position':position,
            }
        )
        # Send the game settings to the client
        await self.announce_settings()
    ## Get old player back
    async def join_with_player_secret(self, secret:str) -> None:
        game = self.games[self.game_id]
        try:
            name, c_count = game.table.update_player_secret(channel=self.channel_name, secret=secret)
        except KeyError as e:
            await self._send_fail_message(e)
            return
        # await self.send(json.dumps({'type':'SECRET_PLAYER','player':name,'c_count':c_count}))
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type':'announce_new_player',
                'player':name,
                'c_count':c_count,
                'position':position
            }
        )
        # Send game settings to client
        await self.announce_settings()
    ## Betting
    async def start_game(self) -> None:
        game = self.games[self.game_id]
        try:
            player = game.table._get_player_by_channel(self.channel_name)
        except KeyError:
            await self._send_fail_message('Must be in game to start it')
            return
        if game.table.players == []:
            await self._send_fail_message('There are no players in the game')
            return
        # Get the positions & start the round
        positions:dict[str and 'Player'] = game.table.start_round()
        # start_round should add a player & we can tell everyone whos turn it is
        curr_player = game.table.curr_player
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type': 'announce_current_turn',
                'player': curr_player.name,
                'owed': game.table.amount_owed()
            }
        )
        # Get the positions to send to the group so tehy can update their state
        # dealer = positions['dealer'].name
        # sb = positions['small_blind'].name
        # bb = positions['big_blind'].name
        for position, player in positions.items():
            positions[position] = player.name
        # get the dealer player object from the table
        dealer = game.table.players[game.table.dealer]
        await self.channel_layer.group_send(
            self.game_id, 
            {
                'type': 'announce_new_round' ,
                'dealer': dealer.name
            }
        )
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type': 'announce_positions',
                'positions': positions
            }
        )

    async def play_bet(self, bet_size:int) -> None:
        game = self.games[self.game_id]
        # Place the bet
        try:
            announcement, \
            next_player, \
            new_bet_round, \
            new_round = game.table.place_bet(channel=self.channel_name, bet_size=bet_size)
        except ValueError as e:
            await self._send_fail_message(e)
            return
        except KeyError as e:
            await self._send_fail_message(e)
            return
        if DEBUG:
            bets = game.table.get_bets()
            await self._send_debug_message(str(bets))
        # Announce the bet that was just played & who is up to play next
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type':'announce_bet',
                'player': announcement['player'],
                'bet_size': announcement['bet_size']
            }
        )

        if new_round:
            # get the elibile pot winners from the table and send it to everyone
            await self.decide_winners()
            return
            # await self.channel_layer.group_send(self.game_id, {'type':'announce_decide_winner'})
            # time.sleep(5)
            # if game.table.winners == []:
                # await self.channel_layer.group_send(self.game_id, {'type':'announce_vote_winner'})
            # else:
                # await self.channel_layer.group_send(self.game_id, {'type':'announce_winners','winners':game.table.winners})
            # await self.channel_layer.group_send(self.game_id,{ 'type':'announce_new_round' })
        elif new_bet_round:
            await self.new_bet_round()
            # temp // send pots to client
            if DEBUG:
                await self.channel_layer.group_send(self.game_id, { 'type':'announce_pot', 'pot':str(game.table.pot) })
        # else:
            # await self.send(
        await self.send_curr_player_announcement()


    async def play_fold(self) -> None:
        game = self.games[self.game_id]
        player, new_bet_round, new_round = game.table.fold(self.channel_name)
        await self.channel_layer.group_send(self.game_id, {'type':'announce_fold', 'player':player})
        # if len(game.table.queue) == 0:
            # await self.decide_winners()
            # await self.channel_layer.group_send( self.game_id, { 'type': 'announce_decide_winner' })
        if new_round:
            await self.decide_winners()
            return
        elif new_bet_round:
            await self.new_bet_round()
        await self.send_curr_player_announcement()

    def start_timer(self) -> None:
        game = self.games[self.game_id]
        timer_len = 5 if DEBUG else game.table.settings['bet_timer']
        # process_id = game.table.update_process_id()
        game.table.timer = bet_timer.apply_async((self.game_id,), countdown=timer_len)

    async def end_timer(self) -> None:
        game = self.games[self.game_id]
        game.table.timer.revoke()
        # await self.send(str(game.table.timer))

    # First function called at the end of the round
    async def decide_winners(self) -> None:
        # winner_timer.apply_async((self.game_id,), countdown=10)
        game = self.games[self.game_id]
        # poss_winners = game.table.get_eligible_winners()
        ## Add bets from the round to the pot in case u havent
        bet = RoundBets()
        for player in game.table.players:
            bet.add_bet_from_player(player)
            player.curr_bet = 0
        game.table.pot += bet
        game.table.reset_bet_round()
        # poss_winners = list()
        game.table.reset_winners()
        eligible_players = [x.name for x in game.table.players if not (x.folded or x.all_in)]
        channel_conversion = {x.channel:x.name for x in game.table.players if not x.folded}
        pots = game.table.pot.get_json_pots(eligible_players, channel_conversion)
        # for idx, x in enumerate(pots[:-1]):
            # pots[idx]['eligible'] = [game.table._get_player_by_channel(y) for y in x['eligible']]
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type':'announce_pots',
                'pots': pots
            }
        )
        return


        # if game.table.pot.bottomless_pot.paid_out:
            # # if game.table.pot.pots == []:
                # # return
            # for idx, p in enumerate(game.table.pot.pots):
                # if not p.paid_out:
                    # poss_winners = list(p.eligible)
                    # pot_amount = p.val
                    # pot_id = idx
                    # break
        # else:
            # poss_winners = [x for x in game.table.players if not (x.folded or x.all_in)]
            # pot_amount = game.table.pot.bottomless_pot.val
            # pot_id = -1
# 
        # if poss_winners == []:
            # # tell the client that all the winners have been paid
            # await self.channel_layer.group_send(
                # self.game_id, 
                # {'type':'announce_paid_out'}
            # )
            # return
        # # start the timer to decide more winners
        # else:
            # # Start the timer w this info
            # game.table.timer = self.start_winner_timer(pot_amount=pot_amount, pot_id=pot_id)
        # await self.channel_layer.group_send(
            # self.game_id,
            # {
                # 'type': 'announce_decide_winners',
                # 'options': [x.name for x in poss_winners]
            # }
        # )

    async def pay_winners(self) -> None:
        game = self.games[self.game_id]
        game.table.reset_voting()
        await self.channel_layer.group_send(self.game_id, {
            'type':'announce_vote_pay'
        })
        game.table.timer = pay_winners_timer.apply_async(kwargs={'game_id':self.game_id}, countdown=5)

    async def new_bet_round(self) -> None:
        game = self.games[self.game_id]
        await self.channel_layer.group_send(self.game_id,{
            'type':'announce_new_bet_round',
            'bet_round':game.table.bet_round
        })

    async def send_curr_player_announcement(self) -> None:
        game = self.games[self.game_id]
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type':'announce_current_turn',
                'player': game.table.curr_player.name,
                'owed': game.table.amount_owed()
            }
        )

    # async def start_claims(self, pot_id) -> None:
        # game = self.games[self.game_id]
        # game.table.reset_winners()
        # await self.channel_layer.group_send(
            # self.game_id,
           # { 'type':'announce_start_claims' }
        # )
        # game.table.timer = winner_timer.apply_async((self.game_id, pot_id), countdown=10)

    # def start_winner_timer(self, vote:bool=False, *args, **kwargs) -> 'Timer':
        # game = self.games[self.game_id]
        # pot_amount = kwargs['pot_amount']
        # pot_id = kwargs['pot_id']
        # if vote:
            # timer = vote_winner_timer.apply_async((self.game_id, pot_amount, pot_id), countdown=10)
        # else:
            # timer = winner_timer.apply_async((self.game_id,pot_amount,pot_id), countdown=10)
        # return timer

    # returns bool saying whether or not ppl were paid
    # async def pay_winners(self, pot_amount:int, pot_id:int) -> bool:
        # game = self.games[self.game_id]
        # 
        # if game.table.winners == []:
            # if game.table.players[0].channel != self.channel_name:
                # return False
            # game.table.timer = self.start_winner_timer(vote=True, pot_amount=pot_amount, pot_id=pot_id)
            # await self.channel_layer.group_send(self.game_id, {
                # 'type':'announce_vote_winners',
                # 'pot_amount': pot_amount,
                # 'pot_id':pot_id
            # })
            # return False
# 
        # for player in game.table.players:
            # if player.channel == self.channel_name and player in game.table.winners:
                # player.c_count += ( pot_amount // len(game.table.winners) )
                # break
                # # if ur the first person to claim winnings u get the extras in the pot
                # if player == game.table.winners[0]:
                    # player.c_count += ( pot_amount % len(game.table.winners) )
        # # update the pot if not done
        # if pot_id == -1:
            # if not game.table.pot.bottomless_pot.paid_out:
                # game.table.pot.bottomless_pot.paid_out = True
        # else:
            # if not game.table.pot.pots[pot_id].paid_out:
                # game.table.pot.pots[pot_id].paid_out = True
        # return True

    # returns bool of whether or not players were paid out
    # async def pay_voted_winners(self, pot_amount:int, pot_id:int) -> bool:
        # game = self.games[self.game_id]
        # 
        # if game.table.vote_winners == {}:
            # winners = None
        # else:
            # winners = max(game.table.vote_winners, key=game.table.vote_winners.get)
            # me = game.table._get_player_by_channel(self.channel_name)
        # 
        # if (not winners) or game.table.vote_winners[winners] == 0:
            # self.start_winner_timer(vote=True, pot_amount=pot_amount, pot_id=pot_id)
            # await self.channel_layer.group_send(self.game_id, {
                # 'type': 'announce_vote_winners',
                # 'pot_amount': pot_amount,
                # 'pot_id': pot_id
            # })
            # return False, []
# 
        # for player in winners:
            # if player == me.name:
                # player.c_count += (pot_amount // len(winners))
                # if player == game.table.winners[0]:
                    # player.c_count += ( pot_amount % len(winners) )
# 
        # if pot_id == -1:
            # if not game.table.pot.bottomless_pot.paid_out:
                # game.table.pot.bottomless_pot.paid_out = True
        # else:
            # if not game.table.pot.pots[pot_id].paid_out:
                # game.table.pot.pots[pot_id].paid_out = True
        # return True, winners

    # async def play(self, play:str, game_id:str, bet_size:int=None):
        # if not self._game_exists(game_id):
            # await self._send_fail_message('The game ID you provided does not exist')
            # return
        # game = self.games[game_id]
        # if play == 'bet':
            # if bet_size is None:
                # await self._send_fail_message('Bet must include a bet size')
                # return
            # try:
                # new_pot = game.place_bet(channel=self.channel_name, bet_size=bet_size)
            # except ValueError as e:
                # await self._send_fail_message(e)
                # return
            # else:
                # # await self.channel_layer.group_send(
                    # # game_id,
                    # # {
                        # # 'type':'announce_bet',
                        # # 'game_id':game_id,
                        # # 'bet_size':bet_size,
                    # # }
                # # )
                # await self.channel_layer.group_send(
                    # game_id,
                    # {
                        # 'type':'announce_pot',
                        # 'pot':new_pot,
                    # }
                # )
        # elif play == 'fold':
            # game.fold(channel=self.channel_name)
        # else:
            # await self._send_fail_message('`play` can only be bet or check')

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

        # Count the vote in the table
        try:
            name, position = game.table.set_player_position(self.channel_name)
        except ValueError as e:
            await self._send_fail_message(e)
            return
        # if DEBUG:
            # await self.send(repr(game.table._get_player_by_channel(self.channel_name)))
        # Send ur new position to everyone in the game
        await self.channel_layer.group_send(self.game_id,
            {
                'type':'POSITION',
                'player':name,
                'position':position
            }
        )

        ordering_completed = game.table.voting_is_finished()
        if ordering_completed:
            game.table.order_players()
            game.set_ordering_free()
            # await self.channel_layer.group_send(
                # self.game_id,
                # {
                    # 'type':'announce_order'
                # }
            # )
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
        # if not game.voting:
            # await self._send_fail_message('No current voting process')
            # return
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
    # async def play_bet(self, game_id:str, amount:int):
        # betting_round, pot, side_pots, max_bet, _, current_player, players, player_order, all_in = self.get_round_info(game_id)
        # bet_amount = int(amount)
        # # Make sure player is up to play
        # if not (curr_p:=player_order[current_player]) == self.channel_name:
            # await self._send_fail_message('It is not your turn to play')
            # return
        # # Make sure player has enough to bet
        # if bet_amount > self.games[game_id]['players'][curr_p]['chips']:
            # await self._send_fail_message('You do not have enough chips to bet that much')
            # return
        # # Make sure the bet is big enough (dont check for doubling on the raise for now)
        # if bet_amount < max_bet:
            # await self._send_fail_message(f'Bet must be at least equal to the max: {max_bet}')
            # return
        # # If the bet is over the max_bet, update it
        # self.games[game_id]['round']['max_bet'] = max(max_bet,bet_amount)
        # # Update game state
        # ## Check if player is going all in
        # if bet_amount == self.games[game_id]['players'][self.channel_name]['chips']:
            # self.games[game_id]['round']['all_in'].append(self.channel_name)
            # self.games[game_id]['round']['players'].__delitem__(self.channel_name)
        # ## Add bet to pot if no one is all in
        # if all_in == []:
            # self.games[game_id]['round']['pot'] += bet_amount
            # # Add bet amount to player dict
            # self.games[game_id]['round']['players'][self.channel_name] += bet_amount
        # else:
            # # Hash a tuple of the players in order and add the pot amount
            # self.games[game_id]['round']['side_pots'][tuple(players.keys())] += bet_amount
        # # Take money out of personal chips
        # self.games[game_id]['players'][self.channel_name]['chips'] -= bet_amount
        # await self.advance_bet()

        
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
        _,_,_,max_bet, starting_player, current_player, players, player_order,_ = self.get_round_info(game_id)
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
    # def get_round_info(self, game_id:str):
        # bet_round = self.games[game_id]['round']
        # betting_round, pot, side_pots, max_bet, starting_player, current_player, players, player_order, all_in = bet_round.values()
        # return betting_round, pot, side_pots, max_bet, starting_player, current_player, players, player_order, all_in

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
        game.table.reset_voting() # Reset voting game state
        game.set_voting_busy() # set game state
        # Announce voting param
        agenda = event['voting_param']
        await self.send(json.dumps({'type':'START_VOTE','voting_param':agenda}))

    # This function gets the vote winner and announces it // resets game voting
    async def announce_vote_result(self, event):
        await self.send(json.dumps({'status':'VOTE_RESULT','result':event['vote']}))
        # self._set_game_active(event['game_id'], 1) # Turn off voting busy for the game
        game = self.games[self.game_id]
        game.table.reset_voting()
        game.set_voting_free()

    # Announce to everyone else when someone makes a bet so their clients update
    async def announce_bet(self, event):
        await self.send(json.dumps({'type':'PREV_BET','player':event['player'],'bet_size':event['bet_size']}))

    async def announce_pot(self, pot):
        await self.send(pot)

    async def announce_positions(self, event:dict[str]):
        await self.send(json.dumps({'type':'POSITIONS','positions':event['positions']}))

    async def announce_position(self, event:dict[str]):
        await self.send(json.dumps({"type":'ORDERING','player':event['player'],'c_count':event['c_count']}))

    async def announce_current_turn(self, event:dict[str]):
        await self.send(json.dumps({'type':'TO_PLAY','player':event['player'], 'owed':event['owed']}))

    async def announce_new_round(self, event:dict[str]):
        await self.send(json.dumps({
            'type':'NEW_ROUND',
            'dealer': event['dealer']
        }))

    async def announce_new_bet_round(self, event:dict[str]):
        bet_rounds = {1:'flop',2:'turn',3:'river'}
        await self.send(json.dumps({
            'type':'NEW_BET_ROUND',
            'bet_round':bet_rounds[event['bet_round']]
        }))

    async def announce_fold(self, event:dict[str]):
        await self.send(json.dumps({'type':'FOLD','player':event['player']}))

    async def announce_new_player(self, event:dict[str]):
        await self.send(json.dumps({
            'type':'NEW_PLAYER',
            'player':event['player'],
            'c_count':event['c_count'],
            'position':event['position']
        }))

    async def announce_player_leave(self, event:dict[str]):
        await self.send(json.dumps({
            'type':'PLAYER_LEAVE',
            'player': event['player'],
        }))

    async def announce_pot(self, event:dict[str]):
        if DEBUG:
            await self.send(json.dumps({
                'type':'POT',
                'pot':event['pot']
            }))

    async def announce_decide_winners(self, event:dict[str]):
        await self.send(json.dumps({
            'type': 'DECIDE_WINNERS',
            'options': event['options'],
        }))
    
    async def announce_winners(self, event:dict[str]):
        game = self.games[self.game_id]
        if max(game.table.vote_count, key=game.table.vote_count.get)==False or game.table.vote_count[True]==0:
            await self.send(json.dumps({'type':'FAILED_VOTE'}))
            return
        await self.send(json.dumps({'type':'END_VOTE'}))
        await self.send(json.dumps({
            'type':'ANNOUNCE_WINNERS',
            'event':str(event)
        }))
        if self.channel_name == game.table.players[0].channel:
            game.table.pay_winners()
            await self.channel_layer.group_send(self.game_id, {
                'type':'announce_pay_out'
            })

    async def announce_pay_out(self, event:dict[str]):
        game = self.games[self.game_id]
        await self.send(json.dumps({'type':'PAY_OUT', 'players':[{'player':x.name,'c_count':x.c_count} for x in game.table.players]}))

    async def announce_vote_pay(self, event:dict[str]):
        game = self.games[self.game_id]
        serializable_winners = game.table.get_serializable_winners()
        await self.send(json.dumps({
            'type':'VOTE_PAY',
            'options': game.table.get_serializable_winners()
        }))
        
    async def announce_claimed_win(self, event:dict[str]):
        await self.send(json.dumps({
            'type': 'CLAIMED_WIN',
            'pot_id': event['pot_id'],
            'player': event['player']
        }))

    # async def announce_vote_winners(self, event:dict[str]):
        # game = self.games[self.game_id]
        # _, pot_amount, pot_id = event.values()
        # if pot_id == -1:
            # eligible = [x for x in game.table.players if not (x.folded or x.all_in)]
        # else:
            # eligible = [x for x in game.table.pot.pots[pot_id].eligible if not x.folded]
        # await self.send(json.dumps({'type':'VOTE_WINNERS', 'eligible':str(eligible)}))

    # async def announce_winners(self, event:dict[str]):
        # paid_out = await self.pay_winners(pot_amount=event['pot_amount'], pot_id=event['pot_id'])
        # if not paid_out:
            # return
        # game = self.games[self.game_id]
        # for winner in game.table.winners:
            # await self.send(json.dumps({
                    # 'type':'WINNER',
                    # 'player':winner.name,
                    # 'amount':event['pot_amount']//len(game.table.winners),
            # }))
        # # The first winner should call for the next winner to be decided
        # if self.channel_name == game.table.winners[0].channel:
            # await self.decide_winners()
        # # await self.send(json.dumps({'type':'WINNERS', 'winners':str(game.table.winners)}))

    # async def announce_voted_winners(self, event:dict[str]):
        # paid_out, winners = await self.pay_voted_winners(pot_amount=event['pot_amount'], pot_id=event['pot_id'])
        # if not paid_out:
            # return
        # for winner in winners:
            # await self.send(json.dumps({
                    # 'type':'WINNER',
                    # 'player': winner,
                    # 'amount': event['pot_amount'] // len(winners)
            # }))

    # async def announce_paid_out(self, event:dict[str]):
        # await self.send(json.dumps({'type':'PAID_OUT'}))

    async def announce_pots(self, event:dict[str]):
        await self.send(json.dumps({
            'type': 'POTS',
            'pots': event['pots']
        }))

    # async def announce_start_claims(self, event:dict[str]):
        # await self.send(json.dumps({
            # 'type': 'START_CLAIMS'
        # }))

    async def announce_settings(self):
        game = self.games[self.game_id]
        await self.send(json.dumps({
            'type':'SETTINGS',
            'settings': game.table.settings
        }))

    # async def announce_time_up(self, event):
        # await self.send(json.dumps({'type':'TIME_UP'}))
    

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
        await self.send(json.dumps({'type':'FAIL','message':str(msg)}))
        return

    async def _send_debug_message(self, msg:str) -> None:
        await self.send(json.dumps({'type':'DEBUG', 'debug':str(msg)}))

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

