"""Write each game to its own Markdown file under md/.

These are the downloadable per-game texts, and they come from the same
`section_markdown` that composes philidor.md, so a game downloaded on its own
is word for word the section it was taken from.

They are transcription, not conversion: nothing here needs a chess board, so
`md/` rebuilds from the scan alone.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import os
import shutil

from build import (EDITORIAL, note_map, number_moves, parse_all, slug,
                   strip_refs)

OUT = "md"


def orphaned_notes(sec, notes):
    """Notes no move refers to, because the scan lost the mark."""
    claimed = {n for plies in notes.values() for n in plies}
    return [n for n in sec["notes"] if strip_refs(n) not in
            {strip_refs(c) for c in claimed}]

SOURCE = ("Philidor, *Analysis of the Game of Chess* (London, P. Elmsley, "
          "1777), collated with volume I of the edition of 1790.")


def game_markdown(sec):
    """One game, with each note set under the move that calls it.

    philidor.md keeps Philidor's own arrangement, moves first and lettered
    notes gathered beneath. On its own a game reads better interleaved: the
    note goes straight under its move and the letters are dropped, since with
    nothing to cross-refer to they only clutter the text.
    """
    notes = note_map(sec)
    moves = number_moves(sec["plies"], sec["first_move"],
                         sec["plies"][0][0] if sec["plies"] else "W")

    lines = ["<!-- Generated from the 1777 scan; see philidor.md for the "
             "whole work. -->", "", "# " + sec["title"], ""]
    if sec["subtitle"]:
        lines += ["*" + sec["subtitle"] + "*", ""]

    for line in sec["setup"]:
        lines.append("**" + line.rstrip(".") + "**" if line.startswith("Situation")
                     else "- " + line)
    if sec["setup"]:
        lines.append("")

    ply = 0
    for number, move in moves:
        for k, (side, text) in enumerate(move):
            label = "White" if side == "W" else "Black"
            stem = "%d. " % number if k == 0 else "   "
            lines.append("%s**%s.** %s" % (stem, label, strip_refs(text)))
            for note in notes.get(ply, []):
                # Indented to stay inside the move it belongs to.
                lines += ["", "   > " + strip_refs(note), ""]
            ply += 1
        if lines[-1] != "":
            lines.append("")

    orphans = orphaned_notes(sec, notes)
    if orphans:
        lines += ["**Notes with no reference in the text.** The scan lost the "
                  "mark that called these, so no move points to them.", ""]
        lines += ["> " + strip_refs(n) + "\n" for n in orphans]

    if sec["title"] in EDITORIAL:
        lines += ["> **Editorial note.** " + EDITORIAL[sec["title"]], ""]

    lines += ["", "---", ""]
    if sec["level"] == 2:
        lines += ["*A back-game: a variation resuming its parent game at "
                  "move %d.*" % sec["first_move"], ""]
    lines.append("Source: " + SOURCE)
    return "\n".join(lines).lstrip("\n") + "\n"


def main():
    sections = parse_all()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for sec in sections:
        path = os.path.join(OUT, slug(sec["title"]) + ".md")
        with open(path, "w") as fh:
            fh.write(game_markdown(sec))
    print("wrote %d game files to %s/" % (len(sections), OUT))


if __name__ == "__main__":
    main()
