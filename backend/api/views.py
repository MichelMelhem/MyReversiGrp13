"""HTTP endpoints used by the HTML/CSS client in ``frontend/``.

Players are identified per game by a secret token (returned when they create
or join a game) sent back in the ``X-Player-Token`` header.
"""
from django.db.models import F, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from database.models import GameRecord, PlayerProfile

from . import services
from .services import GameActionError

TOKEN_HEADER = 'HTTP_X_PLAYER_TOKEN'


def _token(request):
    return request.META.get(TOKEN_HEADER, '')


def _error(exc):
    return Response({'error': exc.message}, status=exc.status)


def _joined(record, token, color):
    return Response({'token': token, 'color': color,
                     'state': services.serialize(record, color)}, status=201)


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})


@api_view(['POST'])
def create_computer_game(request):
    data = request.data
    try:
        record, token, color = services.create_computer_game(
            data.get('name'), data.get('board_size', 8), data.get('difficulty', 'normal'))
    except GameActionError as exc:
        return _error(exc)
    return _joined(record, token, color)


@api_view(['POST'])
def join_online_game(request):
    data = request.data
    try:
        record, token, color = services.join_online_game(
            data.get('name'), data.get('board_size', 8))
    except GameActionError as exc:
        return _error(exc)
    return _joined(record, token, color)


@api_view(['GET'])
def game_state(request, game_id):
    try:
        record, color = services.poll_game(game_id, _token(request))
    except GameActionError as exc:
        return _error(exc)
    return Response(services.serialize(record, color))


@api_view(['POST'])
def make_move(request, game_id):
    try:
        record = services.make_move(game_id, _token(request),
                                    request.data.get('row'), request.data.get('col'))
    except GameActionError as exc:
        return _error(exc)
    return Response(services.serialize(record, record.color_for_token(_token(request))))


@api_view(['POST'])
def computer_move(request, game_id):
    try:
        record = services.play_computer_turn(game_id, _token(request))
    except GameActionError as exc:
        return _error(exc)
    return Response(services.serialize(record, record.color_for_token(_token(request))))


@api_view(['POST'])
def leave_game(request, game_id):
    try:
        record = services.leave_game(game_id, _token(request))
    except GameActionError as exc:
        return _error(exc)
    return Response(services.serialize(record, record.color_for_token(_token(request))))


@api_view(['GET'])
def replay(request, game_id):
    record = GameRecord.objects.select_related('black_player', 'white_player') \
        .filter(pk=game_id, status=GameRecord.Status.FINISHED).first()
    if record is None:
        return Response({'error': 'Finished game not found.'}, status=404)
    return Response({'game': services.serialize(record), 'frames': services.replay_frames(record)})


@api_view(['GET'])
def history(request):
    """Most recent finished games, optionally only those involving ``?name=``."""
    games = GameRecord.objects.filter(status=GameRecord.Status.FINISHED) \
        .select_related('black_player', 'white_player')
    name = request.query_params.get('name', '').strip()
    if name:
        games = games.filter(Q(black_player__name__iexact=name) |
                             Q(white_player__name__iexact=name))
    return Response([
        {
            'id': str(g.id),
            'mode': g.mode,
            'difficulty': g.difficulty,
            'board_size': g.board_size,
            'black': g.player_name('black'),
            'white': g.player_name('white'),
            'black_count': g.black_count,
            'white_count': g.white_count,
            'result': g.result,
            'end_reason': g.end_reason,
            'finished_at': g.finished_at.isoformat() if g.finished_at else None,
        }
        for g in games[:50]
    ])


@api_view(['GET'])
def leaderboard(request):
    players = PlayerProfile.objects.annotate(played=F('wins') + F('losses') + F('draws')) \
        .filter(played__gt=0).order_by('-wins', 'losses', '-draws', 'name')[:20]
    return Response([
        {'name': p.name, 'wins': p.wins, 'losses': p.losses, 'draws': p.draws,
         'played': p.played}
        for p in players
    ])
