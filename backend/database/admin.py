from django.contrib import admin

from .models import GameRecord, MoveRecord, PlayerProfile


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'wins', 'losses', 'draws', 'created_at')
    search_fields = ('name',)


class MoveInline(admin.TabularInline):
    model = MoveRecord
    extra = 0


@admin.register(GameRecord)
class GameRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'mode', 'status', 'black_player', 'white_player',
                    'black_count', 'white_count', 'result', 'created_at')
    list_filter = ('mode', 'status', 'result')
    exclude = ('black_token', 'white_token')
    inlines = [MoveInline]
