"""Find the places where Philidor's own notation contradicts itself.

Descriptive notation is a system, but Philidor does not apply it uniformly, and
every rule the converter follows had to be softened to fit him. This gathers
the evidence for each: which games, which moves, and what he wrote.

Run it to regenerate the citations quoted in the README.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import collections
import re

import chess

from build import parse_all
from games import SECTIONS, replay_section, replayable, start_board
from to_algebraic import (FILES, advance_origins, find_move, home_file,
                          initial_origins, parse_square, piece_and_wing,
                          Unparsed)

FILE_NAME = {v: k for k, v in FILES.items()}


def pawn_naming():
    """Pawns that have captured across: named for which file?

    A pawn that captures changes file. Philidor sometimes goes on calling it by
    the file it came from, and sometimes by the one it now stands on.
    """
    found = collections.defaultdict(list)
    for sec in SECTIONS:
        if not replayable(sec):
            continue
        san, _, _, _, line, first, inherited = replay_section(sec)
        board, origins = start_board(sec) or chess.Board(), initial_origins()
        for i, move in enumerate(san):
            mv = board.parse_san(move)
            piece = board.piece_at(mv.from_square)
            if piece and piece.piece_type == chess.PAWN:
                now = chess.square_file(mv.from_square)
                came = origins.get(mv.from_square, now)
                if came != now:
                    text = line[i][1]
                    try:
                        ptype, _, hint, _ = piece_and_wing(
                            re.sub(r"^the\s+", "", text.lower()))
                    except Unparsed:
                        ptype, hint = None, None
                    if ptype == chess.PAWN and hint is not None:
                        kind = ("origin" if hint == came
                                else "standing" if hint == now else None)
                        if kind:
                            found[kind].append({
                                "game": sec["title"],
                                "move": (1 if inherited
                                         else sec["first_move"]) + i // 2,
                                "side": "White" if i % 2 == 0 else "Black",
                                "text": text,
                                "played": move,
                                "from": chess.square_name(mv.from_square),
                                "began": FILE_NAME[came],
                                "stands": FILE_NAME[now],
                            })
            origins = advance_origins(origins, board, mv)
            board.push(mv)
    return found


def unreachable_pieces():
    """Plies where the reading had to override the text, and why.

    Two very different things end up here. Either the sentence names a piece
    that cannot reach the square it also names, though another piece of the
    same kind can -- a contradiction in the text itself. Or nothing of that
    kind can reach it, which usually means the reading went wrong earlier and
    the position is not the one Philidor was looking at.
    """
    out = []
    for sec in SECTIONS:
        if not replayable(sec):
            continue
        san, _, _, overrides, line, first, inherited = replay_section(sec)
        for ply in overrides:
            if ply - 1 >= len(line):
                continue
            board, origins = start_board(sec) or chess.Board(), initial_origins()
            for move in san[:ply - 1]:
                mv = board.parse_san(move)
                origins = advance_origins(origins, board, mv)
                board.push(mv)
            verdict = "unresolved"
            text = line[ply - 1][1]
            try:
                ptype, wing, hint, end = piece_and_wing(
                    re.sub(r"^the\s+", "", text.lower()))
                dest, _ = parse_square(text.lower()[end:], wing or "king",
                                       board.turn == chess.WHITE, ptype, None)
                reaching = find_move(board, ptype, dest) if dest else []
                if reaching and hint is not None:
                    # The contradiction is only real when the piece he names
                    # cannot get there and another of the same kind can. If
                    # the named piece could have gone, the override happened
                    # for some later reason and says nothing about his usage.
                    named = [mv for mv in reaching
                             if home_file(mv.from_square, origins) == hint]
                    if not named:
                        verdict = "the text contradicts itself"
            except Unparsed:
                pass
            out.append({
                "verdict": verdict,
                "game": sec["title"],
                "move": (1 if inherited else sec["first_move"])
                        + (ply - 1) // 2,
                "side": "White" if (ply - 1) % 2 == 0 else "Black",
                "text": text,
                "played": san[ply - 1] if ply - 1 < len(san) else "?",
            })
    return out


def wording():
    """The several ways he points at the opponent's side of the board."""
    counts = collections.Counter()
    example = {}
    for sec in SECTIONS:
        for _, text in sec["plies"]:
            for pattern, name in (
                    (r"\badversary's\b", "adversary's"),
                    (r"\badverse\b", "adverse"),
                    (r"\bblack\b", "the colour (black)"),
                    (r"\bwhite\b", "the colour (white)")):
                if re.search(pattern, text, re.I):
                    counts[name] += 1
                    example.setdefault(name, (sec["title"], text))
    return counts, example


def repeated_note_letters():
    """Games where one letter is used for two different notes."""
    out = []
    for sec in parse_all():
        seen = collections.Counter()
        for note in sec["notes"]:
            m = re.match(r"\(([a-z]{1,2})\)", note)
            if m:
                seen[m.group(1)] += 1
        for letter, n in seen.items():
            if n > 1:
                out.append((sec["title"], letter, n))
    return out


def same_forms():
    """"The same" standing alone, and hung on the end of a piece."""
    alone, attached = [], []
    for sec in SECTIONS:
        for _, text in sec["plies"]:
            if re.fullmatch(r"the same\.?", text.strip(), re.I):
                alone.append((sec["title"], text))
            elif re.search(r",\s*the same\b", text, re.I):
                attached.append((sec["title"], text))
    return alone, attached


def main():
    print("=" * 72)
    print("1. A pawn that has captured: named for the file it began on, or")
    print("   the file it stands on?")
    print("=" * 72)
    naming = pawn_naming()
    for kind, label in (("origin", "named for where it BEGAN"),
                        ("standing", "named for where it STANDS")):
        rows = naming[kind]
        print("\n%s — %d instances" % (label, len(rows)))
        for r in rows[:4]:
            print("   %s, move %d %s" % (r["game"], r["move"], r["side"]))
            print('      "%s"  ->  %s (pawn on %s, began on the %s file)'
                  % (r["text"], r["played"], r["from"], r["began"]))

    print("\n" + "=" * 72)
    print("2. Where the reading had to override the text")
    print("=" * 72)
    rows = unreachable_pieces()
    for verdict, label in (
            ("the text contradicts itself",
             "the piece he names cannot reach the square he names,\n"
             "   though another of the same kind can"),
            ("unresolved",
             "the override has some other cause: the faithful reading exists\n"
             "   but leads nowhere, so the divergence is earlier or later")):
        picked = [r for r in rows if r["verdict"] == verdict]
        print("\n   %s — %d" % (label, len(picked)))
        for r in picked[:5]:
            print("      %s, move %d %s" % (r["game"], r["move"], r["side"]))
            print('         "%s"  ->  read as %s' % (r["text"], r["played"]))

    print("\n" + "=" * 72)
    print("3. Four ways of pointing at the opponent's side")
    print("=" * 72)
    counts, example = wording()
    for name, n in counts.most_common():
        game, text = example[name]
        print("   %-22s %4d plies   e.g. %s" % (name, n, text[:52]))

    print("\n" + "=" * 72)
    print("4. One letter, two notes")
    print("=" * 72)
    for game, letter, n in repeated_note_letters():
        print("   %s: (%s) used %d times" % (game, letter, n))

    print("\n" + "=" * 72)
    print('5. "The same", two constructions')
    print("=" * 72)
    alone, attached = same_forms()
    print("   standing alone      %4d plies   e.g. %s" % (len(alone), alone[0][1]))
    print("   hung on a piece     %4d plies   e.g. %s"
          % (len(attached), attached[0][1] if attached else "-"))


if __name__ == "__main__":
    main()
