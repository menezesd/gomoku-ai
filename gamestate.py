from __future__ import annotations
import copy
import secrets
from typing import Optional

# Constants
POSITIVE_DIRECTIONS = [(0, 1), (1, 1), (1, 0), (1, -1)]
DEFAULT_WIN_LENGTH = 5


def sign(x: int) -> int:
    """Return the sign of x: -1, 0, or 1."""
    if x == 0:
        return 0
    return 1 if x > 0 else -1


class GameState:
    """
    Represents the state of a Gomoku game.

    Attributes:
        N: Number of stones in a row needed to win
        stones: Dictionary mapping (row, col) to piece values (1, -1, or 0)
        empty: Set of unoccupied positions (O(1) add/remove)
        rows: Number of rows on the board
        cols: Number of columns on the board
        p1Turn: True if it's player 1's turn
        winner: 0 if no winner, 1 or -1 for the winning player
    """

    def __init__(self, rows: int, cols: int, N: int = DEFAULT_WIN_LENGTH) -> None:
        self.N = N
        self.stones: dict[tuple[int, int], int] = {}
        self.empty: set[tuple[int, int]] = set()
        self.rows = rows
        self.cols = cols
        self.p1Turn = True
        self.winner = 0
        self._rng = secrets.SystemRandom()

        for i in range(rows):
            for j in range(cols):
                self.stones[(i, j)] = 0
                self.empty.add((i, j))

        self.multi = self._compute_multigraph()

    def copy(self) -> GameState:
        """Create a shallow copy of this game state."""
        new_copy = GameState(self.rows, self.cols, self.N)
        new_copy.stones = copy.copy(self.stones)
        new_copy.empty = copy.copy(self.empty)
        new_copy.p1Turn = self.p1Turn
        new_copy.winner = self.winner
        return new_copy

    def makeMove(self, move: tuple[int, int]) -> None:
        """Make a move at the given position."""
        self.setStone(move[0], move[1])

    def curPlayer(self) -> int:
        """Return the current player: 1 or -1."""
        return 1 if self.p1Turn else -1

    def setStone(self, r: int, c: int) -> None:
        """Place a stone at position (r, c) for the current player."""
        if self.winner != 0:
            raise ValueError("Cannot place stone: game already has a winner")

        color = 1 if self.p1Turn else -1
        self.stones[(r, c)] = color
        self._updateWinner(r, c, color)
        self.empty.discard((r, c))
        self.p1Turn = not self.p1Turn

    def inBounds(self, coords: tuple[int, int]) -> bool:
        """Check if coordinates are within the board boundaries."""
        r, c = coords
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _updateWinner(self, r: int, c: int, color: int) -> None:
        """Check if the move at (r, c) creates a winning line."""
        for pdir in POSITIVE_DIRECTIONS:
            pcount = 0
            ncount = 0

            # Count stones in positive direction
            for i in range(1, self.N):
                next_spot = (r + i * pdir[0], c + i * pdir[1])
                if self.inBounds(next_spot) and self.stones[next_spot] == color:
                    pcount += 1
                else:
                    break

            # Count stones in negative direction
            for i in range(1, self.N):
                next_spot = (r - i * pdir[0], c - i * pdir[1])
                if self.inBounds(next_spot) and self.stones[next_spot] == color:
                    ncount += 1
                else:
                    break

            line_len = ncount + pcount + 1
            if line_len >= self.N:
                self.winner = color
                return

    def playout(self) -> int:
        """
        Simulate a random game to completion from the current state.
        Returns the winner (1, -1, or 0 for draw).
        """
        game_copy = self.copy()
        empty_list = list(game_copy.empty)

        while empty_list and game_copy.winner == 0:
            idx = self._rng.randint(0, len(empty_list) - 1)
            next_stone = empty_list[idx]
            # Swap and pop for O(1) removal
            empty_list[idx] = empty_list[-1]
            empty_list.pop()
            game_copy.makeMove(next_stone)

        return game_copy.winner

    def hardPlayout(self) -> int:
        """
        Simulate a game with forced move detection.
        Returns the winner (1, -1, or 0 for draw).
        """
        game_copy = self.copy()
        empty_list = list(game_copy.empty)

        while empty_list and game_copy.winner == 0:
            forced = game_copy.findForced()
            if forced is not None:
                next_stone = forced
                # Remove from list
                if next_stone in empty_list:
                    empty_list.remove(next_stone)
            else:
                idx = self._rng.randint(0, len(empty_list) - 1)
                next_stone = empty_list[idx]
                empty_list[idx] = empty_list[-1]
                empty_list.pop()

            game_copy.makeMove(next_stone)

        return game_copy.winner

    def adjacent(self, x: tuple[int, int]) -> list[tuple[int, int]]:
        """Return a list of positions that are in line with x."""
        result = []
        for d in POSITIVE_DIRECTIONS:
            for i in range(1, self.N):
                result.append((x[0] + i * d[0], x[1] + i * d[1]))
        return result

    def _compute_multigraph(self) -> list[list[tuple[int, int]]]:
        """Pre-compute all possible N-in-a-row lines on the board."""
        multi = []
        for r in range(self.rows):
            for c in range(self.cols):
                for d in POSITIVE_DIRECTIONS:
                    new_edge = []
                    for i in range(self.N):
                        square = (r + i * d[0], c + i * d[1])
                        if self.inBounds(square):
                            new_edge.append(square)
                        else:
                            new_edge = []
                            break
                    if new_edge:
                        multi.append(new_edge)
        return multi

    # Keep old name for compatibility
    def multigraph(self) -> list[list[tuple[int, int]]]:
        """Return pre-computed multigraph (alias for compatibility)."""
        return self.multi

    def findForced(self) -> Optional[tuple[int, int]]:
        """
        Find a forced move (one stone away from winning).
        Prioritizes winning moves over blocking moves.
        """
        hold = None
        for edge in self.multi:
            color = None
            empty_pos = None

            for s in edge:
                if self.stones[s] == 0:
                    if empty_pos is not None:
                        empty_pos = None
                        break
                    else:
                        empty_pos = s
                else:
                    if color is None:
                        color = self.stones[s]
                    elif color != self.stones[s]:
                        empty_pos = None
                        break

            if empty_pos is not None:
                if color == self.curPlayer():
                    return empty_pos
                else:
                    hold = empty_pos

        return hold

    def findOpenThrees(self) -> list[tuple[int, int]]:
        """Find positions that would complete an open three-in-a-row."""
        opens = []
        for edge in self.multi:
            if self.stones[edge[0]] == 0 or self.stones[edge[4]] == 0:
                color = self.stones[edge[1]]
                if color != 0:
                    if (self.stones[edge[2]] == color and
                        self.stones[edge[3]] == color):
                        if self.stones[edge[0]] == 0:
                            opens.append(edge[0])
                        if self.stones[edge[4]] == 0:
                            opens.append(edge[4])
        return opens

    def undo(self, move: tuple[int, int]) -> None:
        """Undo a move (for search algorithms)."""
        self.stones[move] = 0
        self.empty.add(move)
        self.winner = 0
        self.p1Turn = not self.p1Turn
