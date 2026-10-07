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

## How to run the project

### 1. Prerequisites
* **Python 3.12 or newer** (Django 6.1 needs it). Check with `python --version` (on macOS/Linux you may need `python3`).
* **Git**, to clone the repository.
* A web browser. Nothing else is needed: the frontend is plain HTML/CSS served by Django, so there is no Node/npm step.

### 2. Get the code
```bash
git clone https://github.com/MichelMelhem/MyReversiGrp13.git
cd MyReversiGrp13
```

### 3. Create and activate a virtual environment (first time only)
```bash
python -m venv .venv
```
Then activate it. Your prompt shows `(.venv)` once it is active:

| System | Command |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `.venv\Scripts\activate.bat` |
| Windows (Git Bash) | `source .venv/Scripts/activate` |
| macOS / Linux | `source .venv/bin/activate` |

If PowerShell refuses to run the script ("running scripts is disabled"), run this once and try again:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 4. Install the dependencies (first time, and after `requirements.txt` changes)
```bash
pip install -r requirements.txt
```

### 5. Create the database (first time, and after pulling new migrations)
```bash
cd backend
python manage.py migrate
```
This creates `backend/db.sqlite3` (it is git-ignored, so everyone has their own local database).

### 6. Start the server
From the `backend/` folder:
```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000/** in your browser. Stop the server with `Ctrl+C`.

If port 8000 is already used, pick another one: `python manage.py runserver 8080`.

### 7. Play
* **Against the computer:** enter a username, choose *Computer*, a difficulty and a board size, then **Start game**.
* **Online against another player:** open the site in two different browsers (or one normal and one private/incognito window). Enter a **different username** in each, choose *Online player* and the **same board size** in both. The second player is paired with the first automatically.
* **From another computer on the same network:** find your machine's IP address (`ipconfig` on Windows, `ifconfig` / `ip addr` on macOS/Linux), allow it, and listen on all interfaces. For example, with IP `192.168.1.20`:
  ```powershell
  # Windows PowerShell
  $env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.1.20"
  python manage.py runserver 0.0.0.0:8000
  ```
  ```bash
  # macOS / Linux / Git Bash
  DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.20 python manage.py runserver 0.0.0.0:8000
  ```
  Then open `http://192.168.1.20:8000/` on the other computer. Your firewall may ask you to allow Python.

### 8. Run the tests
From the `backend/` folder:
```bash
python manage.py test
```

### Next time
You only need to activate the virtual environment (step 3, activation command only), then:
```bash
cd backend
python manage.py migrate     # only needed if someone added new migrations
python manage.py runserver
```

### Optional: admin site
To browse saved players, games and moves at http://127.0.0.1:8000/admin/:
```bash
python manage.py createsuperuser
```

### Configuration
Settings read these environment variables, with local-development defaults:

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev-only key | Set a real secret outside local development |
| `DJANGO_DEBUG` | `1` | `1` = debug on, `0` = off |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names/IPs allowed to reach the server |

### Troubleshooting
* **`ModuleNotFoundError: No module named 'django'`**: the virtual environment is not active, or step 4 was skipped.
* **`no such table: database_gamerecord`**: run `python manage.py migrate` (step 5).
* **`python: can't open file 'manage.py'`**: you are not in the `backend/` folder.
* **Online game stays on "Waiting for an opponent"**: both players must pick the same board size and use different usernames.
* **`DisallowedHost` error when connecting from another device**: add that address to `DJANGO_ALLOWED_HOSTS`.

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
