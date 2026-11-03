from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('board/', views.get_board, name='get_board'),
    path('games/', views.create_game, name='create_game'),
    path('games/<int:game_id>/', views.get_game, name='get_game'),
    path('games/<int:game_id>/join/', views.join_game, name='join_game'),
    path('games/<int:game_id>/moves/', views.make_move, name='make_move'),
    path('games/<int:game_id>/poll/', views.poll_game, name='poll_game'),
]

