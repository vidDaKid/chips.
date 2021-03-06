"""
ASGI config for chips_server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator, AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.conf.urls import url

import bet_api.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chips_server.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
       SessionMiddlewareStack(
            URLRouter(
                # Websocket url routes from each app
                bet_api.routing.websocket_urlpatterns
            )
        ),
    )
        # ['http://localhost:3000/', ] # List of accepted user calls
})
