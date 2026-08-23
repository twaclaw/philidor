"""Extract Philidor's games from the OCR'd source texts into structured data.

Base text is philidor2.txt (1777 London edition, good OCR).
philidor1.txt (1790 edition, vol. 1) is used for cross-verification and for
the Sixth Regular Party, which the 1777 edition does not contain.
"""

import re

# Long-s misread as "f". Auto-detected against /usr/share/dict/words, then
# hand-checked against context (see README of this script's development).
F_FOR_S = {
    "fame": "same", "fide": "side", "loft": "lost", "lofes": "loses",
    "lofing": "losing", "lofs": "loss", "cafe": "case", "fecond": "second",
    "fituation": "situation", "fquare": "square", "befides": "besides",
    "chefs": "chess", "Chefs": "Chess", "foon": "soon", "neceffity": "necessity",
    "poft": "post", "fixth": "sixth", "fubject": "subject", "fubje": "subje",
    "adverfary": "adversary", "fustained": "sustained", "fuftain": "sustain",
    "fustain": "sustain", "fuftained": "sustained", "muft": "must",
    "pofition": "position", "paffing": "passing", "eafily": "easily",
    "paffage": "passage", "fince": "since", "poffible": "possible",
    "difpofed": "disposed", "caft": "cast", "oppofite": "opposite",
    "oppofition": "opposition", "afcribe": "ascribe", "perfuaded": "persuaded",
    "perfon": "person", "precife": "precise", "occafion": "occasion",
    "abfolutely": "absolutely", "elfe": "else", "caftled": "castled",
    "caftle": "castle", "caftles": "castles", "caftling": "castling",
    "alfo": "also", "fome": "some", "confiderable": "considerable",
    "inftead": "instead", "enfure": "ensure", "confequently": "consequently",
    "diflodge": "dislodge", "affume": "assume", "fuperiority": "superiority",
    "fettled": "settled", "neceffarily": "necessarily", "cautioufly": "cautiously",
    "neceffary": "necessary", "arife": "arise", "fucceed": "succeed",
    "feen": "seen", "defire": "desire", "defert": "desert", "fure": "sure",
    "fingle": "single", "oppofing": "opposing", "Suppofing": "Supposing",
    "confecrated": "consecrated", "faid": "said", "decifion": "decision",
    "fet": "set", "facrificing": "sacrificing", "facrifice": "sacrifice",
    "facrificed": "sacrificed", "fuffered": "suffered", "fuppofed": "supposed",
    "demonftrated": "demonstrated", "confequence": "consequence",
    "confift": "consist", "fhews": "shews", "fhew": "shew",
    "fuch": "such", "cafes": "cases", "confifting": "consisting",
    "defenfive": "defensive", "difengage": "disengage",
    "difentangled": "disentangled", "elfewhere": "elsewhere",
    "enfured": "ensured", "expofing": "exposing", "imprifoned": "imprisoned",
    "infure": "insure", "preferved": "preserved", "neeeffity": "necessity",
    "dverfary": "adversary", "atracks": "attacks", "attaek": "attack",
    "difficult": "difficult", "fufficient": "sufficient",
    "fuppofe": "suppose", "fuppofing": "supposing", "fituated": "situated",
}

# Words the scan broke apart or ran together across a line or page break.
SPACING = [
    (r"\bTheking's\b", "The king's"), (r"\bTheking\b", "The king"),
    (r"\bTheking'srook\b", "The king's rook"),
    (r"\batits\b", "at its"), (r"\bathis\b", "at his"),
    (r"\bfitu\s+ated\b", "situated"),
    (r"\bimpoffibilityof\b", "impossibility of"),
    (r"\bking'sorgambit's\b", "king's or gambit's"),
    (r"\bqueen'srook'sthird\b", "queen's rook's third"),
    (r"\bperplexingacondition\b", "perplexing a condition"),
    (r"\bin-favour\b", "in favour"),
    (r"\babovementioned\b", "above-mentioned"),
    (r"im\s*ı\s*nediately|imınediately", "immediately"),
    (r"'spawn\b", "'s pawn"), (r"\bbishop spawn\b", "bishop's pawn"),
    # Ordinals and possessives the scan broke.
    (r"\bthirt\b", "third"), (r"\bfe\s+cond\b", "second"),
    (r"\bcafstles\b", "castles"), (r"\bcaftles\b", "castles"),
    (r"\bsquate\b", "square"), (r"\bat He\b", "at his"),
    # A printer's mark stuck to the word, and a signature letter stuck to the
    # side that follows it: "*square", "AW. The king".
    (r"\*\s*(?=square\b)", ""),
    (r"(?m)^[A-Z](?=[WB]\.\s+The\b)", ""),
    (r"\bfecond\b", "second"), (r"\bqueen rook's\b", "queen's rook's"),
    (r"\bking rook's\b", "king's rook's"),
    (r"\bsecond squares\b", "second square"),
    (r"\bbifhop\b", "bishop"), (r"\bpawh\b", "pawn"), (r"\bbithop\b", "bishop"),
    (r",(?=(?:two|one|at|and)\b)", ", "),
]

