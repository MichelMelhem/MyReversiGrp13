// Game page: renders the server's game state and sends the player's moves.
// The server is the authority: it validates moves, flips pieces, skips turns
// and decides when the game ends. This page only displays and requests.

const gameId = location.pathname.split('/').filter(Boolean)[1];
const seat = gameSeat(gameId);              // null when watching someone else's game
const token = seat ? seat.token : null;

const POLL_MS = 1500;
const COMPUTER_DELAY_MS = 700;               // short pause so the player can follow (UC-05)

const boardEl = document.getElementById('board');
const bannerEl = document.getElementById('turn-banner');
const eventEl = document.getElementById('event-text');
const moveListEl = document.getElementById('move-list');
const noMovesEl = document.getElementById('no-moves');
const hintsToggle = document.getElementById('hints-toggle');
const coordForm = document.getElementById('coord-form');
const coordInput = document.getElementById('coord-input');
const leaveBtn = document.getElementById('leave-btn');
const waitingOverlay = document.getElementById('waiting-overlay');
const resultOverlay = document.getElementById('result-overlay');

let state = null;
let busy = false;
let computerTimer = null;
let resultDismissed = false;

hintsToggle.checked = Store.get('showHints', true);
hintsToggle.addEventListener('change', () => {
  Store.set('showHints', hintsToggle.checked);
  if (state) render(state);
});

async function refresh() {
  if (busy) return;   // a move is in flight; its response will carry the newer state
  try {
    render(await api(`games/${gameId}/`, { token }));
  } catch (err) {
    if (err.status === 404) {
      bannerEl.textContent = 'This game does not exist.';
      stopPolling();
    } else {
      eventEl.textContent = err.message;
    }
  }
}

function render(next) {
  const previous = state;
  state = next;
  const you = next.you;
  const moved = previous && previous.move_count !== next.move_count;

  const lastMove = next.moves.length ? next.moves[next.moves.length - 1] : null;
  const canAct = next.is_your_turn && !busy;
  renderBoard(boardEl, next.board, {
    previous: moved ? previous.board : null,
    playable: canAct && hintsToggle.checked ? next.valid_moves : [],
    lastMove,
    mine: canAct ? you : null,
    onPlay: play,
  });
  // Without hints the squares are still clickable; the server says if a move is illegal.
  if (canAct && !hintsToggle.checked) {
    boardEl.querySelectorAll('.cell:not(:has(.disc))').forEach((c) => { c.style.cursor = 'pointer'; });
  } else {
    boardEl.querySelectorAll('.cell').forEach((c) => { c.style.cursor = ''; });
  }

  for (const color of ['black', 'white']) {
    const card = document.getElementById(`card-${color}`);
    const p = next.players[color];
    card.querySelector('[data-name]').textContent = p.name || 'Waiting…';
    card.querySelector('[data-count]').textContent = p.count;
    card.querySelector('[data-tag]').textContent =
      color === you ? `${COLOR_NAME[color]} · You` : p.is_computer ? `${COLOR_NAME[color]} · AI` : COLOR_NAME[color];
    card.classList.toggle('active', next.current_color === color);
  }

  bannerEl.textContent = bannerText(next);
  bannerEl.classList.toggle('yours', next.is_your_turn);

  if (!previous || previous.last_event !== next.last_event) {
    eventEl.textContent = next.last_event;
    // UC-03: make a skipped turn obvious to both players.
    if (previous && /no legal move/i.test(next.last_event) && next.status === 'in_progress') {
      toast(next.last_event.split('. ').slice(-1)[0], { duration: 3500 });
    }
  }

  renderMoves(next.moves);

  const playing = next.status === 'in_progress';
  coordForm.hidden = !you || !playing;
  coordInput.disabled = !canAct;
  leaveBtn.hidden = !you || !(playing || next.status === 'waiting');

  waitingOverlay.hidden = next.status !== 'waiting' || !you;
  if (next.status === 'finished') showResult(next);
  if (next.status === 'finished' || next.status === 'cancelled') stopPolling();

  maybeScheduleComputer();
}

