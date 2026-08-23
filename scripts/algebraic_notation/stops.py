"""Assemble the evidence at every point a game stops converting.

The parser gets a game as far as it can. Where it stops, this gathers what
anyone -- or any model -- would need to decide the move: the descriptive text,
the position, every legal move from it, the readings the parser was willing to
offer, and the note Philidor attached to that ply.

Notes are the evidence the converter itself never reads. Roughly a third of
them name a specific alternative move, keyed by their reference to an exact
ply, so they are a second telling of the game in prose.

Writes stops.json, and prints a report.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import json

import chess

from games import (SECTIONS, note_map, replay_section, replayable, slug,
                   start_board)
from to_algebraic import (Unparsed, advance_origins, initial_origins,
                          ply_readings)

OUT = "stops.json"


def board_at(san, start=None):
    """The position a line reaches, and the origin map that goes with it.

    A study begins from the position it states rather than from the opening,
    so the board it starts on is passed in, exactly as `games.decisions` does.
    """
    board = start or chess.Board()
    origins = initial_origins()
    for move in san:
        mv = board.parse_san(move)
        origins = advance_origins(origins, board, mv)
        board.push(mv)
    return board, origins


def dossier(sec):
    san, reason, done, overrides, line, first, inherited = replay_section(sec)
    if done and not overrides:
        return None

    i = len(san)
    board, origins = board_at(san, start_board(sec))
    notes = note_map(sec, inherited)

    text = line[i][1] if i < len(line) else ""
    try:
        offered = [board.san(mv) for mv, _ in ply_readings(board, text, origins)]
    except Unparsed as exc:
        offered = ["(unparsed: %s)" % exc]

    return {
        "game": sec["title"],
        "slug": slug(sec["title"]),
        "complete": done,
        "overrode_text_at": overrides,
        "stopped_at_ply": i + 1 if not done else None,
        # A back-game replays its parent first, so its board numbering
        # starts at 1 rather than at the move it branches from.
        "move_number": ((1 if inherited else sec["first_move"]) + i // 2
                        if not done else None),
        "side": ("White" if i % 2 == 0 else "Black") if not done else None,
        "reason": reason if not done else None,
        "text": text,
        "fen": board.fen(),
        "played_so_far": san,
        "preceding": [line[j][1] for j in range(max(0, i - 3), i)],
        "parser_offered": offered,
        "legal_moves": sorted(board.san(mv) for mv in board.legal_moves),
        # Philidor's own words about this ply and the ones around it.
        "notes_here": notes.get(i, []),
        "notes_nearby": [n for j in range(max(0, i - 3), i + 4)
                         for n in notes.get(j, []) if j != i],
    }


def main():
    stops = [d for d in (dossier(s) for s in SECTIONS if replayable(s)) if d]
    with open(OUT, "w") as fh:
        json.dump(stops, fh, indent=1)

    unfinished = [d for d in stops if not d["complete"]]
    print("%d games need a decision: %d stop short, %d completed only by "
          "reading against the text\n"
          % (len(stops), len(unfinished), len(stops) - len(unfinished)))
    for d in unfinished:
        print("%s — move %s, %s" % (d["game"], d["move_number"], d["side"]))
        print('   text     : "%s"' % d["text"])
        print("   offered  : %s" % ", ".join(d["parser_offered"][:8]))
        if d["notes_here"]:
            print("   note     : %s" % d["notes_here"][0][:150])
        print()
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
