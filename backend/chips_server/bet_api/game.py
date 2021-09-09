'''
Holds state for each game and allows for abstracted actions
'''
from bet_api.g_round import Round
from typing import Optional, List
import json, math

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
        ## @var all_in // whether or not the player is all in
        self.all_in:bool = False
        ## @var folded // whether or not player has folded
        self.folded:bool = False
        ## @var voted // keeps track of if the player has voted

    def reset_round(self) -> None:
        self.curr_bet = 0
        self.all_in, self.folded = False, False

    def change_name(self, new_name:str) -> str:
        if type(new_name)!=str:
            raise TypeError('Name must be a string')
        self.name = new_name
        return new_name

    def add_bet(self, bet_size:int) -> None:
        if self.c_count > bet_size:
            raise ValueError('Bet size larger than number of available chips')
        self.curr_bet += bet_size
        self.c_count -= bet_size

    def go_all_in(self) -> None:
        self.current_bet += self.c_count
        self.c_count = 0
        self.all_in = True

    def fold(self) -> None:
        self.folded = True


class Game:
    def __init__(self):
        self.players:List[Player] = list()

        # @var settings // game settings
        self.settings = self.default_settings()

        # @var round // round state for current roudn
        self.round = Round()

        # @var ordering // whether or not the game is currently ordering
        self.ordering = False
        # @var count // keeps track of the current number for ordering
        self.count:int = 0

        # @var voting // whether or not the game is currently voting
        self.voting = False
        # @var vote_count // storing votes from each player (anonymously)
        self.vote_count = {True:0,False:0} # False=reject, True=accept

    # BET FUNCTIONS
    def place_bet(self, channel:str, bet_size:int) -> None:
        if bet_size == (cc := self.players[channel].c_count):
            self.round.place_all_in_bet(channel, bet_size)
        elif bet_size > cc:
            raise ValueError('The bet size is larger than the amount of chips you have')
        else:
            self.round.place_bet(channel, bet_size)

    def fold(self, channel:str) -> None:
        self.round.fold(channel)

    # PLAYER FUNCTIONS
    def order_players(self) -> None:
        self.players.sort(key=lambda x: x.position)

    def add_player(self, channel:str, name:str, c_count:Optional[int]=None):
        if not c_count:
            c_count = self.settings.get('default_count')
        new_player = Player(channel, name=name, c_count=c_count)
        # The new position will be 1 more than the position of the last player
        new_position = self.get_ordered_players
        new_position = len(new_position)
        new_player.position = new_position # Update player position
        self.players.append(new_player)

    # Get player by *channel*
    def get_player(self, channel:str) -> Player:
        for player in self.players:
            if player.channel == channel:
                return player
        raise ValidationError('That player is not in this game')

    def get_player_info(self, channel:str) -> dict[str and int]:
        # This will raise an error if there's no player
        player = self.get_player(channel)
        output = {'status':'ok', 'body':{'Name':player.name,'Chip Count':player.c_count,'Position':player.position}}
        return output

    def player_is_in_game(self, channel:str) -> bool:
        for player in self.players:
            if player.channel == channel:
                return True
        return False

    def name_is_available(self, name:str) -> bool:
        for player in self.players:
            if player.name == name:
                return False
        return True

    # Sets players position as current count && increments count (for serverside ordering)
        # return value says whether or not ordering is complete
    def set_player_position(self, channel:str) -> bool:
        player = self.get_player(channel)
        player.position = self.count
        self.count += 1
        if self.count == len(self.players):
            return True
        return False

    @property
    def get_ordered_players(self) -> List[str]:
        return [x.name for x in sorted(self.players, key=lambda x: x.position)]

    # SETTINGS FUNCTIONS
    def default_settings(self) -> dict[str]:
        settings = {
            'default_count': 200,
            'big_blind': 4,
            # Add in any advance settings that you want later
        }
        return settings

    def update_settings(self, new_settings:dict[str and int]):
        # Do some checking / error handling here at some point
        self.settings = new_settings

    # GAME FUNCTIONS
    def set_ordering_busy(self) -> None:
        self.ordering = True

    def set_ordering_free(self) -> None:
        self.ordering = False

    def reset_ordering(self) -> None:
        for player in self.players:
            player.position = -1
        self.count = 0

    def set_voting_busy(self) -> None:
        self.voting = True

    def set_voting_free(self) -> None:
        self.voting = False

    def cast_bool_vote(self, channel:str, vote:bool) -> None:
        player = self.get_player(channel)
        if vote is not (True or False):
            raise TypeError('Vote must be a boolean value: True or False')
        if player.voted:
            raise ValueError('Each player can only vote once')
        self.vote_count[vote] += 1
        player.voted = True

    # True means that the result is ready, NOT that the result is true
    def verdict_ready(self) -> bool:
        for boolean,num_votes in self.vote_count.items():
            if num_votes >= math.ceil(len(self.players)/2):
                return True
        return False

    def get_verdict(self) -> bool:
        if not self.verdict_ready():
            raise ValidationError('Voting result is not yet ready')
        for boolean, num_votes in self.vote_count.items():
            if num_votes >= math.ceil(len(self.players)/2):
                return boolean

    def reset_voting(self) -> None:
        for player in self.players:
            player.voted = False
        self.vote_count = {True:0,False:0}

    # BUILT IN
    ## represents game as a json string
    # def __repr__(self) -> str:
        # players = self.get_ordered_players
