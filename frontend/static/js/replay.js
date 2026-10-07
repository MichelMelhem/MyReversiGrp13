// Replay: step through the board after each move of a finished game.

const gameId = location.pathname.split('/').filter(Boolean)[1];
const boardEl = document.getElementById('board');
const statusEl = document.getElementById('replay-status');
const scrubber = document.getElementById('scrubber');
const playBtn = document.getElementById('play-btn');
const moveListEl = document.getElementById('move-list');

let frames = [];
let index = 0;
let timer = null;

function show(i, animate = false) {
  const prev = frames[index];
  index = Math.max(0, Math.min(frames.length - 1, i));
  const frame = frames[index];
  renderBoard(boardEl, frame.board, {
    previous: animate && prev ? prev.board : null,
    lastMove: frame.move,
  });
  document.querySelector('#card-black [data-count]').textContent = frame.black;
  document.querySelector('#card-white [data-count]').textContent = frame.white;
  statusEl.textContent = frame.move
    ? `Move ${frame.move.number} of ${frames.length - 1}: ${COLOR_NAME[frame.move.color]} plays ${frame.move.label}, flips ${frame.move.flipped}`
    : `Starting position (${frames.length - 1} moves)`;
  scrubber.value = index;
  moveListEl.querySelectorAll('li').forEach((li, n) => li.classList.toggle('current', n === index - 1));
  const current = moveListEl.querySelector('li.current');
  if (current) current.scrollIntoView({ block: 'nearest' });
}

function stop() {
  clearInterval(timer);
  timer = null;
  playBtn.textContent = 'Play';
}

playBtn.addEventListener('click', () => {
  if (timer) return stop();
  if (index >= frames.length - 1) show(0);
  playBtn.textContent = 'Pause';
  timer = setInterval(() => {
    if (index >= frames.length - 1) return stop();
    show(index + 1, true);
  }, 800);
});
document.getElementById('first-btn').addEventListener('click', () => { stop(); show(0); });
document.getElementById('last-btn').addEventListener('click', () => { stop(); show(frames.length - 1); });
document.getElementById('prev-btn').addEventListener('click', () => { stop(); show(index - 1); });
document.getElementById('next-btn').addEventListener('click', () => { stop(); show(index + 1, true); });
scrubber.addEventListener('input', () => { stop(); show(Number(scrubber.value)); });
moveListEl.addEventListener('click', (e) => {
  const li = e.target.closest('li');
  if (li) { stop(); show(Number(li.dataset.frame)); }
});
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowRight') { stop(); show(index + 1, true); }
  if (e.key === 'ArrowLeft') { stop(); show(index - 1); }
});

(async function load() {
  try {
    const data = await api(`games/${gameId}/replay/`);
    frames = data.frames;
    const g = data.game;
    document.querySelector('#card-black [data-name]').textContent = g.players.black.name;
    document.querySelector('#card-white [data-name]').textContent = g.players.white.name;
    document.getElementById('replay-result').textContent =
      `${resultText(g)} · ${g.players.black.count}–${g.players.white.count} · ${endReasonText(g.end_reason)}`;
    scrubber.max = frames.length - 1;
    moveListEl.innerHTML = g.moves.map((m, n) => `
      <li data-frame="${n + 1}" style="cursor:pointer">
        <span class="num">${m.number}.</span>
        <span class="mini ${m.color}"></span>${m.label}
      </li>`).join('');
    show(0);
  } catch (err) {
    statusEl.textContent = err.message;
  }
})();
