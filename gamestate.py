import copy
import time
import math
import secrets

#----------------------------------------- Game Logic -----------------------------------------#

def sign(x):
    if x==0: return 0
    if x>0: return 1
    if x<0: return -1


#empty should really be a set
class GameState():
    
    posDirs = [(0,1), (1,1), (1,0), (1,-1)]
    
    def __init__(self, rows, cols, N):
        self.N = N  #N in a row to win
        self.stones = {}
        self.empty = []
        self.rows = rows
        self.cols = cols
        self.p1Turn = True

        self.winner = 0

        #either ball or a stone
        for i in range(0,rows):
            for j in range(0,cols):
                self.stones[(i,j)] = 0
                self.empty.append((i,j))

        self.multi = self.multigraph()

    def copy(self):
        newCopy = GameState(self.rows, self.cols, self.N)
        newCopy.stones = copy.copy(self.stones)  #can avoid a rows*cols worth of time by chaning constructor
        newCopy.empty = copy.copy(self.empty)
        newCopy.p1Turn = self.p1Turn
        newCopy.winner = self.winner
        return newCopy
        
        
    def makeMove(self,move):
        self.setStone(move[0], move[1])

    def curPlayer(self):
        if(self.p1Turn):
            return 1
        else:
            return -1
    
    def setStone(self,r,c):

        assert(self.winner == 0)

        if(self.p1Turn):
            color = 1
        else:
            color = -1         
        self.stones[(r,c)] = color
        self.updateWinner(r,c,color)
        self.empty.remove((r,c))                         
        self.p1Turn = not self.p1Turn

    def inBounds(self,coords):
        r,c = coords[0], coords[1]
        return (r>=0 and r<=self.rows-1 and c>=0 and c<=self.cols-1)

    #better way?
    # is there a new winner this turn?
    # also update threat
    def updateWinner(self,r,c,color):
        for pdir in self.posDirs:
            pcount=0
            ncount=0
            for i in range(1,self.N):
                nextSpot = (r+i*pdir[0],c+i*pdir[1])
                if (self.inBounds(nextSpot) and self.stones[nextSpot] == color):
                    pcount = pcount + 1
                else:
                    break
            for i in range(1,self.N):
                nextSpot = (r-i*pdir[0],c-i*pdir[1])
                if (self.inBounds(nextSpot) and self.stones[nextSpot] == color):
                    ncount =ncount + 1
                else:
                    break
            lineLen = ncount+pcount+1
            if(lineLen >= self.N):
               self.winner = color
                

    def playout(self):
        gameCopy = self.copy()
        while(len(gameCopy.empty) != 0 and gameCopy.winner == 0):
            r = secrets.SystemRandom().randint(0,len(gameCopy.empty)-1)
            nextStone = gameCopy.empty[r]
            gameCopy.makeMove(nextStone)
        return gameCopy.winner

    def hardPlayout(self):
        gameCopy = self.copy()
        while(len(gameCopy.empty) != 0 and gameCopy.winner == 0):
            if((forced := gameCopy.findForced()) != None):
                nextStone = forced
            else:
                r = secrets.SystemRandom().randint(0,len(gameCopy.empty)-1)
                nextStone = gameCopy.empty[r]
            gameCopy.makeMove(nextStone)
        return gameCopy.winner

    #returns a list of other squares that are in line with x
    #could just be a lookup
    def adjacent(self, x):
        A = []
        for d in self.posDirs:
            for i in range(1,self.N):
                A.append( (x[0] + i * d[0], x[1] + i * d[1]) )
        return A
            
            

    def multigraph(self):       
        multi = []
        for r in range(0,self.rows):
            for c in range(0,self.cols):
                for d in self.posDirs:
                    newEdge = []
                    for i in range(0,self.N):
                        square = (r+i*d[0], c+i*d[1])
                        if self.inBounds(square):
                            newEdge.append(square)
                        else:
                            newEdge = []
                            break
                    if(newEdge != []):
                        multi.append(newEdge)
        return multi

    #look for a spot that's one stone away from 5
    # (of either color)
    def findForced(self):
        hold = None
        for edge in self.multi:
            color = None
            empty = None
            for s in edge:
                if self.stones[s] == 0:
                    if empty != None:
                        empty = None
                        break
                    else:
                        empty = s
                else:
                    if color == None:
                        color = self.stones[s]
                    elif color != self.stones[s]:
                        empty = None
                        break
                    
            if empty != None:
                if color == self.curPlayer():
                    return empty
                else:
                    hold = empty
        return hold

    def findOpenThrees(self):
        stones = self.stones
        opens = []
        for edge in self.multi:
            if stones[edge[0]] == 0 or stones[edge[4]] == 0:
                color = stones[edge[1]]
                if color != 0:
                    if stones[edge[2]] == color and stones[edge[3]] == color:
                        if(stones[edge[0]] == 0):
                            opens.append(edge[0])
                        if(stones[edge[4]] == 0):
                            opens.append(edge[4])
        return opens
                        
                    
        
        

    def undo(self,move):
        self.stones[move] = 0
        self.empty.append(move)
        self.winner = 0
        self.p1Turn = not self.p1Turn

