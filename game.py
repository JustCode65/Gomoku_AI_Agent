from __future__ import print_function
import copy

GRID_COUNT = 11

WHITE = 'w'
BLACK = 'b'
EMPTY = '.'

ROLLOUT_RNG_MAX = 1000;

class Game:
    """
    Handles the board state and rules for Gomoku (five-in-a-row).
    The board is an 11x11 grid. Players alternate placing stones,
    and the first to get 5 in a line wins.
    """

    def __init__(self, player=BLACK, grid=None):
        self.rollout_rng = 0
        self.reset(player, grid)

    def reset(self, player=BLACK, init_grid=None):
        """Wipe the board and set it up fresh, or restore from a given grid."""
        self.winning_pos = None
        self.winner = None
        self.game_over = False
        self.player = player
        self.actions = []
        self.maxrc = (len(init_grid) - 1) if init_grid is not None else (GRID_COUNT - 1)
        self.max_r = self.max_c = self.min_r = self.min_c = (self.maxrc) // 2

        if init_grid is not None:
            self.grid = copy.deepcopy(init_grid)
            self._scan_board(False)
        else:
            self.grid = self._make_empty_grid(GRID_COUNT)
            self._scan_board()
            self.place(*(self.get_actions()[0]))
            self.place(*self.rand_move())

    def _update_bounds(self, r, c, rebuild_actions=True):
        """Expand the active region of the board around (r,c) and
        add any new cells that fall inside the region to the action list."""
        prev_max_r = self.max_r
        prev_min_r = self.min_r
        prev_max_c = self.max_c
        prev_min_c = self.min_c

        self.max_r = min(self.maxrc, max(self.max_r, r + 1))
        self.max_c = min(self.maxrc, max(self.max_c, c + 1))
        self.min_r = max(0, min(self.min_r, r - 1))
        self.min_c = max(0, min(self.min_c, c - 1))

        if rebuild_actions:
            new_rows = []
            if self.max_r != prev_max_r:
                new_rows.append(self.max_r)
            if self.min_r != prev_min_r:
                new_rows.append(self.min_r)

            for nr in new_rows:
                for cp in range(self.min_c, self.max_c + 1):
                    self.actions.append((nr, cp))

            new_cols = []
            if self.max_c != prev_max_c:
                new_cols.append(self.max_c)
            if self.min_c != prev_min_c:
                new_cols.append(self.min_c)
            for nc in new_cols:
                for rp in range(prev_min_r, prev_max_r + 1):
                    self.actions.append((rp, nc))

    def _scan_board(self, rebuild_actions=True):
        """Walk over every cell, expand bounds around placed stones,
        and check for any existing wins."""
        for r in range(0, self.maxrc + 1):
            for c in range(0, self.maxrc + 1):
                if self.grid[r][c] != EMPTY:
                    self._update_bounds(r, c, rebuild_actions)
                    self._check_winner(r, c)

        for i in range(self.min_r, self.max_r + 1):
            for j in range(self.min_c, self.max_c + 1):
                if self.grid[i][j] == EMPTY:
                    if (i, j) not in self.actions:
                        self.actions.append((i, j))

    def state(self):
        """Return (current_player, grid) tuple."""
        return (self.player, self.grid)

    def _make_empty_grid(self, size):
        """Create a size x size grid filled with EMPTY dots."""
        return [list("." * size) for _ in range(size)]

    def place(self, r, c):
        """Put the current player's stone at (r,c). Returns True on success."""
        if (r, c) in self.get_actions():
            self.actions.remove((r, c))
            self.grid[r][c] = self.player
            self._update_bounds(r, c, True)

            self._check_winner(r, c)
            if len(self.get_actions()) == 0:
                self.game_over = True
                self.winner = WHITE

            # swap turn
            self.player = WHITE if self.player == BLACK else BLACK
            return True
        return False

    def _check_winner(self, r, c):
        """After placing at (r,c), see if that creates a 5-in-a-row."""
        directions = [
            self._count_line(r, c, -1, 0),   # vertical
            self._count_line(r, c, 0, 1),    # horizontal
            self._count_line(r, c, 1, 1),    # diagonal \
            self._count_line(r, c, -1, 1)    # diagonal /
        ]

        longest = max(directions, key=lambda x: x[1])

        if longest[1] >= 5:
            self.winner = self.grid[r][c]
            self.game_over = True
            self.winning_pos = longest[0]

    def _count_line(self, r, c, dr, dc):
        """Count consecutive same-color stones through (r,c) in both directions."""
        start, fwd = self._count_direction(r, c, dr, dc)
        end, bwd = self._count_direction(r, c, -dr, -dc)
        return ((start, end), 1 + fwd + bwd)

    def _count_direction(self, r, c, dr, dc):
        """Count consecutive stones from (r,c) going in direction (dr,dc)."""
        endpoint = (r, c)
        color = self.grid[r][c]
        count = 0
        step = 1
        while True:
            nr = r + dr * step
            nc = c + dc * step
            if 0 <= nr < GRID_COUNT and 0 <= nc < GRID_COUNT:
                if self.grid[nr][nc] == color:
                    count += 1
                    endpoint = (nr, nc)
                else:
                    break
            else:
                break
            step += 1
        return endpoint, count

    def get_actions(self):
        """Return list of legal moves (empty cells in the active area)."""
        return self.actions

    def rand_move(self):
        """Pick a pseudo-random move using a simple cycling index."""
        self.rollout_rng = (self.rollout_rng + 1) % ROLLOUT_RNG_MAX
        return self.get_actions()[(self.rollout_rng) % len(self.actions)]

    def save_state(self, filename="savedata"):
        """Dump current board to a text file."""
        f = open(filename, "w")
        line = " ".join([str(self.grid[int(x / GRID_COUNT)][x % GRID_COUNT]) for x in range(0, GRID_COUNT ** 2)])
        f.write(self.player + " " + line)
        f.close()

    def load_state_text(self, text):
        """Restore a board from a single-line text representation."""
        split = text.split(' ')
        who = str(split[0])
        new_grid = self._make_empty_grid(GRID_COUNT)
        for i in range(0, GRID_COUNT ** 2):
            new_grid[int(i / GRID_COUNT)][i % GRID_COUNT] = str(split[1 + i])
        self.reset(who, new_grid)

    def load_state(self, filename="savedata"):
        """Read a board state from file."""
        f = open(filename, "r")
        line = f.readline()
        self.load_state_text(line)
        f.close()
