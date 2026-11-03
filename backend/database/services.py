import secrets
from django.db import transaction
from database.models import Game, PlayerProfile

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
    @staticmethod 
    def create_game():
        game = Game.objects.create(
            board=GameService.starting_board(),
            board_size=8,
            mode='online',
            current_turn='black',
            status='waiting')
        
        return GameService.serialize_game(game)

    @staticmethod
    def get_game(game_id, token=None):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None

        result = GameService.serialize_game(game)
        result['your_colour'] = None

        if token:
            if game.black_token and secrets.compare_digest(token, game.black_token):
                if game.status in ('in_progress', 'finished'):
                    result['your_colour'] = 'black'
            elif game.white_token and secrets.compare_digest(token, game.white_token):
                if game.status in ('in_progress', 'finished'):
                    result['your_colour'] = 'white'
            else:
                raise PermissionError("Invalid token. You are not authorized to view this game.")

        return result

    @staticmethod
    def poll_game(game_id, token=None):
        if not token:
            raise PermissionError("Token is required to poll the game.")

        game = GameService.get_game(game_id, token)

        if game is None:
            return None

        return game
        

    @staticmethod
    def join_online_game(game_id, name, token=None):

        if not isinstance(name, str):
            raise ValueError("Invalid characters in name. Name must be text.")

        name = name.strip()

        if not 1 <= len(name) <= 30:
            raise ValueError("Invalid name length. Name must be between 1 and 30 characters.")

        with transaction.atomic():
            try:
                game = Game.objects.select_for_update().get(id=game_id)
            except Game.DoesNotExist:
                return None

            if token:
                if secrets.compare_digest(token, game.black_token):
                    if game.black_token:
                        return {
                            **GameService.serialize_game(game),
                            'player_token': token,
                            'your_colour': (
                                'black' if game.status == 'in_progress' else None
                            )
                        }

                if secrets.compare_digest(token, game.white_token):
                    if game.white_token:
                        return {
                            **GameService.serialize_game(game),
                            'player_token': token,
                            'your_colour': (
                                'white' if game.status == 'in_progress' else None
                            )
                        }

                raise PermissionError("Invalid token. You are not authorized to join this game.")

            if game.status != 'waiting':
                raise ValueError("Game is not available for joining. It may have already started or finished.")

            player= PlayerProfile.objects.create(name=name)
            new_token = secrets.token_urlsafe(24)

            if not game.black_token:
                game.black_token = new_token
                game.black_player = name
                game.black_profile = player
                game.save()

                return {
                    **GameService.serialize_game(game),
                    'player_token': new_token,
                    'your_colour': None
                }

            if not game.white_token:
                game.white_token = new_token
                game.white_player = name
                game.white_profile = player
                game.save()

                if secrets.randbelow(2) == 1:
                    game.black_player, game.white_player = (
                        game.white_player, game.black_player
                    )

                    game.black_profile, game.white_profile = (
                        game.white_profile, game.black_profile
                    )

                    game.black_token, game.white_token = (
                        game.white_token, game.black_token
                    )

                game.status = 'in_progress'
                game.current_turn = 'black'
                game.save()

                your_colour = (
                    'black' if game.black_token == new_token else 'white'
                )

                return {
                    **GameService.serialize_game(game),
                    'player_token': new_token,
                    'your_colour': your_colour
                }

            raise ValueError("Game is already full. Cannot join this game.")

    @staticmethod
    def make_move(game_id, token, row, col):
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            raise LookupError("Game not found.")

        if not token:
            raise PermissionError("Token is required to make a move.")

        if game.black_token and secrets.compare_digest(token, game.black_token):
            player_colour = 'black'
        elif game.white_token and secrets.compare_digest(token, game.white_token):
            player_colour = 'white'
        else:
            raise PermissionError("Invalid token. You are not authorized to make a move in this game.")

        if game.status != 'in_progress':
            raise ValueError("Game is not in progress. Cannot make a move.")
        
        if player_colour != game.current_turn:
            raise ValueError(f"It is not {player_colour}'s turn.")

        if type(row) is not int or type(col) is not int:
            raise ValueError("Row and column must be integers.")

        if not (0 <= row < game.board_size and 0 <= col < game.board_size):
            raise ValueError("Invalid row or column. Please choose a position within the board.")

        #FIX THIS ONCE GAME LOGIC IS IMPLEMENTED
        #REPLACE SECTION WITH CALLS TO GAME LOGIC FUNCTIONS
        raise NotImplementedError("Move validation and execution logic is not implemented yet.")

    
    
