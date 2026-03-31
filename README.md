# Gomoku AI — Monte Carlo Tree Search

A Python implementation of the classic board game **Gomoku** (five-in-a-row), featuring an AI opponent powered by **Monte Carlo Tree Search (MCTS)**.

## About the Game

Gomoku is played on an 11×11 grid. Two players take turns placing black and white stones on empty intersections. The first player to form an unbroken line of five stones — horizontally, vertically, or diagonally — wins. Simple rules, but surprisingly deep strategy.

## How the AI Works

The AI uses MCTS, a decision-time planning algorithm that builds a search tree through repeated random simulations:

1. **Selection** — Starting from the root, walk down the tree by picking the child with the highest Upper Confidence Bound (UCB1) score, balancing exploitation of strong moves against exploration of under-tested ones.  
2. **Expansion** — When a node with untried moves is reached, add one new child to the tree.  
3. **Simulation (Rollout)** — Play out the rest of the game randomly from the new node.  
4. **Backpropagation** — Update win/visit counts all the way back to the root.

After a configurable number of iterations (default: 1,000), the move with the highest empirical win rate is chosen. At 6,000+ iterations the AI plays competitively against casual human players.

To keep search tractable, the engine restricts legal moves to an "active zone" — cells within one step of any existing stone. This is shown on the board as the area drawn with dark grid lines.

## Project Structure

| File | Purpose |
|------|---------|
| `game.py` | Core game engine: board state, move legality, win detection |
| `ai.py` | MCTS implementation (Node class + AI search agent) |
| `main.py` | Entry point — pygame GUI and CLI test harness |
| `test.py` | Deterministic UCB regression tests and AI-vs-random matches |
| `test_states` / `test_sols` | Reference board states and expected UCB values for testing |

## Getting Started

**Dependencies:** Python 3, pygame (only needed for the GUI)

```bash
# play against the AI (requires pygame)
python main.py

# run deterministic UCB tests
python main.py -t 1

# watch AI vs random player (AI should win nearly every game)
python main.py -t 2
```

**In-game controls:**
- **Click** — place a stone  
- **Enter** — toggle autoplay (random vs AI)  
- **M** — toggle manual two-player mode  
- **Space** — reset the board  
- **S / L** — save / load board state  

## Key Implementation Details

- **UCB1 formula:** balances win rate against an exploration bonus scaled by √(2 · ln(parent visits) / child visits).  
- **Backpropagation convention:** each node stores wins from its *parent's* perspective, which keeps the selection step consistent when alternating players.  
- **Deterministic rollouts:** rollout moves use a cycling pseudo-random index rather than Python's `random` module, making test outputs reproducible.

## Technologies

Python · Pygame · Monte Carlo Tree Search · UCB1
