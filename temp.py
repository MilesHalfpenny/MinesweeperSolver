for x in range(1,8):
    print(f"\"Mine{x}\", ", end = "")

print()
for n, y in enumerate(["Mine1", "Mine2", "Mine3", "Mine4", "Mine5", "Mine6", "Mine7", "UnsearchedTile", "FlaggedMine", "EmptyTile"]):
    print("\"" + y + "\"" + " : " + str(n + 1) + ", ", end = "")