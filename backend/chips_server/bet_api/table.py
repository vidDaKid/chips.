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

        # @var dealer // tracks which position is the dealer
        self.dealer = 0

        # @var blinds
        # self.small_blind = self._get_next_player(self.players[self.dealer])
        # self.big_blind = self._get_future_player(self.players[self.dealer], 2)
        
        # @var pot // Holds all the pot state
        self.pot = Pots()
        
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
    def add_player(self, channel:str, name:str, c_count:int) -> None:
        new_player = Player(channel=channel, name=name, c_count=c_count) # Make a player
        new_player.position = len(self.players) # put them in the last position
        self.players.append(new_player) # Add them to the table

    def set_player_position(self, channel:str, position:int) -> None:
        player = self._get_player_by_channel(channel)
        player.position = position
 
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
        except KeyError as e:
            return False
        else:
            return True
    
    def cast_bool_vote(self, channel:str, vote:bool) -> None:
        player = self._get_player_by_channel(channel)
        player.vote()

    # SETUP FUNCTIONS
    def reset_voting(self) -> None:
        for player in self.players:
            player.voted = False
    
    def reset_ordering(self) -> None:
        for player in self.players:
            player.position = -1

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
