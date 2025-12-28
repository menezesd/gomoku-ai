from __future__ import annotations
import copy
import time
import bisect
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gamestate import GameState

# Constants
INFINITY = float("inf")
SCORE_VECTOR = [0, 1, 4, 16, 64, 100000]  # Scores for 0-5 stones in a row
DEPTH_FALLOFF = 0.1  # How much heuristic value decreases with depth
TOP_MOVES_LIMIT = 20  # Max number of moves to consider at each depth
ADJACENT_MOVES_LIMIT = 10  # Max moves to keep after adding adjacent positions


class Minimax:
    """
    Minimax AI player with alpha-beta pruning for Gomoku.

    Uses heuristic evaluation based on line patterns and forced move detection
    to optimize search.
    """

    def __init__(self, gamestate: GameState, player: int, depth: int) -> None:
        """
        Initialize the Minimax AI.

        Args:
            gamestate: The current game state
            player: Which player this AI is (1 or -1)
            depth: Maximum search depth
        """
        self.gamestate = gamestate.copy()
        self.player = player
        self.depth = depth
        self.multi = self.gamestate.multigraph()
        self.firstTurn = True

    def heuristic(self, player: int, cur_depth: int) -> float:
        """
        Evaluate the current board position.

        A positive score means the position is good for the given player.
        Score is based on counting stones in potential winning lines.

        Args:
            player: The player to evaluate for (1 or -1)
            cur_depth: Current search depth (used for falloff)

        Returns:
            Heuristic score for the position
        """
        stones = self.gamestate.stones
        score = 0

        for edge in self.multi:
            player_count = 0
            opponent_count = 0

            for square in edge:
                if stones[square] == player:
                    player_count += 1
                elif stones[square] == -player:
                    opponent_count += 1

            # Only count lines that could still be completed
            if player_count > 0 and opponent_count == 0:
                score += SCORE_VECTOR[player_count]
            elif opponent_count > 0 and player_count == 0:
                score -= SCORE_VECTOR[opponent_count]

        return score - cur_depth * DEPTH_FALLOFF

    def orderedMoveList(self) -> list[tuple[float, tuple[int, int]]]:
        """
        Get moves ordered by heuristic value (best first).

        Returns:
            List of (negative_heuristic, move) tuples, sorted best-first
        """
        gamestate = self.gamestate
        move_list: list[tuple[float, tuple[int, int]]] = []

        for move in list(gamestate.empty):
            gamestate.makeMove(move)
            heur = self.heuristic(self.player, 0)
            bisect.insort(move_list, (-heur, move))
            gamestate.undo(move)

        return move_list[:TOP_MOVES_LIMIT]

    def minimaxAlphaBeta(self, depth: int) -> tuple[float, Optional[tuple[int, int]]]:
        """
        Entry point for minimax search with alpha-beta pruning.

        Args:
            depth: Maximum search depth

        Returns:
            Tuple of (score, best_move)
        """
        movelist = self.orderedMoveList()
        return self._minimaxAlphaBetaHelper(depth, True, INFINITY, 0, movelist)

    def _minimaxAlphaBetaHelper(
        self,
        depth: int,
        is_ai_turn: bool,
        sib_extreme: float,
        cur_depth: int,
        movelist: list[tuple[float, tuple[int, int]]]
    ) -> tuple[float, Optional[tuple[int, int]]]:
        """
        Recursive minimax helper with alpha-beta pruning.

        Args:
            depth: Remaining search depth
            is_ai_turn: True if it's the maximizing player's turn
            sib_extreme: Best value found among siblings (for pruning)
            cur_depth: Current depth from root
            movelist: Ordered list of moves to consider

        Returns:
            Tuple of (score, best_move)
        """
        gamestate = self.gamestate

        # Check for terminal state
        if gamestate.winner != 0:
            return (self.heuristic(self.player, cur_depth), None)

        opt_score = -INFINITY if is_ai_turn else INFINITY
        opt_move: Optional[tuple[int, int]] = None

        # Optimization: play forced moves immediately
        forced = gamestate.findForced()
        if forced is not None:
            gamestate.makeMove(forced)
            new_moves = copy.copy(movelist)
            val = self._minimaxAlphaBetaHelper(
                depth, not is_ai_turn, opt_score, cur_depth + 1, new_moves
            )[0]
            gamestate.undo(forced)
            return (val, forced)

        # Base case: reached max depth
        if depth == 0:
            return (self.heuristic(self.player, cur_depth), None)

        for m in movelist:
            move = m[1]
            # BUG FIX: was checking "move in gamestate.empty" but should check if move exists
            if move not in gamestate.empty:
                continue

            gamestate.makeMove(move)
            new_depth = depth - 1

            # Expand move list with adjacent positions
            new_moves = copy.copy(movelist)
            for x in gamestate.adjacent(move):
                # BUG FIX: was checking "move" instead of "x"
                if x not in gamestate.empty:
                    continue
                gamestate.makeMove(x)
                heur = self.heuristic(self.player, 0)
                bisect.insort(new_moves, (-heur, x))
                gamestate.undo(x)
            new_moves = new_moves[:ADJACENT_MOVES_LIMIT]

            val = self._minimaxAlphaBetaHelper(
                new_depth, not is_ai_turn, opt_score, cur_depth + 1, new_moves
            )[0]

            if is_ai_turn:
                if val > sib_extreme:
                    gamestate.undo(move)
                    return (INFINITY, None)  # Pruning
                if val >= opt_score:
                    opt_score = val
                    opt_move = move
            else:
                if val < sib_extreme:
                    gamestate.undo(move)
                    return (-INFINITY, None)  # Pruning
                if val <= opt_score:
                    opt_score = val
                    opt_move = move

            gamestate.undo(move)

        return (opt_score, opt_move)

    def getAIMove(self) -> Optional[tuple[int, int]]:
        """
        Get the best move for the AI.

        Returns:
            The best move as (row, col), or None if no moves available
        """
        # Minor optimization: play center on first move
        if self.firstTurn:
            return (self.gamestate.rows // 2, self.gamestate.cols // 2)

        start = time.time()
        result = self.minimaxAlphaBeta(self.depth)
        end = time.time()
        print(f"AI time: {end - start:.3f}s")

        return result[1]

    def makeMove(self, move: tuple[int, int]) -> None:
        """
        Update the AI's internal game state with a move.

        Args:
            move: The move that was played
        """
        self.firstTurn = False
        self.gamestate.makeMove(move)
