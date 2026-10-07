from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from database.models import GameRecord, PlayerProfile


class HealthEndpointTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})


class ApiTestCase(TestCase):
    def post(self, name, body=None, token=None, **kwargs):
        headers = {'HTTP_X_PLAYER_TOKEN': token} if token else {}
        return self.client.post(reverse(name, kwargs=kwargs), body or {},
                                content_type='application/json', **headers)

    def get(self, name, token=None, **kwargs):
        headers = {'HTTP_X_PLAYER_TOKEN': token} if token else {}
        return self.client.get(reverse(name, kwargs=kwargs), **headers)


class ComputerGameTests(ApiTestCase):
    def start(self, **body):
        response = self.post('create-computer-game', {'name': 'Aurelius', **body})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        return data['state']['id'], data['token'], data['state']

    def test_new_game_player_is_black_and_moves_first(self):
        _, _, state = self.start()
        self.assertEqual(state['you'], 'black')
        self.assertTrue(state['is_your_turn'])
        self.assertEqual(sorted(map(tuple, state['valid_moves'])), [(2, 3), (3, 2), (4, 5), (5, 4)])
        self.assertTrue(state['players']['white']['is_computer'])

    def test_legal_move_then_computer_reply(self):
        game_id, token, _ = self.start(difficulty='easy')
        state = self.post('make-move', {'row': 2, 'col': 3}, token, game_id=game_id).json()
        self.assertEqual(state['players']['black']['count'], 4)
        self.assertEqual(state['current_color'], 'white')
        self.assertFalse(state['is_your_turn'])
        self.assertIn('D3', state['last_event'])

        state = self.post('computer-move', token=token, game_id=game_id).json()
        self.assertEqual(state['move_count'], 2)
        self.assertEqual(state['current_color'], 'black')

    def test_illegal_move_is_rejected_and_board_unchanged(self):
        game_id, token, before = self.start()
        response = self.post('make-move', {'row': 0, 'col': 0}, token, game_id=game_id)
        self.assertEqual(response.status_code, 400)
        self.assertIn('outflank', response.json()['error'])
        after = self.get('game-state', token, game_id=game_id).json()
        self.assertEqual(after['board'], before['board'])

    def test_cannot_move_on_computers_turn(self):
        game_id, token, _ = self.start()
        self.post('make-move', {'row': 2, 'col': 3}, token, game_id=game_id)
        response = self.post('make-move', {'row': 2, 'col': 2}, token, game_id=game_id)
        self.assertEqual(response.status_code, 400)

    def test_requires_token(self):
        game_id, _, _ = self.start()
        response = self.post('make-move', {'row': 2, 'col': 3}, 'wrong', game_id=game_id)
        self.assertEqual(response.status_code, 403)

    def test_full_game_records_result_history_and_leaderboard(self):
        game_id, token, state = self.start(board_size=6, difficulty='easy')
        for _ in range(200):
            if state['status'] != 'in_progress':
                break
            if state['is_your_turn']:
                row, col = state['valid_moves'][0]
                state = self.post('make-move', {'row': row, 'col': col}, token,
                                  game_id=game_id).json()
            else:
                state = self.post('computer-move', token=token, game_id=game_id).json()
        self.assertEqual(state['status'], 'finished')
        self.assertIn(state['result'], ('black', 'white', 'draw'))
        self.assertEqual(state['end_reason'], 'no_moves')

        profile = PlayerProfile.objects.get(name='Aurelius')
        self.assertEqual(profile.games_played, 1)

        history = self.client.get(reverse('history') + '?name=aurelius').json()
        self.assertEqual([g['id'] for g in history], [game_id])

        replay = self.get('replay', game_id=game_id).json()
        self.assertEqual(len(replay['frames']), state['move_count'] + 1)
        self.assertEqual(replay['frames'][-1]['board'], state['board'])

        board = self.client.get(reverse('leaderboard')).json()
        self.assertEqual(board[0]['name'], 'Aurelius')

    def test_leave_is_forfeit(self):
        game_id, token, _ = self.start()
        state = self.post('leave-game', token=token, game_id=game_id).json()
        self.assertEqual(state['status'], 'finished')
        self.assertEqual(state['result'], 'white')
        self.assertEqual(state['end_reason'], 'forfeit')
        self.assertEqual(PlayerProfile.objects.get(name='Aurelius').losses, 1)

    def test_validation(self):
        self.assertEqual(self.post('create-computer-game', {'name': ''}).status_code, 400)
        self.assertEqual(
            self.post('create-computer-game', {'name': 'x', 'board_size': 7}).status_code, 400)
        self.assertEqual(
            self.post('create-computer-game', {'name': 'x', 'difficulty': 'god'}).status_code, 400)


