"""Generate the Quarto book from games.json.

Pages are deliberately content-only: a title, a board carrying the PGN, and
Philidor's own words. Every decision about how those look belongs to
book/theme.scss and book/_includes, so restyling the book never means
regenerating or hand-editing 96 pages.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import collections
import html
import json
import os
import shutil
import re

import yaml

from games import HOW
from to_pgn import game_pgn

BOOK = "book"
GAMES = os.path.join(BOOK, "games")


# How far the board can be trusted. One reading of the record, used for the
# mark in the contents, the notice at the head of a chapter, and the summary
# page -- so the three cannot disagree.
NEEDS_WORK = "\N{LADY BEETLE}"

# What each kind of decision is worth, shown beside its count. Kept next to
# STATES so the two tables on the page speak with one voice.
DECIDED = {
    "forced": ("Forced by the position",
               "The words and the board leave exactly one legal move, so no "
               "choice was made."),
    "mirrored": ('"The same"',
                 "Mirrors the move just played, and the board confirms the "
                 "mirror is legal."),
    "chosen": ("Chosen by the search",
               "Several legal moves fit the words equally well; the one kept "
               "is the one under which the rest of the game replays."),
    "overridden": ("Read against the text",
                   "No legal move fits the words at all. The reading departs "
                   "from the page, and the game is marked for it."),
}

STATES = {
    "clean": (
        "Follows the text",
        "The board plays Philidor's words from the first move to the last."),
    "reconstructed": (
        "Reconstructed",
        "The board plays the game through, but at one or more moves the printed "
        "text admits no legal continuation, so the reading departs from it. The "
        "chapter names those moves."),
    "partial": (
        "Board stops short",
        "The board carries the opening and then stops, on a phrase the converter "
        "cannot yet read. Philidor's whole game stands on the page as text, and "
        "the chapter says how far the board reaches."),
    "none": (
        "No board yet",
        "Too little converts to play through: the reading stops within the "
        "first move or two."),
}


def state(rec):
    """Which of the four a game is in."""
    if len(rec["san"]) < 4:
        return "none"
    if not rec["replay_complete"]:
        return "partial"
    if rec.get("replay_overrides") or rec.get("editorial_readings"):
        return "reconstructed"
    return "clean"


def marker(rec):
    return "" if state(rec) == "clean" else " " + NEEDS_WORK


def notes_by_letter(rec):
    """Philidor's notes, grouped by the letter that refers to them.

    A letter can repeat within a game -- the First Party has two notes marked
    (x) -- so each maps to a list, taken in the order printed.
    """
    out = {}
    for note in rec["notes"]:
        m = re.match(r"\(([a-z]{1,2})\)\s*(.*)", note, re.S)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2).strip())
    return out


def link_refs(text, notes, used):
    """Turn the (a) (b) references in a move into hoverable ones.

    The note travels with the reference, so the popover needs nothing but the
    element it is anchored to. `used` counts references already seen in this
    game, so a repeated letter takes its own note rather than the first.
    """
    def one(m):
        letter = m.group(1)
        seen = used.get(letter, 0)
        options = notes.get(letter, [])
        if seen >= len(options):
            return m.group(0)
        used[letter] = seen + 1
        return ('<span class="note-ref" tabindex="0" data-note="%s">(%s)</span>'
                % (html.escape(options[seen], quote=True), letter))

    return re.sub(r"\(([a-z]{1,2})\)", one, text)


def moves_html(rec, notes, used):
    """Philidor's descriptive moves, numbered as the source numbers them."""
    rows, i, n = [], 0, rec["first_move"]
    if rec["inherited_plies"]:
        n = 1
    plies = rec["plies"]
    while i < len(plies):
        pair, side0 = [], plies[i]["side"]
        pair.append(plies[i])
        if i + 1 < len(plies) and plies[i + 1]["side"] != side0:
            pair.append(plies[i + 1])
        cells = []
        for k, p in enumerate(pair):
            idx = i + k
            inherited = " inherited" if idx < rec["inherited_plies"] else ""
            label = "White" if p["side"] == "W" else "Black"
            # Only plies the board can actually reach are navigable.
            ply_attr = ' data-ply="%d"' % idx if idx < len(rec["san"]) else ""
            cells.append(
                '<span class="ply%s"%s><span class="side">%s.</span> %s</span>'
                % (inherited, ply_attr, label,
                   link_refs(html.escape(p["text"]), notes, used)))
        rows.append('<div class="move"><span class="move-no">%d.</span>%s</div>'
                    % (n, "".join(cells)))
        i += len(pair)
        n += 1
    return '<div class="original-moves">%s</div>' % "".join(rows)


