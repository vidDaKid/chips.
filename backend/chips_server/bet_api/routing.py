from django.urls import re_path

from bet_api.consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<game_id>\w+)?/?$', GameConsumer.as_asgi()),
]
