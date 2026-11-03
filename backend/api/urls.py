from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('board/', views.get_board, name='get_board'),
    path('games/', views.create_game, name='create_game'),
    path('games/available/', views.available_games, name='available_games'),
    path ('games/history/', views.game_history, name='game_history'),
    path('games/<int:game_id>/', views.get_game, name='get_game'),
    path('games/<int:game_id>/join/', views.join_game, name='join_game'),
    path('games/<int:game_id>/moves/', views.make_move, name='make_move'),
    path('games/<int:game_id>/poll/', views.poll_game, name='poll_game'),
    path('games/<int:game_id>/replay/', views.game_replay, name='game_replay'),
    path('games/<int:game_id>/leave/', views.leave_game, name='leave_game'),
]