def notes_html(rec, used):
    """Only the notes no move can reach.

    A note is read by hovering the reference that calls it, so listing them all
    again below the moves would be redundant. The scan lost a few references,
    though, leaving notes with nothing to hover: those are printed, or they
    would be readable only in the downloaded Markdown.
    """
    claimed = dict(used)
    paras = []
    for note in rec["notes"]:
        m = re.match(r"\(([a-z]{1,2})\)\s*(.*)", note, re.S)
        if m and claimed.get(m.group(1), 0) > 0:
            claimed[m.group(1)] -= 1
            continue
        if m:
            paras.append('<p><span class="note-letter">(%s)</span>%s</p>'
                         % (m.group(1), html.escape(m.group(2))))
        else:
            paras.append("<p>%s</p>" % html.escape(note))
    if not paras:
        return ""
    return ('<div class="philidor-notes"><h3>Notes with no reference in the '
            "text</h3><p class=\"note-why\">The scan lost the mark that called "
            "these, so no move points to them.</p>%s</div>" % "".join(paras))


def position_html(rec, notes, used):
    if not rec["position"]:
        return ""
    out, buf = [], []
    for line in rec["position"]:
        if line.startswith("Situation"):
            if buf:
                out.append("<ul>%s</ul>" % "".join(buf))
                buf = []
            out.append('<span class="situation">%s</span>'
                       % html.escape(line.rstrip(".")))
        else:
            buf.append("<li>%s</li>"
                       % link_refs(html.escape(line), notes, used))
    if buf:
        out.append("<ul>%s</ul>" % "".join(buf))
    return '<div class="game-position">%s</div>' % "".join(out)


def board_html(rec):
    # Nothing to show, and the notice at the head of the chapter says why.
    if state(rec) == "none":
        return ""
    # The board column holds the board and its controls, nothing else; any
    # notice about how far the conversion reaches goes above the columns.
    pgn = game_pgn(rec).replace("</script>", "<\\/script>")
    return ('<div class="pgn-board">'
            '<script type="text/pgn">%s</script></div>' % pgn)


def coverage_note(rec):
    """The notice at the head of a chapter whose board falls short."""
    kind = state(rec)
    if kind == "clean":
        return ""
    label, _ = STATES[kind]
    if kind == "none":
        body = ("This game is not yet converted to algebraic notation: "
                + html.escape(rec["replay_stopped"] or ""))
    else:
        moves = (len(rec["san"]) + 1) // 2
        body = ("The board carries the first %d moves; conversion of the rest "
                "is unfinished. " % moves if kind == "partial" else
                "The board plays the game through. ")
    if rec.get("replay_overrides"):
        body += ("The printed text admits no legal continuation at ply %s, so "
                 "the board departs from it there. " %
                 ", ".join(str(p) for p in rec["replay_overrides"]))
    if kind != "none":
        body += "Philidor's words stand unaltered beside it."
    return ('<div class="editorial-note"><strong>%s %s.</strong> %s</div>'
            % (label, NEEDS_WORK, body))


def downloads_html(rec):
    """Links to this game on its own, as text and as moves."""
    links = ['<a class="download" href="../downloads/md/%s.md" download>'
             "Markdown — Philidor's text</a>" % rec["slug"]]
    if len(rec["san"]) >= 4:
        label = ("PGN — algebraic notation" if rec["replay_complete"]
                 else "PGN — algebraic notation (partial)")
        links.append('<a class="download" href="../downloads/pgn/%s.pgn" '
                     "download>%s</a>" % (rec["slug"], label))
    return '<div class="downloads">%s</div>' % "".join(links)


