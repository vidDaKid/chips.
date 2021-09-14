'''
This module holds all the information for each individual player
'''
from typing import Optional, List

class Player:
    def __init__(self, channel:str, name:str=None, c_count:Optional[int]=None):
        # @var channel // self.channel_name in django channels
        self.channel = channel
        # @var position // seat position at table
        self.position:int = -1
        # @var c_count // chip count (total chips)
        self.c_count:int = c_count or 0
        # @var name // player nickname
        self.name:str = name or 'Player ' + str(self.position)

        # ROUND STATE
        ## @var curr_bet // the current bet for the betting round
        self.curr_bet:int = 0
        ## @var curr_rnd_bet // current bet for the player for the round
        # self.curr_rnd_bet:int = 0

        ## @var all_in // whether or not the player is all in
        self.all_in:bool = False
        ## @var folded // whether or not player has folded
        self.folded:bool = False
        ## @var voted // keeps track of if the player has voted
        self.voted:bool = False

    def reset_round(self) -> None:
        self.curr_bet = 0
        # self.curr_rnd_bet = 0
        self.all_in, self.folded = False, False

    # def next_bet_round(self) -> None:
        # self.curr_rnd_bet = 0

    def __repr__(self) -> str:
        return str({'Position':self.position, 'Chip Count':self.c_count, 'Name':self.name})

# BET FUNCTIONS
    def add_bet(self, bet_size:int) -> None:
        # Make sure bet is valid
        if not self.bet_is_valid(bet_size):
            raise ValueError('Bet size is greater than amount of chips remaining')
        ## check if the bet is all in, if so set player.all_in to True
        if self.bet_is_all_in(bet_size):
            self.all_in = True
        # Add the bet_size to the state
        self.curr_bet += bet_size
        # self.curr_rnd_bet += bet_size
        self.c_count -= bet_size

    # def go_all_in(self) -> None:
        # self.curr_bet += self.c_count
        # self.c_count = 0
        # self.all_in = True

    def bet_is_all_in(self, bet_size:int) -> bool:
        if self.c_count == bet_size:
            return True
        return False
    
    def bet_is_valid(self, bet_size:int) -> bool:
        if bet_size > self.c_count:
            return False, 'The bet size is greater than your available chips'
        if bet_size < 0:
            return False, 'Bets must be positive integers'
        return True, ''

    def fold(self) -> None:
        self.folded = True
    
# UPDATE FUNCTIONS
    def change_name(self, new_name:str) -> str:
        if type(new_name)!=str:
            raise TypeError('Name must be a string')
        self.name = new_name
        return new_name

    def vote(self) -> None:
        self.voted = True

# BUILT IN
    def __hash__(self) -> str:
        return self.channel
