# My Reversi (Group 13)

Welcome to the **My Reversi** project repository! This project is a domain-based implementation of the classic board game Reversi (Othello).

## Project Documentation
* **[reversi_domain.puml](./reversi_domain.puml):** The PlantUML source code for our primary domain class diagram.
* **[CRC_Cards_Google_Docs_Format.md](./CRC_Cards_Google_Docs_Format.md):** The Class Responsibility Collaboration (CRC) cards, formatted for easy integration into Google Docs.

## Architecture Overview
The current domain model focuses exclusively on core game logic (without networking components) and consists of the following primary classes:
1. `Game` - Core game loop and state management
2. `Board` - 8x8 grid management and placement rules
3. `Cell` - Individual grid coordinates
4. `Piece` - The game tokens
5. `Player` - Abstract participant
6. `HumanPlayer` - Human interface interactions
7. `ComputerPlayer` - AI opponent heuristics

## Backend (Django)
The backend lives in [`backend/`](./backend) and is split so each part can be worked on independently:

| Folder | Responsibility |
|---|---|
| `backend/config/` | Django project settings and root URL routing |
| `backend/api/` | HTTP endpoints (Django REST Framework views, serializers, URLs) |
| `backend/game/` | Pure-Python game rules: `Board`, `Cell`, `Piece`, `Player`, `HumanPlayer`, `ComputerPlayer`, `Game` (no Django imports) |
| `backend/database/` | Django models and migrations for persisting games, moves and players |

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py runserver      # http://127.0.0.1:8000/api/health/
python manage.py test
```

## Frontend (browser client)
The client lives in [`frontend/`](./frontend) and is plain HTML, CSS and JavaScript (no build step). Django serves it, so it runs on the same address as the API:

| File | Responsibility |
|---|---|
| `frontend/templates/index.html` | The single page: lobby, game board, replay and rules |
| `frontend/static/api.js` | `ApiClient` - sends requests to `/api/...` |
| `frontend/static/lobby.js` | `LobbyPage` - name, create / join games, open games, finished games |
| `frontend/static/game.js` | `GamePage` (polls every 1.5 s, sends moves, shows the result) and `ReplayPage` |
| `frontend/static/rules.js` | Highlights legal moves, counts discs and rebuilds boards for replays (display only, the server decides) |
| `frontend/static/app.js` | `App` - switches between pages |

Start the server as above and open http://127.0.0.1:8000/. To test two players on one computer, use two browser tabs.

Settings read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`) and `DJANGO_ALLOWED_HOSTS` (comma-separated) from the environment, with local-dev defaults.
