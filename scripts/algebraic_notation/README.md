# Algebraic notation

Turning Philidor's descriptive moves — "The king's bishop, at his queen's
bishop's fourth square" — into `Bc4`, and building what depends on that: the
canonical game records, a PGN per game, and the book's chapters.

Input is `philidor.md`'s underlying structure, read through `build.py` in
`../extraction`. Output is `games.json`, `pgn/` and `book/games/`.

Where his notation contradicts itself, and what each contradiction forced the
converter to allow, is set out with citations in **[NOTATION.md](NOTATION.md)**;
`inconsistencies.py` regenerates the evidence.

## The strategy: constrain, don't translate

No move is ever computed. Each ply is parsed for what it *does* say, the board
is asked for every legal move that fits, and the rules of chess eliminate the
rest. Descriptive notation is ambiguous as language; a position rarely is.

**Reading a ply** (`to_algebraic.py`):

- *The piece* is the last noun of the possessive chain. In "the queen's
  bishop's pawn" it is the pawn; everything before names the file it started
  on. Reading that phrase as a bishop was the first bug.
- *The square* takes its file from the last qualifier before the ordinal, and
  at a tie the longest — in "his king's bishop's second square" both `king`
  and `king's bishop` begin at the same character, and the longer names the
  file. The rank counts from the owner's back rank, and "adverse" flips which
  side you count from.
- *A bare qualifier* inherits its wing from the piece moving: "the queen, at
  her bishop's second square" means the queen's bishop, not the king's. That
  default was a second bug, and the branch audit below is what caught it.
