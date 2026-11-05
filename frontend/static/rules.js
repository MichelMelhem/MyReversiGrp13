// Board helpers used only for display: highlighting legal moves, counting
// discs and rebuilding boards for replays. The server stays in charge of
// checking and applying real moves.
// Board values: 0 = empty, 1 = black, 2 = white.
const EMPTY = 0, BLACK = 1, WHITE = 2;

const DIRECTIONS = [
  [-1, -1], [-1, 0], [-1, 1],
  [0, -1],           [0, 1],
  [1, -1],  [1, 0],  [1, 1],
];

const Rules = {
  colourValue(colour) {
    return colour === "black" ? BLACK : WHITE;
  },

  // Returns the list of discs that would be flipped by playing at (row, col).
  flips(board, row, col, value) {
    const size = board.length;
    const other = value === BLACK ? WHITE : BLACK;
    if (board[row][col] !== EMPTY) return [];

    let result = [];
    for (const [dr, dc] of DIRECTIONS) {
      let r = row + dr, c = col + dc;
      const line = [];
      while (r >= 0 && r < size && c >= 0 && c < size && board[r][c] === other) {
        line.push([r, c]);
        r += dr;
        c += dc;
      }
      if (line.length > 0 && r >= 0 && r < size && c >= 0 && c < size && board[r][c] === value) {
        result = result.concat(line);
      }
    }
    return result;
  },

  legalMoves(board, value) {
    const moves = [];
    for (let r = 0; r < board.length; r++) {
      for (let c = 0; c < board.length; c++) {
        if (this.flips(board, r, c, value).length > 0) moves.push([r, c]);
      }
    }
    return moves;
  },

  // Returns a new board with the move played (used by the replay viewer).
  apply(board, row, col, value) {
    const copy = board.map((line) => line.slice());
    for (const [r, c] of this.flips(board, row, col, value)) copy[r][c] = value;
    copy[row][col] = value;
    return copy;
  },

  count(board) {
    let black = 0, white = 0;
    for (const line of board) {
      for (const cell of line) {
        if (cell === BLACK) black++;
        if (cell === WHITE) white++;
      }
    }
    return { black: black, white: white };
  },
};
