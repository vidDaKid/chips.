'''
TABLE
holds all the information for each table (i.e. a list of players in a game)
'''
from bet_api.player import Player
from bet_api.bet import Bet, RoundBets
from bet_api.pot import Pots
from typing import Optional, List

class Table:
    def __init__(self):
        # @var players // all the players in the game -- sorted
        self.players:List[Player] = list()
        # @var queue // all the non folded players in the current iteration
        self.queue:List[Player] = list()
        # @var removed // players that lost connection, may join back
        self.removed:List[Player] = list()

        # @var pot // Holds all the pot state
        self.pot = Pots()

        # @var bet_round // Tracks the current round we're in
        self.bet_round:int = 0 # 0->4 == pre_flop -> river

        # @var dealer // tracks which position is the dealer
        self.dealer = 0

        # @var settings // game settings
        self.settings = self.default_settings()

        # keep track of ordering count
        self.count = 0
        # @var vote_count // storing votes from each player (anonymously)
        self.vote_count = {True:0,False:0} # False=reject, True=accept

        # @var min_raise // holds the smallest amount a player can raise by
        self.min_raise_set:bool = False
        self.min_raise:int = 0
        # @var curr_bet // bets the minimum amount a player needs to bet
        self.curr_bet:int = 0

        # @var first_bet // keeps track of whether or not the first player has bet
        self.first_bet:bool = False
        # @var last_raise // the last person to raise the bet (round ends before them)
        self.last_raise:Player = None
        # @var curr_player // the player who is up to play
        self.curr_player:Player = None

    # RESET FUNCTIONS
    def reset_bet_round(self) -> None:
        self.first_bet = False
        self.last_raise = self.curr_player = None
        self.min_raise_set = False
        self.min_raise = self.curr_bet = 0
        ## Reset player counts
        for player in self.players:
            player.curr_bet = 0
        ## iterate bet round
        self.bet_round += 1

    def reset_round(self) -> None:
        # Maybe get rid of ppl w no chips too ?
        self.reset_bet_round()
        self.bet_round = 0
        self.pot = Pots()
        ## Reset players
        for player in self.players:
            self.folded = False
            self.all_in = False
        ## Iterate starting dealer
        self.dealer = self._get_future_index(1)

    # BET FUNCTIONS
    def place_bet(self, channel:str, bet_size:int) -> dict[str] and str:
        player = self._get_player_by_channel(channel)
        # Make sure player is up to vote
        if self.curr_player is not player:
            raise KeyError('You are not currently up to play')
        # Make sure the bet is legit
        valid, err_msg = player.bet_is_valid(bet_size)
        if not valid:
            raise ValueError(err_msg)

        if bet_size < (o:=self.amount_owed(channel)):
            raise ValueError(f'Error! You must bet at least {o}')

        # Check for raise
        total_bet = bet_size + player.curr_bet
        if total_bet > self.curr_bet:
            # u have to raise by the smallest bet, otherwise its not a valid raise
            if total_bet < (self.min_raise + self.curr_bet):
                raise ValueError(f'Raises must be at least {self.curr_bet} over the current bet')
            # update new current bet and new last raiser
            self.curr_bet = total_bet
            self.last_raise = player
            # Update the min_raise if no one has set it yet
            if ( not self.min_raise_set ) and ( bet_size > 0 ):
                self.min_raise = bet_size
                self.min_raise_set = True

        if not self.first_bet:
            self.first_bet = True
            self.last_raise = player

        # Check for new betting round
        if self.queue[-1] is self.last_raise:
            ''' NEW BET ROUND '''
            next_round:bool = self.next_bet_round()
            # if new_round:
                # self.new_round()
            return {'player':player.name, 'bet_size':bet_size}, self.curr_player.name, True, next_round
        
        # Add the bet to the player
        player.add_bet(bet_size)
        # move to the next better and send it to the consumer
        self.advance_bet()

        # Announcements to send to client
            # [ bet_announcement, to_play, new_bet_round, new_round ]
        return {'player':player.name, 'bet_size':bet_size}, self.curr_player.name, False, False

        # Create a new bet to add to the pot
        # bet = Bet(bet_size=bet_size, player=player)
        ## Then add the bet to the pot
        # self.pots += bet

    def play_blinds(self, player_sb:Player=None, player_bb:Player=None) -> None:
        # Get the blinds
        player_sb = player_sb or self._get_next_player(self.players[self.dealer])
        player_bb = player_bb or self._get_future_player(2, self.players[self.dealer])
        # Get blinds
        big_blind = self.settings['big_blind']
        small_blind = round(big_blind/2)
        # Add small_blind bet
        sb_bet_size = min(small_blind, player_sb.c_count)
        player_sb.add_bet(sb_bet_size)
        # Add big blind bet
        bb_bet_size = min(big_blind, player_bb.c_count)
        player_bb.add_bet(bb_bet_size)
        # Update game state
        self.min_raise = big_blind
        self.min_raise_set = True
        self.curr_bet = big_blind

    def fold(self, channel:str) -> str:
        player = self._get_player_by_channel(channel)
        player.fold()
        self.advance_bet()
        return player.name

    # Starts the round and returns a dictionary containing the dealer, small blind, & big blind
    def start_round(self) -> dict[str and Player]:
        # We want to create a queue of everyone playing in this iteration
        # Since the st_player is dealer, we need the player 3 after in order to start after BB
        ## Order players
        self.order_players()
        ## Get the starting player
        st_player = self.players[self.dealer]
        ## Make a queue starting from the 3rd player after the starting player (excluding blinds)
        self.create_queue(pre_flop=True)
        # update game state
        # Get the game ready for the round
        ## Reset the pot
        self.pot.reset()
        ## Get both the blinds
        player_sb = self._get_next_player(self.players[self.dealer])
        player_bb = self._get_future_player(2, self.players[self.dealer])
        ## add bets to the blinds
        self.play_blinds()
        # Return a dictionary of the dealer & blinds
        return {'dealer':st_player, 'small_blind':player_sb, 'big_blind':player_bb}

    def end_round(self) -> None:
        ''' VOTE ON WINNER '''
        self.dealer += 1
        for player in self.players:
            player.reset_round()

    # Add bets to the pot
    def end_bet_round(self) -> None:
        ''' ADD BETS TO POT '''
        pass

    # For now it just returns a bool of whether or not we need to go to the next round
    def advance_bet(self) -> None:
        self.curr_player = self.queue.pop()
        if self.queue == []:
            # Check for whether or not its preflop
            pre_flop = True if self.bet_round == 0 else False
            self.create_queue(update_curr=False, pre_flop=pre_flop)

    # def start_betting_round(self) -> None:
        # # Same as start_round
        # self.queue = iter([x for x in self.players[self.dealer+1:] + self.players[:self.dealer+1] if not x.folded])
        # # Make sure old side pots are deactivated for new round
        # self.pot.next_bet_round()

    # Advances the bet round and returns True if its the end of the round
    def next_bet_round(self) -> bool:
        # Add bets to pot
        bet = RoundBets()
        for player in self.players:
            bet.add_bet_from_player(player)
        self.pot += bet
        # Check for new round
        if self.bet_round == 3:
            # NEW ROUND #
            self.reset_round()
            self.create_queue()
            return True
        # Advance bet round state
        self.reset_bet_round()
        # get a new queue for the next round
        self.create_queue()
        return False

    def get_bets(self) -> None:
        output = dict()
        for player in self.players:
            output[player.name] = player.curr_bet
        return output

    # PLAYER FUNCTIONS
    def add_player(self, channel:str, name:str='', c_count:int=None, position:int=None) -> str and int:
        if self.player_is_in_game(channel=channel):
            player = self._get_player_by_channel(channel=channel)
            return player.name, player.c_count
        if c_count is None:
            c_count = self.settings['default_count']
        if name == '':
            name = 'Player ' + str(len(self.players))
        elif not self.name_is_available(name):
            raise ValueError('This name is already taken')
        if not position:
            position = len(self.players)
        new_player = Player(channel=channel, name=name, c_count=c_count, position=position) # Make a player
        # new_player.position = len(self.players) # put them in the last position
        self.players.append(new_player) # Add them to the table
        return name, c_count, position,  new_player.secret
    
    def remove_player(self, channel:str) -> None:
        player = self._get_player_by_channel(channel)
        self.players.remove(player)
        self.removed.append(player)

    def update_player_secret(self, channel:str, secret:str) -> str and int:
        for player in list(self.removed):
            if player.secret == secret:
                self.removed.remove(player)
                self.players.append(player)
                if self.position_is_available(player.position):
                    player.position = position
                else:
                    raise ValueError('That position is not available')
                player.channel = channel
                self.order_players()
                return player.name, player.c_count, player.position
        else:
            raise KeyError('No player found with the secret key you provided')

    def set_player_position(self, channel:str) -> None:
        player = self._get_player_by_channel(channel)
        if player.voted:
            raise ValueError('Player has already voted')
        player.position = self.count
        player.voted = True
        self.count += 1
        return player.name, player.position
 
    def order_players(self) -> None:
        self.players.sort(key=lambda x: x.position)

    def name_is_available(self, name:str) -> bool:
        for player in self.players:
            if player.name == name:
                return False
        return True

    def position_is_available(self, position:int) -> bool:
        for player in self.players:
            if player.position == position:
                return False
        return True

    def player_is_in_game(self, channel:str)  -> bool:
        try:
            self._get_player_by_channel(channel)
        except KeyError:
            return False
        else:
            return True
    
    def cast_bool_vote(self, channel:str, vote:bool) -> None:
        player = self._get_player_by_channel(channel)
        player.vote()
        self.vote_count[vote] += 1

    def amount_owed(self, channel:str='') -> int:
        if not channel:
            return self.curr_bet - self.curr_player.curr_bet
        player = self._get_player_by_channel(channel)
        return self.curr_bet - player.curr_bet

    # SETUP FUNCTIONS
    def reset_voting(self) -> None:
        for player in self.players:
            player.voted = False
        self.vote_count = {True:0,False:0}
    
    def reset_ordering(self) -> None:
        self.count = 0
        for player in self.players:
            player.position = -1
            player.voted = False
    
    def voting_is_finished(self) -> bool:
        for player in self.players:
            if not player.voted:
                return False
        else:
            return True
    
    def get_verdict(self) -> bool:
        return max(self.vote_count, key=self.vote_count.get)
    
    # SETTINGS FUNCTIONS
    def default_settings(self) -> dict[int]:
        settings = {
            'default_count': 200,
            'big_blind': 4,
            # Add in any advance settings that you want later
        }
        return settings

    def update_settings(self, new_settings:dict[str and int]):
        # Do some checking / error handling here at some point
        self.settings = new_settings


    # HELPER FUNCTIONS
    ## Create a new queue and update the current player
    def create_queue(self, pre_flop:bool=False, update_curr:bool=True) -> None:
        # Create a new queue for the next round
        num_after_dealer = 3 if pre_flop else 1 # Starts after bb if preflop
        # st_player = self._get_future_player(num_after_dealer)
        # st_idx = self.players.index(st_player)
        st_idx = self._get_future_index(num_after_dealer)
        temp_q = reversed(self.players[st_idx:] + self.players[:st_idx])
        self.queue = [x for x in temp_q if not (x.folded or x.all_in)]
        # Get the first player to play
        if update_curr:
            self.curr_player = self.queue.pop()

    ## Get the position of the next player safely
    def _get_next_player(self, player:Player=None) -> Player:
        # assume player is dealer if not player
        if not player:
            player = self.players[self.dealer]
        if (idx:=self.players.index(player)) == (len(self.players) - 1):
            return self.players[0]
        else:
            return self.players[idx+1]
        # If theres no player, then they want the next to play, check the queu
        # if (not player) or (player is self.curr_player):
            # return self.queue[-1]
        # Otherwise get the player one before the one they want
        # player_idx = self.queue.index(player)
        # return self.queue[player_idx-1]

    # This entire function just calls _get_next_player over and over again
    def _get_future_player(self, future_player:int, player:Player=None) -> Player:
        # Get player based on play position if not specified
        if not player:
            # Will find future player after dealer
            player = self.players[self.dealer]
        for _ in range(future_player):
            player = self._get_next_player(player=player)
        return player

    def _get_future_index(self, future_index:int, st_index:int=None) -> int:
        st_index = st_index or self.dealer
        # Get the summed index and get rid of overflow with a modulus
        return (st_index+future_index) % len(self.players)
    
    # Gets the player w the lowest position
    def _get_starting_player(self) -> Player:
        return min(self.players, key=lambda x: x.position)

    def _get_player_by_channel(self, channel:str) -> Player:
        for player in self.players:
            if player.channel == channel:
                return player
        raise KeyError('The player you are looking for is not at this table')

    @property
    def total_players(self) -> int:
        return len(self.players)

    # BUILT IN FUNCTIONS
    def __repr__(self) -> str:
        output = str('='*8 + 'TABLE' + '='*8)
        for player in self.players:
            output += f'\n\t{player.name}:[{player.c_count=},{player.position=}]'
        return output
