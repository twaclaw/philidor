"""Audit the reconstructed games against the move numbers printed in the source.

The strongest check available: the printer set his own move numbers, so if our
pairing of plies into moves reproduces that sequence, the games are intact.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import re

from build import parse_all
from extract import number_moves

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}
# A move phrase should say what the piece did.
ACTION = re.compile(
    r"\b(square|move|moves|step|steps|castles?|check|mate|takes|retakes|same|"
    r"win|wins|won|lose|loses|lost|home|place|draw|game|advance)\b", re.I)


def read_number(s: str):
    tok = re.sub(r"[^0-9IVX]", "", s.upper())
    if tok.isdigit() and 0 < int(tok) < 100:
        return int(tok)
    return ROMAN.get(tok)


def main():
    short = half = drift = 0
    total_moves = total_plies = 0
    sections = parse_all()

    for sec in sections:
        title, plies = sec["title"], sec["plies"]
        moves = number_moves(plies, sec["first_move"],
                             plies[0][0] if plies else "W")
        total_moves += len(moves)
        total_plies += len(plies)

        for side, txt in plies:
            if not ACTION.search(txt) or len(txt) < 12:
                short += 1
                print("SHORT PLY   %-38s %s. %s" % (title[:38], side, txt[:66]))

        for i, (num, mv) in enumerate(moves):
            if len(mv) != 2 and i < len(moves) - 1:
                half += 1
                print("HALF MOVE   %-38s move %d: %s" % (title[:38], num, [s for s,_ in mv]))

        # Compare our numbering with the printer's, allowing for numbers the
        # scan mangled beyond recognition.
        printed = [n for n in (read_number(s) for s in sec["numbers"]) if n]
        ours = [n for n, _ in moves]
        if printed and ours:
            matched = len(set(printed) & set(ours))
            if matched < 0.8 * len(set(printed)):
                drift += 1
                print("NUMBERING   %-38s printed %s..%s  ours %s..%s (%d/%d agree)"
                      % (title[:38], printed[0], printed[-1], ours[0], ours[-1],
                         matched, len(set(printed))))

    print("\n%d sections, %d moves, %d plies" %
          (len(sections), total_moves, total_plies))
    print("short plies: %d   half moves: %d   numbering drift: %d"
          % (short, half, drift))


if __name__ == "__main__":
    main()
