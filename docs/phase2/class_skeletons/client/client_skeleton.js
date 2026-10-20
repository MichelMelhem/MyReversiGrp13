/**
 * Class skeletons - browser client (frontend/static/js).
 *
 * Phase 2 class design, MyReversi, Group 13.
 * Replaces the Phase 1 `Client` class. The real code uses plain functions per
 * page (common.js, index.js, game.js, history.js, replay.js); they are grouped
 * here as classes to match the system class diagram. The client never decides
 * whether a move is legal: it only shows what the server sends back.
 */

/** <<utility>> Talks to the server and remembers this browser's seats. */
class ApiClient {
  /**
   * Send a JSON request to /api/<path>.
   * @param {string} path
   * @param {{method?: string, body?: object, token?: string}} options
   *   `token` is sent as the X-Player-Token header.
   * @returns {Promise<object>} parsed JSON; throws Error(message) on 4xx/5xx
   */
  static async api(path, { method = 'GET', body, token } = {}) {}

  /** Store the secret token and colour returned when a game is created/joined. */
  static saveSeat(gameId, token, color, settings) {}

  /** @returns {{token: string, color: string} | null} */
  static getSeat(gameId) {}

  /** Escape <, >, &, quotes before inserting a player name into HTML. */
  static escapeHtml(text) {}
}

/** <<boundary>> Lobby page (index.html): choose name, mode, size, difficulty. */
class LobbyPage {
  constructor() {
    this.nameInput = '';      // 1..30 characters
    this.mode = 'computer';   // 'computer' | 'online'
    this.boardSize = 8;       // 6 | 8 | 10
    this.difficulty = 'normal';
  }

  /** POST games/computer/ or lobby/join/, save the seat, open GamePage. */
  async startGame() {}

  /** Offer to go back to the last unfinished game in this browser. */
  async resumeLastGame() {}
}

/** <<boundary>> Game page (game.html): board, scores, move list, result. */
class GamePage {
  constructor(gameId) {
    this.gameId = gameId;
    this.token = null;        // from ApiClient.getSeat
    this.state = null;        // last JSON state from the server
    this.busy = false;        // true while a request is in flight
  }

  /** GET games/<id>/ every 1.5 s so both players see the same board. */
  async poll() {}

  /** UC-02: POST games/<id>/move/ with {row, col}; shows the error if illegal. */
  async play(row, col) {}

  /** POST games/<id>/leave/ (forfeit, or stop waiting). */
  async leave() {}

  /** Draw the board, highlight valid moves, update scores and turn banner. */
  render(state) {}

  /** UC-04: show winner / draw and the final score. */
  showResult(state) {}
}

/** <<boundary>> History page: list finished games, filter by name. */
class HistoryPage {
  async load(name = '') {}
}

/** <<boundary>> Replay page: step through the board after each move. */
class ReplayPage {
  constructor() {
    this.frames = [];
    this.index = 0;
  }

  step(delta) {}
}
