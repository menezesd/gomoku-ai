from __future__ import annotations
import tkinter as tk
import threading
from typing import TYPE_CHECKING, Optional, Union
from enum import Enum, auto

if TYPE_CHECKING:
    from gamestate import GameState
    from minimax import Minimax
    from montecarlo import MCGameTree

# Constants
SQUARE_SIZE = 40
BORDER = 50
STONE_RADIUS_RATIO = 0.3
PLAYER_1_COLOR = "red"
PLAYER_2_COLOR = "blue"
PLAYER_1_PREVIEW_COLOR = "#FFCCCC"
PLAYER_2_PREVIEW_COLOR = "#CCFFFF"


class PlayerType(Enum):
    """Enum representing the type of player."""
    HUMAN = auto()
    MINIMAX = auto()
    MCTS = auto()


# Type alias for player - either human or an AI
Player = Union[PlayerType, "Minimax", "MCGameTree"]


class Board(tk.Frame):
    """Tkinter-based game board for Gomoku."""

    def __init__(
        self,
        parent: tk.Tk,
        gamestate: GameState,
        player1: Player,
        player2: Player
    ) -> None:
        tk.Frame.__init__(self, parent)
        self.gamestate = gamestate
        self.rows: int = self.gamestate.rows
        self.cols: int = self.gamestate.cols
        self.hborder: int = BORDER
        self.vborder: int = BORDER
        self.squaresize: int = SQUARE_SIZE
        self.stonerad: float = STONE_RADIUS_RATIO * self.squaresize
        self.stoneIDs: dict[tuple[int, int], int] = {}

        # Cursor tracking
        self.cursorRow: int = -1
        self.cursorCol: int = -1
        self.cursorStoneId: int = -1
        self.last: Optional[tuple[int, int]] = None

        w = (self.cols - 1) * self.squaresize + 2 * self.hborder
        h = (self.rows - 1) * self.squaresize + 2 * self.vborder
        self.board = tk.Canvas(parent, width=w, height=h)
        self.board.pack()

        # Players
        self.player1 = player1
        self.player2 = player2
        self.clickable: bool = False
        self.ai_thinking: bool = False

        # Draw grid
        for i in range(self.cols):
            x = self.hborder + i * self.squaresize
            self.board.create_line(
                x, self.vborder,
                x, self.vborder + self.squaresize * (self.rows - 1)
            )

        for i in range(self.rows):
            y = self.vborder + i * self.squaresize
            self.board.create_line(
                self.hborder, y,
                self.hborder + self.squaresize * (self.cols - 1), y
            )

        self.board.bind("<Button-1>", self.onClick)
        self.board.bind("<Motion>", self.onMove)

        # Start the game
        self.after(100, self.nextTurn)

    def row_col(self, x: int, y: int) -> tuple[int, int]:
        """Get nearest grid point (in L_1 norm) to given coordinates."""
        r = int((y - self.vborder + 0.5 * self.squaresize) // self.squaresize)
        c = int((x - self.hborder + 0.5 * self.squaresize) // self.squaresize)
        return (r, c)

    def updateStones(self) -> None:
        """Use the game state to update the board GUI."""
        for point in self.gamestate.stones:
            r, c = point[0], point[1]
            last = (point == self.last)

            if (r, c) in self.stoneIDs:
                self.board.delete(self.stoneIDs[(r, c)])

            stone_value = self.gamestate.stones[point]
            if stone_value == 1:
                self.stoneIDs[(r, c)] = self.drawStone(r, c, PLAYER_1_COLOR, last)
            elif stone_value == -1:
                self.stoneIDs[(r, c)] = self.drawStone(r, c, PLAYER_2_COLOR, last)

    def onClick(self, event: tk.Event) -> None:
        """Handle click events on the board."""
        if not self.clickable or self.ai_thinking:
            return

        r, c = self.row_col(event.x, event.y)
        if self.tryPlace(r, c):
            current_ai = self._get_opponent_ai()
            if current_ai is not None:
                current_ai.makeMove((r, c))
            self.after(10, self.nextTurn)

    def tryPlace(self, r: int, c: int) -> bool:
        """
        Try to place a stone at the given position.
        Returns False if spot is taken or out of bounds.
        """
        if r < 0 or r > self.rows - 1 or c < 0 or c > self.cols - 1:
            return False
        if self.gamestate.stones[(r, c)] != 0:
            return False

        self.gamestate.setStone(r, c)
        self.last = (r, c)
        self.updateStones()
        return True

    def onMove(self, event: tk.Event) -> None:
        """Handle mouse movement for stone preview."""
        if not self.clickable or self.ai_thinking:
            return

        r, c = self.row_col(event.x, event.y)
        if r < 0 or r > self.rows - 1 or c < 0 or c > self.cols - 1:
            if self.cursorStoneId != -1:
                self.board.delete(self.cursorStoneId)
                self.cursorStoneId = -1
            return

        if r != self.cursorRow or c != self.cursorCol:
            if self.cursorStoneId != -1:
                self.board.delete(self.cursorStoneId)

            if self.gamestate.stones[(r, c)] == 0:
                color = PLAYER_1_PREVIEW_COLOR if self.gamestate.p1Turn else PLAYER_2_PREVIEW_COLOR
                self.cursorStoneId = self.drawStone(r, c, color, False)
                self.cursorRow, self.cursorCol = r, c
            else:
                self.cursorRow, self.cursorCol = -1, -1

    def drawStone(self, r: int, c: int, color: str, last: bool) -> int:
        """Create stone on canvas and return its ID."""
        center = (
            self.hborder + c * self.squaresize,
            self.vborder + r * self.squaresize
        )
        rad = self.stonerad
        w = 2 if last else 1

        return self.board.create_oval(
            center[0] - rad, center[1] - rad,
            center[0] + rad, center[1] + rad,
            fill=color, width=w, outline="black"
        )

    def _is_human_player(self, player: Player) -> bool:
        """Check if the given player is human."""
        return player == PlayerType.HUMAN or player == "human"

    def _get_current_player(self) -> Player:
        """Get the player whose turn it is."""
        return self.player1 if self.gamestate.p1Turn else self.player2

    def _get_opponent_ai(self) -> Optional[Union[Minimax, MCGameTree]]:
        """Get the opponent AI (if any) to notify of moves."""
        opponent = self.player2 if self.gamestate.p1Turn else self.player1
        if not self._is_human_player(opponent):
            return opponent
        return None

    def _process_ai_move(self, move: Optional[tuple[int, int]]) -> None:
        """Process an AI move on the main thread."""
        self.ai_thinking = False

        if move is None:
            return  # Game over

        self.gamestate.makeMove(move)
        current_player = self._get_current_player()
        if not self._is_human_player(current_player):
            current_player.makeMove(move)

        self.last = move
        self.updateStones()

        # Notify the other player's AI if it exists
        opponent_ai = self._get_opponent_ai()
        if opponent_ai is not None:
            opponent_ai.makeMove(move)

        # Continue to next turn
        self.after(10, self.nextTurn)

    def _run_ai_in_thread(self, ai_player: Union[Minimax, MCGameTree]) -> None:
        """Run AI computation in a background thread."""
        def compute_and_callback():
            move = ai_player.getAIMove()
            # Schedule the result processing on the main thread
            self.after(0, lambda: self._process_ai_move(move))

        thread = threading.Thread(target=compute_and_callback, daemon=True)
        thread.start()

    def nextTurn(self) -> None:
        """
        Handle turn progression. Uses iteration instead of recursion
        to prevent stack overflow in AI vs AI games.
        """
        # Check for game over
        if self.gamestate.winner != 0:
            self.clickable = False
            winner_name = "Player 1" if self.gamestate.winner == 1 else "Player 2"
            print(f"Game over! {winner_name} wins!")
            return

        if len(self.gamestate.empty) == 0:
            self.clickable = False
            print("Game over! It's a draw!")
            return

        current_player = self._get_current_player()

        if self._is_human_player(current_player):
            # Human's turn - enable clicking and wait
            self.clickable = True
            return

        # AI's turn - disable clicking and run AI in background thread
        self.clickable = False
        self.ai_thinking = True
        self._run_ai_in_thread(current_player)