function bannerText(s) {
  if (s.status === 'waiting') return 'Waiting for an opponent to join…';
  if (s.status === 'cancelled') return 'This game was cancelled.';
  if (s.status === 'finished') {
    return `${resultText(s, s.you)} — ${s.players.black.count} : ${s.players.white.count}`;
  }
  const mover = s.players[s.current_color];
  if (s.is_your_turn) {
    const n = s.valid_moves.length;
    return `Your turn (${COLOR_NAME[s.you]}) — ${n} legal move${n === 1 ? '' : 's'}`;
  }
  if (mover.is_computer) return 'Computer is thinking…';
  if (s.you) return `Waiting for ${mover.name} (${COLOR_NAME[s.current_color]})…`;
  return `${mover.name} (${COLOR_NAME[s.current_color]}) to move`;
}

function renderMoves(moves) {
  noMovesEl.hidden = moves.length > 0;
  if (moveListEl.children.length === moves.length) return;
  moveListEl.innerHTML = moves.map((m, i) => `
    <li class="${i === moves.length - 1 ? 'current' : ''}">
      <span class="num">${m.number}.</span>
      <span class="mini ${m.color}" aria-label="${m.color}"></span>
      ${m.label}
    </li>`).join('');
  moveListEl.scrollTop = moveListEl.scrollHeight;
}

async function play(row, col) {
  if (!state || busy) return;
  if (state.status !== 'in_progress') return;
  if (!state.is_your_turn) {
    toast("It's not your turn yet.");
    return;
  }
  busy = true;
  try {
    render(await api(`games/${gameId}/move/`, { method: 'POST', token, body: { row, col } }));
  } catch (err) {
    // UC-02 2a: illegal move — board unchanged, tell the player why.
    toast(`${squareLabel(row, col)}: ${err.message}`, { error: true });
  } finally {
    busy = false;
    if (state) render(state);
  }
}

coordForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const square = parseSquare(coordInput.value, state ? state.board_size : 8);
  if (!square) {
    toast('Type a square such as D3.', { error: true });
    return;
  }
  coordInput.value = '';
  play(square.row, square.col);
});

function maybeScheduleComputer() {
  const s = state;
  const computerToMove = s && s.mode === 'computer' && s.status === 'in_progress'
    && s.you && !s.is_your_turn;
  if (!computerToMove || computerTimer || busy) return;
  computerTimer = setTimeout(async () => {
    busy = true;
    try {
      render(await api(`games/${gameId}/computer-move/`, { method: 'POST', token }));
    } catch (err) {
      toast(err.message, { error: true });
    } finally {
      busy = false;
      computerTimer = null;
      if (state) render(state);
    }
  }, COMPUTER_DELAY_MS);
}

function showResult(s) {
  if (resultDismissed) return;
  const title = document.getElementById('result-title');
  title.textContent = resultText(s, s.you);
  document.getElementById('result-reason').textContent = endReasonText(s.end_reason);
  document.getElementById('result-score').textContent =
    `${s.players.black.name} ${s.players.black.count} – ${s.players.white.count} ${s.players.white.name}`;
  document.getElementById('replay-link').href = `/replay/${s.id}/`;
  document.getElementById('rematch-btn').hidden = !(seat && seat.settings);
  resultOverlay.hidden = false;
}

document.getElementById('close-result-btn').addEventListener('click', () => {
  resultDismissed = true;
  resultOverlay.hidden = true;
});

document.getElementById('rematch-btn').addEventListener('click', async (e) => {
  const settings = seat.settings;
  e.target.disabled = true;
  try {
    const path = settings.mode === 'online' ? 'lobby/join/' : 'games/computer/';
    const data = await api(path, { method: 'POST', body: settings });
    saveSeat(data.state.id, data.token, data.color, settings);
    location.href = `/game/${data.state.id}/`;
  } catch (err) {
    toast(err.message, { error: true });
    e.target.disabled = false;
  }
});

async function leave() {
  try {
    render(await api(`games/${gameId}/leave/`, { method: 'POST', token }));
  } catch (err) {
    toast(err.message, { error: true });
  }
}

leaveBtn.addEventListener('click', () => {
  if (confirm('Leave this game? It will count as a forfeit and your opponent wins.')) leave();
});

document.getElementById('cancel-wait-btn').addEventListener('click', async () => {
  await leave();
  location.href = '/';
});

// --- polling (online games need it to see the opponent's moves) -----------
let pollTimer = null;
function startPolling() {
  if (!pollTimer) pollTimer = setInterval(refresh, POLL_MS);
}
function stopPolling() {
  clearInterval(pollTimer);
  pollTimer = null;
}

refresh().then(() => {
  if (state && (state.mode === 'online') && ['waiting', 'in_progress'].includes(state.status)) {
    startPolling();
  }
});
