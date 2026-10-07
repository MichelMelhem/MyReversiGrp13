// History: list finished games, optionally for one username.

const body = document.getElementById('history-body');
const empty = document.getElementById('history-empty');
const nameInput = document.getElementById('filter-name');

function resultCell(g) {
  if (g.result === 'draw') return 'Draw';
  const winner = g.result === 'black' ? g.black : g.white;
  const suffix = g.end_reason === 'no_moves' ? '' : ' (forfeit)';
  return `${escapeHtml(winner)} wins${suffix}`;
}

async function load(name = '') {
  const query = name ? `?name=${encodeURIComponent(name)}` : '';
  try {
    const games = await api(`games/history/${query}`);
    empty.hidden = games.length > 0;
    empty.textContent = name ? `No finished games for “${name}”.` : 'No finished games yet.';
    body.innerHTML = games.map((g) => `
      <tr>
        <td>${formatDate(g.finished_at)}</td>
        <td>${escapeHtml(g.black)}</td>
        <td class="num">${g.black_count} – ${g.white_count}</td>
        <td>${escapeHtml(g.white)}</td>
        <td><span class="result-pill">${resultCell(g)}</span></td>
        <td>${g.board_size}×${g.board_size}</td>
        <td><a href="/replay/${g.id}/">Replay</a></td>
      </tr>`).join('');
  } catch (err) {
    empty.hidden = false;
    empty.textContent = err.message;
  }
}

document.getElementById('filter-form').addEventListener('submit', (e) => {
  e.preventDefault();
  load(nameInput.value.trim());
});
document.getElementById('clear-filter').addEventListener('click', () => {
  nameInput.value = '';
  load();
});

nameInput.value = Store.get('name', '');
load(nameInput.value);
