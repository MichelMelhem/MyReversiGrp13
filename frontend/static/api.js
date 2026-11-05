// Sends requests to the Django server and returns the JSON answer.
class ApiClient {
  async api(path, method = "GET", body = null, token = null) {
    const headers = { "Content-Type": "application/json" };
    if (token) headers["X-Player-Token"] = token;

    const csrf = document.cookie.match(/csrftoken=([^;]+)/);
    if (csrf) headers["X-CSRFToken"] = csrf[1];

    const response = await fetch("/api/" + path, {
      method: method,
      headers: headers,
      body: body ? JSON.stringify(body) : null,
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || "Server error (" + response.status + ")");
    }
    return data;
  }

  createGame()            { return this.api("games/", "POST"); }
  joinGame(id, name, tok) { return this.api("games/" + id + "/join/", "POST", { name: name }, tok); }
  getGame(id)             { return this.api("games/" + id + "/"); }
  pollGame(id, tok)       { return this.api("games/" + id + "/poll/", "GET", null, tok); }
  makeMove(id, tok, r, c) { return this.api("games/" + id + "/moves/", "POST", { row: r, col: c }, tok); }
  leaveGame(id, tok)      { return this.api("games/" + id + "/leave/", "POST", null, tok); }
  availableGames()        { return this.api("games/available/"); }
  history()               { return this.api("games/history/"); }
  replay(id)              { return this.api("games/" + id + "/replay/"); }
  leaderboard()           { return this.api("leaderboard/"); }
}

const api = new ApiClient();

// Remembers the player name and game tokens for this browser tab, so two
// players can test in two tabs and a page refresh resumes the game.
const storage = {
  get(key) {
    try { return sessionStorage.getItem(key); } catch (e) { return null; }
  },
  set(key, value) {
    try { sessionStorage.setItem(key, value); } catch (e) { /* ignore */ }
  },
  remove(key) {
    try { sessionStorage.removeItem(key); } catch (e) { /* ignore */ }
  },
};
