// Shared helpers: API calls, local storage, board theme and board rendering.

const Store = {
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(`reversi.${key}`);
      return raw === null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try { localStorage.setItem(`reversi.${key}`, JSON.stringify(value)); } catch { /* ignore */ }
  },
  remove(key) {
    try { localStorage.removeItem(`reversi.${key}`); } catch { /* ignore */ }
  },
};

/** The per-game secret token this browser received when creating/joining. */
function gameSeat(gameId) {
  return Store.get(`seat.${gameId}`);
}
function saveSeat(gameId, token, color, settings) {
  Store.set(`seat.${gameId}`, { token, color, settings });
  Store.set('lastGame', gameId);
}

async function api(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Accept': 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers['X-Player-Token'] = token;
  let response;
  try {
    response = await fetch(`/api/${path}`, {
      method, headers, body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error('Cannot reach the MyReversi server. Check your connection and try again.');
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const err = new Error(data.error || `Request failed (${response.status}).`);
    err.status = response.status;
    throw err;
  }
  return data;
}

function applyBoardTheme(theme = Store.get('boardTheme', 'classic')) {
  document.documentElement.dataset.boardTheme = theme;
}
applyBoardTheme();

function markCurrentNav() {
  const here = location.pathname.replace(/\/+$/, '/') || '/';
  document.querySelectorAll('.site-nav a').forEach((a) => {
    if (a.getAttribute('href') === here) a.setAttribute('aria-current', 'page');
  });
}
document.addEventListener('DOMContentLoaded', markCurrentNav);

const COLOR_NAME = { black: 'Black', white: 'White' };

function squareLabel(row, col) {
  return `${String.fromCharCode(65 + col)}${row + 1}`;
}

function parseSquare(text, size) {
  const m = /^\s*([a-z])\s*(\d{1,2})\s*$/i.exec(text || '');
  if (!m) return null;
  const col = m[1].toUpperCase().charCodeAt(0) - 65;
  const row = Number(m[2]) - 1;
  if (row < 0 || col < 0 || row >= size || col >= size) return null;
  return { row, col };
}

let toastTimer;
function toast(message, { error = false, duration = 3000 } = {}) {
  let el = document.querySelector('.toast');
  if (!el) {
    el = document.createElement('div');
    el.className = 'toast';
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.toggle('error', error);
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), duration);
}

/**
 * Draws a board into `root` (a .board-frame element).
 * opts: { playable: [[r,c]...], lastMove: {row,col}, previous: grid, onPlay(row,col), mine }
 */
function renderBoard(root, grid, opts = {}) {
  const size = grid.length;
  root.style.setProperty('--size', size);

  if (root.dataset.size !== String(size)) {
    root.dataset.size = String(size);
    root.innerHTML = '';
    const cols = document.createElement('div');
    cols.className = 'board-cols';
    cols.setAttribute('aria-hidden', 'true');
    const rows = document.createElement('div');
    rows.className = 'board-rows';
    rows.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < size; i++) {
      cols.insertAdjacentHTML('beforeend', `<span>${String.fromCharCode(65 + i)}</span>`);
      rows.insertAdjacentHTML('beforeend', `<span>${i + 1}</span>`);
    }
    const board = document.createElement('div');
    board.className = 'board';
    board.setAttribute('role', 'grid');
    board.setAttribute('aria-label', `${size} by ${size} Reversi board`);
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const cell = document.createElement('button');
        cell.type = 'button';
        cell.className = 'cell';
        cell.dataset.row = r;
        cell.dataset.col = c;
        board.appendChild(cell);
      }
    }
    board.addEventListener('click', (e) => {
      const cell = e.target.closest('.cell');
      if (cell && board._onPlay) board._onPlay(Number(cell.dataset.row), Number(cell.dataset.col));
    });
    root.append(document.createElement('span'), cols, rows, board);
  }

  const board = root.querySelector('.board');
  board._onPlay = opts.onPlay || null;
  board.classList.toggle('mine-black', opts.mine === 'black');
  board.classList.toggle('mine-white', opts.mine === 'white');
  const playable = new Set((opts.playable || []).map(([r, c]) => `${r},${c}`));
  const prev = opts.previous;

  board.querySelectorAll('.cell').forEach((cell) => {
    const r = Number(cell.dataset.row);
    const c = Number(cell.dataset.col);
    const value = grid[r][c];
    const before = prev ? prev[r][c] : value;
    const canPlay = playable.has(`${r},${c}`);

    cell.classList.toggle('playable', canPlay);
    cell.classList.toggle('last', !!opts.lastMove && opts.lastMove.row === r && opts.lastMove.col === c);
    cell.tabIndex = canPlay ? 0 : -1;
    const label = squareLabel(r, c);
    cell.setAttribute('aria-label',
      value ? `${label}, ${value}` : canPlay ? `${label}, legal move` : `${label}, empty`);

    const existing = cell.querySelector('.disc');
    if (!value) {
      if (existing) existing.remove();
      return;
    }
    let disc = existing;
    if (!disc) {
      disc = document.createElement('span');
      cell.appendChild(disc);
    }
    disc.className = `disc ${value}`;
    if (prev && !before) disc.classList.add('placed');
    else if (prev && before && before !== value) {
      void disc.offsetWidth; // restart the animation
      disc.classList.add('flipped');
    }
  });

  // Keep keyboard focus usable: first playable square is reachable by Tab.
  if (!board.querySelector('.cell[tabindex="0"]')) {
    const first = board.querySelector('.cell');
    if (first) first.tabIndex = 0;
  }
}

function resultText(state, viewer) {
  if (state.result === 'draw') return 'Draw';
  if (!state.result) return '';
  const winner = state.players[state.result].name || COLOR_NAME[state.result];
  if (viewer) return state.result === viewer ? 'You win!' : 'You lose';
  return `${winner} wins`;
}

function endReasonText(reason) {
  return {
    no_moves: 'No legal moves remaining',
    forfeit: 'Forfeit — a player left the game',
    disconnect: 'Forfeit — a player lost connection',
  }[reason] || '';
}

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function escapeHtml(text) {
  return String(text ?? '').replace(/[&<>"']/g, (ch) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}
