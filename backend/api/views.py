from rest_framework.decorators import api_view
from rest_framework.response import Response
from database.models import Game
def starting_board():
    #call this function to get the starting board for a new game
    #will cahnge dimensions of board to whatever size we decide on
    board = [[0 for col in range (8)] for row in range(8)]

    board[3][3] = 2
    board[3][4] = 1
    board[4][3] = 1
    board[4][4] = 2

    return board
@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})

@api_view(['GET'])
def get_board(request):

    #Temp board to test the API
    #0 = empty, 1 = black, 2 = white
    board = [[0 for col in range (8)] for row in range(8)]

    board[3][3] = 2
    board[3][4] = 1
    board[4][3] = 1
    board[4][4] = 2

    return Response({'board': board, 
                     'current_turn': 'black',
                     'status': 'in_progress'
                })

@api_view(['POST'])
def create_game(request):
    game = Game.objects.create(board=starting_board(),
                               current_turn='black', 
                               status='in_progress')


    return Response({'id': game.id, 
                     'board': game.board, 
                     'current_turn': game.current_turn, 
                     'status': game.status, 
                     'players': {'black': game.black_player, 
                                 'white': game.white_player}
                    }, status=201)
@api_view(['GET'])
def get_game(request, game_id):

    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return Response({'error': 'Game not found'}, status=404)

    return Response({'id': game.id, 
                     'board': game.board, 
                     'current_turn': game.current_turn, 
                     'status': game.status, 
                     'players': {'black': game.black_player, 
                                 'white': game.white_player}
                    }, status=200)
   