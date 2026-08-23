# Extraction

Turning two eighteenth-century scans into `philidor.md` — every game,
back-game and endgame of Philidor's *Analysis*, one section each, in his own
descriptive notation.

Everything needed to rebuild the transcription is in this folder: the scans,
the text extracted from them, the code, and the record of every correction
made to the printed page.

## The sources

| File | Edition | Role |
| --- | --- | --- |
| `philidor2.pdf` / `philidor2.txt` | London, P. Elmsley, 1777 | **Base text.** The cleaner scan and the more complete book: it alone carries the endgames and the rules. |
| `philidor1.pdf` / `philidor1.txt` | London, 1790, "new edition, improved and greatly enlarged" | **Collation only.** Volume I — it ends "END OF THE FIRST VOLUME". |

Both are public-domain HathiTrust/Google scans of Harvard copies. The PDFs are
about 150 MB and are not tracked in git; the `.txt` files are, and are all the
code reads. `philidor1.txt` was extracted here with `pypdf`, since that PDF
shipped without a text layer.

Everything in the 1790 volume is present in 1777. The later edition renames the
1777 supplement as a series of *Regular Parties*:

| 1777 (transcribed here) | 1790 |
| --- | --- |
| Method of Playing | First Regular Party |
| First Variable | Second Regular Party |
| Second Variable | Third Regular Party |
| Third Variable | Fourth Regular Party |
| Fourth Variable | Fifth Regular Party |
| Another Method of Playing | Sixth Regular Party |

## The procedure

**1. Normalise the scan** (`extract.py`). The long *s* becomes *s*, and so do
the scanner's misreadings of it as *f* — `fame` → same, `fide` → side, `loft` →
lost. That list was not guessed: every word containing an *f* was tested
against a dictionary, keeping those where the substitution produced a real word
that the original was not, and the result was then read by eye. The same pass
repairs Cyrillic and Greek homoglyphs, rejoins words the scan broke or ran
together, and drops running heads, page numbers and printers' signature marks.

**2. Find the games** (`build.py`). A table of 96 sections, each keyed to its
line in `philidor2.txt`, drives the split. Eight of them were missed on the
first pass because the scanner had set their headings in Cyrillic lookalikes
(`ВАСK-GAME` reads as Latin but is not) or split them mid-word (`VAR` /
`IABLE`). They surfaced through the notes: Philidor letters them a…i, k…u, w,
x, y — the eighteenth-century sequence, which omits *j* and *v* — and that
sequence only restarts at a heading.

**3. Separate moves from notes.** The word NOTES is printed as a centred rule
and the scan shatters it across up to three lines (`N` / `0 T E` / `S.`), so it
cannot be matched directly. The parser keys off the note bodies instead: a line
opening `(a)` starts the notes, and the next move number ends them.

**4. Rebuild the numbering.** The printed move numbers are unreliable — `37-`,
`3:`, `II.`, `ΙΙ.` — so plies are paired into moves from scratch and the result
is checked against what the printer set, rather than trusted from it.

## Rebuilding

```
uv run --with chess python scripts/extraction/build.py        # -> philidor.md
uv run --with chess python scripts/extraction/split_games.py  # -> md/
```

`split_games.py` writes each game to its own file under `md/`, for the download
buttons in the book and for reading a game on its own.

The two arrangements differ on purpose. `philidor.md` keeps Philidor's: moves
first, lettered notes gathered beneath. A single game reads better interleaved,
so the per-game files set each note under the move that calls it and drop the
`(a)` letters, which point nowhere once the note is alongside. Both are written
from the same parse, and `verify_outputs.py` checks that nothing is lost in the
rearrangement -- every move and every note of a section reaches its file.

Neither is parsed back into structure: the transcription and `games.json` are
emitted by one pass over the scan, so there is no second parser to disagree
with the first.

Scripts run the same from anywhere; `philidorpath.py` in the parent folder puts
the project root on the path and makes it the working directory.

## Checking it

```
uv run --with chess python scripts/extraction/verify_outputs.py
uv run --with chess python scripts/extraction/audit_moves.py
uv run --with chess python scripts/extraction/crosscheck.py
```

**`verify_outputs.py` — the four forms must agree.** The same games are
published as `philidor.md`, as `md/*.md`, as `games.json` and as the book's
chapters. This checks that each per-game file is its section word for word,
that every move reaches `games.json` and the rendered page, and that no note
is unreachable — either printed on the page or carried by the reference that
calls it. It found two ways notes were being lost: a game with two notes
lettered `(x)`, where a dictionary keyed by letter kept only the second, and
references in an endgame's opening position, which were never made hoverable.

**`audit_moves.py` — the printer's own numbers.** He set a number on every
move, so reproducing that sequence tests whether plies have been paired
correctly. 89 of 96 sections agree exactly; the other seven differ only in
numbers the scan mangled at the end of a range. One half-move remains, and it
is a genuine defect in the printed source, not a transcription slip.

**`crosscheck.py` — collation against 1790.** Each game is reduced to a
canonical token sequence, so the 1777 spelled-out text ("The king's pawn, two
moves") can be compared with the 1790 abbreviations ("The K. P. two moves").
This confirmed the inventory and the naming table above. Agreement runs 60–83%
where the 1790 scan is legible; the ceiling is that scan's quality — it yields
roughly a third of the plies — not a disagreement between the editions.

Two further checks live in `../algebraic_notation`, because they need the games
on a board: replaying each back-game against the parent it branches from, and
diffing against an independent transcription.

## Editorial policy

Philidor's descriptive notation is kept as printed. The long *s* and its
misreadings are corrected, as are broken and run-together words; spelling is
otherwise left alone, so "shews" and "chuse" stand as his translator had them.

Corrections to the printed text itself are listed in the `ERRATA` table in
`build.py`, keyed by line number in `philidor2.txt`, so each can be checked
against the source rather than taken on trust. There is currently one: a `W.`
that must be `B.`, where Black's king answers a check and both plies of the
move are set as White's — the note and Black's next move both confirm it.

Where the source is defective beyond repair, the transcription says so instead
of quietly patching it. The seventh back-game of the First Gambit sets two
White moves at move 30 and omits both Black's reply and the number 31; Black's
move is simply lost, and the section carries an editorial note saying so.
