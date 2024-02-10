import copy
import time
import priority
import random
import bisect

# improvements:
# the heat map
# look for forced wins
class Minimax:

    inf = float("inf")
    scoreVect = [0, 1, 4, 16, 64, 100000] #five in a row
    firstTurn = True #for moving faster on the first move

    def __init__(self,gamestate, player, depth):
        self.gamestate = gamestate.copy()
        self.player = player
        self.depth = depth
        self.multi = self.gamestate.multigraph()

    #trivial initialization
    def initHeatMap(self):
        heatMap = priority.myPriorityQueue()
        for square in self.gamestate.stones:
            heatMap.add_task(square,0)
        heatMap.add_task((self.gamestate.rows/2, self.gamestate.cols/2), 1)
        return heatMap

    #get the value for this position
    #good position for the current player is a positive score
    def heuristic(self, player, curDepth):

        fallOff = 0.1 #let the value of the heuristic die off with greater depth
        
        scoreVect = self.scoreVect
        stones = self.gamestate.stones
        
        score = 0
        
        for edge in self.multi:
            b = 0 #current player
            w = 0
            for square in edge:
                if stones[square] == player:
                    b = b + 1
                elif stones[square] == -player:
                    w = w + 1
            if(b > 0 and w > 0):
                pass #don't count that edge toward the score
            elif b > 0:
                score = score + scoreVect[b]
            elif w > 0:
                score = score - scoreVect[w]
        return score - curDepth * fallOff

    def minimaxMove(self,depth, AIturn): #turn: is it the AI's turn? Either 1 or -1
        
        if(depth == 0):
            return (self.heuristic(), None)

        gamestate = self.gamestate

        if gamestate.winner != 0:
            return (self.heuristic(), None)
 
        optScore = - AIturn * float("inf") #initial safe value
        optMove = None
        
        for move in copy.copy(gamestate.empty):
            gamestate.makeMove(move)
            val = self.minimaxMove(depth-1,-1*AIturn)[0]
            
            if AIturn * val >= AIturn * optScore:
                optScore = val
                optMove = move
            
            gamestate.undo(move)

        return (optScore, optMove)

    #get list of moves in likely order of how good they are
    def orderedMoveList(self):
        gamestate = self.gamestate
        moveList = []
        for move in copy.copy(gamestate.empty):
            gamestate.makeMove(move)
            heur = self.heuristic(self.player, 0)
            bisect.insort(moveList, (-heur,move) ) #minus sign since high heuristic values should come first
            gamestate.undo(move)

        return moveList[:20] #changed
   #     return [A[1] for A in moveList][:20] #test
        

    def minimaxAlphaBeta(self, depth):
 #       movelist = self.heatMap.sorted_list()
        movelist = self.orderedMoveList()
 #       print(movelist)
        return self.minimaxAlphaBetaHelper(depth, True, float("inf"), 0, movelist)

    #siblingExtreme is the extreme value so far among a node's siblings
    def minimaxAlphaBetaHelper(self, depth, AIturn, sibExtreme, curDepth, movelist): #depth is more like "max depth"

        
        gamestate = self.gamestate

        if gamestate.winner != 0:
            return (self.heuristic(self.player, curDepth), None)

        if AIturn:
            optScore = - float("inf")
        else:
            optScore = float("inf")
            
        optMove = None

        ##An optimization (play forced moves immediately) ###############

        #not quite - if you have a win, take it
        
        if (forced := gamestate.findForced()) != None:
            gamestate.makeMove(forced)
            #should depth be 0 here
            newMoves = copy.copy(movelist)
            val = self.minimaxAlphaBetaHelper(depth, not AIturn, optScore, curDepth + 1, newMoves )[0] #The plus one is experimental: allow *more* exploration around forced moves
            gamestate.undo(forced)
            return (val,forced)

        #open threes
 #       opThrees = gamestate.findOpenThrees()
 #       if(opThrees != []):
#            print(opThrees)
 #       for move in opThrees:
#            gamestate.makeMove(move)
#            val = self.minimaxAlphaBetaHelper(depth, not AIturn, optScore, movelist, curDepth + 1)[0]
#            gamestate.undo(forced)
#            return (val,forced)
        ##################### </optimization> ############################
        #should go after the optimization
        if(depth == 0):
            return (self.heuristic(self.player, curDepth), None)

#        movelist = copy.copy(gamestate.empty)
#        moveList = self.heatMap.sorted_list()
#        print(moveList)
#        moves = self.orderedMoveList() #testing!
        
        for m in movelist:
            move = m[1]
            if not move in gamestate.empty: continue #needed when we're using movelist instead of a copy of empty (faster)
            
            gamestate.makeMove(move)

            #open threes
 #           if move in opThrees:
#                newDepth = depth-1
#            else:

            newDepth = depth - 1

            ## <NEW> should really be own method
            newMoves = copy.copy(movelist)
            for x in gamestate.adjacent(move):
                if not move in gamestate.empty: continue
                gamestate.makeMove(move)
                heur = self.heuristic(self.player, 0)
                bisect.insort(newMoves, (-heur, move))
                gamestate.undo(move)
            newMoves = newMoves[:10] #keep the list of moves trimmed
            ## </NEW>
                           
            val = self.minimaxAlphaBetaHelper(newDepth, not AIturn, optScore, curDepth + 1, newMoves)[0]

            if AIturn:    #in the max phase
               if val > sibExtreme: #is the equal okay?
                    gamestate.undo(move)
                    return (float("inf"), None) #pruning              
               if val >= optScore:
                    optScore = val
                    optMove = move
            else:          #in the min phase
                if val < sibExtreme:
                    gamestate.undo(move)
                    return (-float("inf"), None) #pruning
                if val <= optScore:
                    optScore = val
                    optMove = move
            
            gamestate.undo(move)
            
        return (optScore,optMove)    
        
    
    def getAIMove(self):
        
        if self.firstTurn: return (self.gamestate.rows//2, self.gamestate.cols//2) #minor optimization
        
        start = time.time()
        x = self.minimaxAlphaBeta(self.depth)
        ret = x[1]
        end = time.time()
 #       print("score: ", x[0])
        print("AI time: ", end - start)
        return ret
        

    def makeMove(self,move):
        self.firstTurn = False
        self.gamestate.makeMove(move)
 #       heatMap = self.heatMap
#        heatMap.remove_task(move)
 #       for d in [(0,1),(1,0),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
#            heatMap.increase_priority( (move[0] + d[0], move[1] + d[1]), 1 )
        
