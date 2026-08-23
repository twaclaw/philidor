"""Classify where each game's replay stops, and why.

The point is to tell apart the two kinds of failure: a construction the parser
does not yet handle, which is ordinary work, and a ply the scan damaged beyond
reading, which needs judgement.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import collections
import re

from games import SECTIONS, replay_section, replayable

# Digits and stray symbols in a move phrase mean the scanner mangled it.
DAMAGED = re.compile(r"\d|[^\w\s,.'()-]")
# Philidor often runs his commentary straight on from the move.
COMMENTARY = re.compile(
    r"\b(pleases|loses|wins|game|mate being|undoubtedly|best|because"
    r"|will have|every where)\b", re.I)


def main():
    counts = collections.Counter()
    examples = collections.defaultdict(list)

    for sec in SECTIONS:
        if not replayable(sec):
            continue
        san, reason, done, _, line, _, _ = replay_section(sec)
        if not line:
            continue
        if done:
            counts["replayed end to end"] += 1
            continue

        at = re.match(r"ply (\d+)", reason or "")
        text = line[int(at.group(1)) - 1][1] if at else ""
        if not text:
            kind = "no move to read"
        elif DAMAGED.search(text):
            kind = "ply text damaged by the scan"
        elif COMMENTARY.search(text):
            kind = "move with prose commentary attached"
        else:
            kind = "clean text, parser gap"
        counts[kind] += 1
        if len(examples[kind]) < 3:
            examples[kind].append(text)

    for kind, n in counts.most_common():
        print("%3d  %s" % (n, kind))
        for text in examples[kind]:
            print('       "%s"' % text[:76])


if __name__ == "__main__":
    main()
