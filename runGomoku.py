#!/usr/bin/env python3
"""
Gomoku (Five in a Row) game launcher.

Usage:
    python runGomoku.py <board_size> <search_depth> <player_number>

Arguments:
    board_size: Size of the game board (e.g., 15 for a 15x15 board)
    search_depth: AI search depth for minimax algorithm
    player_number: Which player is human (1 or 2)

Example:
    python runGomoku.py 15 3 1  # 15x15 board, depth 3, human plays first
"""
from __future__ import annotations
import sys
import tkinter as tk

from gamestate import GameState
from minimax import Minimax
from board import Board, PlayerType

# Constants
DEFAULT_WIN_LENGTH = 5


def main() -> None:
    """Main entry point for the Gomoku game."""
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    size = int(sys.argv[1])
    depth = int(sys.argv[2])
    player_num = int(sys.argv[3])

    # Determine which player the AI controls
    # If human is player 1, AI is player 2 (-1)
    # If human is player 2, AI is player 1 (1)
    ai_player = -1 if player_num == 1 else 1

    top = tk.Tk()
    top.title("Gomoku")

    game_state = GameState(size, size, DEFAULT_WIN_LENGTH)
    ai = Minimax(game_state, ai_player, depth)

    if ai_player == -1:
        # Human is player 1, AI is player 2
        Board(top, game_state, PlayerType.HUMAN, ai)
    else:
        # AI is player 1, human is player 2
        Board(top, game_state, ai, PlayerType.HUMAN)

    top.mainloop()


if __name__ == "__main__":
    main()
