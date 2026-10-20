// MyReversi - class skeletons for the browser client.
// Based on the refined system class diagram (Fig. 2).

// Sends requests to the server and returns the JSON answer.
class ApiClient {
  async api(path, method, body, token) {}
}

// Lobby page: the player enters a name and chooses the game type.
class LobbyPage {
  constructor() {
    this.name = "";
    this.mode = "computer";   // "computer" or "online"
    this.boardSize = 8;       // 6, 8 or 10
    this.difficulty = "normal";
  }

  async startGame() {}
}

// Game page: shows the board and sends the player's moves.
class GamePage {
  constructor(gameId, token) {
    this.gameId = gameId;
    this.token = token;       // secret token from the server
    this.state = null;        // last game state received
  }

  async poll() {}             // ask the server for the state every 1.5 s
  async play(row, col) {}     // send a move (UC-02)
  async leave() {}            // leave the game (forfeit)
  render() {}                 // draw the board and the legal moves
  showResult() {}             // show the winner (UC-04)
}
