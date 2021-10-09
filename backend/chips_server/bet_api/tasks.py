from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def bet_timer(*args):
    # print(args[0])
    channel_layer = get_channel_layer()
    game_id = args[0]
    # process_id = args[1]
    # game = args[2]
    # if game.table.process != process_id:
        # return
    async_to_sync(channel_layer.group_send)(
        game_id, 
        { 'type':'announce_time_up' }
    )

@shared_task
def pay_winners_timer(*args, **kwargs):
    channel_layer = get_channel_layer()
    game_id = kwargs['game_id']
    async_to_sync(channel_layer.group_send)(
        game_id,
        {'type':'announce_winners'}
    )

# @shared_task
# def winner_timer(*args):
    # channel_layer = get_channel_layer()
    # game_id = args[0]
    # pot_id = args[1]
    # async_to_sync(channel_layer.group_send)(
        # game_id,
        # { 
            # 'type':'announce_winners',
            # 'pot_id':pot_id
        # }
    # )
# 
# 
# @shared_task
# def vote_winner_timer(*args):
    # channel_layer = get_channel_layer()
    # game_id = args[0]
    # pot_amount = args[1]
    # pot_id = args[2]
    # async_to_sync(channel_layer.group_send)(
        # game_id,
        # { 
            # 'type': 'announce_voted_winners',
            # 'pot_amount':pot_amount,
            # 'pot_id':pot_id
        # }
    # )
