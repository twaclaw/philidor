"""Collate the 1777 text against the 1790 edition, game by game.

The two editions print the same games in different words -- 1777 spells out
"The king's pawn, two moves", 1790 abbreviates it "The K. P. two moves" -- so
both are reduced to a canonical token sequence before comparing.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import re

from build import parse_all
from extract import normalise

# 1777 section title -> line where the matching game starts in philidor1.txt.
PAIRS = {
    "First Party": 321,
    "Second Party": 727,
    "Third Party": 1173,
    "Fourth Party": 1713,
    "Second Gambit": 2670,
    "Third Gambit": 3280,
    "Cunningham's Gambit": 3782,
    "Method of Playing": 5447,          # 1790: First Regular Party
    "First Variable": 5873,             # 1790: Second Regular Party
    "Second Variable": 6016,            # 1790: Third Regular Party
    "Third Variable": 6384,             # 1790: Fourth Regular Party
    "Fourth Variable": 6577,            # 1790: Fifth Regular Party
    "Another Method of Playing": 6756,  # 1790: Sixth Regular Party
}

NAMES1 = {
    "First Party": "First Party",
    "Second Party": "Second Party",
    "Third Party": "Party (third)",
    "Fourth Party": "Fourth Party",
    "Second Gambit": "Second Gambit",
    "Third Gambit": "Third Gambit",
    "Cunningham's Gambit": "Cunningham Gambit",
    "Method of Playing": "First Regular Party",
    "First Variable": "Second Regular Party",
    "Second Variable": "Third Regular Party",
    "Third Variable": "Fourth Regular Party",
    "Fourth Variable": "Fifth Regular Party",
    "Another Method of Playing": "Sixth Regular Party",
}

WORDS = [
    (r"\bking'?s?\b|\bK'?s?\b", "K"), (r"\bqueen'?s?\b|\bQ'?s?\b", "Q"),
    (r"\bbishop'?s?\b|\bB'?s?\b", "B"), (r"\bknight'?s?\b|\bKt'?s?\b", "N"),
    (r"\brook'?s?\b|\bR'?s?\b", "R"), (r"\bpawn'?s?\b|\bP'?s?\b", "P"),
    (r"\btakes\b", "x"), (r"\bretakes\b", "x"), (r"\bcastles\b", "0"),
    (r"\bcheck\b", "+"), (r"\bsame\b", "="),
    (r"\btwo\b", "2"), (r"\bone\b", "1"),
    (r"\bfirst\b", "1"), (r"\bsecond\b", "2"), (r"\bthird\b", "3"),
    (r"\bfourth\b", "4"), (r"\bfifth\b", "5"), (r"\bsixth\b", "6"),
    (r"\bhome\b", "1"), (r"\bown\b", ""),
]


def canon(text: str) -> str:
    # Keep only the move phrase: drop the note reference and anything the
    # scanner ran on after it.
    t = re.split(r"[({\[]", text, maxsplit=1)[0].lower()
    t = re.sub(r"\badvers\w*\b|\bhis\b|\bher\b|\bits\b|\bthe\b|\bat\b|\bof\b"
               r"|\bmoves?\b|\bsteps?\b|\bsquare\b|\bplace\b|\bgives\b"
               r"|\bwhite\b|\bblack\b|\band\b|\bin\b|\bto\b", " ", t)
    for pat, rep in WORDS:
        t = re.sub(pat, rep, t, flags=re.I)
    # Only the piece/action alphabet survives; prose letters are scanner spill.
    return re.sub(r"[^KQBNRPX0-6+=]", "", t.upper())[:8]


SIDE1 = re.compile(r"^(?:Wh|Bl|BI|Ih|Nb|VI|V|W|B|N|A)\s*[.,'’]\s*(.*)$")
# Marks a move phrase as finished, so a following line is prose, not more move.
COMPLETE = re.compile(r"\b(square|move|moves|step|steps|castles|check|mate)\b", re.I)


def philidor1_plies(start: int, limit: int = 420):
    """Read the 1790 text's moves, which the scan breaks across lines."""
    # Slice before normalising: normalise() rejoins hyphenated line breaks,
    # which would shift every line number.
    raw_lines = open(philidorpath.source("philidor1.txt")).read().split("\n")[start - 1:start + limit]
    lines = normalise("\n".join(raw_lines)).split("\n")
    plies: list[str] = []
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("##"):
            continue
        m = SIDE1.match(s)
        if m:
            plies.append(m.group(1))
        elif plies and not COMPLETE.search(plies[-1]) and re.match(r"^[A-Za-z]", s):
            # Only join while the move phrase is still unfinished, or the
            # 1790 scan's note paragraphs get swallowed into the move.
            plies[-1] += " " + s
    # A move phrase is short; a long one is a note the scan ran into the move.
    plies = [p for p in plies if len(p.split()) <= 12]
    return [c for c in (canon(p) for p in plies) if 1 < len(c) <= 8]


def alike(x: str, y: str) -> bool:
    """Two moves agree if one reading is a prefix of the other.

    The 1790 scan runs the note reference onto the end of the move ("KBQN30"
    for KBQN3) and truncates others, so exact equality is too strict.
    """
    n = min(len(x), len(y))
    return n >= 3 and x[:n] == y[:n]


def similarity(a: list[str], b: list[str]) -> float:
    """Fraction of the shorter sequence covered by a longest common subsequence."""
    if not a or not b:
        return 0.0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if alike(x, y) else max(cur[j], prev[j + 1]))
        prev = cur
    return prev[-1] / min(len(a), len(b))


def main():
    secs = {s["title"]: s for s in parse_all()}
    print("%-28s %-26s %5s %5s  %s" % (
        "1777 game", "1790 counterpart", "plies", "plies", "agreement"))
    for title, line in PAIRS.items():
        a = [canon(t) for _, t in secs[title]["plies"]]
        b = philidor1_plies(line)
        score = similarity(a, b)
        flag = "ok" if score >= 0.60 else "<-- CHECK"
        print("%-28s %-26s %5d %5d  %4.0f%%  %s" % (
            title, NAMES1[title], len(a), len(b), score * 100, flag))


if __name__ == "__main__":
    main()
