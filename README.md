# My Reversi (Group 13)

Welcome to the **My Reversi** project repository! This project is a domain-based implementation of the classic board game Reversi (Othello), played in the browser against the computer or another player online.

## Project Documentation
* **[reversi_domain.puml](./reversi_domain.puml):** The PlantUML source code for our refined domain class diagram.
* **[CRC_Cards_Google_Docs_Format.md](./CRC_Cards_Google_Docs_Format.md):** The Class Responsibility Collaboration (CRC) cards, formatted for easy integration into Google Docs.

## Features
* **Play against the computer** (UC-05) at three difficulty levels: Easy (random legal move), Normal (prefers corners/edges), Hard (alpha-beta search).
* **Play online** (UC-01): players are paired in a lobby by board size; colours are drawn at random and Black moves first.
* **Server-validated moves** (UC-02): illegal moves are rejected with a reason; all outflanked pieces are flipped in all eight directions.
* **Turn skipping** (UC-03) and **end of game** (UC-04) with win/draw detection, plus forfeit on leaving or on a disconnect longer than 30 seconds.
* Legal moves highlighted; moves can be clicked or typed (e.g. `D3`).
* Custom features from our analysis: move record, game history with replay, leaderboard, highlighted legal moves, custom board size (6×6, 8×8, 10×10) and board colour.

## Architecture Overview
Client/server: the browser client renders the board and sends requests; the Django server owns the game state, enforces the rules, sequences turns and decides the result.

| Folder | Responsibility |
|---|---|
| `frontend/` | HTML/CSS client (pages + small JS for API calls), served by Django |
| `backend/config/` | Django project settings and root URL routing |
| `backend/api/` | HTTP endpoints (`views.py`) and game coordination (`services.py`) |
| `backend/game/` | Pure-Python game rules: `Board`, `Cell`, `Piece`, `Player`, `HumanPlayer`, `ComputerPlayer`, `Game` (no Django imports) |
| `backend/database/` | Django models and migrations for players, games and moves |

The domain classes follow our class diagram:
1. `Game` - Core game loop and state management (turns, skipping, game over, winner)
2. `Board` - Grid management and placement rules
3. `Cell` - Individual grid coordinates
4. `Piece` - The game tokens
5. `Player` - Abstract participant
6. `HumanPlayer` - Human interface interactions
7. `ComputerPlayer` - AI opponent heuristics

## Running it
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py runserver      # open http://127.0.0.1:8000/
python manage.py test
```

To try online play on one machine, open the site in two different browsers (or one normal and one private window), enter different usernames, choose **Online player** with the same board size in both.

Settings read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`) and `DJANGO_ALLOWED_HOSTS` (comma-separated) from the environment, with local-dev defaults.

## API
All endpoints are under `/api/`. A player receives a secret `token` when creating or joining a game and sends it back in the `X-Player-Token` header.

| Method | Path | Purpose |
|---|---|---|
| GET | `health/` | Health check |
| POST | `games/computer/` | New game vs computer: `{name, board_size, difficulty}` |
| POST | `lobby/join/` | Join/wait for an online game: `{name, board_size}` |
| GET | `games/<id>/` | Current state (also used for polling and disconnect detection) |
| POST | `games/<id>/move/` | Play a move: `{row, col}` |
| POST | `games/<id>/computer-move/` | Let the computer play its turn |
| POST | `games/<id>/leave/` | Cancel waiting, or forfeit a game in progress |
| GET | `games/<id>/replay/` | Board after every move of a finished game |
| GET | `games/history/?name=` | Recent finished games |
| GET | `leaderboard/` | Top players by wins |
