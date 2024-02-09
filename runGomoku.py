import tkinter as tk
import gamestate
import minimax
import board
import sys

#improvement: transpositions
#improvement: having more stones on the board gives a score advantage
#not fair if you sometimes play deeper (or if the depth differs in parity)

args = sys.argv
#size, depth, player
size = int(args[1])
depth = int(args[2])
if(int(args[3]) == 1): aiNum = -1
if(int(args[3]) == 2): aiNum = 1


top = tk.Tk()
gamestate = gamestate.GameState(size, size,5)
#AI = montecarlo.MCGameTree(gamestate, 100)

AI = minimax.Minimax(gamestate,aiNum, depth)
if aiNum == -1:
    gameboard = board.Board(top,gamestate,"human", AI)
if aiNum == 1:
    gameboard = board.Board(top,gamestate,AI,"human")
    
top.mainloop()
