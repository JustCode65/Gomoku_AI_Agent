from game import Game, WHITE, BLACK
from ai import AI

# how close our UCB values need to be to the reference answers
TOL = 0.01


def _parse_solution(text):
    """Turn the text block of (row col value) lines into a dict."""
    table = {}
    for line in text.split("\n"):
        parts = line.strip().split(" ")
        table[(int(parts[0]), int(parts[1]))] = float(parts[2])
    return table


def deterministic_test():
    """Load saved board states and their known-correct UCB tables,
    then run MCTS and compare our values against the reference."""
    solutions = []
    boards = []

    with open("test_sols") as f:
        raw = f.read()
        chunks = raw.split("\n\n")[:-1]
        for chunk in chunks:
            solutions.append(_parse_solution(chunk))

    with open("test_states") as f:
        boards = f.readlines()

    # strip trailing newlines
    boards = [b.rstrip("\n") for b in boards]

    assert len(boards) == len(solutions)
    total = len(boards)

    for idx, (board_text, expected) in enumerate(zip(boards, solutions)):
        print("test {}/{}".format(idx + 1, total))

        game = Game()
        game.load_state_text(board_text)

        agent = AI(game.state())
        _, computed = agent.mcts_search()

        misses = 0
        for key in expected:
            diff = computed[key] - expected[key]
            if diff > TOL or diff < -TOL:
                print("  wrong UCB at {}: got {} expected {}".format(
                    key, computed[key], expected[key]))
                misses += 1

        print()
        print("PASSED" if misses == 0 else "FAILED")
        print()


# AI should beat random play almost every time
MIN_WINS = 9
NUM_GAMES = 10


def win_test():
    """Pit the MCTS agent against a random-move opponent.
    The AI plays white (second), random plays black (first)."""
    game = Game()
    victories = 0

    for g in range(NUM_GAMES):
        print("game {}/{}".format(g + 1, NUM_GAMES))
        game.reset(BLACK)
        ai_turn = False

        while not game.game_over:
            if ai_turn:
                agent = AI(game.state())
                (r, c), _ = agent.mcts_search()
            else:
                (r, c) = game.rand_move()

            game.place(r, c)
            ai_turn = not ai_turn

        if game.winner == WHITE:
            print("AI wins")
            victories += 1
        else:
            print("Random player wins")
        print()

    print("PASSED" if victories >= MIN_WINS else "FAILED")
