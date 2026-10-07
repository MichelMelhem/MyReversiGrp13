"""Server-side game coordination.

Loads a ``GameRecord`` into the pure-Python ``game`` objects, applies the
requested action, and writes the result back. Views stay thin; rules stay in
``game/``; storage stays in ``database/``.
"""
import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from database.models import GameRecord, MoveRecord, PlayerProfile, new_token
from game import (
    Board, ComputerPlayer, Game, GameStatus, HumanPlayer, InvalidMoveError,
    PieceColor,
)

# A disconnected online player has this long to come back before forfeiting.
RECONNECT_WINDOW = timedelta(seconds=30)

COLOR_NAMES = {'black': 'Black', 'white': 'White'}


class GameActionError(Exception):
    """An action the client asked for that cannot be done right now."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def _label(row, col):
    return f'{chr(ord("A") + col)}{row + 1}'


def clean_name(raw):
    name = (raw or '').strip()
    if not name:
        raise GameActionError('Please enter a username.')
    if len(name) > 30:
        raise GameActionError('Usernames can be at most 30 characters.')
    return name


# --- loading / saving -------------------------------------------------------

def build_game(record):
    """Rebuild the domain Game object from a stored record."""
    def make_player(color):
        profile = record.black_player if color == 'black' else record.white_player
        if record.mode == GameRecord.Mode.COMPUTER and profile is None:
            return ComputerPlayer(color, record.difficulty or 'normal')
        return HumanPlayer(record.player_name(color) or '?', color)

    game = Game(make_player('black'), make_player('white'),
                board=Board.from_list(record.board_state))
    status = GameStatus.FINISHED if record.status in (
        GameRecord.Status.FINISHED, GameRecord.Status.CANCELLED) else GameStatus(record.status)
    game.resume(record.current_color, status)
    return game


def _save_board(record, game):
    record.board_state = game.board.to_list()
    record.current_color = game.current_player.get_color().value
    record.black_count = game.board.black_count
    record.white_count = game.board.white_count


def _finish(record, game, reason):
    """Store the final result and update both players' win/loss/draw totals."""
    winner = game.get_winner()
    record.status = GameRecord.Status.FINISHED
    record.end_reason = reason
    record.finished_at = timezone.now()
    record.result = winner.get_color().value if winner else GameRecord.Result.DRAW

    for color in ('black', 'white'):
        profile = record.black_player if color == 'black' else record.white_player
        if profile is None:
            continue
        if record.result == GameRecord.Result.DRAW:
            profile.draws += 1
        elif record.result == color:
            profile.wins += 1
        else:
            profile.losses += 1
        profile.save(update_fields=['wins', 'losses', 'draws'])


def _locked(game_id):
    try:
        return (GameRecord.objects.select_for_update()
                .select_related('black_player', 'white_player').get(pk=game_id))
    except GameRecord.DoesNotExist:
        raise GameActionError('Game not found.', status=404)


def _require_player(record, token):
    color = record.color_for_token(token)
    if color is None:
        raise GameActionError('You are not a player in this game.', status=403)
    return color


def _touch(record, color):
    setattr(record, f'{color}_last_seen', timezone.now())


# --- creating and joining games --------------------------------------------

def _new_record(**fields):
    board = Board(fields['board_size'])
    board.initialize()
    return GameRecord(board_state=board.to_list(), current_color='black', **fields)


def _check_size(board_size):
    try:
        size = int(board_size)
    except (TypeError, ValueError):
        raise GameActionError('Board size must be a number.')
    if size not in (6, 8, 10):
        raise GameActionError('Board size must be 6, 8 or 10.')
    return size


@transaction.atomic
def create_computer_game(name, board_size=8, difficulty='normal'):
    """UC-05: the player is Black and moves first; the computer is White."""
    if difficulty not in ('easy', 'normal', 'hard'):
        raise GameActionError('Difficulty must be easy, normal or hard.')
    profile, _ = PlayerProfile.objects.get_or_create(name=clean_name(name))
    token = new_token()
    record = _new_record(
        mode=GameRecord.Mode.COMPUTER, difficulty=difficulty,
        board_size=_check_size(board_size), status=GameRecord.Status.IN_PROGRESS,
        black_player=profile, black_token=token, black_last_seen=timezone.now(),
        last_event='Game started. You are Black and move first.',
    )
    record.save()
    return record, token, 'black'


