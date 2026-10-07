from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('games/computer/', views.create_computer_game, name='create-computer-game'),
    path('lobby/join/', views.join_online_game, name='join-online-game'),
    path('games/history/', views.history, name='history'),
    path('games/<uuid:game_id>/', views.game_state, name='game-state'),
    path('games/<uuid:game_id>/move/', views.make_move, name='make-move'),
    path('games/<uuid:game_id>/computer-move/', views.computer_move, name='computer-move'),
    path('games/<uuid:game_id>/leave/', views.leave_game, name='leave-game'),
    path('games/<uuid:game_id>/replay/', views.replay, name='replay'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
