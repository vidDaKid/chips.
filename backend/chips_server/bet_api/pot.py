'''
This contains all the logic for handling bets in the pot. Obviously.
'''
from collections import defaultdict
from bet_api.bet import Bet, RoundBets
from typing import List, Optional

class Pot:
    def __init__(self, value:int=0, max_bet:int=float('inf')):
        # @var val // value of the current pot
        self.val:int = value

        # @var max_bet // max bet for this pot (if someone goes all in, this becomes that amount)
            # In the case that a second person goes all in for lower, the max bet is dropped and the difference is turned into a new pot
        self.max_bet:int = max_bet

        # @var eligible // players that contributed to the pot are eligible to win it
        self.eligible:List[str] = list() # list of channels

    @classmethod
    def new_all_in_pot(cls, bet_size:int, inherited_val:int, channel:str):
        new_pot = cls(value=bet_size+inherited_val, max_bet=bet_size)
        new_pot.eligible.append(channel)
        return new_pot


    # MAIN FUNCTIONALITY
    def add_all_in(self, bet:Bet) -> None:
        self.val += bet.bet_size
        self.max_bet = bet.bet_size
        self.bets[bet.player] += bet.bet_size
        return self

    # def bet_size_allowed(self, player:'Player'):
        # if self.max == float('inf'):
            # return float('inf')
        # return self.max - self.bets[player]

    @classmethod
    def new_pot_from_bet(cls, bet:Bet) -> 'Pot':
        new_pot = cls(bet.bet_size)
        new_pot.bets[bet.player] = bet.bet_size
        return new_pot

    @classmethod
    def new_pot_from_all_in_bet(cls, bet:Bet) -> 'Pot':
        new_pot = self.new_pot_from_bet(bet)
        new_pot.max_bet = bet.bet_size
        return new_pot

    # BUILT IN
    def __add__(self, bet:tuple[int and str]) -> None:
        return self.val + bet[0]
        # if type(bet) == tuple:
            # bet_size:int, player:'Player' = bet
            # if bet_size > self.max_bet:
                # raise ValueError('Bet is larger than max bet value')
            # new_bets = dict(self.bets)
            # new_bets[player] += bet_size
            # return (self.val + num.val, new_bets)
        # else:
            # raise TypeError('A pot can only be added to an `int` or another `Pot`')

    # Accepts a tuple of a bet_size and channel_name
    def __iadd__(self, bet:tuple[int and str]) -> int:
        self.val += bet[0]
        self.eligible.append(bet[1])
        return self
        # if isinstance(bet, Bet):
            # if bet.bet_size > self.max_bet:
                # raise ValueError('Bet is larger than max bet value')
            # self.val += bet.bet_size
            # self.bets[bet.player] += bet.bet_size
            # return self
        # else:
            # raise TypeError('Only a `Bet` object can be added to a pot')

    def __repr__(self) -> str:
        return str({'Value':self.val,'max bet':self.max_bet,'eligible':self.eligible})
        # return f'\tValue: {self.val}\n\tMax Bet: {self.max_bet}'

class BottomlessPot:
    def __init__(self, val:int=0):
        self.val = val

    def __add__(self, other:int) -> int:
        return self.val + other

    def __iadd__(self, other:int) -> int:
        self.val += other
        return self

    def empty(self) -> None:
        self.val = 0


class Pots:
    def __init__(self):
        # @var pots // list of all the side pots
        self.pots:List[Pot] = list()
    
        # @var bottomless_pot // the pot without a limit 
        self.bottomless_pot:BottomlessPot = BottomlessPot()
    
    # Resets at the beginning of each new round
    def reset(self) -> None:
        self.pots = list()
        self.bottomless_pot = BottomlessPot()

    def add_bet_round_bets(self, bets:RoundBets) -> None:
        bets.sort()
        for bet in bets.bets:
            # 1st put whatever u can in each pot
            for pot in self.pots:
                amount = min(bet.bet_size, pot.max_bet)
                pot += (amount, bet.channel)
                bet.bet_size -= amount
            if ( bet.bet_size > 0 ) and bet.all_in:
                new_pot = Pot.new_all_in_pot(bet.bet_size, self.bottomless_pot.val, bet.channel)
                self.pots.append(new_pot)
                self.bottomless_pot.empty()
                bet.bet_size = 0
            elif ( bet.bet_size > 0 ) and not bet.all_in:
                self.bottomless_pot += bet.bet_size
                bet.bet_size = 0

    # Get rid of all the max bets
    def next_bet_round(self) -> None:
        for pot in self.pots:
            if pot.max_bet != float('inf'):
                pot.max_bet = 0
                # pot.

    # HELPER FUNCTIONS
    def _add_safe(self, bet:Bet) -> None:
        if not isinstance(bet, Bet):
            raise TypeError('Pots can only be added to a`Bet` object')
        for pot in self.pots:
            # If the bet is smaller than the max, just add the bet and move on
            if pot.max_bet >= bet.bet_size:
                # empty the bet into the pot n move on if not all in
                if not bet.all_in:
                    pot += bet
                    bet.bet_size = 0
                    break
                # Otherwise, empty the bet & drop the max bet
                else:
                    pot.add_all_in(bet)
                    bet.bet_size = 0
                    break
            # Otherwise, add what you can to the pot, then move the next one
            else:
                new_bet_size = pot.bet_size_allowed(bet.player)
                pot += new_bet_size
                bet.bet_size -= new_bet_size
            # If we finished adding the bet to the pots, break the loop -- this would never get called
            # if bet.bet_size == 0:
                # break
        # If we r out of pots but still need to bet, make a new side Pot
            # Only time this would happen is if u r the first to bet more than the current all_in
        else:
            # If not all in, just make a new pot with the bet amount
            if not bet.all_in:
                self.pots.append(Pot.new_pot_from_bet(bet))
                bet.bet_amount = 0
            # otherwsie, make a new pot & add an all in bet
            else:
                new_pot = Pot.new_pot_from_all_in_bet(bet)
                self.pots.append(new_pot)
                bet.bet_amount = 0

    # Take in all the bets from every player and create proper pots
    # def _add_bet_round(self, bet:Bet) -> None:
        

    # BUILT IN FUNCTIONS
    def __repr__(self) -> str:
        output = '='*8 + 'Pots' + '='*8
        for i,x in enumerate(self.pots):
                output += f'\nPot {i}:{x}'
        output += f'\nBottomlessPot:{self.bottomless_pot.val}'
        return output

    def __add__(self, *args, **kwargs):
        raise ValueError('Error: cannot create new instance of game state, use `+=` to update or `print()` to get current state')

    def __iadd__(self, bet:RoundBets):
        if not isinstance(bet, RoundBets):
            raise TypeError('Pots can only be added to a RoundBets object')
        # self._add_safe(bet, False)
        self.add_bet_round_bets(bet)
        return self
