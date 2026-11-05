// Draws a board into the #board element. Cells in `hints` get a blue dot
// and call onClick(row, col) when clicked.
function drawBoard(board, hints, onClick) {
  const element = document.getElementById("board");
  const size = board.length;
  element.innerHTML = "";
  element.style.gridTemplateColumns = "repeat(" + size + ", 1fr)";

  const hintSet = new Set(hints.map(([r, c]) => r + "," + c));

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      const disc = document.createElement("div");

      if (board[r][c] === BLACK) disc.className = "disc black";
      else if (board[r][c] === WHITE) disc.className = "disc white";
      else if (hintSet.has(r + "," + c)) {
        disc.className = "disc hint";
        cell.classList.add("legal");
        cell.onclick = () => onClick(r, c);
      }

      cell.append(disc);
      element.append(cell);
    }
  }
}

function showScore(board, players) {
  const score = Rules.count(board);
  document.getElementById("black-label").textContent = "⚫ " + (players.black || "waiting...");
  document.getElementById("white-label").textContent = (players.white || "waiting...") + " ⚪";
  document.getElementById("score-text").textContent = score.black + " : " + score.white;
}

// Game page: shows the board, polls the server and sends the player's moves.
class GamePage {
  constructor(app, gameId, token) {
    this.app = app;
    this.gameId = gameId;
    this.token = token;   // secret token from the server
    this.state = null;    // last game state received
    this.timer = null;
    this.sending = false;

    document.getElementById("quit-btn").onclick = () => this.leave();
    document.getElementById("back-btn").onclick = () => this.app.openLobby();
  }

  show() {
    document.getElementById("game-page").hidden = false;
    document.getElementById("quit-btn").hidden = false;
    document.getElementById("replay-controls").hidden = true;
    document.getElementById("result-box").hidden = true;
    this.setMessage("");
    this.poll();
    this.timer = setInterval(() => this.poll(), 1500);
  }

  hide() {
    document.getElementById("game-page").hidden = true;
    clearInterval(this.timer);
  }

  setMessage(text) {
    document.getElementById("message").textContent = text;
  }

  // Ask the server for the latest state (also tells it we are still here).
  async poll() {
    try {
      this.state = await api.pollGame(this.gameId, this.token);
      this.render();
    } catch (e) {
      clearInterval(this.timer);
      storage.remove("reversi_game_" + this.gameId);
      this.app.openLobby("Game #" + this.gameId + " is no longer available: " + e.message);
    }
  }

  // Send a move (UC-02). The server checks it and returns the new state.
  async play(row, col) {
    if (this.sending) return;
    this.sending = true;
    this.setMessage("");
    try {
      this.state = await api.makeMove(this.gameId, this.token, row, col);
      this.render();
    } catch (e) {
      this.setMessage(e.message);
    }
    this.sending = false;
  }

  // Leave the game. Leaving a running game counts as a forfeit.
  async leave() {
    try {
      if (this.state && this.state.status !== "finished") {
        await api.leaveGame(this.gameId, this.token);
      }
    } catch (e) {
      // The game may already be over; go back to the lobby anyway.
    }
    storage.remove("reversi_game_" + this.gameId);
    this.app.openLobby();
  }

  isMyTurn() {
    const s = this.state;
    return s.status === "in_progress" && s.your_colour === s.current_turn;
  }

  // Draw the board and the legal moves.
  render() {
    const s = this.state;
    const share = document.getElementById("share-text");
    const turn = document.getElementById("turn-text");

    showScore(s.board, s.players);
    document.getElementById("black-label").classList.toggle("active", s.status === "in_progress" && s.current_turn === "black");
    document.getElementById("white-label").classList.toggle("active", s.status === "in_progress" && s.current_turn === "white");

    let hints = [];
    if (s.status === "waiting") {
      share.hidden = false;
      share.textContent = "Waiting for an opponent... Invite a friend with this link: " +
        location.origin + "/?game=" + s.id;
      turn.textContent = "";
    } else {
      share.hidden = true;
      if (s.status === "in_progress") {
        if (this.isMyTurn()) {
          turn.textContent = "Your turn (" + s.your_colour + ")";
          hints = Rules.legalMoves(s.board, Rules.colourValue(s.your_colour));
        } else {
          turn.textContent = "Waiting for " + s.players[s.current_turn] + " (" + s.current_turn + ")";
        }
      }
    }

    drawBoard(s.board, hints, (r, c) => this.play(r, c));

    if (s.status === "finished") this.showResult();
  }

  // Show the winner (UC-04) and stop polling.
  showResult() {
    const s = this.state;
    clearInterval(this.timer);
    storage.remove("reversi_game_" + this.gameId);

    let text;
    if (s.result === s.your_colour) text = "You won!";
    else if (s.result === "draw") text = "It's a draw!";
    else text = "You lost. " + resultText(s.result, s.players) + ".";

    this.setMessage("");
    document.getElementById("turn-text").textContent = "Game over";
    document.getElementById("result-text").textContent = text;
    document.getElementById("result-box").hidden = false;
    document.getElementById("quit-btn").hidden = true;
  }
}

// Replay page: steps through the moves of a finished game.
class ReplayPage {
  constructor(app, gameId) {
    this.app = app;
    this.gameId = gameId;
    this.boards = [];  // board after each move, boards[0] = start
    this.step = 0;
    this.data = null;

    document.getElementById("prev-btn").onclick = () => this.go(this.step - 1);
    document.getElementById("next-btn").onclick = () => this.go(this.step + 1);
    document.getElementById("replay-back-btn").onclick = () => this.app.openLobby();
  }

  async show() {
    document.getElementById("game-page").hidden = false;
    document.getElementById("quit-btn").hidden = true;
    document.getElementById("result-box").hidden = true;
    document.getElementById("share-text").hidden = true;
    document.getElementById("message").textContent = "";
    document.getElementById("replay-controls").hidden = false;

    try {
      this.data = await api.replay(this.gameId);
    } catch (e) {
      this.app.openLobby(e.message);
      return;
    }

    let board = this.data.initial_board;
    this.boards = [board];
    for (const move of this.data.moves) {
      board = Rules.apply(board, move.row, move.col, Rules.colourValue(move.colour));
      this.boards.push(board);
    }
    this.go(0);
  }

  hide() {
    document.getElementById("game-page").hidden = true;
    document.getElementById("replay-controls").hidden = true;
  }

  go(step) {
    if (step < 0 || step >= this.boards.length) return;
    this.step = step;
    const board = this.boards[step];
    const last = this.boards.length - 1;

    showScore(board, this.data.players);
    drawBoard(board, [], null);
    document.getElementById("replay-step").textContent = "Move " + step + " / " + last;
    document.getElementById("turn-text").textContent =
      step === last ? "Final: " + resultText(this.data.result, this.data.players) : "Replay of game #" + this.gameId;
  }
}
