"""Hold every move to what its own sentence claims about it.

Philidor does not only name a move, he often says what it does: that it gives
check, that it mates, that it takes a particular piece, that it covers a check.
Each of those is a statement the board can test, and a move that satisfies the
name while contradicting the claim is a warning that something is wrong --
usually the position it is being played from.

That is how the rook of "A Mate with a single Rook" was caught. The study opens
"The rook gives check", and from the square the scan gave it no rook check
existed at all; the reading was accepted anyway and the wrong board played on
quite happily for twenty-seven plies. This audit exists so the next one is
found by the machinery rather than by a reader.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import re

import chess

from games import SECTIONS, replay_section, start_board

PIECES = {"king": chess.KING, "queen": chess.QUEEN, "rook": chess.ROOK,
          "bishop": chess.BISHOP, "knight": chess.KNIGHT, "pawn": chess.PAWN}


# Philidor often speaks of a move other than this one: what he will play next,
# what he is avoiding, what he would have done. None of it is a claim about the
# move in hand.
ELSEWHERE = re.compile(
    r"\bafterwards?\b|\bfollowing move\b|\bnext move\b|\bto avoid\b"
    r"|\bwould\b|\bhad\b|\bif\b", re.I)


def claims(text):
    """What the sentence says the move does, as far as a board can judge."""
    low = text.lower()
    if ELSEWHERE.search(low):
        return {}
    out = {}
    # "Giving check to the rook" is an attack on a piece, not a check.
    if re.search(r"\bcheck\s+to\s+the\s+(?!king\b)\w+", low):
        return {}
    if re.search(r"\bcheck-?mate\b|\bmates?\b", low):
        out["mates"] = True
    elif re.search(r"\bgiv(?:es|ing)\s+check\b|\bchecks\s+the\b", low):
        out["checks"] = True
    if re.search(r"\bcovers the check\b", low):
        out["covers"] = True
    if re.search(r"\b(takes|retakes)\b", low):
        out["captures"] = True
        tail = re.split(r"\b(?:takes|retakes)\b", low, maxsplit=1)[1]
        # The piece taken is the last plain noun of the phrase.
        nouns = re.findall(r"\b(king|queen|rook|bishop|knight|pawn)\b('s)?", tail)
        plain = [n for n, poss in nouns if not poss]
        if plain:
            out["took"] = PIECES[plain[0]]
    if re.search(r"\bcastles\b", low):
        out["castles"] = True
    return out


def main():
    disagreements = []
    tested = 0

    for sec in SECTIONS:
        san, _, _, _, line, _, _ = replay_section(sec)
        board = start_board(sec) or chess.Board()
        for i, move in enumerate(san):
            text = line[i][1]
            said = claims(text)
            mv = board.parse_san(move)
            was_in_check = board.is_check()
            gives = board.gives_check(mv)
            captures = board.is_capture(mv)
            taken = (board.piece_at(mv.to_square).piece_type
                     if board.piece_at(mv.to_square) else
                     (chess.PAWN if board.is_en_passant(mv) else None))
            castles = board.is_castling(mv)
            board.push(mv)

            for what, ok in (
                    ("says it mates", not said.get("mates") or board.is_checkmate()),
                    ("says it checks", not said.get("checks") or gives),
                    ("says it covers a check", not said.get("covers") or was_in_check),
                    ("says it takes", not said.get("captures") or captures),
                    ("says it castles", not said.get("castles") or castles),
                    ("says which piece it takes",
                     "took" not in said or taken == said["took"])):
                tested += 1
                if not ok:
                    disagreements.append(
                        (sec["title"], i + 1, what, move, text))

    print("%d claims tested against the board" % tested)
    if not disagreements:
        print("every move does what its sentence says it does")
        return 0

    print("\n%d moves contradict their own sentence:\n" % len(disagreements))
    for title, ply, what, move, text in disagreements:
        print("%-44s ply %-3d %s" % (title[:44], ply, move))
        print("   %s, and it does not" % what)
        print('   "%s"' % text[:78])
    return 0


if __name__ == "__main__":
    sys.exit(main())
