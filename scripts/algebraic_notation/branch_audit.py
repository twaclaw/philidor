"""Check every back-game against the parent game it branches from.

Philidor prints a back-game as a variation resuming its parent at a stated
move, so the two must agree on the position at that point. That gives 62
independent consistency checks that need no external source: if our reading of
either game is wrong, the back-game's first move will usually not be legal in
the position the parent reached.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import chess

from build import parse_all, slug
from readings import pinned_for
from replay_search import best_replay
from to_algebraic import Unparsed, ply_candidates

SECTIONS = parse_all()


def prefix_len(parent, sec):
    """How many of the parent's plies precede the back-game.

    A back-game beginning "from the 12th move of the Black" resumes after
    White has already played his 12th, so it needs one ply more than the
    whole moves before it.
    """
    n = 2 * (sec["first_move"] - 1)
    if sec["plies"][0][0] != parent["plies"][0][0]:
        n += 1
    return n


def parent_of(sec):
    i = SECTIONS.index(sec)
    for j in range(i - 1, -1, -1):
        if SECTIONS[j]["level"] == 1:
            return SECTIONS[j]
    return None


def main():
    checked = agreed = short = unresolved = 0
    diverged = 0
    for sec in SECTIONS:
        if sec["level"] != 2 or sec["setup"] or not sec["plies"]:
            continue
        parent = parent_of(sec)
        if parent is None or parent["setup"]:
            continue
        need = prefix_len(parent, sec)
        if need == 0 or need > len(parent["plies"]):
            continue

        # Where the parent stands at the branch move.
        # The parent's own line, as far as the branch move.
        san, _, _, _ = best_replay(parent["plies"][:need],
                                   parent["plies"][0][0],
                                   pinned_for(slug(parent["title"])))
        if len(san) < need:
            short += 1
            continue
        board = chess.Board()
        for mv in san:
            board.push_san(mv)

        checked += 1
        # The back-game's first ply must be playable from that position.
        side = sec["plies"][0][0]
        swap = parent["plies"][0][0] == "B"
        want = chess.WHITE if (side == "W") != swap else chess.BLACK
        if board.turn != want:
            print("SIDE   %-46s branch at move %d" % (sec["title"][:46], sec["first_move"]))
            continue
        try:
            cands = ply_candidates(board, sec["plies"][0][1])
        except Unparsed:
            unresolved += 1
            continue
        if cands:
            agreed += 1
            # A back-game should leave the parent's line, not repeat it.
            if need < len(parent["plies"]):
                parent_next = san[need - 1] if need else None
                if len(cands) == 1 and board.san(cands[0]) != parent_next:
                    diverged += 1
        else:
            print("ILLEGAL %-45s move %d: %s"
                  % (sec["title"][:45], sec["first_move"], sec["plies"][0][1][:60]))

    print("\nback-games whose parent replays to the branch move: %d" % checked)
    print("  branch move legal in the parent's position:        %d" % agreed)
    print("  first ply could not be parsed (no verdict):        %d" % unresolved)
    print("  parent did not replay that far (no verdict):       %d" % short)


if __name__ == "__main__":
    main()
