# The rules Philidor played by

The 1777 edition closes with seventeen rules, "which the Society or Club of
Chess in England have adopted for their code". Several differ from the modern
laws, and two differ from Philidor's own earlier edition. They are worth
setting out, because a game read under the wrong rules can look like a mistake
when it is nothing of the kind.

Everything quoted here is from the closing section of the 1777 scan, after the
games and before the end of the book. It is transcribed but not part of
`philidor.md`, which stops at the last game.

## Stalemate was a win for the stalemated player

The largest difference, and the one most likely to mislead:

> **XVI.** When one has nothing else to play, and his king being out of check
> cannot stir without coming to a check, then the game is stale-mate. **In
> England, he whose king is stale-mate wins the game;** but in France, and
> several other countries, the stale-mate is a drawn game.

So under the code this book prints, stalemating your opponent **lost** you the
game. Modern law makes it a draw everywhere, and the English rule died out in
the early nineteenth century.

It matters for reading the endgames. Where Philidor calls a position drawn, or
warns against a line, the reasoning may rest on a stalemate being worth a whole
point rather than half — and the book was published in England, under the rule
that made it a win.

No game in this transcription ends in stalemate, so nothing here turns on it
directly.

## Promotion had been restricted, and was not

> **IX.** Every pawn which has reached the eighth or last square of the
> chess-board, is intitled to make a queen, or any other piece that shall be
> thought proper; and this, **even when all the pieces remain on the
> chess-board**.

The clause in bold settles an old dispute about whether a second queen was
allowed. A marginal note records that the 1749 edition had it otherwise — the
scan is damaged here, and reads:

> This was much [more?] reasonable in th[e] Edition of 1749. The Pa[w]n at its
> last square [could] only be changed for any Pi[e]ce which [...]

That is, in 1749 a pawn could only be promoted to a piece that had already been
captured. So the rule changed between Philidor's own two editions, and this
book prints the later one.

One pawn promotes in the converted games — `e8=Q+` in the second back-game of
the First Party, "The king's pawn makes a queen, and wins the game" — and it is
a queen, so the difference does not bite.

## Castling was still unsettled elsewhere

> **XI.** The king, when he castles, can only go beyond two squares, that is,
> the rook with which he castles must take its place next to the king, and this
> last, leaping over, will be posted on the other side of the rook.

That is modern castling, described rook-first. But the footnote is the
interesting part:

> **(a)** The old way of castling in several countries, and which still
> subsists in some, was to leave to the player's disposal, all the interval
> between the king and the rook, inclusively, to place therein these two
> pieces.

Free castling — placing king and rook anywhere between their squares — was
still current somewhere in 1777. The English code had already dropped it, which
is why all 66 castlings in these games are the modern move and replay without
complaint.

> **XII.** The king cannot castle when in check, nor after having been moved,
> nor, if in passing he was exposed to a check.

Also modern, though it is silent on castling *into* check, which the wording of
XI arguably covers.

## The fifty-move rule was something you asked for

> **XVII.** At all the conclusions of parties, when a player seems not to know
> how to give the difficult mates, as that of a knight and a bishop against the
> king, that of a rook and a bishop against a rook, &c. at the adversary's
> request, fifty moves on either side must be appointed for the end of the
> game: these moves being over, it will be a drawn game.

Not automatic, as it is now, but claimed — and claimed specifically against a
player who appears not to know the mate. The two mates it names are chapters
70 and 74 of this book, which is presumably the point: Philidor is teaching
exactly what the rule assumes you might not know.

## En passant, as now

> **X.** Any pawn has the privilege of advancing two squares, at its first
> move: but, in this case, it may, in passing, be taken by any pawn which might
> have taken it if it had been pushed but one move.

Worth noting only because the capture was still refused by the Italian school
at the time. The code here takes it for granted.

## A rule with no modern counterpart

> **XV.** If any one touches a piece which he cannot play without giving check,
> he must then play his king.

A touch-move rule with a peculiar consequence attached. Modern law simply
requires a legal move with the touched piece if one exists.

## What this means for the transcription

Nothing here required the converter to depart from modern rules. All 66
castlings, the single promotion and every capture are legal under both codes,
and `python-chess` — which enforces the modern laws — replays 76 of the 96
games without complaint.

The place to keep the old rules in mind is the reasoning rather than the moves:
when Philidor calls a position won or drawn, particularly in the endgames, he
is judging it under a code where a stalemate was a win in the country the book
was printed in.
