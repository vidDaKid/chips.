'''
This contains all the logic for handling bets in the pot. Obviously.
'''
from collections import defaultdict
from bet_api.bet import Bet

class Pot:
    def __init__(self, value:int=0):
        # @var val // value of the current pot
        self.val:int = value

        # @var max_bet // max bet for this pot (if someone goes all in, this becomes that amount)
            # In the case that a second person goes all in for lower, the max bet is dropped and the difference is turned into a new pot
        self.max_bet:int = float('inf')

        # @var bets // how much each player has bet to the pot
        self.bets = defaultdict(int) # { Player : bet_size }
        
        # @var eligible // players that contributed to the pot are eligible to win it
        self.eligible:List['Player'] = list()

    # MAIN FUNCTIONALITY
    def add_all_in(self, bet:Bet) -> None:
        self.val += bet.bet_size
        self.max_bet = bet.bet_size
        self.bets[bet.player] += bet.bet_size
        return self

    def bet_size_allowed(self, player:'Player'):
        if self.max == float('inf'):
            return float('inf')
        return self.max - self.bets[player]

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
    def __add__(self, bet:'Bet') -> None:
        raise ValueError('Cannot create temporary pot')
        # if type(bet) == tuple:
            # bet_size:int, player:'Player' = bet
            # if bet_size > self.max_bet:
                # raise ValueError('Bet is larger than max bet value')
            # new_bets = dict(self.bets)
            # new_bets[player] += bet_size
            # return (self.val + num.val, new_bets)
        # else:
            # raise TypeError('A pot can only be added to an `int` or another `Pot`')

    def __iadd__(self, bet:Bet) -> 'Pot':
        if isinstance(bet, Bet):
            if bet.bet_size > self.max_bet:
                raise ValueError('Bet is larger than max bet value')
            self.val += bet.bet_size
            self.bets[bet.player] += bet.bet_size
            return self
        else:
            raise TypeError('Only a `Bet` object can be added to a pot')

    def __repr__(self) -> str:
        return str({'Value':self.val,'max bet':self.max_bet})
        # return f'\tValue: {self.val}\n\tMax Bet: {self.max_bet}'


class Pots:
    def __init__(self):
        # @var pots // list of all the side pots
        self.pots:List[Pot] = [Pot()]
    
    # MAIN FUNCTIONS
    ## Adds bets for all in players
    def add_all_in(self, amount:int) -> 'Pots':
        self._add_safe(amount, True)
        return self

    def reset(self) -> 'Pots':
        self.pots = [Pot()]
        return self

    # Get rid of all the max bets
    def next_bet_round(self) -> None:
        for pot in self.pots:
            if pot.max_bet != float('inf'):
                pot.max_bet = 0

    # HELPER FUNCTIONS
    def _add_safe(self, bet:Bet, all_in:bool) -> None:
        if not isinstance(bet, Bet):
            raise TypeError('Pots can only be added to a`Bet` object')
        for pot in self.pots:
            # If the bet is smaller than the max, just add the bet and move on
            if pot.max_bet >= bet.bet_size:
                # empty the bet into the pot n move on if not all in
                if not all_in:
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
            if not all_in:
                self.pots.append(Pot.new_pot_from_bet(bet))
                bet.bet_amount = 0
            # otherwsie, make a new pot & add an all in bet
            else:
                new_pot = Pot.new_pot_from_all_in_bet(bet)
                self.pots.append(new_pot)
                bet.bet_amount = 0

    # BUILT IN FUNCTIONS
    def __repr__(self) -> str:
        output = '='*8 + 'Pots' + '='*8 + '\n'
        for i,x in enumerate(self.pots):
            if i==len(self.pots)-1:
                output += f'Pot {i}:\n{x}'
            else:
                output += f'Pot {i}:\n{x}\n'
        return output

    def __add__(self, *args, **kwargs):
        raise ValueError('Error: cannot create new instance of game state, use `+=` to update or `print()` to get current state')

    def __iadd__(self, bet:Bet):
        if not isinstance(bet, Bet):
            raise TypeError('Pots can only be added to a Bet object')
        self._add_safe(bet, False)
        return self
