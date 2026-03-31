from __future__ import absolute_import, division, print_function
from math import sqrt, log
from game import Game, WHITE, BLACK, EMPTY
import copy
import time
import random

# how many iterations of the MCTS loop we run per move
BUDGET = 1000


class Node:
    """
    Single node in the search tree. Tracks visit/win stats
    and which moves haven't been explored yet.
    """
    def __init__(self, state, actions, parent=None):
        self.state = (state[0], copy.deepcopy(state[1]))
        self.num_wins = 0
        self.num_visits = 0
        self.parent = parent
        self.children = []  # list of (action, child_node) pairs
        self.untried_actions = copy.deepcopy(actions)
        sim = Game(*state)
        self.is_terminal = sim.game_over


class AI:
    """
    Monte Carlo Tree Search agent for Gomoku.
    Builds a search tree from the current board position,
    runs BUDGET simulations, then picks the best move.
    """

    def __init__(self, state):
        self.sim = Game()
        self.sim.reset(*state)
        self.root = Node(state, self.sim.get_actions())

    # --- core MCTS loop ---

    def mcts_search(self):
        """Run the full MCTS pipeline and return (best_action, win_rate_table)."""
        win_rates = {}

        for i in range(BUDGET):
            if (i + 1) % 100 == 0:
                print("\riters/budget: {}/{}".format(i + 1, BUDGET), end="")

            # tree policy: walk down to a promising leaf
            leaf = self._select(self.root)

            # grow the tree by one node if we can
            if not leaf.is_terminal:
                leaf = self._expand(leaf)

            # simulate a random game from that node
            outcome = self._simulate(leaf)

            # propagate the result back up the tree
            self._backprop(leaf, outcome)

        print()

        # pick the move with the highest win rate (c=0 means no exploration bonus)
        _, best_action, win_rates = self._pick_best(self.root, explore_weight=0)
        return best_action, win_rates

    # --- tree traversal ---

    def _select(self, node):
        """Walk down the tree, always picking the best child via UCB,
        until we hit a node that still has untried moves or is terminal."""
        while not node.is_terminal and not node.untried_actions:
            node, _, _ = self._pick_best(node, explore_weight=1)
        return node

    def _expand(self, node):
        """Take the first untried action, simulate it, and add the
        resulting board state as a new child node."""
        action = node.untried_actions.pop(0)

        self.sim.reset(*node.state)
        self.sim.place(*action)

        child_state = self.sim.state()
        child_actions = self.sim.get_actions()

        new_child = Node(child_state, child_actions, parent=node)
        node.children.append((action, new_child))
        return new_child

    # --- simulation & backprop ---

    def _simulate(self, node):
        """Play out the game randomly from this node's state
        and return who won as a dict {color: 0 or 1}."""
        self.sim.reset(*node.state)

        while not self.sim.game_over:
            mv = self.sim.rand_move()
            self.sim.place(*mv)

        result = {BLACK: 0, WHITE: 0}
        if self.sim.winner in result:
            result[self.sim.winner] = 1
        return result

    def _backprop(self, node, result):
        """Walk back up to the root, updating visit counts and
        win tallies. Each node stores wins from its *parent's* perspective."""
        while node is not None:
            node.num_visits += 1
            if node.parent is not None:
                parent_color = node.parent.state[0]
                node.num_wins += result.get(parent_color, 0)
            node = node.parent

    # --- child selection ---

    def _pick_best(self, node, explore_weight=1):
        """Apply the UCB1 formula to every child and return
        (best_child_node, best_action, {action: ucb_value})."""
        top_node = None
        top_action = None
        top_score = float("-inf")
        ucb_table = {}

        for action, child in node.children:
            if child.num_visits > 0:
                exploitation = child.num_wins / child.num_visits
                exploration = explore_weight * sqrt(2 * log(node.num_visits) / child.num_visits)
                score = exploitation + exploration
            else:
                score = float("inf")

            ucb_table[action] = score

            # on ties, keep the first one we found
            if score > top_score:
                top_score = score
                top_node = child
                top_action = action

        return top_node, top_action, ucb_table
