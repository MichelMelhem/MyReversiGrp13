// Starts the client and switches between the lobby, game and replay pages.
class App {
  constructor() {
    this.lobby = new LobbyPage(this);
    this.page = null;

    const dialog = document.getElementById("rules-dialog");
    document.getElementById("rules-btn").onclick = () => dialog.showModal();
    document.getElementById("close-rules").onclick = () => dialog.close();
  }

  switchTo(page) {
    if (this.page) this.page.hide();
    this.page = page;
    page.show();
  }

  openLobby(message = "") {
    history.replaceState(null, "", "/");
    this.switchTo(this.lobby);
    this.lobby.showMessage(message);
  }

  openGame(gameId, token) {
    history.replaceState(null, "", "/?game=" + gameId);
    this.switchTo(new GamePage(this, gameId, token));
  }

  openReplay(gameId) {
    this.switchTo(new ReplayPage(this, gameId));
  }

  renderLeaderboard(players) {
    const list = document.getElementById("leaderboard");
    list.innerHTML = "";
    for (const p of players.slice(0, 10)) {
      const item = document.createElement("li");
      item.textContent = p.name + " - " + p.wins + "W " + p.losses + "L " + p.draws + "D";
      list.append(item);
    }
    if (players.length === 0) list.innerHTML = "<li class=\"empty\">No players yet.</li>";
  }

  // Only show the invite if that game is still waiting for a second player.
  async showInvite(gameId) {
    try {
      const game = await api.getGame(gameId);
      if (game.status === "waiting") {
        this.lobby.showMessage("You were invited to game #" + gameId +
          ". Enter your name and click Join next to it under Open games.");
      }
    } catch (e) {
      // Unknown game: just stay in the lobby.
    }
  }

  // A link like /?game=5 either resumes our own game (token saved in the
  // browser) or is an invite to join that game.
  start() {
    const gameId = new URLSearchParams(location.search).get("game");
    if (!gameId) {
      this.openLobby();
      return;
    }
    const token = storage.get("reversi_game_" + gameId);
    if (token) {
      this.openGame(gameId, token);
    } else {
      this.openLobby();
      this.showInvite(gameId);
    }
  }
}

const app = new App();
app.start();