class OnlineGameTests(ApiTestCase):
    def join(self, name, size=8):
        response = self.post('join-online-game', {'name': name, 'board_size': size})
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_first_player_waits_second_is_paired(self):
        first = self.join('Emma')
        self.assertEqual(first['state']['status'], 'waiting')

        second = self.join('Rita')
        self.assertEqual(second['state']['id'], first['state']['id'])
        self.assertEqual(second['state']['status'], 'in_progress')
        self.assertNotEqual(first['token'], second['token'])

        # Each player sees their own colour; exactly one of them is Black.
        game_id = first['state']['id']
        colors = {self.get('game-state', p['token'], game_id=game_id).json()['you']
                  for p in (first, second)}
        self.assertEqual(colors, {'black', 'white'})

    def test_players_are_matched_by_board_size(self):
        first = self.join('Emma', 6)
        second = self.join('Rita', 8)
        self.assertNotEqual(first['state']['id'], second['state']['id'])

    def test_moves_alternate_between_players(self):
        first, second = self.join('Emma'), self.join('Rita')
        game_id = first['state']['id']
        tokens = {}
        for p in (first, second):
            tokens[self.get('game-state', p['token'], game_id=game_id).json()['you']] = p['token']

        wrong = self.post('make-move', {'row': 2, 'col': 3}, tokens['white'], game_id=game_id)
        self.assertEqual(wrong.status_code, 400)
        self.assertIn('not your turn', wrong.json()['error'])

        ok = self.post('make-move', {'row': 2, 'col': 3}, tokens['black'], game_id=game_id)
        self.assertEqual(ok.status_code, 200)
        white_view = self.get('game-state', tokens['white'], game_id=game_id).json()
        self.assertTrue(white_view['is_your_turn'])
        self.assertEqual(white_view['board'], ok.json()['board'])

    def test_cancel_while_waiting(self):
        first = self.join('Emma')
        state = self.post('leave-game', token=first['token'], game_id=first['state']['id']).json()
        self.assertEqual(state['status'], 'cancelled')
        second = self.join('Rita')
        self.assertEqual(second['state']['status'], 'waiting')

    def test_disconnected_opponent_forfeits_after_window(self):
        first, second = self.join('Emma'), self.join('Rita')
        game_id = first['state']['id']
        later = timezone.now() + timedelta(seconds=45)
        with mock.patch('django.utils.timezone.now', return_value=later):
            state = self.get('game-state', second['token'], game_id=game_id).json()
        self.assertEqual(state['status'], 'finished')
        self.assertEqual(state['end_reason'], 'disconnect')
        self.assertEqual(state['result'], state['you'])

    def test_stale_waiting_game_is_not_joined(self):
        first = self.join('Emma')
        GameRecord.objects.filter(pk=first['state']['id']).update(
            black_last_seen=timezone.now() - timedelta(minutes=5))
        second = self.join('Rita')
        self.assertNotEqual(second['state']['id'], first['state']['id'])
        self.assertEqual(second['state']['status'], 'waiting')


class PageTests(TestCase):
    def test_pages_render(self):
        for path in ('/', '/history/', '/leaderboard/', '/rules/',
                     '/game/00000000-0000-0000-0000-000000000000/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertContains(response, 'MyReversi')