- *Special forms*: captures (the piece taken is the last plain noun, so "takes
  the adverse king's pawn" is the pawn, not the king), pawn pushes by distance
  and file, castling, "covers the check", "gives check" with no square named,
  and "the same", which mirrors the opponent's previous move.

**Resolving what is left** (`replay_search.py`). If a ply still admits several
readings, each is tried and whichever lets the rest of the game replay legally
is kept — depth-first, with a node cap.

**Two structural transforms.** The four games Philidor sets out *beginning with
the Black* replay with the colours exchanged, so the first player moves as
White. A back-game is a variation, not a game: it resumes its parent at a
stated move, so the parent's plies are prepended — plus one more when the
back-game begins with the opposite side, since "from the 12th move of the
Black" resumes after White has already played his 12th.

## What this is worth, and what it is not

Every one of the 96 games has a board. 76 play through to the end, and 92% of
plies convert. Sixty-five of those readings keep faith with the text
throughout; the other eleven needed a departure and say so.

### How much of this the search actually does

Run `uv run python scripts/algebraic_notation/certainty.py`. Every accepted
ply is labelled in `games.json` under `ply_decided`, and the book's *State of
the conversion* chapter tabulates it on each build.

| How the ply was settled | Plies | Share | What it rests on |
| --- | ---: | ---: | --- |
| Forced by the position | 3138 | 93.7% | The words and the board leave exactly one legal move. Nothing was chosen. |
| "The same" | 104 | 3.1% | Mirrors the previous move, and the mirror is legal. |
| Chosen by the search | 84 | 2.5% | Several readings fit equally well; the one kept is the one under which the game finishes. |
| Read against the text | 23 | 0.7% | No legal move fits the words. The reading departs from the page and is flagged. |

**So the search decides 3.2% of the book.** The other 96.8% is arithmetic:
the position admits one move and the parser finds it. That is the honest
headline, and it cuts both ways -- the conversion is mostly not a search
result, and where it *is* a search result is exactly where to be careful.

Those 84 choice points are not, however, 84 isolated coin-flips. Replaying
every game greedily -- first reading each time, no backtracking -- reaches
2721 of the 3349 plies and dies in 27 games. So **backtracking is what settles
628 plies**, and at 48 of them greedy plays a different move altogether. A
handful of decisions gate a fifth of the book, because one wrong turn kills
every ply after it.

### Where it fails, and what it cannot tell you

- **Legality is a weak oracle.** Where two readings are both legal the search
  has nothing to separate them, and it will not notice. The 1777 d6 / 1790 d5
  misprint is exactly this: both replay, and only a second edition caught it.
  Nothing in this machinery could have.
- **A complete replay is not proof.** A wrong board played 27 plies quite
  happily before `check_claims.py` caught it. Finishing means only that some
  legal reading exists, not that it is Philidor's.
- **The first complete replay wins.** The search stops at the first success
  and never enumerates the rest, so where a game completes, that reading is
  not known to be the only one. No count of alternatives is claimed here
  because none has been made.
- **Failure is not proof either.** `MAX_BUDGET = 2` and `MAX_NODES = 30000`
  mean a game can stop for want of budget rather than for want of a reading.
  The 278 unconverted plies are "not found", not "not there".
- **The headline double-counts.** Of the 3349 converted plies, 757 are a
  back-game replaying its parent. Only **2592 are distinct positions read from
  the page**; the rest are the same evidence counted twice.
- **The 23 overrides are repairs, not readings.** They keep a game moving past
  a phrase no legal move fits, which is a guess dressed as a result. They are
  listed per game rather than absorbed.

What the search is genuinely good at is the thing descriptive notation is bad
at: local ambiguity under global constraint. "The knight gives check" names
two knights and one position usually rules out one of them. What it cannot do
is arbitrate between two readings the rules of chess both permit, and that is
where every disagreement found so far has been.

### What corroborates it

None of these use legality, so none of them can be satisfied by the same
mistake that produced the reading:

| Check | Scope | Result |
| --- | --- | --- |
| Printer's own move numbers (`audit_moves.py`) | 1462 moves | 7 drift |
| Back-game meets parent at the branch move (`branch_audit.py`) | 49 branches | 49 agree |
| Move does what its sentence claims (`check_claims.py`) | 20094 claims | 4 contradict |
| Independent transcription of 5 lines | 160 plies | 159 identical |

The one disagreement in that last row is the d6/d5 edition variance, and the
four in the third are listed in `TODO.md`.

The endgames state their position rather than playing to it -- "Situation of
the White. The king, at his fourth square." -- in the same descriptive
notation as the moves, so `position_board` reads them with the same parser. A
back-game branching off an endgame starts from its parent's position and
replays the parent to the branch move, exactly as an opening back-game does.

### Where the positions came from a person

Four studies had no working board, and I did not get them from the text on my
own. The maintainer supplied a starting position for each, by hand, as a FEN,
and they are kept in `missing.json` at the root. What happened next is worth
recording, because only one of the four was needed in the end and the rest
turned out to be worth more than a patch.

- **One was genuinely missing.** *A Drawn-game with two separated Pawns against
  two united Pawns* has no "Situation of the White" block in the scan at all,
  so there was nothing to read. That position is used as supplied, and is
  recorded in `POSITIONS` in `readings.py` with a note saying so.
- **Two were already built, but a piece short.** A stated position can run two
  pieces onto one line divided by nothing but a comma -- "The king, at his
  fourth square, The bishop, at his king's third square." -- and only the first
  was being read. The bishop was missing from the board, which is why neither
  study could play a third move. The supplied positions showed the bishop on
  e3, which is what sent me looking for the split. Both studies now replay in
  full from the text alone.
- **The fourth needed no position either.** Its board was already right; a
  scan-damaged *move* was stopping it, four plies in.

Three of the four also carried a `Q` where a `K` was meant -- a slip the
maintainer confirmed -- so they had no kings at all and `python-chess` rejected
them outright. That is the argument for asking for FEN rather than a looser
format: a wrong position failed loudly, at once, instead of being accepted and
quietly played on. Had the format merely listed squares, three broken boards
would have gone in unnoticed.

One of the four did not survive checking. For *A Drawn-game with a Rook and a
Pawn against a Rook* the supplied position is neither the one the study starts
from nor any the game passes through, and Philidor's text is unambiguous
about it, line by line:

> The king, at the adverse king's bishop's fourth square. The pawn, at its
> king's fourth square. The rook, at the adverse king's rook's second square.
> ... The king, at his home. The rook, at its queen's rook's third square.

which is `4k3/7R/r7/5K2/4P3/8/8/8` -- white king f5, pawn e4, rook h7 against
a black king on e8 and rook on a6. The supplied board had a white king on g7,
a pawn on f6 and a rook on d3, and nothing in the passage answers to that. It
is left out of `missing.json`, and recorded here instead.

Because three of the four are not needed, they are kept as a standing check
rather than discarded. `check_supplied.py`, in `make check`, holds each to the
board: it must be legal, and must be either the position its study starts from
or one the game actually reaches. Two agree with a position the parser derives
from the text on its own, and the third with the position after ply 13 -- the
branch move of that back-game. That is a second pair of eyes on the parser,
arrived at independently, and it is worth more than the patch would have been.

### The endgames rest on one source

Everything said above about collation covers the openings. The 1790 file in
`../extraction` is **volume I**, which ends "END OF THE FIRST VOLUME" and holds
the parties and gambits; the endgames were in volume II, which is not here. So
chapters 70 to 98 have never been read against a second edition, and the
outside transcription used for the openings does not cover them either.

One reading from another edition has since reached us, and it did both things a
second source can do. It **confirmed** the corrected position of *A Drawn-game
with a Queen against a Rook and a Pawn* -- white queen on b3, not g3 -- which
had been wrong here until the bug below was found. And it **disagreed** about
what the position is worth: that edition heads the study "A check mate with a
queen against a Castle and a Pawn", and gives eighteen moves ending in mate,
where 1777 gives four moves and this note:

> In this position, it is a drawn-game, because the queen cannot take
> backwards, neither the king nor the pawn, as in the former party.

Whether the queen wins there is a question about chess, not about the scan,
and it is not settled here. What is recorded is that the two editions differ,
from a position both agree on. Chapters 70 to 98 should be read with that in
mind.

### Holding a move to what its sentence claims

Philidor does not only name a move, he often says what it does: that it gives
check, that it mates, that it takes a bishop. Each is a statement the board can
test, and `check_claims.py` tests all of them -- twenty thousand claims across
the book.

It exists because of a board that was wrong for a whole study. *A Mate with a
single Rook* opens "The rook gives check", and the scan had dropped a word from
the position, leaving the rook on the king's square rather than the king's
rook's square. From there **no rook check exists at all**. The converter took a
move that fitted the name, ignored the claim, and played on quite happily for
twenty-seven plies from the wrong board. A reader comparing another edition
caught it; nothing here did.

So a claim now costs something. If the text says a move checks and none of the
readings check, the reading that ignores it is demoted to a fallback, which the
search only reaches for when it must -- and `check_claims.py` reports whatever
survives. Four moves still contradict their own sentence, and they are listed
in [TODO.md](../../TODO.md); each looks like a symptom of something wrong
upstream rather than a fault in the sentence.

The general shape is the same as the pawn that had captured, and the queen on
the wrong wing: the text says more than the move, and every part of it that a
board can check is worth checking.

### A wrong board that played perfectly well

Two studies were built on the wrong squares, and nothing in this repository
noticed. Philidor writes the black queen "at her bishop's fourth square" --
*her* bishop, the queen's, so c5. The move parser knows that rule; the position
parser did not, and put her on f5, the king's bishop's file. The same mistake
put a white queen on g3 instead of b3 in another study.

Neither game complained. Both replayed to the same depth from the wrong square
as from the right one, because the moves that follow are legal either way. No
audit here can catch that: legality tests whether a move is possible, not
whether it is the one on the page, and the branch and collation checks compare
games against each other, not against a board a reader can see. It was caught
by the maintainer looking at the rendered board and recognising the queen was
on the wrong side.

Both parsers now take the rule from one `default_wing`, so they cannot differ
again. But the general point stands, and it is the same one the search taught:
a reading can be lawful from beginning to end and still be wrong, and only
something outside the machinery -- another edition, another transcription, or
a person looking at the board -- will say so.

The lesson for anyone supplying one: check first whether the position is
really absent. `games.json` records a `start_fen` for every study whose
position could be built, and a game can have a perfectly good board and still
lack a playable line because a move stopped the reading. See
[CONTRIBUTING.md](../../CONTRIBUTING.md).

**Ambiguity was never the limit.** Backtracking alone took it from 13 to 22
games. What moved it to 44 was reading the text more carefully -- following
pieces through captures, accepting the colour of a square ("the black queen's
bishop's fourth square"), taking a bare "at his third square" to mean the
piece's own file, and using the captured piece's name and the check. Each was
a gap in the parser, not a case needing judgement. So were promotion ("makes
a queen"), a move named by its effect ("the queen's rook attacks the bishop"),
a rank with no file ("the knight, at his third square"), a plural ("one of the
two rooks takes the pawn"), and a line closing on a verdict rather than a move
("Loses the game").

Twenty-one stops remain, and `classify.py` puts seventeen of them on perfectly
clean text -- still parser coverage, not judgement. Two are moves with prose
fused to them and two are plies the scan damaged. Twelve are positions where no
legal move answers the text at all, which means the reading went wrong earlier
or the source is defective; `make stops` lays out the evidence for each.

**Legality is a filter, not an oracle.** A wrong-but-legal reading replays
cleanly and cascades, so the failure surfaces many plies after the mistake: the
First Party used to stop at move 21 on "the queen's rook's pawn, one move" with
no pawn on that file, because the reading had gone wrong at move 14, seven
moves earlier. Worse, a reading can be legal to the end and still be wrong --
the search once completed a game by quietly overriding a misprint. Only
redundancy catches that: the 1790 edition, an outside transcription, the
branch-point positions, and Philidor's own notes.

## Running it

```
uv run python scripts/algebraic_notation/games.py       # -> games.json
uv run python scripts/algebraic_notation/to_pgn.py      # -> pgn/
uv run python scripts/algebraic_notation/build_book.py
cd book && quarto preview
```

`games.json` is the source of truth, not the PGN. It holds the descriptive
original, the note letters, the source line numbers, where a back-game's
inherited moves end, how far the replay reached, and the editorial flags — none
of which PGN can carry, and whose comments cannot even contain a brace. The PGN
files and the book chapters are both generated from it, so improving the parser
regenerates everything instead of stranding hand-edits in a PGN.

Philidor's notes are keyed to individual moves by his own `(a) (b) (c)`
references, so they map onto PGN move comments exactly. Stepping through a
board shows the descriptive text for that move, and any note he wrote about it,
against the move itself. In the book the references are hoverable: the note
appears in a floating panel and goes when the pointer leaves. The panel is
appended to the page body rather than nested in the move list, which scrolls
and would otherwise clip it.

Those letters are repaired in `parse_all` (`../extraction/build.py`) rather
than at render time, so the transcription, `games.json`, the PGN files and the
book all carry the same ones. Repairing at render time meant the book was
showing raw scanner glyphs — an `(l)` read as `(1)`, which no hover could
match, and an `(h)` read as `(b)`, which collided with the real `(b)`.

The notes are not listed again beneath the moves: hovering reads them, and the
downloadable Markdown carries them in full. The exception is a note the scan
left with no reference to call it -- 12 of the 411, across 11 games. Those are
printed, or they would exist only in the download.

Each chapter ends with two download buttons: the game's Markdown, and its PGN
where a board exists. `build_book.py` copies both out of `md/` and `pgn/` into
`book/downloads/` so Quarto serves them. A PGN is labelled *partial* when the
converter stopped before the end of the game -- it holds the moves that
converted, and says where it stopped in a `PhilidorTruncated` tag.

## Checking it

```
uv run python scripts/algebraic_notation/branch_audit.py
uv run python scripts/algebraic_notation/coverage.py
uv run python scripts/algebraic_notation/classify.py
```

**`branch_audit.py` — the best check here.** A back-game must agree with its
parent on the position at the branch move. That is a consistency test needing
no external source at all, and all 48 whose parent replays that far now pass.
It earned its place immediately: it found the bare-qualifier bug above, which
neither the legality replay nor comparison against an outside transcription had
caught.

**Against an independent transcription.** Eight of Philidor's games in
algebraic notation, posted to a
[chess.com thread](https://www.chess.com/forum/view/general/chess-analyse-by-philidor-in-pgn-file),
were matched by their moves — the thread's labels are offset from the 1777
headings, so its "Fourth party" is the 1777 *Third Party*:

| Reference line | This transcription | Result |
| --- | --- | --- |
| "First party, second variation" | First Variable | 6 plies, identical |
| "Fourth party" | Third Party | 64 plies, identical |
| "Second party, first backgame" | First Back-game of the Second Party | 41 plies, identical |
| (main line) | Second Party | 10 plies, identical |
| "Third party" | Another Method of Playing | 39 plies, one difference |

The back-game is the searching one, since it exercises the inherited-prefix
rule: its parent's first four plies are prepended and all 27 match.

That single difference is a real disagreement between the editions rather than
a transcription error. At Black's 4th move 1777 reads "the queen's pawn, one
move" (d6) where 1790 reads "two moves" (d5); the external line agrees with
1790, and so does the play that follows. The 1777 reading is transcribed as
printed and flagged in an editorial note. Nothing about it is detectable by
legality — both readings are legal, which is the whole argument for keeping a
second source in the loop.
