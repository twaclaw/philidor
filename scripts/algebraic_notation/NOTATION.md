# Philidor's notation, and where it contradicts itself

Descriptive notation is a system, and Philidor mostly keeps to it. But every
rule the converter follows had to be loosened to fit him, and each loosening
was forced by a specific passage. This records those passages.

Regenerate the citations with:

```
uv run --with chess python scripts/algebraic_notation/inconsistencies.py
```

## The system, in short

A piece is named for the file it stands on at the start of the game: the
**queen's rook** is the a-file, the **king's knight** the g-file. A square is
named by file and rank counted **from the owner's own back rank**, so White's
"king's fourth square" is e4 and Black's is e5. To name a square on the far
side he says *adverse* or *adversary's*, and the count runs from that side
instead.

The important part is that a piece keeps its name for the whole game. The
knight that began on g1 is "the king's knight" wherever it later stands. That
is the one rule the converter most depends on, and also the one he breaks.

## 1. A pawn that has captured

A pawn changes file when it captures, and then two names fit it: the file it
began on, and the file it now stands on. **Philidor uses both.**

**Named for where it began — 9 instances.** The clearest is the First Party.
At move 14 Black recaptures with the a-pawn, `axb6`, and the pawn now stands on
the knight's file. Seven moves later:

> **First Party, move 21, Black** — "The queen's rook's pawn, one move."
> The pawn stands on b6; it began on the queen's rook's file. The move is `b5`.

He is still calling it the queen's rook's pawn. Note (i) to that game confirms
the capture was intended, remarking that taking the bishop "would make an
opening to his queen's rook" — the a-file, opened precisely because the a-pawn
left it.

The same in the First Gambit, where the pawn that took on f4 came from e5:

> **First Gambit, move 9, Black** — "The king's pawn takes the pawn."
> The pawn stands on f4; it began on the king's file. The move is `fxg3`.

**Named for where it stands — 40 instances.** The opposite habit is commoner:

> **First Party, move 12, White** — "The queen's pawn retakes it."
> The pawn stands on d4; it began on the queen's bishop's file. The move is `dxe5`.

> **First Party, move 32, White** — "The king's bishop's pawn, one move."
> The pawn stands on f5; it began on the king's knight's file. The move is `f6`.

So neither rule holds. The converter offers both readings — the pawn standing
on that file first, the one that began there second — and the search decides
from the rest of the game. Insisting on either alone loses games: this was what
stopped the First Party at move 21, and forcing the other rule instead broke a
back-game that had been correct.

## 2. A piece that cannot reach the square he names

Once, and only once in the whole book, the sentence names a piece and a square
that piece cannot reach, though another piece of the same kind can.

> **Fourth Party, move 8, White** — "The queen's knight, at his king's second
> square."

The position is `rnb1kb1r/ppp2qpp/5n2/5p2/3PpP2/2P1B3/PP4PP/RN1QKBNR w`. His
knights stand on b1 and g1. The king's second square is e2, and `Ne2` is legal
— but only from g1. From b1 a knight can reach a3 or d2, never e2. Either the
piece or the square is misprinted, and the text gives no way to tell which.

That is the only one the evidence supports. Twenty-two further plies also had to
be read against the text, but they are not his fault: in each, the faithful
reading is available and legal, and the search departed from it because that
reading leads nowhere later. The divergence is ours, several moves earlier, or
damage further on. `inconsistencies.py` lists them separately and they should
not be read as his mistakes.

I had this wrong at first. The second-back-game-of-the-second-gambit case
looked like a twin of the Fourth Party until the position was checked: the
king's rook stands on h8, `Rhg8` is legal and is what the parser offers first.
The test now asks the narrower question — can the piece he *names* reach it? —
rather than whether anything of that kind can.

## 3. Four ways of pointing across the board

| Wording | Plies | Example |
| --- | --- | --- |
| *adverse* | 372 | "takes the adverse queen's pawn" |
| *adversary's* | 44 | "at the adversary's king's third square" |
| the colour, *black* | 3 | "The queen's bishop takes the black bishop." |
| the colour, *white* | 1 | "the white pushes to the queen" |

The last two matter more than their count suggests: a square named by colour
counts from that player's side, exactly as *adverse* does, and reading "the
black queen's bishop's fourth square" from the wrong end puts the move on the
wrong half of the board.

## 4. One letter, two notes

Notes are lettered a…i, k…u, w, x, y — the eighteenth-century sequence, which
omits *j* and *v*. In five games a letter is used twice:

- First Party — **(x)** twice
- First Variable — **(a)** twice
- Third Back-game of the Gambit of Salvio — **(c)** twice
- Back-game of the Supplement to the First Gambit — **(a)** twice
- Variable of the same Party of the Gambit — **(a)** twice

This is not harmless. The book shows a note by hovering the reference that
calls it, and a dictionary keyed by letter kept only the second of each pair,
so one note in each of those games was reachable from nowhere. References are
now taken in reading order.

## 5. "The same", two constructions

Thirty-five plies are just "The same." — repeat the move your opponent has
played, mirrored. One is not:

> **"The king's rook's pawn, the same."**

Same meaning, with the piece named as well. A parser that only recognised the
bare form stopped dead on it.

## 6. Where the printing itself fails

Distinct from the above, and recorded in the transcription rather than worked
around:

- **Two White moves at move 30** of the seventh back-game of the First Gambit,
  with Black's reply and the number 31 both missing. Black's move is lost.
- **A `W.` that must be `B.`**, where Black's king answers a check and both
  plies are set as White's. Corrected in the `ERRATA` table of
  `../extraction/build.py`, keyed to the line of the scan it alters.
- **d6 for d5** at Black's 4th in *Another Method of Playing*. The 1790 edition
  and modern transcriptions both read "two moves"; 1777 reads "one move", and
  the play that follows assumes d5. Transcribed as printed, flagged in an
  editorial note.
- **Move numbers omitted or garbled** — `37-`, `3:`, `ΙΙ.` in Greek letters, and
  a missing "4." in *Another Method of Playing*. The converter pairs plies into
  moves itself and checks the result against the printed numbers rather than
  trusting them; 89 of 96 sections agree exactly.