# Straight OCR garbles (not long-s related).
FIXES = [
    (r"\bBIHSOP\b", "BISHOP"),
    (r"\bbithop\b", "bishop"),
    (r"\bbi\s*ſhop\b", "bishop"),
    (r"\binate\b", "mate"),
    (r"\bfuare\b", "square"),
    (r"\broth\b", "10th"),
    (r"\biſt\b", "1st"),
    (r"\bMave\b", "Move"),
    (r"\bPHULIDOR\b", "PHILIDOR"),
    (r"\bHeisnowobliged\b", "He is now obliged"),
    (r"\bknights two moves\b", "knight's pawn, two moves"),
    (r"\bDRAWN-GAΜΕ\b", "DRAWN-GAME"),
    (r"\bGAME\.\.", "GAME."),
    (r"\bA\.DRAWN-GAME,\.\.", "A DRAWN-GAME,"),
    (r"\bADRAWN-GAME\b", "A DRAWN-GAME"),
]

PAGE_MARK = re.compile(r"^##\s*p\..*#+\s*$")
PAGE_NUM = re.compile(r"^[\[\(]\s*\d+\s*[\]\)]\.?$")
MOVE_LINE = re.compile(r"^([WB])\s*[.,:;]\s*(.*)$")
# A bare move number: arabic or roman, with assorted OCR trailing punctuation.
MOVENUM = re.compile(r"^(?:\d{1,2}|[IVXΙΙ]{1,6})\s*[.,:;\-–—]*$")
# A note opener at the start of a line: (a), (b), and their OCR lookalikes.
NOTE_OPEN = re.compile(r"^\(\s*([A-Za-z0-9])\s*\)")
# Debris from the word "NOTES" printed as a centred rule, which the scanner
# scatters over several lines: "N", "0 T E S.", "E S.", "NO", "T".
NOTES_JUNK = re.compile(r"^[NO0TESΕs\s.:,;|\[\]!()]{1,14}$")

# Philidor's printer letters the notes a...i, k...u, w, x, y -- the
# eighteenth-century convention, which omits j and v.
NOTE_LETTERS = "abcdefghiklmnopqrstuwxyz"


# Glyphs the scanner produces for each note letter. Nearly all the damage is
# letters read as digits: (b) as (6), (o) as (0), (l) as (1), (h) as (4).
LOOKALIKE = {
    "a": "42", "b": "658", "e": "co", "f": "t", "g": "q98", "h": "4bn",
    "i": "1lj", "k": "h", "l": "1i|", "n": "mhu", "o": "0ec", "p": "gq",
    "q": "g9p", "r": "nv", "s": "5f", "t": "f", "u": "nv", "w": "v",
    "x": "%", "y": "vg",
}


def repair_letters(glyphs: list[str]) -> list[str]:
    """Recover the printed note letters from their scanned glyphs.

    The letters run in alphabetical order, so the previous letter predicts the
    next one. A glyph is corrected only when it is a digit or a known
    misreading of the predicted letter; a plain letter that does not fit is
    trusted as printed and restarts the run.
    """
    out: list[str] = []
    prev = None
    for g in glyphs:
        nxt = 0 if prev is None else NOTE_LETTERS.find(prev) + 1
        want = NOTE_LETTERS[nxt] if 0 <= nxt < len(NOTE_LETTERS) else None
        low = g.lower()
        if want and (low == want or low in LOOKALIKE.get(want, "")):
            chosen = want
        elif low in NOTE_LETTERS:
            chosen = low          # a legible letter out of sequence: trust it
        else:
            chosen = want or "a"  # unrecognised glyph: take the predicted one
        out.append(chosen)
        prev = chosen
    return out
