'''
This contains all the logic for handling bets in the pot. Obviously.
'''

class Pot:
    def __init__(self, value:int=0):
        # @var val // value of the current pot
        self.val:int = value

        # @var max_bet // max bet for this pot (if someone goes all in, this becomes that amount)
            # In the case that a second person goes all in for lower, the max bet is dropped and the difference is turned into a new pot
        self.max_bet:int = float('inf')

    # MAIN FUNCTIONALITY
    def add_all_in(self, value:int) -> None:
        self.val += value
        self.max_bet = value
        return self

    # BUILT IN
    def __add__(self, num:int or 'Pot') -> int:
        if type(num) == int:
            return self.val + num
        elif isinstance(num, Pot):
            return self.val + num.val
        else:
            raise TypeError('A pot can only be added to an `int` or another `Pot`')

    def __iadd__(self, num:int or 'Pot'):
        if type(num)==int:
            self.val += num
            return self
        elif isinstance(num, Pot):
            self.val += num.val
            return self
        else:
            raise TypeError('A pot can only be added to an `int` or another `Pot`')

    def __repr__(self) -> str:
        return f'\tValue: {self.val}\n\tMax Bet: {self.max_bet}'


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
    def _add_safe(self, bet_amount:int, all_in:bool) -> None:
        for pot in self.pots:
            # If the bet is smaller than the max, just add the bet and move on
            if pot.max_bet >= bet_amount:
                # empty the bet into the pot n move on if not all in
                if not all_in:
                    pot += bet_amount
                    bet_amount = 0
                    break
                # Otherwise, empty the bet & drop the max bet
                else:
                    pot.add_all_in(bet_amount)
                    bet_amount = 0
                    break
            # Otherwise, add what you can to the pot, then move the next one
            else:
                pot += pot.max_bet
                bet_amount -= pot.max_bet
            # If we finished adding the bet to the pots, break the loop
            if bet_amount == 0:
                break
        # If we r out of pots but still need to bet, make a new side Pot
            # Only time this would happen is if u r the first to bet more than the current all_in
        else:
            # If not all in, just make a new pot with the bet amount
            if not all_in:
                self.pots.append(Pot(bet_amount))
                bet_amount = 0
            # otherwsie, make a new pot & add an all in bet
            else:
                new_pot = Pot()
                new_pot.add_all_in(bet_amount)
                self.pots.append(new_pot)

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
        return 'Error: cannot create new instance of game state, use `+=` to update or `print()` to get current state'

    def __iadd__(self, o:int):
        self._add_safe(o, False)
        return self
