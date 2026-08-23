"""Canonical per-game records: the single source of truth for everything built
downstream (PGN, Quarto pages, audits).

Deliberately richer than PGN, which cannot hold the descriptive original, the
note letters, the source line numbers or the editorial flags. PGN and the book
are both generated from these records, so improving the parser regenerates
everything rather than stranding hand-edits in a PGN file.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import json
import re

import chess

from build import parse_all, note_map, EDITORIAL  # noqa: F401
from readings import pinned_for, position_for
from replay_search import best_replay
from to_algebraic import (advance_origins, initial_origins, ply_readings,
                          position_board, Unparsed)

SECTIONS = parse_all()


def parent_of(sec):
    """The main game a back-game branches from."""
    i = SECTIONS.index(sec)
    for j in range(i - 1, -1, -1):
        if SECTIONS[j]["level"] == 1:
            return SECTIONS[j]
    return None


def prefix_len(parent, sec):
    """How many of the parent's plies precede the back-game.

    A back-game beginning "from the 12th move of the Black" resumes after White
    has already played his 12th, so it needs one ply more than the whole moves
    before it.
    """
    n = 2 * (sec["first_move"] - 1)
    if sec["plies"] and parent["plies"] and sec["plies"][0][0] != parent["plies"][0][0]:
        n += 1
    return n


def start_board(sec):
    """The position a game begins from: the opening, or a stated one.

    An endgame states its position, and a back-game branching off one starts
    from that same position and replays its parent up to the branch move.
    """
    owner = sec if sec["setup"] else (parent_of(sec) if sec["level"] == 2 else None)
    if owner is None:
        owner = sec
    supplied = position_for(slug(owner["title"]))
    if owner["setup"]:
        try:
            return position_board(owner["setup"], owner["plies"][0][0])
        except Unparsed:
            pass
    # Nothing printed, or nothing readable: fall back to a position given by
    # hand in readings.py.
    return chess.Board(supplied) if supplied else None


def full_line(sec):
    """The game as played from the opening, with any inherited prefix.

    Returns the plies, who moved first, and how many of them came from the
    parent -- the book shows those greyed, as context rather than text.
    """
    if sec["level"] == 1 or not sec["plies"]:
        return sec["plies"], (sec["plies"][0][0] if sec["plies"] else "W"), 0
    parent = parent_of(sec)
    if parent is None or not parent["plies"]:
        return sec["plies"], sec["plies"][0][0], 0
    need = prefix_len(parent, sec)
    if need <= 0 or need > len(parent["plies"]):
        return sec["plies"], sec["plies"][0][0], 0
    return parent["plies"][:need] + sec["plies"], parent["plies"][0][0], need


def replay_section(sec):
    """Replay one game the way the whole pipeline does.

    Every reader of a game -- the records, the audits, the reports -- goes
    through here, so none of them can drift from what is published.
    """
    line, first, inherited = full_line(sec)
    if not line:
        return [], "no moves", False, [], line, first, inherited
    san, reason, done, overrides = best_replay(
        line, first, pinned_for(slug(sec["title"])), start_board(sec))
    return san, reason, done, overrides, line, first, inherited


def replayable(sec):
    """Can this game be put on a board at all?

    Every game can, now that a stated position is read from the text like any
    other move -- except one whose position will not parse.
    """
    if sec["setup"] or (sec["level"] == 2 and (parent_of(sec) or {}).get("setup")):
        return start_board(sec) is not None
    return True


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


MIRROR = re.compile(r"\bthe same\b", re.I)

# How a ply came to be the move it is, in descending order of how much the
# text alone settles. Recorded per ply so a reader can weigh a game rather
# than take it whole: a move the position forced is not the same kind of
# claim as one the search chose between equals, which is not the same again
# as one it had to override the text to play.
HOW = ("forced", "mirrored", "chosen", "overridden")


def decisions(sec, san, line, overrides):
    """Label every accepted ply with how it was settled."""
    board = start_board(sec) or chess.Board()
    origins = initial_origins()
    out = []
    prev = None
    for i, mv_san in enumerate(san):
        text = line[i][1]
        if (i + 1) in overrides:
            how = "overridden"
        elif MIRROR.search(text) and prev is not None:
            how = "mirrored"
        else:
            try:
                plain = [mv for mv, tier in ply_readings(board, text, origins)
                         if tier == 0]
            except Unparsed:
                plain = []
            how = "forced" if len(plain) == 1 else "chosen"
        out.append(how)
        mv = board.parse_san(mv_san)
        origins = advance_origins(origins, board, mv)
        board.push(mv)
        prev = mv
    return out


def records():
    for sec in SECTIONS:
        plies, first, inherited = full_line(sec)
        san, reason, complete, overrides = ([], "no moves", False, [])
        how = []
        if plies:
            san, reason, complete, overrides, _, _, _ = replay_section(sec)
            how = decisions(sec, san, plies, overrides)
        yield {
            "title": sec["title"],
            "slug": slug(sec["title"]),
            "subtitle": sec["subtitle"],
            "level": sec["level"],
            "kind": "endgame" if sec["setup"] else
                    ("back-game" if sec["level"] == 2 else "game"),
            "parent": (parent_of(sec) or {}).get("title") if sec["level"] == 2 else None,
            "first_move": sec["first_move"],
            "first_side": first,
            "inherited_plies": inherited,
            "source_line": sec["start"],
            "position": sec["setup"],
            # Where the board starts, for a game that does not start at move 1.
            "start_fen": (start_board(sec).fen()
                          if start_board(sec) is not None else None),
            "plies": [{"side": s, "text": t} for s, t in plies],
            "notes": sec["notes"],
            "note_for_ply": {str(k): v for k, v in note_map(sec, inherited).items()},
            "san": san,
            "replay_complete": complete,
            "replay_stopped": reason,
            # Plies where the reading had to override what the text says
            # for the game to continue; empty means it was read as printed.
            "replay_overrides": overrides,
            # How each accepted ply was settled, one label per move of "san".
            "ply_decided": how,
            # Plies settled by hand in readings.py rather than read off the
            # page, so a reader can tell them from Philidor's own text.
            "editorial_readings": sorted(pinned_for(slug(sec["title"]))),
            "editorial": EDITORIAL.get(sec["title"]),
        }


def main():
    recs = list(records())
    with open("games.json", "w") as fh:
        json.dump(recs, fh, indent=1)
    done = sum(r["replay_complete"] for r in recs)
    print("wrote games.json: %d games, %d with a complete algebraic replay"
          % (len(recs), done))


if __name__ == "__main__":
    main()