@transaction.atomic
def join_online_game(name, board_size=8):
    """UC-01: pair with a waiting player of the same board size, or start waiting."""
    profile, _ = PlayerProfile.objects.get_or_create(name=clean_name(name))
    size = _check_size(board_size)
    now = timezone.now()

    waiting = (GameRecord.objects.select_for_update()
               .filter(mode=GameRecord.Mode.ONLINE, status=GameRecord.Status.WAITING,
                       board_size=size)
               .exclude(black_player=profile)
               .order_by('created_at'))
    for record in waiting:
        if record.black_last_seen is None or now - record.black_last_seen > RECONNECT_WINDOW:
            record.status = GameRecord.Status.CANCELLED
            record.save(update_fields=['status', 'updated_at'])
            continue
        # Waiting host is parked in the black slot; colours are then drawn at random.
        token = new_token()
        record.white_player, record.white_token, record.white_last_seen = profile, token, now
        if random.random() < 0.5:
            record.black_player, record.white_player = record.white_player, record.black_player
            record.black_token, record.white_token = record.white_token, record.black_token
            record.black_last_seen, record.white_last_seen = (
                record.white_last_seen, record.black_last_seen)
        record.status = GameRecord.Status.IN_PROGRESS
        record.last_event = (f'{record.black_player.name} (Black) vs '
                             f'{record.white_player.name} (White). Black moves first.')
        record.save()
        return record, token, record.color_for_token(token)

    token = new_token()
    record = _new_record(
        mode=GameRecord.Mode.ONLINE, board_size=size, status=GameRecord.Status.WAITING,
        black_player=profile, black_token=token, black_last_seen=now,
        last_event='Waiting for an opponent to join...',
    )
    record.save()
    return record, token, 'black'


# --- in-game actions ---------------------------------------------------------

def _record_turn(record, game, result):
    """Persist one played turn and build the message both players will see."""
    number = record.moves.count() + 1
    MoveRecord.objects.create(
        game=record, number=number, color=result.color.value,
        row=result.row, col=result.col, flipped_count=len(result.flipped),
    )
    mover = COLOR_NAMES[result.color.value]
    message = f'{mover} played {_label(result.row, result.col)} and flipped {len(result.flipped)}.'
    if result.skipped is not None:
        skipped = COLOR_NAMES[result.skipped.value]
        message += f' {skipped} has no legal move — {mover} plays again.'
    _save_board(record, game)
    if result.game_over:
        _finish(record, game, GameRecord.EndReason.NO_MOVES)
        message += ' No legal moves remain: game over.'
    record.last_event = message


@transaction.atomic
def make_move(game_id, token, row, col):
    """UC-02: validate and apply a human move."""
    record = _locked(game_id)
    color = _require_player(record, token)
    _touch(record, color)
    if record.status == GameRecord.Status.WAITING:
        record.save(update_fields=[f'{color}_last_seen'])
        raise GameActionError('Still waiting for an opponent.')
    try:
        row, col = int(row), int(col)
    except (TypeError, ValueError):
        raise GameActionError('Row and column must be numbers.')

    game = build_game(record)
    try:
        result = game.play_turn(row, col, color=color)
    except InvalidMoveError as exc:
        record.save(update_fields=[f'{color}_last_seen'])
        raise GameActionError(str(exc))
    _record_turn(record, game, result)
    record.save()
    return record


