"""
How should this work?

HERE - neeed to check in 'both' directions - that the current minesweeper has none that don't work, AND the one checking against also has 
none that don't work

For each exposed minesweeper that has not yet been visited:
1. Find every combination of mines around it that would fit into the empty space around it, and its mine number
2. Look at every minesweeper around it (in a one tile radius) (that has found all of its combinations)
    a. If any of the current minesweepers combiations do not work with ANY of the combinations found in these other minesweepers, 
    delete that combination
    b. Add the current minesweeper to the queue of minesweepers that have changed (decreased) the numebr of combinations available to them
        - so that every minesweeper around tha current minesweeper can check its combinations against the now smaller combination list
        of the current minesweeper, with the aim of reducing the size of their combination lists
3. Empty the queue of changed minesweepers - see 'Empty the changed queue' - HERE may be better to do this at another time for efficiency reasons
4. Move to the next unvisited exposed minesweeper
5. If all of the exposed minesweepers has been visited, then there should be only one combination that is guaranteed to not hit a mine
    (this may not be the case, there may be a true 50/50 to choose from()

Empty the changed queue (a function)
For every minesweeper in the changed queue, visit every one of its neightbours and for each one do:
1. See if their combinations list can be decreased any further
    a. If it can, deacrease its list then add it to the changed queue
2. Move onto the next minesweeper in the changed queue
ISSUES (with this setuo) - if multiple minesweepers flag on the same different mineweeper, it may check multiple times, only getting rid of a
combinations at a time (don't think is serious issue)


HERE - how can we figure out if the pattern works independantly of the rest of the board, and use it before checking any other sections, 
so as to get more info and be more efficient - similarly to how I do it
When only 1 combination works, instantly lock that in as guaranteed - flag the mine there and decrement as required, then add the places next to it to be checked
"""

import queue
import ImgRecog
from pathlib import Path 
import numpy as np

