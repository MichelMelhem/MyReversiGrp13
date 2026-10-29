from database.models import Game

class GameService:
    @staticmethod
    def starting_board(size=8):
        board = [[0 for _ in range(size)] for _ in range(size)]

        middle = size // 2

        board[middle - 1][middle - 1] = 2
        board[middle - 1][middle] = 1
        board[middle][middle - 1] = 1
        board[middle][middle] = 2

        return board

    @staticmethod
    def serialize_game(game):
        return {
            'id': game.id,
            'board': game.board,
            'board_size': game.board_size, 
            'mode': game.mode,
            'current_turn': game.current_turn,
            'status': game.status,
            'players': {
                'black': game.black_player,
                'white': game.white_player
            },
            'result': game.result,
        }
    def create_game():
        game = Game.objects.create(
            board=GameService.starting_board(),
            board_size=8,
            mode='online',
            current_turn='black',
            status='waiting')
        
        return GameService.serialize_game(game)

    @staticmethod
    def get_game(game_id):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None

        return GameService.serialize_game(game)
