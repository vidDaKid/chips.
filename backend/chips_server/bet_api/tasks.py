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
