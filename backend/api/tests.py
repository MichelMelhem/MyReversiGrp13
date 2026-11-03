from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse


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

    # TEST 11: Valid move reaches engine placeholder

    def test_valid_move_reaches_engine_placeholder(self):
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

        # change this when engine is implemented
        self.assertEqual(response.status_code, 501)

    # TEST 12: Nonexistent game returns 404

    def test_nonexistent_game_returns_404(self):
        response = self.client.get(
            "/api/games/999999/"
        )

        self.assertEqual(response.status_code, 404)