# Printer's signature at a page foot: "Bij", "B iij", "Qij", "U iij", "Tiij".
SIGNATURE = re.compile(r"\s*\b[A-Z]\s?i{1,3}j?\b\s*$")

NOISE = re.compile(
    r"^(?:[^A-Za-z0-9]{1,4}|[a-z]{1,2}|\d{1,3}|[A-Za-z]\s*[A-Za-z]?)$"
)


# The scanner drops Cyrillic and Greek lookalikes into headings, so that
# "BACK-GAME" comes out as "ВАСK-GAME" and hides from any Latin-only search.
HOMOGLYPHS = str.maketrans({
    "А": "A", "В": "B", "С": "C", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "Т": "T", "Х": "X", "У": "Y", "І": "I", "Ј": "J",
    "Ѕ": "S", "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y",
    "х": "x", "ѕ": "s", "і": "i",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
    "Ϲ": "C", "α": "a", "ο": "o", "ρ": "p", "τ": "t", "ι": "i", "κ": "k",
    "​": "",
})


def normalise(text: str) -> str:
    text = text.translate(HOMOGLYPHS)
    text = text.replace("ſ", "s").replace("ﬅ", "st").replace("ﬀ", "ff")
    text = text.replace("—", "-")
    # De-hyphenate across line breaks before any per-word work.
    text = re.sub(r"([A-Za-z])[-‑]\s*\n\s*([a-z])", r"\1\2", text)
    text = text.replace("ı", "i")
    for pat, rep in FIXES + SPACING:
        text = re.sub(pat, rep, text)
    # The very first game names the sides in full before settling on W. and B.
    text = re.sub(r"(?m)^White\.", "W.", text)
    text = re.sub(r"(?m)^Black\.", "B.", text)
    # Where the scan ran two plies onto one line -- and often read the side's
    # full stop as a comma -- put the second ply back on its own line.
    text = re.sub(r"[^\S\n]*[•*]?[^\S\n]*\b([WB])\s*[.,]\s+(The\b)",
                  r"\n\1. \2", text)

    def swap(m):
        w = m.group(0)
        return F_FOR_S.get(w, F_FOR_S.get(w.lower(), w))

    return re.sub(r"[A-Za-z]+", swap, text)


def clean_lines(raw: str) -> list[str]:
    out, drop = [], False
    for line in raw.split("\n"):
        s = line.strip()
        if not s or PAGE_MARK.match(s) or PAGE_NUM.match(s):
            continue
        if s.startswith("##"):
            continue
        # A later owner's marginal note citing the 1804 "History and Analysis
        # of Chess" is not Philidor's text; skip it and its run-on lines.
        if s.startswith("*") and "Philidor" in s:
            drop = True
        if drop:
            if MOVENUM.match(s) or MOVE_LINE.match(s):
                drop = False
            else:
                continue
        out.append(s)
    return out


def notes_header_len(lines: list[str], i: int) -> int:
    """How many lines the word NOTES occupies at position i, or 0.

    It is printed as a centred rule and the scanner shatters it across up to
    three lines -- "N" / "0 T E" / "S." -- so it is reassembled here.
    """
    acc = ""
    for j in range(i, min(i + 3, len(lines))):
        s = lines[j]
        if len(s) > 10 or not NOTES_JUNK.match(s):
            break
        acc += re.sub(r"[^A-Za-z0]", "", s).upper().replace("0", "O")
        if acc in ("NOTE", "NOTES"):
            return j - i + 1
    return 0


