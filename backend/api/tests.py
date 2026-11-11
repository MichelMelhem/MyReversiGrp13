from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from database.models import Game, MoveRecord, PlayerProfile
from datetime import timedelta
from django.utils import timezone


class HealthEndpointTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})


class GameAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_game(self):
        response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data)

    
    def test_first_player_can_join(self):
        # Create a new game
        create_response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )

        game_id = create_response.data["id"]

        # Join the game as Alice
        join_response = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"},
            format="json"
        )

        # Check the response
        self.assertEqual(join_response.status_code, 200)
        self.assertEqual(
            join_response.data["status"],
            "waiting"
        )
        self.assertIsNone(
            join_response.data["your_colour"]
        )
        self.assertIn(
            "player_token",
            join_response.data
        )

    
    # TEST 3: Second player joins and game starts

    def test_second_player_starts_game(self):
        create_response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )
        game_id = create_response.data["id"]

        alice = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"},
            format="json"
        )

        bob = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Bob"},
            format="json"
        )

        self.assertEqual(bob.status_code, 200)
        self.assertEqual(bob.data["status"], "in_progress")
        self.assertEqual(bob.data["current_turn"], "black")

        self.assertNotEqual(
            alice.data["player_token"],
            bob.data["player_token"]
        )

        self.assertEqual(
            {
                bob.data["players"]["black"],
                bob.data["players"]["white"]
            },
            {"Alice", "Bob"}
        )

    # TEST 4: Players receive different assigned colours

    def test_players_have_opposite_colours(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        alice = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"},
            format="json"
        )

        bob = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Bob"},
            format="json"
        )

        alice_poll = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=alice.data["player_token"]
        )

        bob_poll = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=bob.data["player_token"]
        )

        self.assertEqual(alice_poll.status_code, 200)
        self.assertEqual(bob_poll.status_code, 200)

        self.assertEqual(
            {
                alice_poll.data["your_colour"],
                bob_poll.data["your_colour"]
            },
            {"black", "white"}
        )

    # TEST 5: Both players see the same board

    def test_poll_returns_same_board(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        alice = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"}, format="json"
        )

        bob = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Bob"}, format="json"
        )

        alice_poll = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=alice.data["player_token"]
        )

        bob_poll = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=bob.data["player_token"]
        )

        self.assertEqual(
            alice_poll.data["board"],
            bob_poll.data["board"]
        )

        self.assertNotIn("player_token", alice_poll.data)
        self.assertNotIn("player_token", bob_poll.data)

    # TEST 6: Polling without token is rejected

    def test_poll_requires_token(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        response = self.client.get(
            f"/api/games/{game_id}/poll/"
        )

        self.assertEqual(response.status_code, 403)

    # TEST 7: Empty player name is rejected

    def test_empty_player_name_rejected(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        response = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": ""},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    # TEST 8: Third player cannot join full game

    def test_third_player_cannot_join(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        for name in ["Alice", "Bob"]:
            response = self.client.post(
                f"/api/games/{game_id}/join/",
                data={"name": name},
                format="json"
            )
            self.assertEqual(response.status_code, 200)

        charlie = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Charlie"},
            format="json"
        )

        self.assertEqual(charlie.status_code, 400)

    # TEST 9: Move request without token is rejected

    def test_move_requires_token(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        for name in ["Alice", "Bob"]:
            self.client.post(
                f"/api/games/{game_id}/join/",
                data={"name": name}, format="json"
            )

        response = self.client.post(
            f"/api/games/{game_id}/moves/",
            data={"row": 2, "col": 3},
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    # TEST 10: Invalid move coordinates are rejected

    def test_invalid_move_coordinates(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        alice = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"}, format="json"
        )

        bob = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Bob"}, format="json"
        )

        game_response = self.client.get(
            f"/api/games/{game_id}/"
        )

        black_name = game_response.data["players"]["black"]

        black_token = (
            alice.data["player_token"]
            if black_name == "Alice"
            else bob.data["player_token"]
        )

        response = self.client.post(
            f"/api/games/{game_id}/moves/",
            data={"row": 20, "col": 3},
            format="json",
            HTTP_X_PLAYER_TOKEN=black_token
        )

        self.assertEqual(response.status_code, 400)

    # TEST 11: Valid move is played by the engine

    def test_valid_move_is_played(self):
        create_response = self.client.post(
            "/api/games/", data={}, format="json"
        )
        game_id = create_response.data["id"]

        alice = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"}, format="json"
        )

        bob = self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Bob"}, format="json"
        )

        game_response = self.client.get(
            f"/api/games/{game_id}/"
        )

        black_name = game_response.data["players"]["black"]

        black_token = (
            alice.data["player_token"]
            if black_name == "Alice"
            else bob.data["player_token"]
        )

        response = self.client.post(
            f"/api/games/{game_id}/moves/",
            data={"row": 2, "col": 3},
            format="json",
            HTTP_X_PLAYER_TOKEN=black_token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["board"][2][3], 1)    # new black piece
        self.assertEqual(response.data["board"][3][3], 1)    # flipped
        self.assertEqual(response.data["flipped"], [[3, 3]])
        self.assertEqual(response.data["current_turn"], "white")
        self.assertEqual(response.data["your_colour"], "black")
        self.assertEqual(response.data["status"], "in_progress")

        move = MoveRecord.objects.get(game_id=game_id)
        self.assertEqual((move.number, move.colour, move.row, move.col), (1, "black", 2, 3))

    # --- helpers and tests for the rules engine integration ---------------

    def start_online_game(self):
        """Create a game, join two players, return (game_id, black_token, white_token)."""
        game_id = self.client.post("/api/games/", data={}, format="json").data["id"]
        alice = self.client.post(f"/api/games/{game_id}/join/", data={"name": "Alice"}, format="json")
        bob = self.client.post(f"/api/games/{game_id}/join/", data={"name": "Bob"}, format="json")
        black_name = Game.objects.get(id=game_id).black_player
        if black_name == "Alice":
            return game_id, alice.data["player_token"], bob.data["player_token"]
        return game_id, bob.data["player_token"], alice.data["player_token"]

    def move(self, game_id, token, row, col):
        return self.client.post(
            f"/api/games/{game_id}/moves/",
            data={"row": row, "col": col},
            format="json",
            HTTP_X_PLAYER_TOKEN=token,
        )

    def test_illegal_move_is_rejected_and_nothing_changes(self):
        game_id, black_token, _ = self.start_online_game()
        before = Game.objects.get(id=game_id).board

        response = self.move(game_id, black_token, 0, 0)   # flips nothing

        self.assertEqual(response.status_code, 400)
        game = Game.objects.get(id=game_id)
        self.assertEqual(game.board, before)
        self.assertEqual(game.current_turn, "black")
        self.assertFalse(MoveRecord.objects.filter(game_id=game_id).exists())

    def test_occupied_square_is_rejected(self):
        game_id, black_token, _ = self.start_online_game()
        response = self.move(game_id, black_token, 3, 3)
        self.assertEqual(response.status_code, 400)

    def test_players_alternate_and_moves_are_numbered(self):
        game_id, black_token, white_token = self.start_online_game()

        self.assertEqual(self.move(game_id, black_token, 2, 3).status_code, 200)
        self.assertEqual(self.move(game_id, black_token, 2, 2).status_code, 400)  # not black's turn
        self.assertEqual(self.move(game_id, white_token, 2, 2).status_code, 200)

        moves = list(MoveRecord.objects.filter(game_id=game_id).values_list("number", "colour"))
        self.assertEqual(moves, [(1, "black"), (2, "white")])
        self.assertEqual(Game.objects.get(id=game_id).current_turn, "black")

    def test_finishing_move_ends_game_and_updates_leaderboard(self):
        game_id, black_token, _ = self.start_online_game()
        game = Game.objects.get(id=game_id)
        # Near-final position: Black plays (0, 2) and takes White's last piece.
        game.board = [[1, 2, 0, 0, 0, 0, 0, 0]] + [[0] * 8 for _ in range(7)]
        game.save()

        response = self.move(game_id, black_token, 0, 2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "finished")
        self.assertEqual(response.data["result"], "black")
        game.refresh_from_db()
        self.assertEqual(game.black_profile.wins, 1)
        self.assertEqual(game.white_profile.losses, 1)
        self.assertEqual(self.move(game_id, black_token, 1, 1).status_code, 400)

    def test_draw_updates_both_profiles(self):
        game_id, black_token, _ = self.start_online_game()
        game = Game.objects.get(id=game_id)
        # Black plays (0, 3): row 0 becomes 4 black + 4 white, nobody can move.
        game.board = [[1, 1, 2, 0, 2, 2, 2, 2]] + [[0] * 8 for _ in range(7)]
        game.save()

        response = self.move(game_id, black_token, 0, 3)

        self.assertEqual(response.data["result"], "draw")
        game.refresh_from_db()
        self.assertEqual(game.black_profile.draws, 1)
        self.assertEqual(game.white_profile.draws, 1)

    def test_skip_keeps_turn_with_mover(self):
        game_id, black_token, _ = self.start_online_game()
        game = Game.objects.get(id=game_id)
        rows = [[0] * 8 for _ in range(8)]
        rows[0][:2] = [1, 2]
        rows[7][:2] = [1, 2]
        game.board = rows
        game.save()

        response = self.move(game_id, black_token, 0, 2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["skipped"], "white")
        self.assertEqual(response.data["current_turn"], "black")
        self.assertEqual(response.data["status"], "in_progress")

    # TEST 12: Nonexistent game returns 404

    def test_nonexistent_game_returns_404(self):
        response = self.client.get(
            "/api/games/999999/"
        )

        self.assertEqual(response.status_code, 404)

    
    def test_available_games_lobby(self):
        # Create a new game
        create_response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )

        game_id = create_response.data["id"]

        # Join as Alice
        self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Alice"},
            format="json"
        )

        # Check the available games
        lobby_response = self.client.get(
            "/api/games/available/"
        )

        self.assertEqual(lobby_response.status_code, 200)

        # The API returns a list directly
        game_ids = [
            game["id"]
            for game in lobby_response.data
        ]

        # Alice's game should appear
        self.assertIn(game_id, game_ids)

        # Join as Bob
        self.client.post(
            f"/api/games/{game_id}/join/",
            data={"name": "Bob"},
            format="json"
        )

        # Check the lobby again
        lobby_response = self.client.get(
            "/api/games/available/"
        )

        self.assertEqual(lobby_response.status_code, 200)

        game_ids = [
            game["id"]
            for game in lobby_response.data
        ]

        # The game should no longer be available
        self.assertNotIn(game_id, game_ids)

    
    # TEST 15: History initially has no finished games

    def test_history_empty(self):
        response = self.client.get(
            "/api/games/history/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    # TEST 16: Finished games appear in history

    def test_finished_game_appears_in_history(self):
        create_response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )

        game_id = create_response.data["id"]

        # Simulate a finished game in the test database
        game = Game.objects.get(id=game_id)
        game.status = "finished"
        game.result = "black"
        game.save()

        response = self.client.get(
            "/api/games/history/"
        )

        self.assertEqual(response.status_code, 200)

        ids = [item["id"] for item in response.data]

        self.assertIn(game_id, ids)

    # TEST 17: Replay contains recorded moves

    def test_game_replay_returns_moves(self):
        create_response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )

        game_id = create_response.data["id"]

        game = Game.objects.get(id=game_id)
        game.status = "finished"
        game.result = "black"
        game.save()

        # Simulate moves stored by the future game engine
        MoveRecord.objects.create(
            game=game,
            number=1,
            colour="black",
            row=2,
            col=3
        )

        MoveRecord.objects.create(
            game=game,
            number=2,
            colour="white",
            row=2,
            col=2
        )

        response = self.client.get(
            f"/api/games/{game_id}/replay/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["moves"]), 2)

        self.assertEqual(
            response.data["moves"][0]["number"], 1
        )

        self.assertEqual(
            response.data["moves"][0]["colour"], "black"
        )

    # TEST 18: Unfinished games cannot be replayed

    def test_unfinished_game_replay_rejected(self):
        create_response = self.client.post(
            "/api/games/",
            data={},
            format="json"
        )

        game_id = create_response.data["id"]

        response = self.client.get(
            f"/api/games/{game_id}/replay/"
        )

        self.assertEqual(response.status_code, 400)

    
    def test_leave_game_forfeits_and_awards_win(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )
        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Bob"},
            format="json"
        )

        game = Game.objects.get(id=game_id)

        response = self.client.post(
            f"/api/games/{game_id}/leave/",
            HTTP_X_PLAYER_TOKEN=game.black_token
        )

        self.assertEqual(response.status_code, 200)

        game.refresh_from_db()
        self.assertEqual(game.status, "finished")
        self.assertEqual(game.result, "white")

        game.black_profile.refresh_from_db()
        game.white_profile.refresh_from_db()

        self.assertEqual(game.black_profile.losses, 1)
        self.assertEqual(game.white_profile.wins, 1)

    def test_leave_game_requires_token(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        response = self.client.post(
            f"/api/games/{game_id}/leave/"
        )

        self.assertEqual(response.status_code, 403)

    def test_leave_waiting_game_cancels_it(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        join_response = self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )

        token = join_response.data["player_token"]

        response = self.client.post(
            f"/api/games/{game_id}/leave/",
            HTTP_X_PLAYER_TOKEN=token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "cancelled")
        self.assertFalse(
            Game.objects.filter(id=game_id).exists()
        )

    def test_finished_game_cannot_be_forfeited_twice(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )
        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Bob"},
            format="json"
        )

        game = Game.objects.get(id=game_id)
        token = game.black_token

        first_response = self.client.post(
            f"/api/games/{game_id}/leave/",
            HTTP_X_PLAYER_TOKEN=token
        )
        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post(
            f"/api/games/{game_id}/leave/",
            HTTP_X_PLAYER_TOKEN=token
        )
        self.assertEqual(second_response.status_code, 400)

        game.refresh_from_db()
        game.white_profile.refresh_from_db()

        self.assertEqual(game.white_profile.wins, 1)

    
    def test_poll_updates_player_last_seen(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )
        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Bob"},
            format="json"
        )

        game = Game.objects.get(id=game_id)
        original_time = game.black_last_seen

        response = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=game.black_token
        )

        self.assertEqual(response.status_code, 200)

        game.refresh_from_db()
        self.assertGreaterEqual(
            game.black_last_seen,
            original_time
        )
        self.assertEqual(game.status, "in_progress")

    def test_disconnected_player_forfeits_after_30_seconds(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )
        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Bob"},
            format="json"
        )

        game = Game.objects.get(id=game_id)

        # Simulate White being disconnected for 31 seconds.
        Game.objects.filter(id=game_id).update(
            black_last_seen=timezone.now(),
            white_last_seen=(
                timezone.now() - timedelta(seconds=31)
            )
        )

        response = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=game.black_token
        )

        self.assertEqual(response.status_code, 200)

        game.refresh_from_db()
        self.assertEqual(game.status, "finished")
        self.assertEqual(game.result, "black")

        game.black_profile.refresh_from_db()
        game.white_profile.refresh_from_db()

        self.assertEqual(game.black_profile.wins, 1)
        self.assertEqual(game.white_profile.losses, 1)

    def test_reconnecting_before_timeout_keeps_game_active(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )
        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Bob"},
            format="json"
        )

        game = Game.objects.get(id=game_id)

        # White was last seen 20 seconds ago.
        Game.objects.filter(id=game_id).update(
            black_last_seen=timezone.now(),
            white_last_seen=(
                timezone.now() - timedelta(seconds=20)
            )
        )

        response = self.client.get(
            f"/api/games/{game_id}/poll/",
            HTTP_X_PLAYER_TOKEN=game.white_token
        )

        self.assertEqual(response.status_code, 200)

        game.refresh_from_db()
        self.assertEqual(game.status, "in_progress")
        self.assertEqual(game.result, "")

    def test_timeout_is_not_counted_twice(self):
        response = self.client.post("/api/games/")
        game_id = response.data["id"]

        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Alice"},
            format="json"
        )
        self.client.post(
            f"/api/games/{game_id}/join/",
            {"name": "Bob"},
            format="json"
        )

        game = Game.objects.get(id=game_id)

        Game.objects.filter(id=game_id).update(
            black_last_seen=timezone.now(),
            white_last_seen=(
                timezone.now() - timedelta(seconds=31)
            )
        )

        for _ in range(2):
            response = self.client.get(
                f"/api/games/{game_id}/poll/",
                HTTP_X_PLAYER_TOKEN=game.black_token
            )
            self.assertEqual(response.status_code, 200)

        game.black_profile.refresh_from_db()
        game.white_profile.refresh_from_db()

        self.assertEqual(game.black_profile.wins, 1)
        self.assertEqual(game.white_profile.losses, 1)

    
    def test_leaderboard_returns_empty_list(self):
        response = self.client.get("/api/leaderboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_leaderboard_ranks_players_by_wins(self):
        PlayerProfile.objects.create(
            name="Alice",
            wins=5,
            losses=1,
            draws=0
        )

        PlayerProfile.objects.create(
            name="Bob",
            wins=2,
            losses=3,
            draws=0
        )

        PlayerProfile.objects.create(
            name="Charlie",
            wins=8,
            losses=2,
            draws=1
        )

        response = self.client.get("/api/leaderboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        self.assertEqual(response.data[0]["name"], "Charlie")
        self.assertEqual(response.data[0]["rank"], 1)

        self.assertEqual(response.data[1]["name"], "Alice")
        self.assertEqual(response.data[1]["rank"], 2)

        self.assertEqual(response.data[2]["name"], "Bob")
        self.assertEqual(response.data[2]["rank"], 3)

    def test_leaderboard_games_played(self):
        PlayerProfile.objects.create(
            name="Alice",
            wins=3,
            losses=2,
            draws=1
        )

        response = self.client.get("/api/leaderboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data[0]["games_played"],
            6
        )






    
    

class FrontendPageTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="board"')
