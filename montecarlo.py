import math
import time
import copy
import secrets

class MCGameTreeNode:
    #need to set the player for the root node
    def __init__(self, parent, move):
        self.parent = parent
        self.childMoves = {}

        if(self.parent != None):
            self.player = -1 * self.parent.player
        
        self.move = move #the move used to get to this node
        self.p1Wins = 0
        self.p2Wins = 0
        self.lastScore = None
        
 #       self.projectedWinner = 0 #player with a detected forced win

    def winUpdate(self,winner):
        if winner == 1:
            self.p1Wins = self.p1Wins + 1
            return
        if winner == -1:
            self.p2Wins = self.p2Wins + 1
            return
        if winner == 0:
            self.p1Wins = self.p1Wins + 0.5
            self.p2Wins = self.p2Wins + 0.5
            return

    def printDescendents(self, depth):
        print(depth * "    ", str(self.move), " :: [", self.p1Wins, " ", self.p2Wins, "]", "  :: ", self.lastScore)
        for m in self.childMoves:
            self.childMoves[m].printDescendents(depth+1)

    #matters whose turn it is
    #t is the total simulations involving the parent
    def score(self, t):


        #IS THIS RIGHT?
 #       if(self.winner != 0):
#            print("yo")
#            return lastPlayer * self.winner * float("inf")
        
        if((lastPlayer := -1*self.player) == 1): #CHANGED
            wins = self.p1Wins
        else:
            wins = self.p2Wins

        n = self.p1Wins + self.p2Wins
        c = 1.5 #EXPLORATION CONSTANT

        if n == 0:
            print("this probably shouldn't happen...")
            return float("inf")

        s = (wins/n) + c * math.sqrt(math.log(t)/n)

        self.lastScore = s

        return s #the "suggested" function
        
        

#creates the abstraction of a full game tree stored in memory which can be accessed
class MCGameTree:
    posDirs = [(0,1), (1,1), (1,0), (1,-1)]
    
    #gamestate gets update as we move up and down the tree
    def __init__(self, gamestate, iterations):
        self.gamestate = gamestate
        self.root = MCGameTreeNode(None, None)
        self.root.player = 1 #set!
        self.curNode = self.root
        self.iterations = iterations

    def up(self):
        self.gamestate.undo(self.curNode.move)
        self.curNode = self.curNode.parent
        
        if(self.curNode == None):
            print("tried to access parent of root") #TESTING CODE

    def down(self,move):
        if(move in self.curNode.childMoves):
            self.curNode = self.curNode.childMoves[move]
        else:
            newNode = MCGameTreeNode(self.curNode,move)
            self.curNode.childMoves[move] = newNode
            self.curNode = newNode
        self.gamestate.makeMove(move)

    #go down the tree until finding unexplored moves
    def newMCSelectNode(self):
        while(True):
            curPlayer = self.gamestate.curPlayer()
            bestScore = -float("inf")
            bestMove = None
            children = self.curNode.childMoves
            if(len(children) != len(self.gamestate.empty) ): #there are unexplored children
                #EXPAND EVERYTHING?
                return
            
            for move in self.curNode.childMoves:
                childNode = self.curNode.childMoves[move]
                childScore = childNode.score(self.curNode.p1Wins + self.curNode.p2Wins)
                if childScore > bestScore:
                    bestScore = childScore
                    bestMove = move
            if(bestMove != None):
                self.down(bestMove)
            else:
                return

    def printMovePath(self):
        while(True):
            curPlayer = self.gamestate.curPlayer()
            bestScore = -float("inf")
            bestMove = None
            children = self.curNode.childMoves
            
            for move in self.curNode.childMoves:
                childNode = self.curNode.childMoves[move]
                childScore = childNode.score(self.curNode.p1Wins + self.curNode.p2Wins)
                if childScore > bestScore:
                    bestScore = childScore
                    bestMove = move
            if(bestMove != None):
                print("move: ", bestMove)
                self.down(bestMove)
            else:
                while(self.curNode.parent != None): self.up()
                return
        
    
    #explores a totally random child node
    def MCRandomExplore(self):
        numMoves = len(self.gamestate.empty)
        
        if self.gamestate.winner != 0:
            return #don't try to explore for a winning position
        
        if numMoves == 0: return #other things we could do...
        
        #Might want to make sure that this function does choose something that's already in the tree

        randMove = None
        while((randMove==None) or (randMove in self.curNode.childMoves)): #Really stupid!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            randMove = self.gamestate.empty[secrets.SystemRandom().randint(0,numMoves - 1)] #just use random choice
        self.down(randMove)

    def MCExploreAll(self):
        if self.gamestate.winner != 0:
            return []
        return copy.copy(self.gamestate.empty) #need to copy?
        

    def updateWinCount(self,p1Wins, p2Wins):
        self.curNode.p1Wins  = self.curNode.p1Wins + p1Wins
        self.curNode.p2Wins = self.curNode.p2Wins + p2Wins
    
    #assumes that self.curNode is the state that winner corresponds to
    def backProp(self, p1Wins, p2Wins):
        while(True):
#            if(winner == 1): self.curNode.p1Wins = self.curNode.p1Wins + 1
#            if(winner == -1): self.curNode.p2Wins = self.curNode.p2Wins + 1
#            if(winner == 0):
#                self.curNode.p1Wins = self.curNode.p1Wins + 0.5
#                self.curNode.p2Wins = self.curNode.p2Wins + 0.5
            #do something for a tie...
            self.updateWinCount(p1Wins,p2Wins)
                
            if(self.curNode.parent != None):
                self.up()
            else:
                return
    
    def MCiteration(self):
        self.newMCSelectNode()
 #       print("selected: ", self.curNode.move)
 #       self.root.printDescendents(0)
  #      self.MCRandomExplore()
        moves = self.MCExploreAll()
        p1Wins = 0
        p2Wins = 0
#        print("random child: ", self.curNode.move)

        # print("here")
        if self.gamestate.winner == 1:
            p1Wins = 1
        elif self.gamestate.winner == -1:
            p2Wins = 1
                
        for m in moves:
            self.down(m)
            
            winner = self.gamestate.playout()

            p1Inc = 0
            p2Inc = 0
            if winner == 1:
                p1Inc = p1Inc+1
            elif winner == -1:
                p2Inc = p2Inc + 1
            elif winner == 0:
                p1Inc = p1Inc + 0.5
                p2Inc = p2Inc + 0.5
            p1Wins = p1Wins + p1Inc
            p2Wins = p2Wins + p2Inc
            self.updateWinCount(p1Inc,p2Inc)
            self.up()
            
        self.backProp(p1Wins, p2Wins)
           
    def getAIMove(self):
        start = time.time()
        for i in range(0,self.iterations):
            if(i % 100 == 0): print(i)
            self.MCiteration()
 #       self.root.printDescendents(0)

        curBestMove = None
        curMax = 0
        for m in self.root.childMoves:
            node = self.root.childMoves[m]
            numVisited = node.p1Wins + node.p2Wins
            if(numVisited > curMax):
                curMax = numVisited
                curBestMove = m
        end = time.time()
        print("AI time: ", end-start)
        
#        self.printMovePath()
 #       self.root.printDescendents(0)
        
        return curBestMove


    def makeMove(self,move):
 #       self.gamestate.makeMove(move)
        self.root = MCGameTreeNode(None, None)
        self.root.player = self.gamestate.curPlayer() #set!
        self.curNode = self.root
