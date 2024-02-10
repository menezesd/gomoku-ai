import tkinter as tk
import gamestate
import montecarlo

class Board(tk.Frame):

    cursorRow=-1
    cursorCol=-1
    cursorStoneId = -1
    last = None #the last stone to be placed

    #get nearest grid point (in L_1 norm) to given coordinates
    def row_col(self,x,y):
        r = (y-self.vborder + 0.5*self.squaresize)//self.squaresize
        c = (x-self.hborder+ 0.5*self.squaresize)//self.squaresize
        return (r,c)

    #use the game state to update the baord GUI
    def updateStones(self):
        for point in self.gamestate.stones:
            
            r,c = point[0],point[1]

            last = (point == self.last)
            
            if((r,c) in self.stoneIDs):
                self.board.delete(self.stoneIDs[(r,c)])
            if (self.gamestate.stones[point] == 1):
                self.stoneIDs[(r,c)] = self.drawStone(r,c,"red",last)
            elif (self.gamestate.stones[point] == -1):
                self.stoneIDs[(r,c)] = self.drawStone(r,c,"blue", last)

        

    #called on a click
    def onClick(self,event):

        if not self.clickable: return
        
        r,c = self.row_col(event.x,event.y)
        ifsuccess := self.tryPlace(r,c):
            if self.gamestate.p1Turn:
                self.player1.makeMove((r,c))
            else:
                self.player2.makeMove((r,c))

            #########
            #print(self.gamestate.findForced())
            ##########
            
            self.nextTurn()



    #try to place a stone
    #fails if spot is taken or if it's out of bounds
    def tryPlace(self,r,c):
        if r<0 or r>self.rows-1 or c<0 or c>self.cols-1:
            return False
        if self.gamestate.stones[(r,c)] != 0:
            return False
        self.gamestate.setStone(r,c)

        self.last = (r,c) #new
                   
        self.updateStones()
        return True
        
    #called when the cursor moves
    def onMove(self,event):

        if not self.clickable: return
        
        r,c = self.row_col(event.x,event.y)
        if r<0 or r>self.rows-1 or c<0 or c>self.cols-1:
            if(self.cursorStoneId != -1): #copy pasta
                self.board.delete(self.cursorStoneId)
                self.cursorStoneId = -1
            return
        if(r != self.cursorRow or c != self.cursorCol):
            if(self.cursorStoneId != -1):
                self.board.delete(self.cursorStoneId)
            if(self.gamestate.stones[(r,c)] == 0): #empty square
                if(self.gamestate.p1Turn):
                    color = "#FFCCCC"
                else:
                    color = "#CCFFFF"
                self.cursorStoneId = self.drawStone(r,c,color,False)
                self.cursorRow, self.cursorCol = r,c
            else:
                self.cursorRow, self.cursorCol = -1,-1
        
    #create stone, return ID
    def drawStone(self,r,c,color,last):
        center = (self.hborder + c*self.squaresize, self.vborder + r*self.squaresize)
        rad = self.stonerad

        if last:
            w = 2
            out = "black"
        else:
            w = 1
            out = "black"
        
        return self.board.create_oval(center[0]-rad, center[1]-rad,center[0]+rad,center[1]+rad, fill=color, width = w, outline = out)

    #set the current player to the player specified in gamestate
    #SUPER UGLY CODE
    def nextTurn(self):
        if self.gamestate.p1Turn:
            if self.player1 == "human":
                self.clickable = True
                return
            else:
                nextMove = self.player1.getAIMove()
                self.gamestate.makeMove(nextMove)
                self.player1.makeMove(nextMove)
    
                self.last = nextMove #added
                
                self.updateStones()
                if(self.player2 != "human"):
                    self.player2.makeMove(nextMove)
                self.nextTurn() #this isn't a great idea                
        else:
            if self.player2 == "human":
                self.clickable = True
                return
            else:
                nextMove = self.player2.getAIMove()
                if(nextMove == None): return #the AI won
                
                self.gamestate.makeMove(nextMove)
                self.player2.makeMove(nextMove)
                
                self.last = nextMove
                
                self.updateStones()
                if(self.player1 != "human"):
                    self.player1.makeMove(nextMove)
                self.nextTurn() #this isn't a great idea
            


    def __init__(self, parent, gamestate, player1, player2):
        
        tk.Frame.__init__(self,parent)
        self.gamestate = gamestate
        self.rows = self.gamestate.rows #number of horizontal lines
        self.cols = self.gamestate.cols #number of vertical lines
        self.hborder = 50 #left-right border
        self.vborder = 50 #top-bottom border
        self.squaresize = 40
        self.stonerad = 0.3*self.squaresize
        self.stoneIDs = {} #keep track of stone id's

        w = (self.cols-1)*self.squaresize + 2*self.hborder
        h = (self.rows-1)*self.squaresize + 2*self.vborder
        self.board = tk.Canvas(parent, width=w, height=h) #why does this need to be parent rather than self?
        self.board.pack() #necessary?

        ##### AI #####
        self.player1 = player1
        self.player2 = player2
 #       self.AI2 = montecarlo.MCGameTree(self.gamestate)
        ##############
        self.clickable = False #can the player click on the screen?

        for i in range(0,self.cols):
            x = self.hborder+i*self.squaresize
            self.board.create_line(x,self.vborder,x,self.vborder+self.squaresize*(self.rows-1))
    
        for i in range(0,self.rows):
            y = self.vborder+i*self.squaresize
            self.board.create_line(self.hborder,y,self.hborder+self.squaresize*(self.cols-1),y)
        
        self.board.bind("<Button-1>", self.onClick)
        self.board.bind("<Motion>", self.onMove)

        self.nextTurn() #start the game
