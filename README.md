# Philidor's *Analysis of the Game of Chess*

![](./book/assets/philidor_book.jpeg)

I think this is the kind of task where LLMs really shine: text extraction and understanding anachronisms, as well as programmatic and contextual reconstruction, using a chess engine for verification, context information, and human supervision. There has been a lot of hand-holding and verification, but I would say that the results are turning out very nicely.


Every game in Philidor's *Analysis of the Game of Chess*, transcribed from
scans of two eighteenth-century editions, converted to algebraic notation, and
published as a book you can play through.


- **[philidor.md](philidor.md)** — the transcription. 96 games, 1,462 moves,
  2,869 plies, in Philidor's own descriptive notation.
- **`book/downloads/pgn`** — one PGN per game, with his notes as move comments.
- **`book/`** — a Quarto book: one chapter per game, a board on the left,
  Philidor's moves on the right, the two kept in step. Clicking a move plays
  the board to it, the board's controls move the highlight back, and hovering
  a lettered reference shows the note it calls.

## Layout

```
philidor.md                  the transcription, whole
md/                          one file per game, notes set under their moves (downloadable)
games.json                   canonical records; everything downstream is built from these
html/                        a standalone page per game, straight from its Markdown
book/                        the Quarto book
scripts/
  extraction/                scans -> philidor.md, and the checks on it
  algebraic_notation/        descriptive -> algebraic, and everything built on it
```



## Building

```
uv sync         # chess and pyyaml, per pyproject.toml
make            # the book, and everything it needs
make preview    # the book, served
make html       # a standalone page per game, from md/ via pandoc
make check      # every audit
make stops      # the evidence where a game stops converting
make inconsistencies  # where Philidor's notation contradicts itself
make clean
```

## References

- **[Chess analyse by Philidor in PGN file](https://www.chess.com/forum/view/general/chess-analyse-by-philidor-in-pgn-file)**
  — chess.com forum thread. Eight of Philidor's games in algebraic notation,
  the independent reference the conversion was validated against. It holds no
  complete PGN of the book; the poster abandoned that attempt.
- **[Philidor position](https://en.wikipedia.org/wiki/Philidor_position)** —
  Wikipedia, for the rook-and-pawn-versus-rook endgame he analysed in 1777.
- **[Philidor's "L'Analyze des Echecs"](https://en.chessbase.com/post/philidor-s-l-analyze-des-echecs)**
  — ChessBase, on the editions and their publication history.
- **[L'analyze des echecs, 1749](https://archive.org/details/bim_eighteenth-century_lanalyze-des-echecs-co_philidor-f-d-franco_1749_0)**
  and **[Analysis of the game of chess](https://archive.org/details/analysisgameche03philgoog)**
  — Internet Archive scans of the first edition and of an English edition.
- **[Philidor Defence](https://en.wikipedia.org/wiki/Philidor_Defence)** —
  Wikipedia, for the opening named after him.
