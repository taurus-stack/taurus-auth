"""
Ticket URLs routing
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TicketViewSet, health_check

router = DefaultRouter()
router.register(r'api/v1/tickets', TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check, name='health'),
]