class mineNumTile:
    #the effective (remaining unflagged number) of mines surrounding this mineNum tile
    effectiveMineNum : int

    #a set containing the coordinates of any surrounding unsearched coords - where mines could be potentially flagged
    surUnsearchedCoords : set[ tuple[int,int] ]
    
    #the possible configurations of mines surrounding this tile
    # stored as a set of all of the configurations, where each configuration is a tuple of all of the coordinates of mines 
    possMineConfigs : set[ frozenset[ tuple[int,int] ] ]

    #a set containing all of the coords of mineNums that share an unsearched tile with this mineNum
    # (Therefore all mineNums that are influenced by the configs of this mineNum and vice versa)
    connectedMineNums : set[ tuple ]  = set() #a set of mineNumTile objects

    def __init__(self, 
                 StartingEffectiveMineNum : int, 
                 StartingSurUnsearchedCoords : set[ tuple[int,int] ],
                 StartingConnectedMineNums : set[ tuple ] | None = None) -> None:
        self.effectiveMineNum = StartingEffectiveMineNum
        self.surUnsearchedCoords = StartingSurUnsearchedCoords
        if StartingConnectedMineNums:
            self.connectedMineNums = StartingConnectedMineNums

    def addSurroundingUnsearchedCoord(self, coordinate : tuple[ int,int ]):
        self.surUnsearchedCoords.add(coordinate)

    def connectMineNums(self, connectedMineNums : tuple | list | set):
        """
        Connects all of the mineNums given in connectedMineNums to this mineNum
        If it is given itself, it will ignore it (to prevent having to prune it from the tuple/list/set before passing)
        """
        for mineNumToCon in connectedMineNums:
            if mineNumToCon == self:
                continue
            self.connectedMineNums.add(mineNumToCon)
            

    def calcPossMineConfigs(self) -> None:
        allPossMineConfigs : set[ frozenset[ tuple[int,int] ] ] = set()

        def recursivelyGenEachMine(currentMineCoords : tuple [ tuple[int,int], ... ], 
                                   numMinesToPlace : int):
            
            if numMinesToPlace == 0:
                allPossMineConfigs.add(frozenset(currentMineCoords))
            
            for unsearchedCoord in self.surUnsearchedCoords:
                if unsearchedCoord in currentMineCoords:
                    continue
                recursivelyGenEachMine(currentMineCoords + (unsearchedCoord,), numMinesToPlace - 1)

        recursivelyGenEachMine((), self.effectiveMineNum)

        self.possMineConfigs = allPossMineConfigs

    def checkPossConfigsAgainstConnected(self) -> set:
        """
        Will check every mine config against all of the mineNums connected to this mineNum, 
            then return all of the mineNums that had their possConfig list pruned (so they can be checked next)
             - returns in form {mineNumTile, ...} (as a set)
        HERE - need to work in a solution having been found - will be when every config for a mineNum shares the same mine OR only one config possible  
        """
        #mineNumTile(s) that have had their possMineConfigs pruned when checking against other mineNum tiles
        prunedMineNumTiles : set[ mineNumTile ] = set()
        for cMN in self.connectedMineNums:
            #sequence used to get type hinting for conMineNum
            conMineNum : mineNumTile = cMN # type: ignore
            if type(conMineNum) != mineNumTile: #to ensure no errors sneak in because of the type ignore above
                raise TypeError(f"Type of conMineNum should be mineNumTile, is {type(conMineNum)}")
            
            #the mine configs to be removed and whether the conMineNum's possMineConfigs were pruned
            mineConfigsToRemove, conMineNumBeenPruned = conMineNum.checkMineConfigsAgainstGivenConfigs(self.possMineConfigs, self.surUnsearchedCoords)
            
            if len(mineConfigsToRemove) != 0:
                self.removeMineConfigs(mineConfigsToRemove)
                prunedMineNumTiles.add(self)

            if conMineNumBeenPruned:
                prunedMineNumTiles.add(conMineNum)

        return prunedMineNumTiles
    

    def checkMineConfigsAgainstGivenConfigs(self, 
                                            mineConfigsCheckingAgainst : set[ frozenset[ tuple[int,int] ] ], 
                                            surUnsearchedTilesOfGiven : set[ tuple[int,int] ]
                                            ) -> tuple[ set[ frozenset[ tuple[int,int] ] ]  ,   bool ]:
        """
        Checks the current possMineConfigs on this mineNumTile against the given mine configs (mineConfigsCheckingAgainst)

        REMOVES/prunes the CURRENT mine configs that are impossible (that are not shared by both mineNumTiles)
        RETURNS the GIVEN mine configs that are impossible and whether or not any of the CURRENT mine configs were impossible (been removed)
        """
        
        def convertToStandardFormat(mineConfigsSet : set[ frozenset[ tuple[int,int] ] ],
                                    overlappingSurUnsearchedTiles : set[ tuple[int,int ] ]
                                    ) -> tuple[ set[ frozenset[ tuple[int,int] ] ]  ,  dict[ frozenset[tuple[int,int]], frozenset[frozenset[tuple[int,int]]] ] ]:
            """
            Converts every mineConfig in mineConfigsSet to a standard form 
            in which only the mines that are in overlappingSurUnsearchedTiles are kept

            Will also create a dictionary mapping every convertedMineConfig 
            to the unconverted (there may be multiple) mineConfig(s) that they were converted from 
            """
            convertedMineConfigsSet : set[ frozenset[ tuple[int,int]] ] = set()
            convertedToNotMineConfigsDict : dict[ frozenset[ tuple[int,int] ], frozenset[ frozenset[ tuple[int,int] ] ] ]= {}
            for mineConfig in mineConfigsSet:
                
                convertedMineConfig : set[ tuple[int,int] ] = set()
                for mineCoord in mineConfig:
                    if mineCoord in overlappingSurUnsearchedTiles:
                        convertedMineConfig.add(mineCoord)

                if len(convertedMineConfig) > 0:
                    frozenConvertedMineConfig = frozenset(convertedMineConfig)

                    convertedMineConfigsSet.add(frozenConvertedMineConfig)

                    if frozenConvertedMineConfig in convertedToNotMineConfigsDict:  
                        valueToUpdate = convertedToNotMineConfigsDict[frozenConvertedMineConfig].union(frozenset((mineConfig, )))
                    else:
                        valueToUpdate = frozenset((mineConfig, ))
                    convertedToNotMineConfigsDict.update({frozenConvertedMineConfig : valueToUpdate})
            
            return convertedMineConfigsSet, convertedToNotMineConfigsDict

        overlappingSurUnsearchedTiles = self.surUnsearchedCoords.intersection(surUnsearchedTilesOfGiven)

        currentConvertedMineConfigs, curConToNotMineConfigsDict = convertToStandardFormat(self.possMineConfigs, overlappingSurUnsearchedTiles)
        givenConvertedMineConfigs, givenConToNotMineConfigsDict = convertToStandardFormat(mineConfigsCheckingAgainst, overlappingSurUnsearchedTiles)


        #get the converted configs to be pruned from their respective set of possible mine configs 
        # (because the other set of possible configs doesn't have them, therefore that config is impossible)
        convToPruneFromCurMineConfigs : set[ frozenset[tuple[int,int]]] = set()
        for curConvConfig in currentConvertedMineConfigs:
            if curConvConfig not in givenConvertedMineConfigs:
                convToPruneFromCurMineConfigs.add(curConvConfig)
        
        convToPruneFromGivenMineConfigs : set[ frozenset[tuple[int,int]]] = set()
        for givenConvConfig in givenConvertedMineConfigs:
            if givenConvConfig not in currentConvertedMineConfigs:
                convToPruneFromGivenMineConfigs.add(givenConvConfig)

        #converting the mine configs to prune BACK to being not converted
        toPruneFromCurMineConfigs : set[ frozenset[tuple[int,int]]]= set()
        for curConvToPrune in convToPruneFromCurMineConfigs:
            toPruneFromCurMineConfigs.update(curConToNotMineConfigsDict[curConvToPrune])

        toPruneFromGivenMineConfigs : set[ frozenset[tuple[int,int]]] = set()
        for givenConvToPrune in convToPruneFromGivenMineConfigs:
            toPruneFromGivenMineConfigs.update(givenConToNotMineConfigsDict[givenConvToPrune])
        
        if len(toPruneFromCurMineConfigs) != 0:
            self.removeMineConfigs(toPruneFromCurMineConfigs)
            curMineConfigsBeenPruned = True
        else:
            curMineConfigsBeenPruned = False

        #HERE - pot efficiency saving - check if only connection and then if is send curMineConfigsBeenPruned = False
        return toPruneFromGivenMineConfigs, curMineConfigsBeenPruned 
        
        
    def removeMineConfigs(self, mineConfigsToRemove : set[ frozenset[ tuple[int,int] ] ]) -> None:
        self.possMineConfigs.difference_update(mineConfigsToRemove)