def copy_downloads(recs):
    """Put the published files where the book can serve them."""
    out = os.path.join(BOOK, "downloads")
    if os.path.isdir(out):
        shutil.rmtree(out)
    for kind, src in (("md", "md"), ("pgn", "pgn")):
        dst = os.path.join(out, kind)
        os.makedirs(dst, exist_ok=True)
        if not os.path.isdir(src):
            continue
        for rec in recs:
            path = os.path.join(src, rec["slug"] + "." + kind)
            if os.path.exists(path):
                shutil.copy2(path, dst)


def follow_html(rec):
    """The tick-box, and the box that follows the board a move at a time.

    The move being shown is repeated under the board, numbered as the move
    list numbers it: on a narrow screen there is no room for the moves beside
    the board at all, and on a wide one it saves looking across. The box is
    filled from the move list by the page's script, and is left out of games
    with no board to follow.

    It is set here rather than by the script so the box is not drawn unticked
    for a moment first; a reader who turns it off is remembered in
    localStorage, and the script unticks it again on the next page.
    """
    if len(rec["san"]) < 4:
        return ""
    return (
        '<label class="follow-toggle">'
        '<input type="checkbox" class="follow-text" checked>'
        " Show the text with the board"
        "</label>"
        '<div class="move-text" hidden>'
        '<p class="move-text__move"></p><div class="move-text__notes"></div>'
        "</div>")


def page(rec):
    meta = rec["kind"]
    if rec["parent"]:
        meta += " &middot; branches from %s at move %d" % (
            html.escape(rec["parent"]), rec["first_move"])
    if rec["first_side"] == "B":
        meta += " &middot; Philidor sets this out beginning with the Black"

    # The position is set before the moves, so its references take their notes
    # first, in reading order.
    letters, used = notes_by_letter(rec), {}
    position = position_html(rec, letters, used)
    moves = moves_html(rec, letters, used)

    editorial = ""
    if rec["editorial"]:
        editorial = ('<div class="editorial-note"><strong>Editorial note.</strong> '
                     + html.escape(rec["editorial"]) + "</div>")

    # Wrapped so a narrow screen can put the board first and everything that
    # describes the game after it.
    body = [
        '<div class="game-page">',
        '<div class="game-head">',
        '<div class="game-meta">%s</div>' % meta,
        '<div class="game-subtitle">%s</div>' % html.escape(rec["subtitle"] or ""),
        '<hr class="game-rule">',
        editorial,
        coverage_note(rec),
        "</div>",
        '<div class="philidor-game">',
        '<div class="game-board">', board_html(rec), follow_html(rec), "</div>",
        '<div class="game-text">',
        position, moves, notes_html(rec, used),
        "</div>",
        "</div>",
        "</div>",
        downloads_html(rec),
        "",
    ]
    # A PGN carries a mandatory blank line between its tags and its moves,
    # which would end an ordinary raw-HTML block and orphan every div after
    # it. A fenced raw block passes the whole page through untouched.
    # The mark rides on the title, which is what Quarto lists in the contents.
    front = yaml.safe_dump({"title": rec["title"] + marker(rec),
                            "pagetitle": rec["title"]},
                           allow_unicode=True).strip()
    return "---\n%s\n---\n\n```{=html}\n%s\n```\n" % (
        front, "\n".join(b for b in body if b))


ORDER = ["clean", "reconstructed", "partial", "none"]

# The chapters before the games. Quarto numbers chapters in order, so a game's
# number is its place in the records after these -- taken from the same list
# that builds the book, rather than written out again.
FRONT = ["index.qmd", "editions.qmd", "state.qmd"]


def chapter_number(recs, rec):
    return len(FRONT) + recs.index(rec) + 1


