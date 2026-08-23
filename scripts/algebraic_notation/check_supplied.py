"""Check the positions supplied by hand in missing.json against the board.

These were read off the page by the maintainer, independently of the parser,
for four studies that had no board at the time. Three of the four turned out
not to be needed -- the text gives those positions once it is read properly --
which makes them something better than a patch: a second pair of eyes on what
the parser produces.

So they are kept and checked rather than thrown away. Each must be a legal
position, and must either be the one the study starts from or a position the
game actually reaches.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import json
import os

import chess

from build import slug
from games import SECTIONS, replay_section, start_board

SUPPLIED = "missing.json"


def main():
    if not os.path.exists(SUPPLIED):
        print("no %s: nothing supplied by hand." % SUPPLIED)
        return 0

    supplied = json.load(open(SUPPLIED))
    by_slug = {slug(sec["title"]): sec for sec in SECTIONS}
    problems = 0

    for name, fen in sorted(supplied.items()):
        print(name)
        sec_for_text = by_slug.get(name)
        if not fen.strip():
            # An entry left blank is a position still wanted, not a failure.
            derived = start_board(sec_for_text) if sec_for_text else None
            print("   awaiting a position. What the text gives, for comparison:")
            print("      %s" % (derived.fen() if derived else "nothing readable"))
            continue
        board = chess.Board(fen)
        if board.status() != chess.STATUS_VALID:
            print("   FAILS: %s" % board.status())
            problems += 1
            continue
        sec = by_slug.get(name)
        if sec is None:
            print("   FAILS: no such game")
            problems += 1
            continue

        wanted = set()
        for word, kind in (("queen", chess.QUEEN), ("rook", chess.ROOK),
                           ("bishop", chess.BISHOP), ("knight", chess.KNIGHT),
                           ("pawn", chess.PAWN)):
            if word in sec["title"].lower():
                wanted.add(kind)
        present = {p.piece_type for p in board.piece_map().values()}
        stray = wanted - present
        if wanted and stray:
            print("   FAILS: the title names %s, and the board has none"
                  % ", ".join(sorted(chess.piece_name(k) for k in stray)))
            problems += 1
            continue

        start = start_board(sec)
        if start is not None and start.board_fen() == board.board_fen():
            print("   agrees with the position the study starts from")
            continue

        # Not the start: is it a position the game passes through?
        san, _, _, _, _, _, _ = replay_section(sec)
        walk = start.copy() if start else chess.Board()
        found = None
        for i, move in enumerate(san):
            walk.push_san(move)
            if walk.board_fen() == board.board_fen():
                found = i + 1
                break
        if found:
            print("   agrees with the position after ply %d of the replay" % found)
        else:
            print("   DISAGREES: neither the starting position nor one the "
                  "game reaches")
            print("      supplied : %s" % board.board_fen())
            print("      from text: %s" % (start.board_fen() if start else "-"))
            problems += 1

    print("\n%d supplied positions disagree with the board" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
