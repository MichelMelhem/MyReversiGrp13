"""Persistence layer: Django models for saved games, moves and players.

Keep game rules in ``game/``; models here only store and load state.
"""
from django.db import models  # noqa: F401

class PlayerProfile(models.Model):
    name = models.CharField(max_length=100)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)

    def __str__(self):
        return self.name
class Game(models.Model):

    mode = models.CharField(max_length=20, 
                            choices=[('online', 'Online'), ('computer', 'Computer')], 
                            default='online')

    board_size = models.IntegerField(choices=[(6, "6x6"), (8, "8x8"), (10, "10x10")], default=8)
    
    board = models.JSONField(default=list)

    current_turn = models.CharField(max_length=10, default='black')
    status = models.CharField(max_length=20, default='waiting')

    # for api use
    black_player = models.CharField(max_length=100, null=True, blank=True)
    white_player = models.CharField(max_length=100, null=True, blank=True)
    # ----

    black_profile = models.ForeignKey(PlayerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='black_games')
    white_profile = models.ForeignKey(PlayerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='white_games')
    
    #seceret player token
    black_token = models.CharField(max_length=64, blank=True, default='')
    white_token = models.CharField(max_length=64, blank=True, default='')
    result = models.CharField(max_length=20, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'Game {self.id} - {self.status}'

class MoveRecord(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='moves')

    number = models.PositiveBigIntegerField()
    colour = models.CharField(max_length=10)
    row = models.IntegerField()
    col = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']
        constraints = [
            models.UniqueConstraint(fields=['game', 'number'], name='unique_game_move_number')
        ]
    

    def __str__(self):
        return f'Game {self.game_id} - Move {self.number}: {self.colour} at ({self.row}, {self.col})'