@transaction.atomic
def play_computer_turn(game_id, token):
    """Let the computer play one move if it is its turn (UC-05 step 3)."""
    record = _locked(game_id)
    color = _require_player(record, token)
    _touch(record, color)
    if record.mode != GameRecord.Mode.COMPUTER or record.status != GameRecord.Status.IN_PROGRESS:
        record.save(update_fields=[f'{color}_last_seen'])
        return record

    game = build_game(record)
    computer = game.current_player
    if not computer.is_computer:
        record.save(update_fields=[f'{color}_last_seen'])
        return record
    row, col = computer.make_move(game.board)
    result = game.play_turn(row, col)
    _record_turn(record, game, result)
    record.save()
    return record


@transaction.atomic
def leave_game(game_id, token):
    """Quit: cancels a lobby wait, or forfeits a game in progress."""
    record = _locked(game_id)
    color = _require_player(record, token)
    if record.status == GameRecord.Status.WAITING:
        record.status = GameRecord.Status.CANCELLED
        record.last_event = 'Stopped waiting for an opponent.'
    elif record.status == GameRecord.Status.IN_PROGRESS:
        game = build_game(record)
        game.forfeit(color)
        _finish(record, game, GameRecord.EndReason.FORFEIT)
        record.last_event = f'{COLOR_NAMES[color]} left the game and forfeits.'
    record.save()
    return record


@transaction.atomic
def poll_game(game_id, token):
    """Return the latest state; also marks the caller as present and checks
    whether the online opponent has been gone longer than RECONNECT_WINDOW."""
    record = _locked(game_id)
    color = record.color_for_token(token)
    if color is None:
        return record, None

    _touch(record, color)
    if record.mode == GameRecord.Mode.ONLINE and record.status == GameRecord.Status.IN_PROGRESS:
        other = 'white' if color == 'black' else 'black'
        last_seen = getattr(record, f'{other}_last_seen')
        if last_seen is not None and timezone.now() - last_seen > RECONNECT_WINDOW:
            game = build_game(record)
            game.forfeit(other)
            _finish(record, game, GameRecord.EndReason.DISCONNECT)
            record.last_event = (f'{COLOR_NAMES[other]} lost connection and did not '
                                 f'return in time — {COLOR_NAMES[color]} wins by forfeit.')
    record.save()
    return record, color


# --- read-only views -------------------------------------------------------

def serialize(record, viewer=None):
    game = build_game(record)
    in_progress = record.status == GameRecord.Status.IN_PROGRESS
    moves = list(record.moves.all())
    return {
        'id': str(record.id),
        'mode': record.mode,
        'difficulty': record.difficulty,
        'board_size': record.board_size,
        'board': record.board_state,
        'status': record.status,
        'current_color': record.current_color if in_progress else None,
        'you': viewer,
        'is_your_turn': in_progress and viewer == record.current_color,
        'valid_moves': [list(m) for m in game.valid_moves()] if in_progress else [],
        'players': {
            color: {
                'name': record.player_name(color),
                'count': getattr(record, f'{color}_count'),
                'is_computer': record.mode == GameRecord.Mode.COMPUTER and color == 'white',
            }
            for color in ('black', 'white')
        },
        'result': record.result or None,
        'end_reason': record.end_reason or None,
        'last_event': record.last_event,
        'move_count': len(moves),
        'moves': [
            {'number': m.number, 'color': m.color, 'row': m.row, 'col': m.col,
             'label': m.label, 'flipped': m.flipped_count}
            for m in moves
        ],
        'created_at': record.created_at.isoformat(),
        'finished_at': record.finished_at.isoformat() if record.finished_at else None,
    }


def replay_frames(record):
    """Board after each move, rebuilt by replaying the stored moves."""
    board = Board(record.board_size)
    board.initialize()
    frames = [{'board': board.to_list(), 'move': None,
               'black': board.black_count, 'white': board.white_count}]
    for move in record.moves.all():
        board.place_piece(move.row, move.col, PieceColor(move.color))
        frames.append({
            'board': board.to_list(),
            'move': {'number': move.number, 'color': move.color, 'row': move.row,
                     'col': move.col, 'label': move.label, 'flipped': move.flipped_count},
            'black': board.black_count, 'white': board.white_count,
        })
    return frames
