from __future__ import annotations
import math
import time
import copy
import secrets
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gamestate import GameState

# Constants
EXPLORATION_CONSTANT = 1.5  # UCB1 exploration parameter
INFINITY = float("inf")


class MCGameTreeNode:
    """
    A node in the Monte Carlo game tree.

    Tracks win statistics and child nodes for MCTS.
    """

    def __init__(
        self,
        parent: Optional[MCGameTreeNode],
        move: Optional[tuple[int, int]]
    ) -> None:
        self.parent = parent
        self.childMoves: dict[tuple[int, int], MCGameTreeNode] = {}
        self.player: int = 1  # Will be set properly

        if self.parent is not None:
            self.player = -1 * self.parent.player

        self.move = move
        self.p1Wins: float = 0
        self.p2Wins: float = 0
        self.lastScore: Optional[float] = None

    def winUpdate(self, winner: int) -> None:
        """Update win counts based on game outcome."""
        if winner == 1:
            self.p1Wins += 1
        elif winner == -1:
            self.p2Wins += 1
        else:  # Draw
            self.p1Wins += 0.5
            self.p2Wins += 0.5

    def totalVisits(self) -> float:
        """Return total number of visits to this node."""
        return self.p1Wins + self.p2Wins

    def score(self, parent_visits: float) -> float:
        """
        Calculate UCB1 score for this node.

        Args:
            parent_visits: Total visits to parent node

        Returns:
            UCB1 score balancing exploitation and exploration
        """
        last_player = -1 * self.player
        wins = self.p1Wins if last_player == 1 else self.p2Wins
        n = self.totalVisits()

        if n == 0:
            return INFINITY

        exploitation = wins / n
        exploration = EXPLORATION_CONSTANT * math.sqrt(math.log(parent_visits) / n)
        s = exploitation + exploration

        self.lastScore = s
        return s


class MCGameTree:
    """
    Monte Carlo Tree Search implementation for Gomoku.

    Uses UCB1 for node selection and random playouts for evaluation.
    """

    def __init__(self, gamestate: GameState, iterations: int = 1000) -> None:
        """
        Initialize the MCTS tree.

        Args:
            gamestate: The current game state (reference, not copied)
            iterations: Number of MCTS iterations per move
        """
        self.gamestate = gamestate
        self.root = MCGameTreeNode(None, None)
        self.root.player = -gamestate.curPlayer()  # Root's player is who just moved
        self.curNode = self.root
        self.iterations = iterations
        self._rng = secrets.SystemRandom()

    def _up(self) -> None:
        """Move up the tree (undo the move)."""
        if self.curNode.move is not None:
            self.gamestate.undo(self.curNode.move)
        if self.curNode.parent is not None:
            self.curNode = self.curNode.parent

    def _down(self, move: tuple[int, int]) -> None:
        """Move down the tree (make a move)."""
        if move in self.curNode.childMoves:
            self.curNode = self.curNode.childMoves[move]
        else:
            new_node = MCGameTreeNode(self.curNode, move)
            self.curNode.childMoves[move] = new_node
            self.curNode = new_node
        self.gamestate.makeMove(move)

    def _selectNode(self) -> None:
        """
        Selection phase: traverse tree using UCB1 until finding
        a node with unexplored children.
        """
        while True:
            children = self.curNode.childMoves

            # If there are unexplored children, stop here
            if len(children) != len(self.gamestate.empty):
                return

            # Select best child using UCB1
            best_score = -INFINITY
            best_move: Optional[tuple[int, int]] = None
            parent_visits = self.curNode.totalVisits()

            for move, child_node in children.items():
                child_score = child_node.score(parent_visits)
                if child_score > best_score:
                    best_score = child_score
                    best_move = move

            if best_move is not None:
                self._down(best_move)
            else:
                return

    def _getUnexploredMoves(self) -> list[tuple[int, int]]:
        """Get list of moves not yet explored from current node."""
        if self.gamestate.winner != 0:
            return []
        return [m for m in self.gamestate.empty if m not in self.curNode.childMoves]

    def _updateWinCount(self, p1_wins: float, p2_wins: float) -> None:
        """Update win counts for current node."""
        self.curNode.p1Wins += p1_wins
        self.curNode.p2Wins += p2_wins

    def _backPropagate(self, p1_wins: float, p2_wins: float) -> None:
        """Backpropagate win statistics up to root."""
        while True:
            self._updateWinCount(p1_wins, p2_wins)
            if self.curNode.parent is not None:
                self._up()
            else:
                return

    def _mcIteration(self) -> None:
        """Perform one MCTS iteration: select, expand, simulate, backpropagate."""
        self._selectNode()

        # Get unexplored moves
        unexplored = self._getUnexploredMoves()
        p1_wins = 0.0
        p2_wins = 0.0

        # Handle terminal states
        if self.gamestate.winner == 1:
            p1_wins = 1
        elif self.gamestate.winner == -1:
            p2_wins = 1

        # Expand and simulate for each unexplored move
        for move in unexplored:
            self._down(move)

            winner = self.gamestate.playout()

            p1_inc = 0.0
            p2_inc = 0.0
            if winner == 1:
                p1_inc = 1
            elif winner == -1:
                p2_inc = 1
            else:
                p1_inc = 0.5
                p2_inc = 0.5

            p1_wins += p1_inc
            p2_wins += p2_inc
            self._updateWinCount(p1_inc, p2_inc)
            self._up()

        self._backPropagate(p1_wins, p2_wins)

    def getAIMove(self) -> Optional[tuple[int, int]]:
        """
        Run MCTS and return the best move.

        Returns:
            Best move as (row, col), or None if no moves available
        """
        start = time.time()

        for i in range(self.iterations):
            if i % 100 == 0:
                print(f"MCTS iteration {i}/{self.iterations}")
            self._mcIteration()

        # Select most visited child
        best_move: Optional[tuple[int, int]] = None
        max_visits = 0.0

        for move, node in self.root.childMoves.items():
            visits = node.totalVisits()
            if visits > max_visits:
                max_visits = visits
                best_move = move

        end = time.time()
        print(f"AI time: {end - start:.3f}s")

        return best_move

    def makeMove(self, move: tuple[int, int]) -> None:
        """
        Update tree after a move is made.

        Reuses the subtree if the move was explored, otherwise creates fresh tree.
        This preserves learned information from previous searches.

        Args:
            move: The move that was played
        """
        if move in self.root.childMoves:
            # Reuse the subtree - this preserves learned information
            self.root = self.root.childMoves[move]
            self.root.parent = None
            self.root.move = None
        else:
            # Create fresh tree if move wasn't explored
            self.root = MCGameTreeNode(None, None)
            self.root.player = self.gamestate.curPlayer()

        self.curNode = self.root