def getSurroundingTileCoords(baseCoords : tuple[int, int], 
                             maxX : int, maxY : int) -> set[ tuple[int, int] ]:
    """
    Returns the coordinates of all the tiles directly surrounding the current tile
     - provided those tiles are valid - have 0 <= xCoord <= maxX and 0 <= yCoord <= maxY
    """
    #a tuple containing all of the coordinate changes to get the surrounding tiles - starting at directly up and rotating clockwise
    surroundingCoordChanges = ((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)) 

    newCoordSet : set[ tuple[int, int] ] = set()
    for coordChange in surroundingCoordChanges:
        newCoords = (baseCoords[0] + coordChange[0], baseCoords[1] + coordChange[1])
        if newCoords[0] >= 0 and newCoords[0] <= maxX and newCoords[1] >= 0 and newCoords[1] <= maxY:
            newCoordSet.add(newCoords)
    return newCoordSet

def prepQueue(board) -> tuple[ queue.Queue, dict[ tuple[int,int], tuple[ mineNumTile, ... ] ]]:
    """
    Adds every mine number tile that is next to an empty space and has mines still to be placed to a queue that will then be solved from
    Also creates a dictionary containing every unsearched space next to a mineNum (key)
        and the mineNums that space is next to (value)
    """
    checkQueue = queue.Queue()
    unsearchedAndMineNumConDict : dict[ tuple[int,int], tuple[ mineNumTile, ... ] ] = {}

    for rowNum, row in enumerate(board):
        for columnNum, tile in enumerate(row):

            if tile in range(1,8): #if tile is a mine number
                effectiveMineNum = int(tile)
                #as don't want to add solved mines
                addToQueue : bool = False
                surroundingUnsearchedTiles=set()
                #HERE - could do some error checking here
                for surroundingTileCoord in getSurroundingTileCoords((columnNum, rowNum), board.shape[1]-1, board.shape[0]-1):
                    surroundingTileVal = int(board[surroundingTileCoord[1]][surroundingTileCoord[0]])
                    if surroundingTileVal == 0:
                        surroundingUnsearchedTiles.add((surroundingTileCoord))
                        addToQueue = True
                    elif surroundingTileVal == -2:
                        #if surrounding tile is a mine then reduce the effective mine number - as only
                        effectiveMineNum -= 1

                if effectiveMineNum < 0:
                    raise Exception(f"Mine num tile has effective mine number lower than 0 ({effectiveMineNum}) - mine mistakenly flagged or original mine num incorrect")

                if addToQueue and effectiveMineNum != 0:
                    curMineNumTile = mineNumTile(effectiveMineNum, surroundingUnsearchedTiles)
                    curMineNumTile.calcPossMineConfigs()
                    checkQueue.put_nowait(curMineNumTile)

                    for surUnsearchedTile in surroundingUnsearchedTiles:
                        if surUnsearchedTile in unsearchedAndMineNumConDict:
                            #(columnNum, rowNum) is the coordinates of the current tile - a mineNum
                            valToUpdate = unsearchedAndMineNumConDict[surUnsearchedTile] + (curMineNumTile,)
                        else:
                            valToUpdate = (curMineNumTile,)
                        unsearchedAndMineNumConDict.update({surUnsearchedTile : valToUpdate})
    return checkQueue, unsearchedAndMineNumConDict

