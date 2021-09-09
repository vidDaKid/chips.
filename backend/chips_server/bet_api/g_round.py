'''
This class holds all of the information for each round and handles
betting. The bets are sent the to the pot class in pot.py
'''
from typing import List
from bet_api.pot import Pots

class Round:
    def __init__(self, starting_player:int=0):
        # @var bet_rnd // current betting round 0 -> 4 == pre-flop -> river
        self.bet_rnd:int = 0

        # @var sm_bet // smallest bet so you know the minimum size of the raise (curr_bet + sm_bet) 
        self.sm_bet:int = 0

        # @var min_bet // minimum amount you can bet (i.e. current bet)
        self.min_bet:int = 0

        # @var pot // holds the pot state - <classtype Pot>
        self.pot = Pots()

        # @var st_player // starting player for the round (increases each roung)
        self.st_player:int = starting_player

        # @var curr_player // current player
        self.curr_player:int = self.st_player

        # @var tot_players // total number of players in game
        self.tot_players:int

        # @var last_raise // last person to raise the bet (person before this is the last to play)
        self.last_raise:int = self.st_player
        # @var rnd1_last_raise // the last person to raise just for the pre flop (to account for blinds)
        self.rnd1_last_raise:int = self.st_player + 2

        # @var state // game state for each player (bets per round & all_in status)
            # I had a decision here to store players as integers & just reorder the main dict each time
            # but i decided it'd be better just to take up a lil extra memory to store the actual player ids
        # self.state:dict[dict[int and bool]] = dict() # {'player_id': {'curr_bet': 0, 'all_in': False, 'fold': False }}

    # HELPER FUNCTIONS
    def reset(self) -> None:
        self.pot.reset()
        # for player in self.state:
            # player.reset_round()

    # IN GAME FUNCTIONS
    def place_bet(self, player:'Player', bet_size:int) -> None:
        if self.min_bet > bet_size:
            raise ValueError(f'Bet size must be at least the minimum bet: {self.min_bet}')
        # Catch raises that don't raise at least over the smallest bet
        if (bet_size > self.min_bet) and not ( bet_size > (self.min_bet + self.sm_bet) ):
            raise ValueError(f'Raise must be at least {self.sm_bet} over the current bet')
        if bet_size > self.min_bet:
            self.last_raise = self.curr_player
        self.pot += bet_size
        player.add_bet(bet_size)

    def place_all_in_bet(self, player:'Player', bet_size:int) -> None:
        self.pot.add_all_in(bet_size)
        player.go_all_in()

    def fold(self, player:'Player') -> None:
        player.fold()

    # PLAYER MOVEMENT FUNCTIONS
    def advance_bet(self) -> None:
        self.curr_player += 1
