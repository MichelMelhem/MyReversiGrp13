from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from database.services import GameService

from rest_framework.decorators import api_view
from rest_framework.response import Response



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
    game = GameService.get_game(game_id)

    if game is None:
        return Response(
            {"error": "Game not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(game)
    return Response({'status': 'ok'})
