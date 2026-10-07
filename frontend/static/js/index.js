// Lobby: choose opponent, board size, difficulty and colour, then start a game.

const form = document.getElementById('new-game-form');
const nameInput = document.getElementById('name');
const errorEl = document.getElementById('form-error');
const startBtn = document.getElementById('start-btn');
const difficultyField = document.getElementById('difficulty-field');
const sizeHint = document.getElementById('size-hint');

function selected(name) {
  return form.querySelector(`input[name="${name}"]:checked`).value;
}
function select(name, value) {
  const input = form.querySelector(`input[name="${name}"][value="${value}"]`);
  if (input) input.checked = true;
}

function syncModeFields() {
  const online = selected('mode') === 'online';
  difficultyField.hidden = online;
  sizeHint.hidden = !online;
  startBtn.textContent = online ? 'Find an opponent' : 'Start game';
}

// Restore last-used settings.
const saved = Store.get('settings', {});
nameInput.value = Store.get('name', '');
if (saved.mode) select('mode', saved.mode);
if (saved.difficulty) select('difficulty', saved.difficulty);
if (saved.board_size) select('board_size', saved.board_size);
select('theme', Store.get('boardTheme', 'classic'));
syncModeFields();

form.addEventListener('change', (e) => {
  if (e.target.name === 'mode') syncModeFields();
  if (e.target.name === 'theme') {
    Store.set('boardTheme', e.target.value);
    applyBoardTheme(e.target.value);
  }
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.textContent = '';
  const name = nameInput.value.trim();
  if (!name) {
    errorEl.textContent = 'Please enter a username.';
    nameInput.focus();
    return;
  }
  const settings = {
    mode: selected('mode'),
    difficulty: selected('difficulty'),
    board_size: Number(selected('board_size')),
  };
  Store.set('name', name);
  Store.set('settings', settings);

  startBtn.disabled = true;
  try {
    const path = settings.mode === 'online' ? 'lobby/join/' : 'games/computer/';
    const data = await api(path, { method: 'POST', body: { name, ...settings } });
    saveSeat(data.state.id, data.token, data.color, { name, ...settings });
    location.href = `/game/${data.state.id}/`;
  } catch (err) {
    errorEl.textContent = err.message;
    startBtn.disabled = false;
  }
});

// Offer to resume the last game if it is still running.
(async function checkResume() {
  const lastId = Store.get('lastGame');
  const seat = lastId && gameSeat(lastId);
  if (!seat) return;
  try {
    const state = await api(`games/${lastId}/`, { token: seat.token });
    if (state.status !== 'in_progress' && state.status !== 'waiting') return;
    const opponent = state.players[seat.color === 'black' ? 'white' : 'black'].name;
    document.getElementById('resume-detail').textContent = state.status === 'waiting'
      ? 'Waiting for an online opponent.'
      : `You (${COLOR_NAME[seat.color]}) vs ${opponent} — ${state.players.black.count}–${state.players.white.count}`;
    document.getElementById('resume-link').href = `/game/${lastId}/`;
    document.getElementById('resume').hidden = false;
  } catch {
    /* game gone or server down: just don't offer resume */
  }
})();
