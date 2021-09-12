'''
This class holds all of the information for each round and handles
betting. The bets are sent the to the pot class in pot.py
'''
from typing import List
from bet_api.pot import Pots

class Round:
    def __init__(self, starting_player:int=0):
        # @var players // all the players in the game
        self.players:List[Player] = list()

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

        # @var last_raise // last person to raise the bet (person before this is the last to play)
        self.last_raise:int = self.st_player
        # @var rnd1_last_raise // the last person to raise just for the pre flop (to account for blinds)
        self.rnd1_last_raise:int = self.get_future_player(self.st_player, 2) # Get the player 2 after the small blind

    # HELPER FUNCTIONS
    # def reset(self) -> None:
        # self.pot.reset()
        # for player in self.state:
            # player.reset_round()

    # IN GAME FUNCTIONS
    def place_bet(self, bet_size:int) -> None:
        if self.min_bet > bet_size:
            raise ValueError(f'Bet size must be at least the minimum bet: {self.min_bet}')
        # Catch raises that don't raise at least over the smallest bet
        if (bet_size > self.min_bet) and not ( bet_size > (self.min_bet + self.sm_bet) ):
            raise ValueError(f'Raise must be at least {self.sm_bet} over the current bet')
        if bet_size > self.min_bet:
            self.last_raise = self.curr_player
        self.pot += bet_size
        player = self.players(channel)
        player.add_bet(bet_size)

    def place_all_in_bet(self, player:'Player', bet_size:int) -> None:
        self.pot.add_all_in(bet_size)
        player.go_all_in()

    def fold(self, player:'Player') -> None:
        player.fold()

    ## GAME STATUS FUNCTIONS
    def get_current_turn(self) -> int:
        return self.curr_player

    def check_if_iteration_finished(self) -> bool:
        last_raise = self.rnd1_last_raise if self.bet_rnd==0 else self.last_raise
        if self.get_next_player(self.curr_player) == last_raise:
            return True
        return False
    
    @property
    def real_last_raise(self) -> int:
        return self.rnd1_last_raise if self.bet_rnd==0 else self.last_raise

    @property
    def total_players(self) -> int:
        return len(self.players)

    # PLAYER MOVEMENT FUNCTIONS
    def advance_bet(self) -> None:
        self.curr_player += 1

    # def get_next_player(self, curr_player:int) -> int:
        # if curr_player + 1 == self.total_players:
            # return 0
        # else:
            # return curr_player + 1

    # def get_future_player(self, curr_player:int, turns_ahead:int) -> int:
        # for _ in range(turns_ahead):
            # curr_player = self.get_next_player(curr_player)
        # return curr_player

    def advance_bet_round(self) -> None:
        self.bet_rnd += 1
        self.sm_bet = 0
        self.min_bet = 0
        self.update_last_raise(self.st_player)

    # PRIVATE HELPER FUNCTIONS
    def update_last_raise(self, new_val:int) -> None:
        if self.bet_rnd==0:
            self.rnd1_last_raise = new_val
        else:
            self.last_raise = new_val
