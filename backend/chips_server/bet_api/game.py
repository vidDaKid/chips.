'''
Holds state for each game and allows for abstracted actions
'''
# from bet_api.g_round import Round
from bet_api.player import Player
from bet_api.table import Table
from typing import Optional, List
import json, math

class Game:
    def __init__(self):
        # @var settings // game settings
        self.settings = self.default_settings()

        # @var round // round state for current roudn
        # self.round = Round()

        # @var table // stores table info 
        self.table = Table()

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
        self.table.place_bet(channel, bet_size)

        return self.table.pots
        # if bet_size == (cc := self.players[channel].c_count):
            # self.round.place_all_in_bet(self.get_player(channel), bet_size)
        # elif bet_size > cc:
            # raise ValueError('The bet size is larger than the amount of chips you have')
        # else:
            # self.round.place_bet(self.get_player(channel), bet_size)
        # # Then check if the iteration has finished
        # if self.round.check_if_iteration_finished():
            # nxt_player = self.get_player_by_position(self.round.real_last_raise) # The 1st player in new iter
            # for i in range(len(self.total_players)):
                # if not nxt_player.all_in:
                    # break
                # # if so, check if there needs to be another go around
                # new_pos = self.round.get_next_player(nxt_player.position)
                # nxt_player = self.get_player_by_position(new_pos)
            # else:
                # # if everyone is all in, we can just jump to deciding a winner
                # ''' DECIDE WINNER '''
                # pass
        # else:
            # # Otherwise just go to the next betting round
            # # self.round.
            # pass


    def fold(self, channel:str) -> None:
        self.table.fold(channel)
        # self.round.fold(self.get_player(channel))

    # PLAYER FUNCTIONS
    def order_players(self) -> None:
        # self.players.sort(key=lambda x: x.position)
        self.table.order_players()

    def add_player(self, channel:str, name:str, c_count:Optional[int]=None):
        if not c_count:
            c_count = self.settings.get('default_count')
        self.table.add_player(channel,name,c_count)
        # new_player = Player(channel, name=name, c_count=c_count)
        # The new position will be 1 more than the position of the last player
        # new_position = len(self.players)
        # new_player.position = new_position # Update player position
        # self.players.append(new_player)
        # self.round.total_players += 1 # Add 1 to the player count

    # Get player by *channel*
    # def get_player(self, channel:str) -> Player:
        # for player in self.players:
            # if player.channel == channel:
                # return player
        # raise ValidationError('That player is not in this game')

    # def get_player_by_position(self, positon:int) -> Player:
        # return self.get_ordered_players[position]

    def get_player_info(self, channel:str) -> dict[str and int]:
        player = self.table._get_player_by_channel(channel)
        return player
        # This will raise an error if there's no player
        # player = self.get_player(channel)
        # output = {'status':'ok', 'body':{'Name':player.name,'Chip Count':player.c_count,'Position':player.position}}
        # return output

    def player_is_in_game(self, channel:str) -> bool:
        return self.table.player_is_in_game(channel)
        # for player in self.players:
            # if player.channel == channel:
                # return True
        # return False

    def name_is_available(self, name:str) -> bool:
        return self.table.name_is_available(name)
        # for player in self.players:
            # if player.name == name:
                # return False
        # return True

    # Sets players position as current count && increments count (for serverside ordering)
        # return value says whether or not ordering is complete
    def set_player_position(self, channel:str) -> bool:
        self.count += 1
        return self.table.set_player_position(channel, self.count)
        # player = self.get_player(channel)
        # player.position = self.count

    def get_ordered_players(self) -> List[str]:
        return [x.name for x in sorted(self.table.players, key=lambda x: x.position)]

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

    # SETUP FUNCTIONS
    def set_ordering_busy(self) -> None:
        self.ordering = True

    def set_ordering_free(self) -> None:
        self.ordering = False

    def ordering_is_finished(self) -> bool:
        if self.count == len(self.table.players):
            return True
        return False

    def reset_ordering(self) -> None:
        self.table.reset_ordering()
        # for player in self.players:
            # player.position = -1
        # self.count = 0

    def set_voting_busy(self) -> None:
        self.voting = True

    def set_voting_free(self) -> None:
        self.voting = False

    def cast_bool_vote(self, channel:str, vote:bool) -> None:
        self.table.cast_bool_vote(channel, vote)
        # player = self.get_player(channel)
        # if vote is not (True or False):
            # raise TypeError('Vote must be a boolean value: True or False')
        # if player.voted:
            # raise ValueError('Each player can only vote once')
        # player.voted = True
        self.vote_count[vote] += 1 # KEEP THIS

    # True means that the result is ready, NOT that the result is true
    def verdict_ready(self) -> bool:
        for boolean,num_votes in self.vote_count.items():
            if num_votes >= math.ceil(len(self.table.players)/2):
                return True
        return False

    def get_verdict(self) -> bool:
        if not self.verdict_ready():
            raise ValidationError('Voting result is not yet ready')
        for boolean, num_votes in self.vote_count.items():
            if num_votes >= math.ceil(len(self.players)/2):
                return boolean

    def reset_voting(self) -> None:
        self.table.reset_voting()
        # for player in self.players:
            # player.voted = False
        self.vote_count = {True:0,False:0}

    # BUILT IN
    ## represents game as a json string
    # def __repr__(self) -> str:
        # players = self.get_ordered_players