def parse_section(lines: list[str]) -> dict:
    """Split a section's lines into a move list and its notes.

    The word "NOTES" is printed as a centred rule and the scanner shatters it
    ("N" / "0 T E S." / "E S."), so the header is not reliably matchable.
    We key off the note bodies instead: a line opening with "(a)", "(b)" etc.
    starts the notes, and the next move number or move line ends them.
    """
    moves_raw, notes_raw, in_notes = [], [], False
    skip = 0
    for i, s in enumerate(lines):
        if skip:
            skip -= 1
            continue
        if not in_notes and moves_raw:
            hdr = notes_header_len(lines, i)
            if hdr:
                # A note block may open mid-sentence, continuing one carried
                # over from the previous page, so the header is the only mark.
                in_notes, skip = True, hdr - 1
                continue
        if not in_notes and NOTE_OPEN.match(s) and moves_raw:
            in_notes = True
            while moves_raw and NOTES_JUNK.match(moves_raw[-1]):
                moves_raw.pop()
        elif in_notes and (MOVENUM.match(s) or MOVE_LINE.match(s)):
            in_notes = False
        (notes_raw if in_notes else moves_raw).append(s)
    return {"moves": moves_raw, "notes": notes_raw}


def join_moves(lines: list[str]) -> list[tuple[str, str]]:
    """Collapse wrapped move text into (side, text) pairs, dropping OCR noise."""
    plies: list[list[str]] = []
    for s in lines:
        if MOVENUM.match(s) or NOTES_JUNK.match(s):
            continue
        m = MOVE_LINE.match(s)
        if m:
            plies.append([m.group(1), m.group(2)])
        elif plies and not NOISE.match(s):
            plies[-1][1] += " " + s
    result = []
    for side, txt in plies:
        txt = re.sub(r"\s+", " ", txt).strip()
        txt = SIGNATURE.sub("", txt)
        txt = re.sub(r"\s+([,.;:])", r"\1", txt)
        txt = re.sub(r"(\S)(\([A-Za-z0-9]\))", r"\1 \2", txt)
        txt = re.sub(r"[.,;:\s]+$", ".", txt)
        if len(txt) > 2:
            result.append((side, txt))
    return result


def join_notes(lines: list[str]) -> list[str]:
    """Regroup note paragraphs, each introduced by a (a) (b) ... marker."""
    notes: list[str] = []
    for s in lines:
        if NOTES_JUNK.match(s) or (NOISE.match(s) and not s.startswith("(")):
            continue
        if NOTE_OPEN.match(s):
            notes.append(s)
        elif notes:
            notes[-1] += " " + s
        else:
            notes.append(s)
    cleaned = []
    for n in notes:
        n = re.sub(r"\s+", " ", n).strip()
        n = SIGNATURE.sub("", n)
        n = re.sub(r"\s+([,.;:])", r"\1", n)
        if len(n) > 4:
            cleaned.append(n)
    return cleaned


def marker_glyphs(texts: list[str], anchored: bool) -> list[str]:
    """The raw note-letter glyphs, in reading order."""
    pat = NOTE_OPEN if anchored else re.compile(r"\(\s*([A-Za-z0-9])\s*\)")
    out = []
    for t in texts:
        if anchored:
            m = pat.match(t)
            if m:
                out.append(m.group(1))
        else:
            out += pat.findall(t)
    return out


def apply_letters(texts: list[str], letters: list[str], anchored: bool) -> list[str]:
    """Write the repaired letters back over the scanned glyphs."""
    it = iter(letters)
    out = []
    for t in texts:
        if anchored:
            out.append(NOTE_OPEN.sub(lambda m: "(%s)" % next(it), t, count=1))
        else:
            out.append(re.sub(r"\(\s*[A-Za-z0-9]\s*\)",
                              lambda m: "(%s)" % next(it), t))
    return out


def number_moves(plies, start, first_side):
    """Re-derive move numbers from the section's stated starting move.

    The OCR's own numerals are unreliable (37- , 3: , II. , ΙΙ.), so we rebuild
    the sequence and pair the plies instead of trusting them.
    """
    moves, n, cur = [], start, []
    expect = first_side
    for side, txt in plies:
        # A move closes when the side that opened it comes round again.
        if cur and (side == expect or any(s == side for s, _ in cur)):
            moves.append((n, cur))
            n += 1
            cur = []
        cur.append((side, txt))
        if not expect:
            expect = side
    if cur:
        moves.append((n, cur))
    return moves