def connectMineNums(unsearchedAndMineNumConDict : dict[ tuple[int,int], tuple[ mineNumTile, ... ] ]):
    """
    Takes in a dict mapping unsearched tiles to the mineNums next to them, 
    and uses that to connect mineNums that share unsearched tiles 
     - as the possible configurations of mines around one of those mineNums may effect the possible configs of the other (connected) mineNum
    """
    for connectedMineNums in unsearchedAndMineNumConDict.values():
        if len(connectedMineNums) <= 1:
            continue
        for baseConnectingFrom in connectedMineNums:
            baseConnectingFrom.connectMineNums(connectedMineNums)

def solve(board):
    #A queue of the mineNums that need to be checked against their adjacenet mineNums
    temp = prepQueue(board) #temp used to keep type annotation
    
    #connect all of mineNums to each other as required
    unsearchedAndMineNumConDict : dict[ tuple[int,int], tuple[ mineNumTile, ... ] ] = temp[1]
    connectMineNums(unsearchedAndMineNumConDict)

    #a set containing all mineNumTiles that are in the queue, in order to prevent more than one item being in the queue
    # whilst maintaining the efficiency advantage that visiting every tile once rather than a select segment many times provides 
    # HERE - is that true? is it only better for getting all of the information possible, 
    #     rather than trying to get one guaranteed mine/empty tile found very quickly by clustering around a small chunk of tiles
    #           The advantage is you get a lot of information into the system as quickly as possible, 
    #           but is that needed if a 1 2 1 pattern is right there, or a 1
    #               Therefore how much does the game run on patterns vs on long chains of logic
    #               but also looking at a lot of places ups chances of finding a pattern, guaranteeing solution if a 1 2 1 present in n, and would
    #               be likely to be much smaller
    # so just set def worse than queue and set
    # clustering out from a point better? real q is better to do a smaller section twice before everything once
    #HERE - maybe want to go for most click efficient way of solving as well? - so want as much information as possible
    inTheQueueSet : set[ mineNumTile ] = set()
    for mineNumTuple in unsearchedAndMineNumConDict.values():
        inTheQueueSet.update(mineNumTuple)

    allRelevantMineNums = tuple(inTheQueueSet) #HERE - temp

    toCheckMineNumQueue = temp[0]

    while toCheckMineNumQueue.qsize() > 0:
        curMineNumTile : mineNumTile = toCheckMineNumQueue.get_nowait()

        

        alteredMineNumTiles = curMineNumTile.checkPossConfigsAgainstConnected()

        for alteredMineNum in alteredMineNumTiles:
            if alteredMineNum not in inTheQueueSet:
                toCheckMineNumQueue.put_nowait(alteredMineNum)
                inTheQueueSet.add(alteredMineNum)

        
    for mineNumT in allRelevantMineNums:
            print(mineNumT.possMineConfigs)

        
#the path to the folder where we will be pulling all of the reference images of the game board from
pathToReferenceImages = Path("C:\\BigProj\MinesweeperSolver\ReferencesImages")

board = ImgRecog.convertImage(0.95, 
                      0.99, 
                      0.9,
                      pathToReferenceImages, 
                      debugging = False)


print("start")
solve(board)
print("end")