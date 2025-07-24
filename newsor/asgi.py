"""
ASGI config for newsor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsor.settings')

# Import after Django setup
django_asgi_app = get_asgi_application()

from api.consumers_enhanced import GraphQLSubscriptionConsumer

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('graphql/', GraphQLSubscriptionConsumer.as_asgi()),
        ])
    ),
})
