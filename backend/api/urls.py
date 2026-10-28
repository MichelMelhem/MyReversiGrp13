from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('board/', views.get_board, name='get_board'),
    path('create_game/', views.create_game, name='create_game'),
    path('game/<int:game_id>/', views.get_game, name='get_game'),
]
