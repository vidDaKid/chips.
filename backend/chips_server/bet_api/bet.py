'''
BET
creates bet objects solely for the purpose of propogation through the pot class
'''

class Bet:
    def __init__(self, bet_size:int, player:'Player'):
        self.bet_size = bet_size
        self.player = player
