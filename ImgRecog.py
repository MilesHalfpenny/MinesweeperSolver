import skimage as ski
from pathlib import Path
import os

import numpy as np
import matplotlib.pyplot as plt

def convertImage(goodMatchRequirement, 
                 goodMatchRequirementSolidColour, 
                 goodMatchRequirementMineFlag,
                 pathToReferenceImages, 
                 debugging = False):
    """
    ARGUEMENTS:    
    goodMatchRequirement and goodMatchRequirementSolidColour
    are the values (0 to 1 inclusive) required for a match to be considered accurate using skimage.feature.match_template
    where 0 is no match and 1 is a perfect match

    goodMatchRequirement is used for the mine numbers and flags, as they are quite distinct
        - therefore a lower value can be used without error, meaning alternate images may not have to be required
        - 0.95 is good here for the Google minesweeper HERE
    goodMatchRequirementSolidColour is used for the empty and unsearched tiles, as they are often background colours for other tiles
        - therefore they need a high value, so mine numbers and flags are not mistaken for these tiles
        - this also means they may be more likely to require an alternate image
        - 0.99 is good here for the Google minesweeper HERE

    pathToReferenceImages if the Path object (using pathlib.Path) to the reference images folder

    
    RETURN VALUE:
    Will return a numpy array with the same dimensions as the minesweeper board, with:
    1-7 being the corresponding mineNums at that spot
    0 being an unsearched tile (that has not been swept)
    -1 being an empty tile that has been swept (has nothing in confirmed and no mines around it)
    -2 being a tile with a flag for a mine

    
    REQUIREMENTS FOR REFERENCE IMAGES:
    alternate images are provided in case the minesweeper game uses a checkboard style pattern for its tiles, like the Google minesweeper
    (https://share.google/CCypPLSMMFglnS7vM)

    the filenames of the reference images should be as follows:
    Board   - the minesweeper board to convert
    FlaggedMine
    EmptyTile
    UnsearchedTile   - HERE - not used currently, may be used for error checking
    Mine1
    Mine2
    Mine3
    Mine4
    Mine5
    Mine6
    Mine7
    ReferenceTile  - an exact sized tile, which can contain anything - the dimensions MUST be correct
    and their 'Alt' versions e.g. Mine2Alt or EmptyTileAlt

    As ReferenceTile is used with EXACT dimensions, all other tiles may be differently sized as required to ensure they are still
    recognisable regardless of visual effects (such as border effects when adjacent to an unsearched tile)
    HOWEVER all other tiles MUST be smaller or the same size as ReferenceTile
    """

    #HERE - currently pulling the board from where the reference images are, probably shouldn't (so should store it somewhere else)
    board = ski.io.imread(Path.joinpath(pathToReferenceImages, "Board2.png"))

    #a seperate tile used as the reference tile for sizing, as it MUST have as close to the exact dimensions for a tile as possible 
    #       (whereas the dimensions for a specific mine number may be cropped for whatever reason)
    referenceTile = ski.io.imread(Path.joinpath(pathToReferenceImages, "ReferenceTile.png"))

    tileWidth = referenceTile.shape[0]
    tileHeight = referenceTile.shape[1]
    resultingBoardArray = np.zeros((round(board.shape[0]/tileWidth), round(board.shape[1]/tileHeight)))

        #Gets the reference image for a tile, and uses match_template to find where on the board that tile occurs
        #then populates the board array based off the number allocated to that tile 

    #HERE "UnsearchedTile" : 0 skipped bc that by default - use for error checking?
    tileNameNumberValDict : dict[str, int] = {"FlaggedMine" : -2, "EmptyTile" : -1, "Mine1" : 1, "Mine2" : 2, "Mine3" : 3, "Mine4" : 4, "Mine5" : 5, "Mine6" : 6, "Mine7" : 7}
    for tileName in tileNameNumberValDict.keys():
        for altPath in ("", "Alt"):
            tileImagePath = Path.joinpath(pathToReferenceImages, tileName+altPath+".png")

            if debugging:
                print(tileImagePath)

            if not os.path.exists(tileImagePath):
                print(f"No reference image stored for  {tileName}{altPath}, skipping")
                continue

            tileImage = ski.io.imread(tileImagePath)
            
            templateMatchResult = ski.feature.match_template(board, tileImage)

            #sets the good match requirement that will be used to the corresponding arguement depending on what tile is being looked for
            if tileNameNumberValDict[tileName] in (-1, 0): #HERE - potentially flaggedMine is also a single colour
                goodMatchReqUsing = goodMatchRequirementSolidColour
            elif tileNameNumberValDict[tileName] == -2:
                goodMatchReqUsing = goodMatchRequirementMineFlag
            else:
                goodMatchReqUsing = goodMatchRequirement

            #a set to store all good matches found
            goodMatches : set[ tuple[int,int] ]= set()

            for rowNum, row in enumerate(templateMatchResult):
                for coloumnNum, pixel in enumerate(row):
                    if pixel >= goodMatchReqUsing:
                        goodMatches.add((coloumnNum, rowNum))

                    if debugging and pixel < goodMatchReqUsing:
                        #for debugging purposes - to highlight where a good match was found
                        templateMatchResult[rowNum][coloumnNum] = 0


            if debugging:
                #for debugging purposes - shows the input to and result of ski.feature.match_template
                fig = plt.figure(figsize=(8, 3))
                ax1 = plt.subplot(1, 3, 1)
                ax2 = plt.subplot(1, 3, 2)
                ax3 = plt.subplot(1, 3, 3)

                ax1.imshow(board)
                ax2.imshow(tileImage)
                ax3.imshow(templateMatchResult)

                plt.show()

            if debugging:
                print(goodMatches)
                print(tileNameNumberValDict[tileName])

            for matchRepresentingPixel in goodMatches:
                #(tileWidth - mineNumImage.shape[0]) and y axis equivalent acts as a correction for the reference image for the mineNum 
                #potentially being smaller than the actual tileWidth or Height in order to correct for visual effects
                matchXCoord : int = round( (matchRepresentingPixel[0] + (tileWidth - tileImage.shape[0])) / tileWidth )
                matchYCoord : int = round( (matchRepresentingPixel[1] + (tileHeight - tileImage.shape[1])) / tileHeight )
                
                resultingBoardArray[matchYCoord][matchXCoord] = tileNameNumberValDict[tileName]
            
            if debugging:
                for row in resultingBoardArray:
                    print(row)
                print()

    for row in resultingBoardArray:
        print(row)

    return resultingBoardArray
    




