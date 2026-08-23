"""Emit one PGN per game, with Philidor's notes as move comments.

Generated from games.json, never hand-edited: the records hold the descriptive
original and the provenance that PGN has no room for, so regenerating after a
parser fix rewrites every file rather than stranding corrections here.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import json
import os
import re
import textwrap

OUT = "pgn"


def clean_comment(text):
    """PGN comments are brace-delimited, so braces cannot appear inside."""
    text = text.replace("{", "(").replace("}", ")")
    return re.sub(r"\s+", " ", text).strip()


def game_pgn(rec):
    tags = [
        ("Event", "Philidor, Analysis of the Game of Chess (London, 1777)"),
        ("Site", "?"), ("Date", "1777.??.??"), ("Round", "-"),
        ("White", "Philidor (analysis)"), ("Black", "Philidor (analysis)"),
        ("Result", "*"),
        ("Annotator", "F. D. Philidor"),
        ("PhilidorGame", rec["title"]),
        ("PhilidorKind", rec["kind"]),
        ("SourceLine", str(rec["source_line"])),
    ]
    if rec.get("start_fen"):
        # Philidor states the position for a study rather than playing to it.
        tags.append(("SetUp", "1"))
        tags.append(("FEN", rec["start_fen"]))
    if rec["parent"]:
        tags.append(("PhilidorParent", rec["parent"]))
        tags.append(("PhilidorBranchMove", str(rec["first_move"])))
    if rec["first_side"] == "B":
        tags.append(("PhilidorNote",
                     "Philidor sets this game out beginning with the Black; "
                     "the sides are exchanged here so that the first player "
                     "moves as White."))
    if rec.get("replay_overrides"):
        tags.append(("PhilidorReconstructed",
                     "Completing this game meant reading against the text at "
                     "ply " + ", ".join(str(p) for p in rec["replay_overrides"])
                     + "; the printed reading admits no legal continuation."))
    if not rec["replay_complete"]:
        tags.append(("PhilidorTruncated",
                     "Converted as far as the parser reaches: "
                     + (rec["replay_stopped"] or "")))

    head = "".join('[%s "%s"]\n' % (k, v.replace('"', "'")) for k, v in tags)

    body = []
    for i, san in enumerate(rec["san"]):
        if i % 2 == 0:
            body.append("%d." % (i // 2 + 1))
        body.append(san)
        # The descriptive original, then any note Philidor keyed to this move.
        parts = []
        if i < len(rec["plies"]):
            parts.append(rec["plies"][i]["text"])
        for note in rec["note_for_ply"].get(str(i), []):
            parts.append("NOTE: " + note)
        if i < rec["inherited_plies"]:
            parts.insert(0, "[from the parent game]")
        if parts:
            body.append("{%s}" % clean_comment("  ".join(parts)))
    if not rec["replay_complete"] and rec["san"]:
        body.append("{The board stops here; Philidor's game continues in the "
                    "text beside it.}")
    body.append("*")

    return head + "\n" + textwrap.fill(" ".join(body), 96) + "\n"


def main():
    recs = json.load(open("games.json"))
    os.makedirs(OUT, exist_ok=True)
    written = 0
    for rec in recs:
        # A partial line is still worth a board: most games convert far enough
        # to be played through, and the text alongside carries the remainder.
        if len(rec["san"]) < 4:
            continue
        with open(os.path.join(OUT, rec["slug"] + ".pgn"), "w") as fh:
            fh.write(game_pgn(rec))
        written += 1
    complete = sum(r["replay_complete"] for r in recs)
    print("wrote %d PGN files to %s/ (%d of them complete, of %d games)"
          % (written, OUT, complete, len(recs)))


if __name__ == "__main__":
    main()
