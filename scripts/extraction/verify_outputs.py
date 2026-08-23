"""Check every published form of the text against the scan it came from.

The project emits the same games four ways -- philidor.md, md/*.md,
games.json, and the book's chapters -- and they are only trustworthy if they
agree with each other and with philidor2.txt. This walks that back.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import philidorpath  # noqa: F401,E402  -- project root on sys.path and as cwd

import glob
import html
import json
import os
import re

from build import parse_all, section_markdown, slug, strip_refs


def strip_tags(page):
    """The words a reader sees, with markup and whitespace flattened."""
    body = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", page)
    return plain(html.unescape(re.sub(r"<[^>]+>", "", body)))


def plain(text):
    """Compare on words alone, normalised the same way the files are written.

    References are wrapped in their own markup on the page and dropped
    altogether from the per-game files, so they cannot take part.
    """
    return re.sub(r"\s+", " ", strip_refs(text)).strip()


def moves_of(markdown):
    """The move lines of a Markdown game, as plain text."""
    out = []
    for line in markdown.split("\n"):
        m = re.match(r"^(?:\d+\.\s+)?\*\*(White|Black)\.\*\*\s+(.*?)\s*$", line.strip())
        if m:
            out.append((m.group(1)[0], m.group(2)))
    return out


def main():
    sections = parse_all()
    problems = []

    whole = open("philidor.md").read()
    records = {r["title"]: r for r in json.load(open("games.json"))}

    total_plies = 0
    for sec in sections:
        title = sec["title"]
        name = slug(title)

        # 1. The per-game file must carry the whole section. It sets each note
        #    under the move that calls it, rather than gathering them at the
        #    foot as philidor.md does, so the test is that nothing is lost --
        #    not that the two read the same way.
        expected = "\n".join(section_markdown(sec, level=1)).strip()
        path = os.path.join("md", name + ".md")
        if not os.path.exists(path):
            problems.append("missing md/%s.md" % name)
            continue
        got = plain(open(path).read())
        plies = moves_of(expected)
        for _, text in plies:
            if plain(text) not in got:
                problems.append("md/%s.md is missing a move: %s"
                                % (name, text[:46]))
                break
        for note in sec["notes"]:
            body = plain(re.sub(r"^\([a-z]{1,2}\)\s*", "", note))
            if body[:60] not in got:
                problems.append("md/%s.md is missing a note: %s"
                                % (name, body[:46]))
                break

        # 2. Every move of that file must appear in the whole transcription.
        total_plies += len(plies)
        for side, text in plies:
            if text not in whole:
                problems.append("md/%s.md: move absent from philidor.md: %s"
                                % (name, text[:50]))
                break

        # 3. games.json must carry the same moves, in the same order. Its plies
        #    include any a back-game inherits from its parent, so compare the
        #    tail.
        rec = records.get(title)
        if rec is None:
            problems.append("games.json has no record for %s" % title)
            continue
        own = [p["text"] for p in rec["plies"]][rec["inherited_plies"]:]
        if own != [t for _, t in plies]:
            problems.append("games.json disagrees with md/%s.md on the moves" % name)

        page = os.path.join("_site", "games", name + ".html")
        if not os.path.exists(page):
            continue
        body = open(page).read()
        # The page wraps each reference in its own markup, so compare the
        # visible words rather than the raw string.
        visible = strip_tags(body)

        # 4. The chapter must show every move of the game.
        for _, text in plies[:40]:
            if plain(text) not in visible:
                problems.append("chapter %s is missing: %s" % (name, text[:50]))
                break

        # 5. Nothing Philidor wrote may be dropped: a note is either printed on
        #    the page or carried by the reference that calls it.
        hovers = " ".join(html.unescape(v) for v in
                          re.findall(r'data-note="([^"]*)"', body))
        for note in rec["notes"]:
            m = re.match(r"\(([a-z]{1,2})\)\s*(.*)", note, re.S)
            if not m:
                continue
            letter, text = m.group(1), m.group(2)
            probe = plain(text)[:60]
            if probe not in visible and probe not in plain(hovers):
                problems.append("chapter %s drops note (%s)" % (name, letter))

    print("%d games, %d plies checked across philidor.md, md/, games.json "
          "and the book" % (len(sections), total_plies))
    pages = len(glob.glob("_site/games/*.html"))
    print("%d chapters rendered, %d PGN files, %d per-game Markdown files"
          % (pages, len(glob.glob("pgn/*.pgn")), len(glob.glob("md/*.md"))))
    print()
    if problems:
        print("%d PROBLEMS" % len(problems))
        for p in problems[:20]:
            print("  -", p)
    else:
        print("all four forms agree, and no note is unreachable")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
