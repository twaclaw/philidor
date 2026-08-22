# Philidor — Analysis of the Game of Chess

PY := uv run python

EXTRACT := scripts/extraction
ALGEB   := scripts/algebraic_notation

SCAN    := $(EXTRACT)/philidor2.txt
COLLATE := $(EXTRACT)/philidor1.txt

# Every game, by the name it is published under in each format.
SLUGS   := $(basename $(notdir $(wildcard md/*.md)))
HTML    := $(addprefix html/,$(addsuffix .html,$(SLUGS)))

# The chapters and the downloads are committed, so the book renders and
# publishes on its own. Where the extraction toolchain is present, rendering
# waits on it as before.
ifneq ($(wildcard $(ALGEB)/build_book.py),)
CHAPTERS := book/games/.stamp
endif

.PHONY: help all book site publish chapters clean clean-data check preview html \
        stops inconsistencies claims certainty
.DEFAULT_GOAL := help

## Print this list
help:
	@awk -F: '/^## / { d = substr($$0, 4); next } /^[a-zA-Z][a-zA-Z0-9_\/.-]*:/ && d { printf "  \033[36m%-16s\033[0m %s\n", $$1 ":", d; d = "" }' $(MAKEFILE_LIST)

## Build the book
all: book

# --- Transcription ---------------------------------------------------------

## Extract the transcription from the scans
philidor.md: $(SCAN) $(EXTRACT)/build.py $(EXTRACT)/extract.py
	$(PY) $(EXTRACT)/build.py

# The per-game files are written in one pass, so a stamp stands for all 96.
md/.stamp: $(SCAN) $(EXTRACT)/split_games.py $(EXTRACT)/build.py $(EXTRACT)/extract.py
	$(PY) $(EXTRACT)/split_games.py
	@touch $@

## Split the transcription into one file per game
md: md/.stamp

# --- Algebraic notation ----------------------------------------------------

## Convert every game to algebraic notation
games.json: philidor.md $(ALGEB)/games.py $(ALGEB)/replay_search.py \
            $(ALGEB)/to_algebraic.py $(EXTRACT)/build.py
	$(PY) $(ALGEB)/games.py

pgn/.stamp: games.json $(ALGEB)/to_pgn.py
	$(PY) $(ALGEB)/to_pgn.py
	@touch $@

## Write one PGN per game
pgn: pgn/.stamp

# --- The book --------------------------------------------------------------

book/games/.stamp: games.json md/.stamp pgn/.stamp $(ALGEB)/build_book.py \
                   book/theme.scss book/_includes/foot.html book/_includes/head.html
	$(PY) $(ALGEB)/build_book.py
	@touch $@

## Regenerate the book's chapters from the data
chapters: book/games/.stamp

# Quarto renders each chapter beside its source and then moves it into the
# output directory. A cache left from an earlier run makes it try to move a
# file it did not write this time, which fails with a bare "NotFound"; both
# are cleared first so a build is always reproducible.
## Render the Quarto book into _site
site: $(CHAPTERS)
	rm -rf book/.quarto book/site_libs _site/site_libs
	find book/games -name '*.html' -delete
	cd book && quarto render

## Build the data and render the book
book: site

## Serve the book with live reload
preview: $(CHAPTERS)
	cd book && quarto preview

## Push the rendered book to GitHub Pages
publish: site
	cd book && quarto publish gh-pages --no-render

# --- A standalone page per game, straight from its Markdown ----------------
# Independent of the book: pandoc turns any downloaded game file into a
# readable page on its own.

## Build a standalone page per game
html: $(HTML)

html/%.html: md/%.md
	@mkdir -p html
	@pandoc --standalone --from=gfm --to=html5 \
	        --metadata pagetitle="$$(sed -n 's/^# //p' $< | head -1)" \
	        --output=$@ $<
	@echo "pandoc -> $@"

# --- Checks ----------------------------------------------------------------

# verify_outputs compares every published form against the scan, so it needs
# the book rendered as well as the data built.
## Run every check against the scan
check: philidor.md games.json md/.stamp pgn/.stamp
	$(PY) $(EXTRACT)/verify_outputs.py
	$(PY) $(EXTRACT)/audit_moves.py
	$(PY) $(EXTRACT)/crosscheck.py
	$(PY) $(ALGEB)/branch_audit.py
	$(PY) $(ALGEB)/check_readings.py
	$(PY) $(ALGEB)/check_supplied.py
	$(PY) $(ALGEB)/check_claims.py
	$(PY) $(ALGEB)/coverage.py
	$(PY) $(ALGEB)/certainty.py

# The evidence at every point a game stops converting: the position, the legal
# moves, the readings offered, and Philidor's note on that ply. This is what a
# reconstruction by hand -- or by a model -- would work from.
## Show the evidence at every ply that stops converting
stops: games.json
	$(PY) $(ALGEB)/stops.py

# How each ply was settled, and what depth-first search is worth against a
# greedy replay that never backtracks.
## Report how each ply was settled
certainty: games.json
	$(PY) $(ALGEB)/certainty.py

# Moves that contradict what their own sentence says they do.
## List moves that contradict their own sentence
claims: games.json
	$(PY) $(ALGEB)/check_claims.py

# The passages where Philidor's notation contradicts itself, with citations.
## List passages whose notation contradicts itself
inconsistencies: philidor.md
	$(PY) $(ALGEB)/inconsistencies.py

## Remove the rendered site
clean:
	rm -rf _site html book/site_libs book/.quarto

## Remove the generated chapters and downloads as well
clean-data: clean
	rm -rf book/games book/downloads
	rm -f md/.stamp pgn/.stamp stops.json
