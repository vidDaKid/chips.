'''
BET
creates bet objects solely for the purpose of propogation through the pot class
'''
from typing import List, Optional

class Bet:
    def __init__(self, channel:str, bet_size:int, all_in:bool=False, folded:bool=False):
        self.bet_size = bet_size
        self.channel = channel
        self.all_in = all_in
        self.folded = folded

    def __lt__(self, other:'Bet') -> bool:
        if other.all_in and not self.all_in:
            return False
        if self.all_in and not other.all_in:
            return True
        return self.bet_size < other.bet_size

    def __le__(self, other:'Bet') -> bool:
        if other.all_in and not self.all_in:
            return False
        if self.all_in and not other.all_in:
            return True
        return self.bet_size <= other.bet_size

    def __gt__(self, other:'Bet') -> bool:
        if other.all_in and not self.all_in:
            return True
        if self.all_in and not other.all_in:
            return False
        return self.bet_size > other.bet_size

    def __ge__(self, other:'Bet') -> bool:
        if other.all_in and not self.all_in:
            return True
        if self.all_in and not other.all_in:
            return False
        return self.bet_size >= other.bet_size

    def __eq__(self, other:'Bet') -> bool:
        if other.all_in != self.all_in:
            return False
        return self.bet_size == other.bet_size
    
    def __repr__(self) -> str:
        return str({'bet_size':self.bet_size, 'channel':self.channel, 'all_in':self.all_in, 'folded':self.folded})

class RoundBets:
    def __init__(self):
        self.bets:List[Bet] = list()

    def add_bet(self, channel:str, bet_size:int, all_in:bool=False, folded:bool=False) -> None:
        self.bets.append(Bet(channel=channel,bet_size=bet_size,all_in=all_in,folded=folded))

    # Ease of use function
    def add_bet_from_player(self, player:'Player') -> None:
        self.add_bet(channel=player.channel,bet_size=player.curr_bet,all_in=player.all_in,folded=player.folded)

    def sort(self) -> List[Bet]:
        self.bets.sort()
        return self.bets
       
    def __repr__(self) -> str:
        return str(self.bets)
    