def state_page(recs):
    """A chapter reporting how far each game has been converted.

    Written from the records on every build, so it cannot fall behind the
    books it describes.
    """
    counts = {key: [r for r in recs if state(r) == key] for key in ORDER}
    playable = sum(len(counts[k]) for k in ("clean", "reconstructed", "partial"))
    plies = sum(len(r["san"]) for r in recs)
    total = sum(len(r["plies"]) for r in recs)
    done = len(counts["clean"]) + len(counts["reconstructed"])
    inherited = sum(r["inherited_plies"] for r in recs)

    tally = collections.Counter(h for r in recs for h in r["ply_decided"])
    how = ["| How the move was settled | Plies | Share | Standing |",
           "| --- | ---: | ---: | --- |"]
    for key in HOW:
        label, standing = DECIDED[key]
        how.append("| %s | %d | %.1f%% | %s |"
                   % (label, tally[key], 100.0 * tally[key] / plies, standing))

    rows = ["| Ch. | Game | State | Plies | Where it needs care |",
            "| ---: | --- | --- | ---: | --- |"]
    for key in ORDER[1:]:
        for rec in counts[key]:
            n = len(rec["san"])
            # For a game that stops, where it stopped is the thing to say;
            # any override it also carries comes after.
            care = []
            if key != "reconstructed" and rec["replay_stopped"]:
                care.append(rec["replay_stopped"])
            if rec.get("replay_overrides"):
                care.append("departs from the text at ply %s" % ", ".join(
                    str(p) for p in rec["replay_overrides"]))
            if rec.get("editorial_readings"):
                care.append("ply %s settled by hand" % ", ".join(
                    str(p) for p in rec["editorial_readings"]))
            care = "; ".join(care) or "stops early"
            rows.append("| %d | [%s](games/%s.qmd) | %s | %d&nbsp;/&nbsp;%d | %s |"
                        % (chapter_number(recs, rec), rec["title"], rec["slug"],
                           STATES[key][0], n, len(rec["plies"]), care))

    return "\n".join([
        "---", "title: State of the conversion", "---", "",
        "Philidor's text is transcribed in full: all %d games, every move and "
        "every note. Turning his descriptive notation into moves on a board is "
        "further along in some games than others, and this page says where each "
        "stands. It is written afresh on every build." % len(recs),
        "",
        "Of the %d games with a board, %d play through to the end. Across the "
        "whole book %d of %d plies convert, of which %d are a back-game "
        "repeating its parent, so %d are distinct positions read from the page."
        % (playable, done, plies, total, inherited, plies - inherited),
        "",
        "## How the moves were arrived at",
        "",
        "No move is ever computed. Each ply is read for what it says, the board "
        "is asked which legal moves fit, and the rules of chess remove the "
        "rest. How much work that leaves varies from ply to ply, and the four "
        "cases are not equally sound.",
        "",
        "\n".join(how),
        "",
        "The first two are as good as the transcription: nothing was chosen, "
        "because nothing was open to choose. The last two are where a reader "
        "should look first, and they are %.1f%% of the book between them."
        % (100.0 * (tally["chosen"] + tally["overridden"]) / plies),
        "",
        "## Games needing attention",
        "",
        "A game marked %s in the contents appears here. **Reconstructed** means "
        "the board plays it through, but at some ply the printed text admits no "
        "legal continuation and the reading departs from it. **Board stops "
        "short** means the board carries the opening and then halts on a phrase "
        "the converter cannot read; Philidor's whole game still stands on the "
        "page as text. **No board yet** means the reading stops within the "
        "first move or two." % NEEDS_WORK,
        "",
        "\n".join(rows),
        "",
        "The %d games not listed follow the text from the first move to the "
        "last." % len(counts["clean"]),
        ""])



def main():
    recs = json.load(open("games.json"))
    copy_downloads(recs)
    os.makedirs(GAMES, exist_ok=True)
    # Clear the previous build, including the support directories Quarto
    # leaves beside a chapter.
    for old in os.listdir(GAMES):
        path = os.path.join(GAMES, old)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    with open(os.path.join(BOOK, "state.qmd"), "w") as fh:
        fh.write(state_page(recs))

    chapters = list(FRONT)
    for rec in recs:
        path = os.path.join(GAMES, rec["slug"] + ".qmd")
        with open(path, "w") as fh:
            fh.write(page(rec))
        chapters.append("games/" + rec["slug"] + ".qmd")

    cfg_path = os.path.join(BOOK, "_quarto.yml")
    cfg = yaml.safe_load(open(cfg_path))
    cfg["book"]["chapters"] = chapters
    with open(cfg_path, "w") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False, allow_unicode=True)

    boards = sum(len(r["san"]) >= 4 for r in recs)
    complete = sum(r["replay_complete"] for r in recs)
    print("wrote %d game pages to %s/ (%d with a board, %d of those complete)"
          % (len(recs), GAMES, boards, complete))


if __name__ == "__main__":
    main()
