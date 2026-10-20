# Phase 2 – Refined Class Diagrams, Class Skeletons and Vulnerability Review

MyReversi – Group 13 – author: Michel Melhem

This part follows on from the Phase 1 primary class list and class diagram (Blanche and Michel).
It covers deliverable 2 (refined class diagrams) and deliverable 7 (class skeletons). It also adds the
technical vulnerability review the lecturer asked for in the Phase 1 feedback.

| Folder / file | Contents |
|---|---|
| `refined_class_diagrams/domain_class_diagram.*` | Fig. 1: domain classes (`game` package) with every attribute, operation and association |
| `refined_class_diagrams/system_class_diagram.*` | Fig. 2: client/server classes (replaces `Server` and `Client` from Phase 1) |
| `refined_class_diagrams/deployment_diagram.*` | Fig. 3: where each part runs (section 3.2.1 of the brief) |
| `class_skeletons/` | Python and JavaScript class skeletons generated from Fig. 1 and Fig. 2 |

Diagrams are written in PlantUML (`.puml`) and exported as `.png`. To re-render:
`java -jar plantuml.jar -tpng docs/phase2/refined_class_diagrams/*.puml`

---

## 1. What changed since the Phase 1 class diagram

| # | Phase 1 | Phase 2 | Why |
|---|---|---|---|
| 1 | `Server` (sockets, `broadcastGameState`) | `GameAPI` (HTTP endpoints) + `GameService` (game coordination) | We use Django over HTTP with clients polling every 1.5 s, not raw sockets. Splitting the endpoints from the logic keeps the API classes thin. |
| 2 | `Client` (`connectToServer`, `sendMove`, `updateUI`) | `ApiClient` + `LobbyPage`, `GamePage`, `HistoryPage`, `ReplayPage` | One boundary class per screen; `ApiClient` is the only class that talks to the server. |
| 3 | `Server 1 o-- * Client : coordinates` | `ApiClient 0..* --> 1 GameAPI : sends requests to` | The server does not hold client objects any more; a client is identified by a secret token per game. |
| 4 | `Client 1 *-- Game : renders view` | removed | The client never owns a `Game`. It only shows the JSON state the server sends, so the rules cannot be bypassed from the browser. |
| 5 | `Game.currentTurn : Player`, `gameState : String` | `currentPlayerIndex : int`, `status : GameStatus` (enum) | An enumeration only allows valid states (WAITING, IN_PROGRESS, FINISHED). The State Machine diagrams use the same names. |
| 6 | `Game` operations: `initializeGame`, `switchTurn`, `checkGameOver` | `start`, `resume`, `playTurn → TurnResult`, `validMoves`, `forfeit`, `getWinner`, `checkGameOver` | Each use case now has an operation: UC-01 `start`, UC-02 `playTurn`, UC-03 `advanceTurn` (skip), UC-04 `getWinner`/`forfeit`. |
| 7 | `Move` (in the earlier draft) | `TurnResult` (domain value object) and `MoveRecord` (saved move) | A move is just (row, col) in; what we need out is *what happened* (flips, skip, game over), and a stored copy for history/replay. |
| 8 | `Board.rows`, `Board.cols` | `Board.size ∈ {6, 8, 10}` | Custom feature 5 (custom board sizes). Reversi boards are always square. |
| 9 | `Board.isValidMove(row, col, piece)`, `executeFlip` | `piecesToFlip`, `isValidMove`, `getValidMoves`, `hasValidMove`, `placePiece`, `flipPieces`, `count`, `copy`, `toList/fromList` | `getValidMoves` supports "highlight possible moves" (custom feature 4); `hasValidMove` drives skip (UC-03) and end (UC-04); `copy` is used by the computer's search; `toList` stores the board. |
| 10 | `Cell.isObstacle` | removed | Obstacle tiles were not kept in scope; custom boards are done by size instead. |
| 11 | `Cell 0..1 ◇— 1 Piece : holds` | `Cell 1 ◆— 0..1 Piece : holds` | Phase 1 had the multiplicities on the wrong ends. A cell holds zero or one piece; a piece always sits on exactly one cell and is created/removed with it (composition). |
| 12 | `Board 1 ◆— * Cell` | `Board 1 ◆— 36..100 Cell {size × size}` | The exact number is now known from the supported sizes. |
| 13 | `Piece.color : String` | `Piece.color : PieceColor` (enum with `opponent()`) | No invalid colours possible; `flip()` becomes `color = color.opponent`. |
| 14 | `ComputerPlayer.difficultyLevel : String`, `calculateHeuristicMove()` | `difficultyLevel ∈ {easy, normal, hard}`, `makeMove` + private `bestGreedyMove`, `calculateBestMove`, `minimax`, `evaluate` | Resolves the open question "is difficulty in scope?" (yes, UC-05 variation 1'). |
| 15 | – | `PlayerProfile`, `GameRecord`, `MoveRecord` (entity classes) | Needed for custom features 1–3 (move record, game history, leaderboard) and so both players' browsers share one saved game. |
| 16 | – | `InvalidMoveError ← NotYourTurnError, GameOverError`, `GameActionError` | Named errors give the "move not allowed" feedback in UC-02 extension 2a. |

### Open questions from the Phase 1 walkthrough – now resolved in the design

| Question | Decision | Where in the design |
|---|---|---|
| Colours random or by joining order? | Random once two players are paired | `GameService.joinOnlineGame` |
| Rematch after a game? | Not in this version; players go back to the lobby | `GamePage.showResult` |
| Pauses (how many, approval, how long)? | Pause is not implemented; leaving a game = forfeit | `GameService.leaveGame`, `Game.forfeit` |
| Is computer difficulty in scope? | Yes: easy, normal, hard | `ComputerPlayer.DIFFICULTIES` |
| Does a disconnected player forfeit? | Yes, after a 30 s reconnection window | `GameService.RECONNECT_WINDOW`, `pollGame` |

---

## 2. Association details (Fig. 1 and Fig. 2)

Read each name in the arrow direction (e.g. "Game *is played on* Board").

| Association | Type | Multiplicity (from – to) | Role name at target | Navigability | Meaning |
|---|---|---|---|---|---|
| Game – Board : *is played on* | Composition | 1 – 1 | `board` | Game → Board | The board is created with the game and dies with it. |
| Game – Player : *is played by* | Aggregation | 1 – 2 {ordered} | `players` | Game → Player | Index 0 is Black, 1 is White. Players are created outside the game and passed in. |
| Board – Cell : *is made of* | Composition | 1 – 36..100 {size × size} | `cells` | Board → Cell | 6×6, 8×8 or 10×10 grid. |
| Cell – Piece : *holds* | Composition | 1 – 0..1 | `piece` | Cell → Piece | A cell is empty or holds one piece. |
| Game – GameStatus : *is in* | Association | 1 – 1 | `status` | Game → GameStatus | Current state of the game. |
| Piece – PieceColor : *shows* | Association | * – 1 | `color` | Piece → PieceColor | Side facing up. |
| Player – PieceColor : *plays as* | Association | * – 1 | `color` | Player → PieceColor | Colour assigned at the start. |
| Player ◁ HumanPlayer, ComputerPlayer | Generalisation | – | – | – | Both implement the abstract `makeMove(board)`. |
| InvalidMoveError ◁ NotYourTurnError, GameOverError | Generalisation | – | – | – | All rule errors can be caught as one type. |
| Game ⇢ TurnResult | Dependency «create» | – | – | – | `playTurn` returns a new TurnResult each time. |
| Player, ComputerPlayer ⇢ Board | Dependency «use» | – | – | – | Read the board to choose a move; the computer searches on copies. |
| ApiClient – GameAPI : *sends requests to* | Association | 0..* – 1 | – | ApiClient → GameAPI | HTTP/JSON, token in `X-Player-Token` header. |
| LobbyPage, GamePage, HistoryPage, ReplayPage ⇢ ApiClient | Dependency «use» | – | – | – | Only `ApiClient` makes network calls. |
| GameAPI ⇢ GameService | Dependency «use» | – | – | – | Views delegate all work. |
| GameService ⇢ Game | Dependency «create» | – | – | – | `buildGame` rebuilds Game + Board + Players from a GameRecord on each request. |
| GameService ⇢ GameRecord, PlayerProfile, MoveRecord | Dependency «use»/«create» | – | – | – | Loads with a row lock, saves results, creates one MoveRecord per move. |
| GameRecord – PlayerProfile : *black seat taken by* | Association | 0..* – 0..1 | `blackPlayer` | GameRecord → PlayerProfile | Null = computer, or nobody yet. |
| GameRecord – PlayerProfile : *white seat taken by* | Association | 0..* – 0..1 | `whitePlayer` | GameRecord → PlayerProfile | Null = computer, or waiting for an opponent. |
| GameRecord – MoveRecord : *records* | Composition | 1 – 0..* {ordered by number} | `moves` | both ways | Deleting a game deletes its moves. |

---

## 3. Technical vulnerability review

The Phase 1 feedback asked for a formal review of technical vulnerabilities. We used the STRIDE headings
(Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege) and
checked each risk against the classes above.

| # | Threat (STRIDE) | Example attack | Mitigation in the design | Class / operation | Status |
|---|---|---|---|---|---|
| V1 | Spoofing | Player B sends a move as Player A | Each seat gets a random 32-character secret token (`secrets.token_urlsafe(24)`), returned only to that browser. Every action checks it with a constant-time compare. | `GameRecord.colorForToken`, `GameService.makeMove` | Mitigated |
| V2 | Tampering | Client sends a fake board or an illegal square | The server is the only authority. The client sends only (row, col); `Board.placePiece` re-checks the rules and raises `InvalidMoveError`, leaving the board unchanged. | `Board.placePiece`, `Game.playTurn` | Mitigated |
| V3 | Tampering | Playing out of turn / after the end | `NotYourTurnError`, `GameOverError` | `Game.playTurn` | Mitigated |
| V4 | Tampering (race condition) | Two moves for the same game sent at the same moment | Each action runs in one DB transaction with `select_for_update` (row lock); move numbers are unique per game. | `GameService` (all actions), `MoveRecord` constraint | Mitigated |
| V5 | Tampering (bad input) | Non-numeric row, board size 7, 1000-character name | `int()` checks, `Board.inBounds`, size must be 6/8/10, name 1–30 characters | `GameService.cleanName`, `checkSize`, `Board` | Mitigated |
| V6 | Information disclosure / XSS | Username like `<script>…</script>` shown to the opponent | Names are inserted with `textContent` or `escapeHtml`, never as raw HTML | `ApiClient.escapeHtml`, `GamePage.render` | Mitigated |
| V7 | Information disclosure | Token stolen from the browser | Token lives in `localStorage` for that game only, and is useless once the game ends. XSS protection (V6) also protects the token. | `ApiClient.saveSeat` | Accepted risk |
| V8 | Information disclosure | Token sniffed on the network | Must be served over HTTPS when deployed (dev server is plain HTTP) | Deployment (Fig. 3) | Open – deployment task |
| V9 | Spoofing | Someone plays under another person's username to change their leaderboard totals | No accounts or passwords in this version, so a name is not proof of identity | `PlayerProfile` | Accepted risk – out of scope; would need login |
| V10 | Denial of service | Opponent stops responding so the game never ends | 30 s reconnection window, then forfeit; stale lobby games are cancelled | `GameService.pollGame`, `joinOnlineGame` | Mitigated |
| V11 | Denial of service | Making the computer think forever | Search depth is fixed (3, or 2 on 10×10) and the computer only moves when asked by the seated player | `ComputerPlayer.calculateBestMove` | Mitigated |
| V12 | Denial of service | Flooding the API with requests / new games | History limited to 50 rows and leaderboard to 20, but there is no rate limiting | `GameAPI` | Open – add rate limiting (e.g. DRF throttling) |
| V13 | Elevation of privilege | Using debug pages or a known secret key in production | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS` must be set by environment variables | `config/settings.py` | Open – deployment checklist |
| V14 | Repudiation | Player claims "I never played that move" | Every move is stored with number, colour, square and time | `MoveRecord` | Mitigated |
| V15 | CSRF | Another site makes the player's browser send a move | The API does not use cookies/sessions; the token must be sent in a custom header, which other sites cannot add | `GameAPI`, `ApiClient.api` | Mitigated |

---

## 4. Class skeletons

`class_skeletons/` contains the skeletons for every class in Fig. 1 and Fig. 2:

| File | Classes |
|---|---|
| `game/piece.py` | `PieceColor`, `Piece` |
| `game/cell.py` | `Cell` |
| `game/board.py` | `Board`, `InvalidMoveError` |
| `game/player.py` | `Player`, `HumanPlayer`, `ComputerPlayer` |
| `game/game.py` | `GameStatus`, `TurnResult`, `Game`, `NotYourTurnError`, `GameOverError` |
| `database/models.py` | `PlayerProfile`, `GameRecord`, `MoveRecord` |
| `api/services.py` | `GameService`, `GameActionError` |
| `client/client_skeleton.js` | `ApiClient`, `LobbyPage`, `GamePage`, `HistoryPage`, `ReplayPage` |

Each skeleton has the attributes, operation signatures with types, and docstrings that link back to the
use cases. Method bodies are `...`. The full implementation is in `backend/` and `frontend/`.
