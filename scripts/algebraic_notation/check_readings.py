"""Check the moves settled by hand in readings.py.

A hand-settled move has to earn its place. It must be legal in the position it
claims, the game must actually reach that ply, and it must leave the game no
worse off than before. This proves all three against the board.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import chess

from build import slug
from games import SECTIONS, full_line, replay_section
from readings import POSITIONS, READINGS, reason_for
from replay_search import best_replay


def main():
    by_game = {}
    for (game, ply) in READINGS:
        by_game.setdefault(game, []).append(ply)

    problems = 0
    for name, (fen, why) in sorted(POSITIONS.items()):
        board = chess.Board(fen)
        ok = board.status() == chess.STATUS_VALID
        print("position %s\n   %s -> %s" % (name, fen, "stands up" if ok
                                             else "FAILS: %s" % board.status()))
        problems += not ok
        if len(why) < 20:
            print("   FAILS: no reason recorded")
            problems += 1
        sec = next((s for s in SECTIONS if slug(s["title"]) == name), None)
        if sec is None:
            print("   FAILS: no such game")
            problems += 1
        elif sec["setup"]:
            print("   note: the book prints a position for this game; the "
                  "supplied one is only used if that will not parse")

    if not READINGS:
        print("\nreadings.py pins no moves: every move is read from the page.")
        return 1 if problems else 0

    for sec in SECTIONS:
        name = slug(sec["title"])
        if name not in by_game:
            continue
        line, first, _ = full_line(sec)
        san, _, done, overrides, _, _, _ = replay_section(sec)
        # The same game read without any of the hand-settled moves.
        plain_san, _, plain_done, plain_overrides = best_replay(line, first)

        for ply in sorted(by_game[name]):
            move = READINGS[(name, ply)][0]
            print("%s, ply %d — %s" % (sec["title"], ply, move))

            if ply > len(line):
                print("   FAILS: the game has only %d plies" % len(line))
                problems += 1
                continue

            # Legal in the position it claims?
            board = chess.Board()
            for played in san[:ply - 1]:
                board.push_san(played)
            try:
                board.parse_san(move)
                print("   legal in that position")
            except ValueError:
                print("   FAILS: not a legal move there")
                problems += 1
                continue

            if ply - 1 >= len(san) or san[ply - 1] != move:
                print("   FAILS: the replay does not use it")
                problems += 1
                continue

            why = reason_for(name, ply)
            if not why or len(why) < 20:
                print("   FAILS: no reason recorded")
                problems += 1

        # It must not make the game worse than leaving it alone did.
        if len(san) < len(plain_san) or (plain_done and not done):
            print("   FAILS: %s reads further without these" % sec["title"])
            problems += 1
        elif len(san) > len(plain_san) or len(overrides) < len(plain_overrides):
            print("   the game reads further, or against the text less often,"
                  " than without them")

    print("\n%d problems" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
