"""Moves and positions settled by hand, where the printed text cannot.

The converter reads Philidor's words and the board rules out the rest. A few
plies defeat both: the scan destroyed the move, or the text names something
impossible, and no reading of it lets the game go on. Those are decided here,
in the open, one entry at a time.

Each entry says what was played and why, and the reason must rest on evidence
in the book -- most often Philidor's own note on that move, which the
converter never reads. `make stops` prints the evidence for every ply still
waiting on a decision.

An entry is keyed by the game's slug and the ply's number in the line the
board plays, counting the moves a back-game inherits from its parent. Both
numbers are in the `stops.json` that `make stops` writes.

Nothing here is silent: a move taken from this table is marked `editorial` in
games.json, tagged in the PGN, and stated on the chapter, so a reader can tell
it apart from what Philidor actually wrote.
"""

# (slug, ply): (move in algebraic notation, why it is that move)
READINGS = {}


# slug: (position as a FEN, where it comes from)
#
# A study states its position in the text, and that is read like any other
# move, so almost none are needed here. This is for the few the scan lost.
POSITIONS = {
    "a-drawn-game-with-two-separated-pawns-against-two-united-pawns": (
        "8/8/8/1pPk2p1/1P6/3K4/8/8 w - - 0 1",
        "The scan carries no 'Situation of the White' block for this study, "
        "so there is nothing to read. Supplied by hand by the maintainer, and "
        "consistent with the play that follows: two separated black pawns "
        "against two united white ones.",
    ),
}


def position_for(slug):
    entry = POSITIONS.get(slug)
    return entry[0] if entry else None


def pinned_for(slug):
    """The hand-settled moves for one game, by ply."""
    return {ply: san for (game, ply), (san, _) in READINGS.items()
            if game == slug}


def reason_for(slug, ply):
    entry = READINGS.get((slug, ply))
    return entry[1] if entry else None
