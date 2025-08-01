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
"""