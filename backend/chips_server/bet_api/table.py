'''
TABLE
holds all the information for each table (i.e. a list of players in a game)
'''
from bet_api.player import Player
from bet_api.bet import Bet
from bet_api.pot import Pots
from typing import Optional, List

class Table:
    def __init__(self):
        # @var players // all the players in the game -- sorted
        self.players:List[Player] = list()
        # @var pot // Holds all the pot state
        self.pot = Pots()

        # @var dealer // tracks which position is the dealer
        self.dealer = 0

        # @var settings // game settings
        self.settings = self.default_settings()

        # keep track of ordering count
        self.count = 0
        # @var vote_count // storing votes from each player (anonymously)
        self.vote_count = {True:0,False:0} # False=reject, True=accept

        # @var blinds
        # self.small_blind = self._get_next_player(self.players[self.dealer])
        # self.big_blind = self._get_future_player(self.players[self.dealer], 2)
        
        # @var min_raise // holds the smallest amount a player can raise by
        self.min_raise_set:bool = False
        self.min_raise:int = 0
        # @var curr_bet // bets the minimum amount a player needs to bet
        self.curr_bet:int = 0

    # BET FUNCTIONS
    def place_bet(self, channel:str, bet_size:int) -> None:
        player = self._get_player_by_channel(channel)
        # Make sure the bet is legit
        valid, err_msg = player.bet_is_valid(bet_size)
        if not valid:
            raise ValueError(err_msg)
        # Then add the bet to the player obj
        player.add_bet(bet_size)

        # Create a new bet to add to the pot
        bet = Bet(bet_size=bet_size, player=player)
        ## Then add the bet to the pot
        self.pots += bet


    def fold(self, channel:str) -> None:
        player = self._get_player_by_channel(channel)
        player.fold()


    # PLAYER FUNCTIONS
    def add_player(self, channel:str, name:str='', c_count:int=None) -> None:
        if c_count is None:
            c_count = self.settings['default_count']
        if name == '':
            name = 'Player ' + str(len(self.players))
        new_player = Player(channel=channel, name=name, c_count=c_count) # Make a player
        new_player.position = len(self.players) # put them in the last position
        self.players.append(new_player) # Add them to the table
    
    def remove_player(self, channel:str) -> None:
        player = self._get_player_by_channel(channel)
        self.players.remove(player)

    def set_player_position(self, channel:str) -> None:
        player = self._get_player_by_channel(channel)
        if player.voted:
            return
        player.position = self.count
        player.voted = True
        self.count += 1
 
    def order_players(self) -> None:
        self.players.sort(key=lambda x: x.position)

    def name_is_available(self, name:str) -> bool:
        for player in self.players:
            if player.name == name:
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
    def _get_next_player(self, curr_player:Player) -> Player:
        if curr_player.position + 1 == len(self.players):
            return self.players[0]
        else:
            return self.players[curr_player.position+1]

    def _get_future_player(self, curr_player:Player, future_player:int) -> Player:
        for _ in range(future_player):
            curr_player = self._get_next_player(curr_player.position)
        return curr_player

    def _get_player_by_channel(self, channel:str) -> Player:
        for player in self.players:
            if player.channel == channel:
                return player
        raise KeyError('The player you are looking for is not at this table')

    # BUILT IN FUNCTIONS
    def __repr__(self) -> str:
        output = str('='*8 + 'TABLE' + '='*8)
        for player in self.players:
            output += f'\n\t{player.name}:[{player.c_count=},{player.position=}]'
        return output
