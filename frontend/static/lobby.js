// Lobby page: the player enters a name, creates or joins an online game,
// and can look at finished games and the leaderboard.
class LobbyPage {
  constructor(app) {
    this.app = app;
    this.timer = null;
    this.nameInput = document.getElementById("name-input");
    this.message = document.getElementById("lobby-message");
    this.nameInput.value = storage.get("reversi_name") || "";

    document.getElementById("create-btn").onclick = () => this.createGame();
    document.getElementById("random-btn").onclick = () => this.joinRandom();
  }

  show() {
    document.getElementById("lobby-page").hidden = false;
    this.refresh();
    this.timer = setInterval(() => this.refresh(), 3000);
  }

  hide() {
    document.getElementById("lobby-page").hidden = true;
    clearInterval(this.timer);
  }

  showMessage(text) {
    this.message.textContent = text;
  }

  // Returns the typed name, or null (with a message) if it is empty.
  getName() {
    const name = this.nameInput.value.trim();
    if (!name) {
      this.showMessage("Please enter your name first.");
      this.nameInput.focus();
      return null;
    }
    storage.set("reversi_name", name);
    return name;
  }

  async createGame() {
    const name = this.getName();
    if (!name) return;
    try {
      const game = await api.createGame();
      await this.joinGame(game.id);
    } catch (e) {
      this.showMessage(e.message);
    }
  }

  // Joins the oldest open game, or creates a new one if there are none.
  async joinRandom() {
    const name = this.getName();
    if (!name) return;
    try {
      const games = await api.availableGames();
      if (games.length === 0) {
        this.showMessage("No open games, so a new one was created for you.");
        await this.createGame();
      } else {
        await this.joinGame(games[games.length - 1].id);
      }
    } catch (e) {
      this.showMessage(e.message);
    }
  }

  async joinGame(gameId) {
    const name = this.getName();
    if (!name) return;
    try {
      const result = await api.joinGame(gameId, name, null);
      storage.set("reversi_game_" + gameId, result.player_token);
      this.app.openGame(gameId, result.player_token);
    } catch (e) {
      this.showMessage(e.message);
    }
  }

  async refresh() {
    try {
      const [games, history, leaders] = await Promise.all([
        api.availableGames(), api.history(), api.leaderboard(),
      ]);
      this.renderOpenGames(games);
      this.renderHistory(history);
      this.app.renderLeaderboard(leaders);
    } catch (e) {
      this.showMessage("Cannot reach the server: " + e.message);
    }
  }

  renderOpenGames(games) {
    const list = document.getElementById("open-games");
    list.innerHTML = "";
    if (games.length === 0) {
      list.innerHTML = "<li>No open games right now.</li>";
      return;
    }
    for (const game of games) {
      const item = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = "#" + game.id + " - " + game.host + " (" + game.board_size + "x" + game.board_size + ")";
      const button = document.createElement("button");
      button.className = "pill";
      button.textContent = "Join";
      button.onclick = () => this.joinGame(game.id);
      item.append(text, button);
      list.append(item);
    }
  }

  renderHistory(games) {
    const list = document.getElementById("history");
    list.innerHTML = "";
    if (games.length === 0) {
      list.innerHTML = "<li>No finished games yet.</li>";
      return;
    }
    for (const game of games.slice(0, 10)) {
      const item = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = "#" + game.id + " " + game.players.black + " vs " + game.players.white +
        " - " + resultText(game.result, game.players);
      const button = document.createElement("button");
      button.className = "pill";
      button.textContent = "Replay";
      button.onclick = () => this.app.openReplay(game.id);
      item.append(text, button);
      list.append(item);
    }
  }
}

// Turns the server's result field into a short sentence.
function resultText(result, players) {
  if (result === "black" || result === "white") {
    return (players[result] || result) + " (" + result + ") won";
  }
  if (result === "draw") return "Draw";
  return result || "Unknown result";
}
