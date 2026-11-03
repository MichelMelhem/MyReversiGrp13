from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from database.services import GameService

@api_view(['GET'])
def health(request):
    return Response({"status": "ok"})


@api_view(['GET'])
def get_board(request):
    board = GameService.starting_board()

    return Response({
        "board": board,
        "current_turn": "black",
        "status": "in_progress"
    })


@api_view(['POST'])
def create_game(request):
    game = GameService.create_game()

    return Response(
        game,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
def get_game(request, game_id):

    token = request.headers.get('X-Player-Token')

    try:
        game = GameService.get_game(game_id, token)
    except PermissionError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN
        )

    if game is None:
        return Response(
            {"error": "Game not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(game, status=200)
    
@api_view(['POST'])
def join_game(request, game_id):
    name = request.data.get('name')
    token = request.headers.get('X-Player-Token')

    try:
        result = GameService.join_online_game(game_id, name, token)
    except PermissionError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    if result is None:
        return Response(
            {"error": "Game not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(result, status=200)

@api_view(['POST'])
def make_move(request, game_id):
    token = request.headers.get('X-Player-Token')
    row = request.data.get('row')
    col = request.data.get('col')

    try:
        result = GameService.make_move(game_id, token, row, col)
    except LookupError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except PermissionError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN
        )
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except NotImplementedError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    if result is None:
        return Response(
            {"error": "Game not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(result, status=200)

@api_view(['GET'])
def poll_game(request, game_id):
    token = request.headers.get('X-Player-Token')

    try:
        result = GameService.poll_game(game_id, token)
    except LookupError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_404_NOT_FOUND        )
    except PermissionError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN
        )

    if result is None:
        return Response(
            {"error": "Game not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(result, status=200)

@api_view(['GET'])
def available_games(request):

    try:
        result = GameService.get_available_games()
    except PermissionError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN
        )

    return Response(result, status=200)

@api_view(['GET'])
def game_history(request):
    history = GameService.get_game_history()

    return Response(history, status=200)

@api_view(['GET'])
def game_replay(request, game_id):
    try:
        replay = GameService.get_game_replay(game_id)
    except LookupError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(replay, status=200)
