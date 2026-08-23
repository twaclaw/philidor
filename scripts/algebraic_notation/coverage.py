"""Report how much of the transcription replays as algebraic notation."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import collections
import re

from games import SECTIONS, replay_section, replayable


def main():
    games = converted = total = 0
    reconstructed = 0
    reasons = collections.Counter()
    sample = {}

    for sec in SECTIONS:
        if not replayable(sec):
            continue
        san, reason, done, overrides, line, _, _ = replay_section(sec)
        if not line:
            continue
        games += 1
        total += len(line)
        converted += len(san)
        if done:
            reconstructed += bool(overrides)
            continue
        key = re.sub(r"^ply \d+: ", "", reason or "?").split(":")[0].strip()
        key = re.sub(r"\(\d+\)", "(n)", key)
        reasons[key] += 1
        sample.setdefault(key, (sec["title"], reason))

    complete = games - sum(reasons.values())
    print("opening games: %d   replayed end to end: %d   plies: %d/%d (%.0f%%)"
          % (games, complete, converted, total, 100.0 * converted / total))
    print("of those, %d needed a reading against the text; %d are faithful throughout"
          % (reconstructed, complete - reconstructed))
    print()
    for key, n in reasons.most_common():
        title, reason = sample[key]
        print("%3d  %-24s %-34s %s" % (n, key, title[:34], (reason or "")[:44]))


if __name__ == "__main__":
    main()
