"""What the search is worth, measured rather than asserted.

How each ply was settled is recorded in games.json by the converter itself.
What that record cannot show is whether the search earns its keep, so this
replays every game a second way -- greedily, taking the first reading at every
ply and never backtracking -- and compares. The gap is what depth-first search
buys: plies it reaches that greedy cannot, and plies where greedy would have
played something else.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import collections  # noqa: E402
import json  # noqa: E402

import chess  # noqa: E402

from games import (HOW, MIRROR, SECTIONS, replay_section,  # noqa: E402
                   start_board)
from to_algebraic import (Unparsed, advance_origins,  # noqa: E402
                          initial_origins, ply_readings)


def greedy(sec):
    """Replay taking the first reading every time, never backtracking.

    Returns how many plies it managed before dying, and how many of those
    match the reading the search settled on.
    """
    san, _, _, _, line, _, _ = replay_section(sec)
    board = start_board(sec) or chess.Board()
    origins = initial_origins()
    prev, agreed = None, 0
    for i in range(min(len(san), len(line))):
        text = line[i][1]
        if MIRROR.search(text) and prev is not None:
            mirror = chess.Move(chess.square_mirror(prev.from_square),
                                chess.square_mirror(prev.to_square))
            cands = [(mirror, 0)] if mirror in board.legal_moves else []
        else:
            try:
                cands = ply_readings(board, text, origins)
            except Unparsed:
                return i, agreed
        if not cands:
            return i, agreed
        mv = cands[0][0]
        if board.san(mv) == san[i]:
            agreed += 1
        origins = advance_origins(origins, board, mv)
        board.push(mv)
        prev = mv
    return min(len(san), len(line)), agreed


def main():
    recs = json.load(open("games.json"))
    tally = collections.Counter(h for r in recs for h in r["ply_decided"])
    converted = sum(len(r["san"]) for r in recs)
    total = sum(len(r["plies"]) for r in recs)
    inherited = sum(r["inherited_plies"] for r in recs)

    print("%d plies of text, %d converted, %d of those inherited from a parent"
          % (total, converted, inherited))
    print("so %d distinct positions were read from the page\n"
          % (converted - inherited))

    for key in HOW:
        print("%-12s %6d  %5.1f%%"
              % (key, tally[key], 100.0 * tally[key] / converted))

    reached = agreed = died = diverged = 0
    for sec in SECTIONS:
        san, _, _, _, _, _, _ = replay_section(sec)
        n, ok = greedy(sec)
        reached += n
        agreed += ok
        died += n < len(san)
        diverged += ok < n

    print("\ngreedy: first reading every time, no backtracking")
    print("  reaches %d of %d plies, dying in %d games" % (reached, converted, died))
    print("  and plays a different move at %d of them, across %d games"
          % (reached - agreed, diverged))
    print("  so the search is what settles %d plies and corrects %d"
          % (converted - reached, reached - agreed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
