from __future__ import absolute_import, division, print_function
import argparse
from game import Game, WHITE, BLACK, EMPTY, GRID_COUNT
from test import deterministic_test, win_test
from ai import AI

gen_tests = False

# board drawing constants
CELL_SIZE = 46
RADIUS = CELL_SIZE // 2
BOARD_X = 38
BOARD_Y = 55
MARGIN = CELL_SIZE // 2
STATUS_POS = (10, 8)

PROMPT_TEXT = "{0} Click to place piece. Press Enter for rand/AI play and [m] for user/{1} play."

WHITE_RGB = [255] * 3
BLACK_RGB = [0] * 3
BORDER_RGB = [0] * 3
BOARD_RGB = [153, 118, 103]
TEXT_RGB = [0] * 3
FAINT_LINE = [70] * 3
BOLD_LINE = [0] * 3


class Gomoku():
    """Main game loop with pygame rendering and input handling."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((530, 550))
        pygame.display.set_caption("Gomoku")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("ariel", 18)

        self.running = True
        self.game = Game(BLACK)
        self.autoplay = False
        self.vs_ai = True
        self.ai_thinking = False

    def run(self):
        """Main event loop."""
        while self.running:
            self._handle_frame()
            self._draw()
            self.clock.tick(60)
        pygame.quit()

    def _save_action_table(self, table, path="savedata_actions"):
        """Write action->value pairs to disk (used for generating test data)."""
        with open(path, "w") as f:
            for key in table:
                f.write("{} {} {}\n".format(key[0], key[1], table[key]))

    def _handle_frame(self):
        """Process one frame of input and AI logic."""
        if self.ai_thinking:
            if not self.game.game_over:
                agent = AI(self.game.state())
                (r, c), rates = agent.mcts_search()
                if gen_tests:
                    self.game.save_state()
                    self._save_action_table(rates)
                self.game.place(r, c)
            self.ai_thinking = False
        else:
            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = False
                if ev.type == MOUSEBUTTONDOWN:
                    self.autoplay = False
                    if self.vs_ai:
                        if self._click(ev):
                            self.ai_thinking = True
                    else:
                        self._click(ev)
                if ev.type == KEYDOWN:
                    if ev.key == K_s:
                        self.game.save_state()
                    if ev.key == K_l:
                        self.game.load_state()
                    if ev.key == K_RETURN:
                        self.autoplay = not self.autoplay
                    if ev.key == K_SPACE:
                        self.autoplay = False
                        self.game.reset()
                    if ev.key == K_m:
                        self.vs_ai = not self.vs_ai
            if self.autoplay:
                if not self.game.game_over:
                    r, c = self.game.rand_move()
                    self.game.place(r, c)
                    self.ai_thinking = True

    def _draw(self):
        """Render the board, pieces, status text, and winning line."""
        self.screen.fill((255, 255, 255))

        # board background
        pygame.draw.rect(self.screen, BOARD_RGB,
                         [BOARD_X - MARGIN, BOARD_Y - MARGIN,
                          (GRID_COUNT - 1) * CELL_SIZE + MARGIN * 2,
                          (GRID_COUNT - 1) * CELL_SIZE + MARGIN * 2], 0)

        # horizontal grid lines
        for r in range(GRID_COUNT):
            y = BOARD_Y + r * CELL_SIZE
            pygame.draw.line(self.screen, FAINT_LINE,
                             [BOARD_X, y],
                             [BOARD_X + CELL_SIZE * (GRID_COUNT - 1), y], 2)
            if r in range(self.game.min_r, self.game.max_r + 1):
                x0 = BOARD_X + self.game.min_c * CELL_SIZE
                x1 = BOARD_X + self.game.max_c * CELL_SIZE
                pygame.draw.line(self.screen, BOLD_LINE, [x0, y], [x1, y], 2)

        # vertical grid lines
        for c in range(GRID_COUNT):
            x = BOARD_X + c * CELL_SIZE
            pygame.draw.line(self.screen, FAINT_LINE,
                             [x, BOARD_Y],
                             [x, BOARD_Y + CELL_SIZE * (GRID_COUNT - 1)], 2)
            if c in range(self.game.min_c, self.game.max_c + 1):
                y0 = BOARD_Y + self.game.min_r * CELL_SIZE
                y1 = BOARD_Y + self.game.max_r * CELL_SIZE
                pygame.draw.line(self.screen, BOLD_LINE, [x, y0], [x, y1], 2)

        # stones
        for r in range(GRID_COUNT):
            for c in range(GRID_COUNT):
                piece = self.game.grid[r][c]
                if piece != EMPTY:
                    color = BLACK_RGB if piece == BLACK else WHITE_RGB
                    px = BOARD_X + c * CELL_SIZE
                    py = BOARD_Y + r * CELL_SIZE
                    pygame.draw.circle(self.screen, color, [px, py], RADIUS, 0)

        # highlight winning line
        if self.game.game_over and self.game.winning_pos:
            s, e = self.game.winning_pos
            sp = [BOARD_X + s[1] * CELL_SIZE, BOARD_Y + s[0] * CELL_SIZE]
            ep = [BOARD_X + e[1] * CELL_SIZE, BOARD_Y + e[0] * CELL_SIZE]
            pygame.draw.line(self.screen, (0, 200, 0), sp, ep, 6)

        # status bar text
        if self.ai_thinking:
            msg = "AI Calculating..."
        elif self.game.game_over:
            who = "Black" if self.game.winner == 'b' else "White"
            msg = "{} has won. Press [space] to restart".format(who)
        elif self.autoplay:
            msg = "rand/AI play."
        elif self.vs_ai:
            msg = PROMPT_TEXT.format("User vs AI.", "user")
        else:
            turn = "Black" if self.game.player == BLACK else "White"
            msg = "Next to play: {}. Click to place piece. Press [m] to stop manual play.".format(turn)

        self.screen.blit(self.font.render(msg, True, (0, 0, 0)), STATUS_POS)
        pygame.display.update()

    def _click(self, event):
        """Translate a mouse click to board coordinates and try to place a stone."""
        ox = BOARD_X - MARGIN
        oy = BOARD_Y - MARGIN
        board_px = (GRID_COUNT - 1) * CELL_SIZE + MARGIN * 2
        mx, my = event.pos

        if ox <= mx <= ox + board_px and oy <= my <= oy + board_px:
            if not self.game.game_over:
                c = int((mx - ox) // CELL_SIZE)
                r = int((my - oy) // CELL_SIZE)
                return self.game.place(r, c)
        return False


# --- entry point ---

parser = argparse.ArgumentParser(description='Gomoku with MCTS AI')
parser.add_argument('--test', '-t', dest="test", type=int, default=0,
                    help='1: deterministic UCB test, 2: AI vs random play')
args = parser.parse_args()

if __name__ == '__main__':
    if args.test == 1:
        deterministic_test()
    elif args.test == 2:
        win_test()
    else:
        import pygame
        from pygame.locals import *
        app = Gomoku()
        app.run()
