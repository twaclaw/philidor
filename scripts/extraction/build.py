"""Build philidor.md from the OCR'd sources."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import re

from extract import (
    apply_letters, clean_lines, join_moves, join_notes, marker_glyphs,
    normalise, number_moves, parse_section, repair_letters,
    MOVENUM, MOVE_LINE,
)

SRC = philidorpath.source("philidor2.txt")

# (start_line, level, title, subtitle)
# Line numbers index philidor2.txt (1777 London edition).
SECTIONS = [
    # ---- Part I: the edition of 1749 -------------------------------------
    (218, 1, "First Party", "With two back-games; the first beginning from the 12th, and the second from the 37th move."),
    (583, 2, "First Back-game of the First Party", "Beginning to change from the 12th move of the Black."),
    (700, 2, "Second Back-game of the First Party", "Beginning from the 37th move."),
    (751, 1, "Second Party", "With three back-games: the first beginning from the 3d, another from the 8th, and the last from the 26th move."),
    (1040, 2, "First Back-game of the Second Party", "Beginning from the 3d move of the Black."),
    (1119, 2, "Second Back-game of the Second Party", "Beginning from the 8th move of the Black."),
    (1173, 2, "Third and Last Back-game of the Second Party", "Beginning at the 26th move of the Black."),
    (1219, 1, "Third Party", "Beginning with the Black. This game is not quite exact; but the first moves of the White are very well calculated, especially when some advantage is granted."),
    (1549, 2, "First Back-game of the Third Party", "Beginning at the 3d move of the Black."),
    (1667, 2, "Second Back-game of the Third Party", "Beginning at the 5th move of the Black."),
    (1717, 2, "Third Back-game of the Third Party", "Beginning from the 10th move of the Black."),
    (1809, 1, "Fourth Party", "With two back-games; one from the 5th, the other from the 6th move. Beginning with the Black."),
    (2052, 2, "First Back-game of the Fourth Party", "Beginning from the 5th move of the Black."),
    (2161, 2, "Second Back-game of the Fourth Party", "Beginning at the 6th move of the Black."),
    # ---- The gambits ------------------------------------------------------
    (2266, 1, "First Gambit", "With seven back-games; two at the 4th move, one at the 5th, one at the 6th, two at the 7th, and the last at the 8th move."),
    (2490, 2, "First Back-game of the First Gambit", "On the 4th move of the White."),
    (2564, 2, "Second Back-game of the First Gambit", "From the 4th move of the Black."),
    (2614, 2, "Third Back-game of the First Gambit", "On the 5th move of the Black."),
    (2652, 2, "Fourth Back-game of the First Gambit", "From the 6th move of the Black."),
    (2688, 2, "Fifth Back-game of the First Gambit", "From the 7th move of the Black."),
    (2716, 2, "Sixth Back-game of the First Gambit", "From the 7th move of the Black."),
    (2773, 2, "Seventh and Last Back-game of the First Gambit", "Beginning from the 8th move of the Black."),
    (2878, 1, "Second Gambit", "With four back-games; two from the 4th, one from the 9th, and the last from the 11th move."),
    (3132, 2, "First Back-game of the Second Gambit", "From the 4th move of the Black."),
    (3176, 2, "Second Back-game of the Second Gambit", "Beginning at the 4th move."),
    (3387, 2, "Third Back-game of the Second Gambit", "On the 8th move of the Black."),
    (3464, 2, "Fourth Back-game of the Second Gambit", "Beginning at the 11th move of the Black."),
    (3538, 1, "Third Gambit", "With three back-games; one beginning from the 2d, one from the 3d, and the last from the 11th move."),
    (3736, 2, "First Back-game of the Third Gambit", "At the 2d move of the Black."),
    (3858, 2, "Second Back-game of the Third Gambit", "Beginning at the 3d move of the Black."),
    (3953, 2, "Third Back-game of the Third Gambit", "At the 11th move of the Black."),
    (4049, 1, "Cunningham's Gambit", "With two back-games; one from the 7th, and the other at the 11th move."),
    (4326, 2, "First Back-game of Cunningham's Gambit", "On the 7th move of the Black."),
    (4359, 2, "Sequel to the First Back-game of Cunningham's Gambit", "At the 8th move of the Black."),
    (4429, 2, "Second Back-game of Cunningham's Gambit", "Beginning at the 11th move of the Black."),
    (4567, 1, "The Queen's Gambit", "Otherwise the Gambit of Aleppo. With six back-games."),
    (4887, 2, "First Back-game of the Queen's Gambit", "At the 3d move of the White."),
    (5027, 2, "Second Back-game of the Queen's Gambit", "At the 3d move of the Black."),
    (5132, 2, "Third Back-game of the Queen's Gambit", "At the 4th move of the White."),
    (5270, 2, "Fourth Back-game of the Queen's Gambit", "At the 7th move of the White."),
    (5312, 2, "Fifth Back-game of the Queen's Gambit", "At the 8th move of the Black."),
    (5484, 2, "Sixth Back-game of the Queen's Gambit", "At the 10th move of the White."),
    # ---- Supplement to the edition of 1749 --------------------------------
    (5549, 1, "Method of Playing", "Consisting of four variables and five back-games. (The 1790 edition prints this as the First Regular Party.)"),
    (5700, 2, "First Back-game of the Method of Playing", "Beginning at the 3d move of the Black."),
    (5753, 2, "Supplement to the First Back-game", "On the 4th move of the Black."),
    (5824, 2, "Second Back-game of the Method of Playing", "On the 4th move of the White."),
    (5843, 2, "Third Back-game of the Method of Playing", "On the 4th move of the White."),
    (5920, 2, "Fourth Back-game of the Method of Playing", "At the 5th move of the Black."),
    (5974, 2, "Fifth Back-game of the Method of Playing", "At the 6th move of the White."),
    (6021, 1, "First Variable", "On the 2d move of the Black. (The 1790 edition prints this as the Second Regular Party.)"),
    (6178, 1, "Second Variable", "On the 2d move of the Black. (The 1790 edition prints this as the Third Regular Party.)"),
    (6324, 2, "First Back-game of the Second Variable", "On the 3d move of the Black."),
    (6397, 2, "Second Back-game of the Second Variable", "On the 7th move of the Black."),
    (6526, 2, "Third Back-game of the Second Variable", "On the 11th move of the Black."),
    (6601, 1, "Third Variable", "On the 3d move of the Black. (The 1790 edition prints this as the Fourth Regular Party.)"),
    (6744, 2, "Back-game of the Third Variable", "On the 5th move of the White."),
    (6815, 1, "Fourth Variable", "At the 3d move of the Black. (The 1790 edition prints this as the Fifth Regular Party.)"),
    (6956, 2, "First Back-game of the Fourth Variable", "On the 3d move of the Black."),
    (7058, 1, "Another Method of Playing", "(The 1790 edition prints this as the Sixth Regular Party.)"),
    (7303, 1, "Gambit of Salvio", "With three back-games and a variable."),
    (7448, 2, "First Back-game of the Gambit of Salvio", "On the 7th move of the White, with a variable on the 7th move of the Black."),
    (7567, 2, "Variable of the First Back-game of the Gambit of Salvio", "On the 7th move of the Black."),
    (7642, 2, "Second Back-game of the Gambit of Salvio", "On the 7th move of the White."),
    (7662, 2, "Third Back-game of the Gambit of Salvio", "On the 8th move of the Black."),
    (7756, 1, "Supplement to the First Gambit of the Edition of 1749", ""),
    (7885, 2, "Back-game of the Supplement to the First Gambit", "On the 6th move of the White."),
    (7966, 2, "Variable of the same Party of the Gambit", "On the 5th move of the Black."),
    # ---- Ends of games ----------------------------------------------------
    (8028, 1, "Method of giving Check-mate with a Rook and a Bishop against a Rook", ""),
    (8128, 2, "First Back-game (Rook and Bishop against a Rook)", "On the 4th move of the Black."),
    (8177, 2, "Second Back-game (Rook and Bishop against a Rook)", "On the 5th move of the Black."),
    (8235, 2, "Third Back-game (Rook and Bishop against a Rook)", "On the 7th move of the Black."),
    (8268, 1, "Method of forcing the Black to take the above-mentioned Situation", "In order to give mate with a Rook and Bishop against a Rook."),
    (8384, 2, "Back-game (forcing the Situation)", "On the 7th move of the Black."),
    (8466, 1, "Method of giving Check-mate with a Bishop and a Knight", ""),
    (8630, 2, "Back-game (Check-mate with a Bishop and a Knight)", "On the 11th move of the Black."),
    (8701, 1, "A Party won with a Rook and a Pawn against a Bishop", ""),
    (8763, 1, "A Drawn-game with a Rook and a Pawn against a Bishop", ""),
    (8885, 1, "A Mate with a single Rook", ""),
    (8987, 1, "A Game won with a Queen against a Rook and a Pawn", ""),
    (9183, 2, "First Back-game (Queen against a Rook and a Pawn)", "On the 9th move of the Black."),
    (9221, 2, "Second Back-game (Queen against a Rook and a Pawn)", "On the 15th move of the Black."),
    (9247, 2, "A Check-mate with a Queen against a Rook", "By way of back-game, beginning at the 24th move of the White."),
    (9399, 1, "A Drawn-game with a Queen against a Rook and a Pawn", ""),
    (9436, 1, "A Drawn-game with a Rook and a Pawn against a Rook", "Or lost game, if he who has only a Rook plays ill."),
    (9513, 2, "Back-game (Rook and Pawn against a Rook)", "On the 1st move of the Black, when a Rook and a Pawn win against a Rook."),
    (9669, 1, "A Drawn-game of a Queen and a Pawn against a Queen", ""),
    (9739, 1, "A Game won with a Queen against a Pawn near making a Queen", ""),
    (9832, 1, "A Drawn-game with a Queen against a Pawn near making a Queen", ""),
    (9871, 1, "Another Drawn-game with a Queen against a Pawn near making a Queen", ""),
    (9914, 1, "A Drawn-game with a single Pawn", "Or a game won, if he who remains with his King alone does not play well."),
    (9996, 2, "Back-game (a Drawn-game with a single Pawn)", "On the 4th move of the Black."),
    (10024, 1, "A Drawn-game of a Knight far off from his King, against a Pawn near making a Queen", ""),
    (10074, 1, "A Drawn-game, or a Party won, with two Pawns against one", ""),
    (10128, 2, "First Back-game (two Pawns against one)", "On the 1st move of the Black."),
    (10177, 2, "Second Back-game (two Pawns against one)", "On the 2d move of the Black."),
    (10270, 1, "A Drawn-game with two separated Pawns against two united Pawns", ""),
]

END_OF_GAMES = 10329  # "OBSERVATIONS ON THE ENDS OF PARTIES" follows

# Corrections to the printed text itself, keyed by line in philidor2.txt.
# Listed here rather than applied quietly, so each can be checked.
ERRATA = {
    # The second ply of move 8 is set "W." for both sides; it is Black's king
    # answering the check, as the note and Black's move 9 confirm.
    8195: "B. The king, at his biſhop's ſquare. (b)",
    # "at its king's ſquare" leaves the rook on e1, from where the first move
    # of the study -- "The rook gives check" -- is not possible: the white king
    # on e4 stands between it and the black king on e6. On the king's rook's
    # square it is Rh6+, which is a check, and the scan has dropped a word.
    # Noticed by a reader comparing another edition.
    8889: "The rook, at its king's rook's ſquare.",
}

# Places where the source is defective and no reconstruction is possible.
EDITORIAL = {
    "Seventh and Last Back-game of the First Gambit":
        "The 1777 text sets two White moves at 30 and omits both Black's reply "
        "and the number 31, so the mating move is shown as White's second. "
        "Black's 30th move is lost.",
    "Another Method of Playing":
        "The editions disagree at Black's 4th move. 1777 reads \"the queen's "
        "pawn, one move\" (d6), as transcribed here; 1790 reads \"two moves\" "
        "(d5), which is also the reading in modern transcriptions of this game "
        "and the move the following play assumes. Treat 1777 as a misprint.",
}

GROUPS = [
    (218, "Part I — The Edition of 1749",
     "The four parties and five gambits of Philidor's original *Analyse*, each "
     "followed by its back-games: alternative continuations branching from a "
     "numbered move of the main game."),
    (5549, "Supplement to the Edition of 1749",
     "New material first printed in 1777. The 1790 edition reorganises these "
     "under the heading *Regular Parties*; the correspondence is noted on each game."),
    (8028, "Ends of Games",
     "Endgame studies. Each begins from a stated position rather than from the "
     "opening move."),
]


def sections():
    lines = open(SRC).read().split("\n")
    for n, replacement in ERRATA.items():
        lines[n - 1] = replacement
    bounds = [s[0] for s in SECTIONS] + [END_OF_GAMES]
    for i, (start, level, title, subtitle) in enumerate(SECTIONS):
        body = "\n".join(lines[start - 1:bounds[i + 1] - 1])
        yield start, level, title, subtitle, normalise(body)


def rebalance_notes(parsed):
    """Give back the notes that the printer set after the following heading.

    A note block often runs past the next game's title, so the tail of one
    game's notes is scanned as the head of the next game's. Where a section is
    short of notes for the references it carries, take that many from the front
    of the next section.
    """
    for i in range(1, len(parsed)):
        prev, cur = parsed[i - 1], parsed[i]
        deficit = prev["n_refs"] - len(prev["notes"])
        if deficit > 0 and cur["notes"]:
            take = min(deficit, len(cur["notes"]))
            prev["notes"] += cur["notes"][:take]
            cur["notes"] = cur["notes"][take:]
    return parsed


def fix_markers(setup, plies, notes):
    """Restore the (a) (b) (c) cross-references on the moves and the notes.

    The two sequences spell out the same letters, so when they are the same
    length we repair one and copy it to the other; that keeps a move's
    reference and its note in agreement even where the scan is poor. When the
    lengths differ -- the scanner dropped a marker -- each is repaired on its
    own. In the endgames the first reference often sits on a line of the
    opening position, so the setup block is part of the same sequence.
    """
    ref_texts = setup + [t for _, t in plies]
    ref_glyphs = marker_glyphs(ref_texts, anchored=False)
    note_glyphs = marker_glyphs(notes, anchored=True)

    if ref_glyphs and len(ref_glyphs) == len(note_glyphs):
        ref_letters = note_letters_ = repair_letters(note_glyphs)
    else:
        ref_letters = repair_letters(ref_glyphs)
        note_letters_ = repair_letters(note_glyphs)

    fixed = apply_letters(ref_texts, ref_letters, anchored=False)
    setup = fixed[:len(setup)]
    plies = [(s, t) for (s, _), t in zip(plies, fixed[len(setup):])]
    notes = apply_letters(notes, note_letters_, anchored=True)
    return setup, plies, notes


def split_setup(lines):
    """Pull a 'Situation of the White/Black' block off the front of a section."""
    setup, i = [], 0
    if not any(l.startswith("Situation of the") for l in lines[:12]):
        return [], lines
    while i < len(lines):
        s = lines[i]
        if MOVENUM.match(s) or MOVE_LINE.match(s):
            break
        # Page furniture strayed into the position: a signature mark, a
        # catchword, a scrap of another script. A line of the position always
        # names a piece.
        if not s.startswith("Situation") and not SETUP_LINE.search(s):
            i += 1
            continue
        # The lines of a position wrap just as the moves do.
        if setup and not s.startswith("Situation") and not setup[-1].endswith("."):
            setup[-1] += " " + s
        else:
            setup.append(s)
        i += 1
    setup = [tidy_setup(s) for s in setup if len(s) > 3]
    return setup, lines[i:]


# A line of a stated position names a piece, or carries the square a wrapped
# line ran on to. Anything else is page furniture.
SETUP_LINE = re.compile(
    r"\b(king|queen|rook|bishop|knight|pawn)s?\b|\b(square|place|home)\b", re.I)


def tidy_setup(line):
    """Clean a line of a stated position.

    The scans put a signature letter at the end of a printed line, which the
    wrap then buries mid-sentence: "at the adverse king's bishop's fourth K
    square". It has to go, or the ordinal cannot be read.
    """
    line = re.sub(r"\s+([,.])", r"\1", line)
    line = re.sub(r"\b([a-z]+)\s+[A-Z]\s+(square|place)\b", r"\1 \2", line)
    return re.sub(r"\s{2,}", " ", line).strip()


ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}


def first_printed(numbers, expect):
    """The move number the game actually opens on, as the printer set it.

    Stray "1"s from the scan sit above real numbers, so a candidate counts only
    if it is the number the heading led us to expect, or it starts an ascending
    run of its own.
    """
    seen = []
    for s in numbers[:4]:
        tok = re.sub(r"[^0-9IVX]", "", s.upper())
        if tok.isdigit() and 0 < int(tok) < 100:
            seen.append(int(tok))
        elif tok in ROMAN:
            seen.append(ROMAN[tok])
    for i, n in enumerate(seen):
        if n == expect:
            return n
        if i + 1 < len(seen) and seen[i + 1] == n + 1:
            return n
    return None


def parse_all():
    """Parse every section, then settle the notes across section boundaries."""
    group_at = {g[0]: g for g in GROUPS}
    parsed = []
    for start, level, title, subtitle, text in sections():
        lines = clean_lines(text)
        # Drop the heading block itself: everything before the first move
        # number or "Situation of the" line.
        k = 0
        while k < len(lines) and not (
            MOVENUM.match(lines[k]) or MOVE_LINE.match(lines[k])
            or lines[k].startswith("Situation of the")
        ):
            k += 1
        setup, body = split_setup(lines[k:])
        cut = parse_section(body)
        plies = join_moves(cut["moves"])
        notes = join_notes(cut["notes"])

        # A back-game resumes its parent's numbering at the branch move; a main
        # game or endgame starts at 1.
        first_move = 1
        if level == 2:
            m = re.search(r"(\d+)(?:st|nd|rd|d|th)?\s+move", subtitle, re.I)
            if m:
                first_move = int(m.group(1))
        # Some sections headed "on the Nth move" nonetheless replay the game
        # from the start. Where the printer's own first number is legible,
        # it settles the question.
        numbers = [s for s in cut["moves"] if MOVENUM.match(s)]
        printed = first_printed(numbers, first_move)
        if printed in (1, first_move):
            first_move = printed

        parsed.append({
            "start": start, "level": level, "title": title,
            "subtitle": subtitle, "group": group_at.get(start),
            "setup": setup, "plies": plies, "notes": notes,
            "first_move": first_move,
            "numbers": [s for s in cut["moves"] if MOVENUM.match(s)],
            "n_refs": len(marker_glyphs(setup + [t for _, t in plies], False)),
        })
    parsed = rebalance_notes(parsed)
    # Repair the (a) (b) references here rather than at render time, so every
    # consumer -- the transcription, games.json, the PGN and the book -- sees
    # the same letters. Notes must be settled across sections first, since the
    # repair reads each section's sequence as a whole.
    for sec in parsed:
        sec["setup"], sec["plies"], sec["notes"] = fix_markers(
            sec["setup"], sec["plies"], sec["notes"])
    return parsed


def render():
    out = ["# Philidor — *Analysis of the Game of Chess*", ""]
    out += [
        "Every game, back-game and endgame set out in Philidor's *Analysis of the",
        "Game of Chess*, one section per game.",
        "",
        "**Sources.** The base text is the 1777 London edition printed for P. Elmsley",
        "(`philidor2.pdf`), whose scan is much the cleaner of the two. It has been",
        "collated against volume I of the 1790 \"new edition, improved and greatly",
        "enlarged\" (`philidor1.pdf`), which prints the same games but renames the",
        "supplement of 1777 as a series of *Regular Parties*; where the two editions",
        "differ in naming, both names are given. Everything in the 1790 volume is",
        "present in 1777, including the game it calls the Sixth Regular Party, which",
        "1777 heads *Another Method of Playing*.",
        "",
        "**Notation.** Philidor's descriptive notation is kept as printed. A main game",
        "is numbered from move 1; a back-game resumes its parent's numbering at the",
        "move where it branches, which is why several begin at move 4, 7 or 26. The",
        "lettered references on the moves point to the notes below them, and run",
        "a...i, k...u, w, x, y, the eighteenth-century sequence that omits *j* and *v*.",
        "",
        "**Editing.** The long *s* (\"ſame\", \"ſubject\") and the scanner's misreadings",
        "of it as *f* (\"fame\", \"fide\", \"loft\") are silently corrected, as are broken",
        "and run-together words; spelling is otherwise left as printed, so \"shews\",",
        "\"chuse\" and \"in the mean time\" stand as Philidor's translator had them.",
        "Running heads, page numbers and printers' signature marks are dropped. A few",
        "moves lack their lettered reference where the scan lost it, though the note",
        "itself is present.",
        "",
        "---",
        "",
    ]

    parsed = parse_all()

    out += ["## Contents", ""]
    for sec in parsed:
        if sec["group"]:
            out += ["", "**" + sec["group"][1] + "**", ""]
        anchor = re.sub(r"[^a-z0-9 -]", "", sec["title"].lower()).replace(" ", "-")
        indent = "" if sec["level"] == 1 else "    "
        out.append("%s- [%s](#%s)" % (indent, sec["title"], anchor))
    out += ["", "---", ""]

    for sec in parsed:
        if sec["group"]:
            _, gtitle, gdesc = sec["group"]
            out += ["", "## " + gtitle, "", gdesc, ""]
        out += section_markdown(sec, level=sec["level"] + 2)

    return "\n".join(out)


def section_markdown(sec, level=1):
    """One game as Markdown.

    Shared by the whole transcription and by the per-game files, so the two
    cannot drift: a game downloaded on its own is the same text as the section
    it comes from.
    """
    setup, plies, notes = sec["setup"], sec["plies"], sec["notes"]
    moves = number_moves(plies, sec["first_move"],
                         plies[0][0] if plies else "W")

    out = ["", "#" * level + " " + sec["title"], ""]
    if sec["subtitle"]:
        out += ["*" + sec["subtitle"] + "*", ""]
    for j, s in enumerate(setup):
        if s.startswith("Situation"):
            out += (["**" + s.rstrip(".") + "**", ""] if j == 0
                    else ["", "**" + s.rstrip(".") + "**", ""])
        else:
            out.append("- " + s)
    if setup:
        out.append("")
    for n, mv in moves:
        parts = ["**%s.** %s" % ("White" if side == "W" else "Black", txt)
                 for side, txt in mv]
        out.append("%d. %s" % (n, "  \n   ".join(parts)))
    if moves:
        out.append("")
    if notes:
        out += ["**Notes.**", ""]
        for n in notes:
            out.append("- " + n)
        out.append("")
    if sec["title"] in EDITORIAL:
        out += ["> **Editorial note.** " + EDITORIAL[sec["title"]], ""]
    return out


def note_map(sec, offset=0):
    """Which ply each lettered note belongs to, by its (a) (b) reference.

    `offset` is the inherited prefix, so the indices line up with the full line
    the book shows rather than with the section's own plies.

    This is a fact about the transcription, not about chess: Philidor keys each
    note to a move himself, and both the per-game files and the book rely on it.
    """
    out, letters = {}, []
    for i, (_, text) in enumerate(sec["plies"], start=offset):
        for ref in re.findall(r"\(([a-z]{1,2})\)", text):
            letters.append((ref, i))
    by_ref = dict(letters)
    for note in sec["notes"]:
        m = re.match(r"\(([a-z]{1,2})\)\s*(.*)", note, re.S)
        if m and m.group(1) in by_ref:
            out.setdefault(by_ref[m.group(1)], []).append(m.group(2).strip())
    return out


def strip_refs(text):
    """Drop the (a) (b) letters and tidy the punctuation behind them.

    Some are printed between two full stops -- "takes the bishop's pawn. (h)."
    -- so removing one leaves a double.
    """
    text = re.sub(r"\s*\([a-z]{1,2}\)", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return re.sub(r"([,.;:])\1+", r"\1", text).strip()


def slug(title):
    """The file name a game is published under, in every format."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


if __name__ == "__main__":
    open("philidor.md", "w").write(render())
    print("wrote philidor.md")
