"""Read one ply of Philidor's descriptive notation into moves on a board.

Nothing here computes a move. Each ply is parsed for what it does say -- the
piece, the square, whether it captures or checks -- and the board is asked for
every legal move that fits. Descriptive notation is ambiguous as language; a
position rarely is.

What comes back is a list of readings in tiers, plainest first: tier 0 answers
to the text, tier 1 contradicts it but keeps the game alive. `replay_search`
does the choosing.
"""

import re

import chess

FILES = {
    "queen's rook": 0, "queen's knight": 1, "queen's bishop": 2, "queen": 3,
    "king": 4, "king's bishop": 5, "king's knight": 6, "king's rook": 7,
}
# Bare names inherit the wing of the piece that is moving.
BARE = {"rook": "rook", "knight": "knight", "bishop": "bishop"}
ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "home": 1, "own": 1,
}
PIECES = {
    "king": chess.KING, "queen": chess.QUEEN, "rook": chess.ROOK,
    "bishop": chess.BISHOP, "knight": chess.KNIGHT, "pawn": chess.PAWN,
}


class Unparsed(Exception):
    pass


def rank_of(ordinal: int, mover_white: bool, adverse: bool) -> int:
    """Descriptive ranks count from the owner's back rank."""
    from_white_side = mover_white != adverse
    return ordinal - 1 if from_white_side else 8 - ordinal


def parse_square(text: str, wing: str, mover_white: bool, ptype=None,
                 own_file=None):
    """Read 'at his queen's bishop's fourth square' into a board square."""
    # The opponent's numbering is signalled either by "adverse"/"adversary's"
    # or by naming his colour: "the black queen's bishop's fourth square".
    adverse = bool(re.search(r"\badvers\w+\b", text))
    if not adverse:
        theirs = "black" if mover_white else "white"
        adverse = bool(re.search(r"\b%s\b" % theirs, text))
    m = re.search(r"\b(\w+)\s+square\b", text)
    if m and m.group(1) in ORDINALS:
        ordinal = ORDINALS[m.group(1)]
    elif re.search(r"(?:'s|\b(?:his|her|its|own))\s+(?:square|place)\b", text) \
            or re.search(r"\bhome\b", text):
        # "at his king's square", "at his square", "at her own home". A piece
        # is at home on the back rank; a pawn is at home on the second.
        ordinal = 2 if ptype == chess.PAWN else 1
        m = re.search(r"(?:'s|\b(?:his|her|its|own))\s+(?:square|place)\b"
                      r"|\bhome\b", text)
    else:
        raise Unparsed("no ordinal: %s" % text)

    # The file is the last piece-name qualifier before the ordinal.
    head = text[:m.start()]
    # Take the last qualifier, and at a tie the longest: in "his king's
    # bishop's second square" both "king" and "king's bishop" start together,
    # and it is the longer that names the file.
    best, key = None, (-1, -1)
    for name, idx in FILES.items():
        for hit in re.finditer(re.escape(name) + r"'?s?\b", head):
            if (hit.start(), len(name)) > key:
                best, key = idx, (hit.start(), len(name))
    if best is None:
        # No wing was named, so a bare "his bishop's third square" takes the
        # wing from the piece that is moving.
        for name in BARE:
            for hit in re.finditer(r"\b" + name + r"'?s?\b", head):
                if (hit.start(), len(name)) > key:
                    best, key = FILES["%s's %s" % (wing, name)], (hit.start(), len(name))
    if best is None and ptype in (chess.QUEEN, chess.KING):
        # "The queen, at her second square" means her own file.
        best = FILES["queen" if ptype == chess.QUEEN else "king"]
    if best is None and own_file is not None:
        # No file named at all: "the king's bishop, at his third square" is
        # that bishop's own file, the one he is named for.
        best = own_file
    rank = rank_of(ordinal, mover_white, adverse)
    if best is None:
        # "The knight, at his third square" names no file. The rank is still
        # known, so the caller is given the whole rank to choose from.
        return None, rank
    return chess.square(best, rank), rank


NOUN = r"(?:king|queen|rook|bishop|knight|pawn|gambit)"
DESCRIPTOR = re.compile(
    r"^(?:the\s+)?((?:%s'?s\s+)*)(%s)\b" % (NOUN, NOUN), re.I)


def piece_and_wing(text: str):
    """Read a descriptor like "the queen's bishop's pawn".

    The piece is the last noun of the possessive chain -- everything before it
    names the file it stands on. Returns its type, the wing it belongs to (so
    a later bare "his bishop's third square" can be resolved), the file it
    started on, and how much of the string was consumed.
    """
    text = re.sub(r"^one of the two\s+", "the ", text)
    text = re.sub(r"\b(king|queen|rook|bishop|knight|pawn)s\b", r"\1", text)
    m = DESCRIPTOR.match(text)
    if not m:
        raise Unparsed("no piece: %s" % text)
    chain = [w.rstrip("'s") for w in m.group(1).split()] if m.group(1) else []
    chain = [w for w in chain if w]
    word = m.group(2).lower()
    if word == "gambit":
        raise Unparsed("gambit's pawn: %s" % text)
    ptype = PIECES[word]

    wing = chain[0] if chain and chain[0] in ("king", "queen") else None
    # The starting file: the whole chain for a pawn, chain + noun for a piece.
    if ptype == chess.PAWN:
        # "queen's bishop's pawn" -> the queen's bishop's file.
        name = " ".join(c + ("'s" if i < len(chain) - 1 else "")
                        for i, c in enumerate(chain))
    else:
        name = " ".join(["%s's" % c for c in chain] + [word])
    return ptype, wing, FILES.get(name.strip()), m.end()


def default_wing(ptype):
    """Whose side a bare qualifier belongs to when none is named.

    "The queen, at her bishop's fourth square" means the queen's bishop, not
    the king's. Anything else takes the king's wing.
    """
    return "queen" if ptype == chess.QUEEN else "king"


def position_board(setup, first_side):
    """The position an endgame study starts from, as Philidor states it.

    He gives it in the same descriptive notation as the moves -- "Situation of
    the White. The king, at his fourth square." -- so it is read with the same
    parser rather than supplied by hand.
    """
    board = chess.Board(None)
    side = None
    for line in setup:
        if line.startswith("Situation"):
            side = chess.WHITE if "White" in line else chess.BLACK
            continue
        if side is None:
            continue
        # The scan sometimes runs two pieces onto one line, divided by nothing
        # more than a comma: "The king, at his fourth square, The bishop, at
        # his king's third square."
        for part in re.split(r"\s*[:;,]\s*(?=The\b)", line):
            part = re.sub(r"^the\s+", "", part.strip().rstrip(".").lower())
            if not part:
                continue
            ptype, wing, hint, end = piece_and_wing(part)
            square, _ = parse_square(part[end:], wing or default_wing(ptype),
                                     side == chess.WHITE, ptype, hint)
            if square is None:
                raise Unparsed("no square: %s" % part)
            board.set_piece_at(square, chess.Piece(ptype, side))
    board.turn = chess.WHITE if first_side == "W" else chess.BLACK
    if not board.is_valid():
        raise Unparsed("position does not stand up: %s" % board.status())
    return board


def find_move(board: chess.Board, ptype, dest, capture=None):
    """The one legal move of this piece type to this square."""
    cands = []
    for mv in board.legal_moves:
        pc = board.piece_at(mv.from_square)
        if pc.piece_type != ptype:
            continue
        if dest is not None and mv.to_square != dest:
            continue
        if capture is not None and board.is_capture(mv) != capture:
            continue
        cands.append(mv)
    return cands


def advance_origins(origins, board, mv):
    """Carry the origin map across one move, without replaying the game.

    Every piece is followed, not only pawns: "the king's knight" stays the
    knight that began on the king's knight's file however far it has ridden.
    """
    out = dict(origins)
    captured = mv.to_square
    if board.is_en_passant(mv):
        captured = chess.square(chess.square_file(mv.to_square),
                                chess.square_rank(mv.from_square))
    out.pop(captured, None)
    piece = board.piece_at(mv.from_square)
    came = out.pop(mv.from_square, chess.square_file(mv.from_square))
    if not (piece and piece.piece_type == chess.PAWN and mv.promotion):
        out[mv.to_square] = came
    if board.is_castling(mv):
        # The rook travels with the king, in a move of its own that the
        # notation does not record.
        rank = chess.square_rank(mv.from_square)
        short = chess.square_file(mv.to_square) > chess.square_file(mv.from_square)
        rook_from = chess.square(7 if short else 0, rank)
        rook_to = chess.square(5 if short else 3, rank)
        out[rook_to] = out.pop(rook_from, 7 if short else 0)
    return out


def initial_origins():
    """Every piece answers to the file it stands on at the start."""
    origins = {}
    for f in range(8):
        for rank in (0, 1, 6, 7):
            origins[chess.square(f, rank)] = f
    return origins


def home_file(square, origins=None):
    """The file a piece is named for: where a pawn began, else where it is."""
    if origins is not None and square in origins:
        return origins[square]
    return chess.square_file(square)


def by_name(cands, file_hint, origins=None):
    """Split candidates by how well each answers to the name given.

    Philidor is not consistent about a pawn that has captured. He calls the
    b6 pawn of the First Party "the queen's rook's pawn", for the file it came
    from; but the d5 pawn of the second party's first back-game, which came
    from the queen's bishop's file, he calls "the queen's pawn", for the file
    it stands on. So both readings are kept, the plainer one first, and the
    search settles it.
    """
    standing = [mv for mv in cands
                if chess.square_file(mv.from_square) == file_hint]
    came = [mv for mv in cands if mv not in standing
            and home_file(mv.from_square, origins) == file_hint]
    rest = [mv for mv in cands if mv not in standing and mv not in came]
    return standing, came, rest


def narrow_tiered(cands, file_hint, ptype, origins=None):
    """Split into readings that answer to the name, and ones that do not."""
    if file_hint is None or len(cands) < 2:
        return cands, []
    standing, came, rest = by_name(cands, file_hint, origins)
    if standing or came:
        return standing + came, rest
    if ptype != chess.PAWN:
        side = 0 if file_hint <= 3 else 7
        best = min(abs(chess.square_file(mv.from_square) - side) for mv in cands)
        near = [mv for mv in cands
                if abs(chess.square_file(mv.from_square) - side) == best]
        if len(near) == 1:
            return near, [mv for mv in cands if mv not in near]
    return cands, []


def narrow(cands, file_hint, ptype, origins=None):
    """Prefer the piece named: by the file it stands on, else where it began."""
    if file_hint is None or len(cands) < 2:
        return cands
    standing, came, _ = by_name(cands, file_hint, origins)
    if standing or came:
        return standing + came
    if ptype != chess.PAWN:
        # A developed piece is identified by whichever is nearer its own wing.
        side = 0 if file_hint <= 3 else 7
        best = min(abs(chess.square_file(mv.from_square) - side) for mv in cands)
        near = [mv for mv in cands
                if abs(chess.square_file(mv.from_square) - side) == best]
        if len(near) == 1:
            return near
    return cands


def tiers(preferred, fallback=()):
    """Tag readings: 0 keeps faith with the text, 1 overrides it."""
    out = [(mv, 0) for mv in preferred]
    out += [(mv, 1) for mv in fallback if mv not in preferred]
    return out


def ply_candidates(board: chess.Board, text: str, origins=None):
    """Every legal move this ply could denote, plainest reading first."""
    return [mv for mv, _ in ply_readings(board, text, origins)]


def ply_readings(board: chess.Board, text: str, origins=None):
    """Every legal move this ply could denote.

    Descriptive notation leaves genuine ambiguity -- "the knight gives check"
    when either knight can -- so the caller may need to try each in turn and
    keep whichever lets the rest of the game replay.
    """
    t = text.lower().strip().rstrip(".")
    t = re.sub(r"\s*\([a-z]{1,2}\)\s*$", "", t)
    t = re.sub(r"\s+", " ", t)

    if "castle" in t:
        avail = [mv for mv in board.legal_moves if board.is_castling(mv)]
        if len(avail) == 1:
            return tiers(avail)   # Philidor often just says "castles"
        want_q = bool(re.search(r"queen'?s?\s*(side|wing)", t))
        named = [mv for mv in avail
                 if board.is_queenside_castling(mv) == want_q]
        return tiers(named, avail)

    white = board.turn == chess.WHITE
    ptype, wing, file_hint, end = piece_and_wing(t)
    if wing is None:
        # "The queen, at her bishop's second square" means the queen's bishop;
        # an unqualified piece otherwise takes the king's wing.
        wing = default_wing(ptype)
    rest = t[end:]

    # "The bishop covers the check": any legal move of that piece answers it,
    # since the side to move is in check.
    if "covers the check" in rest:
        cands = narrow(find_move(board, ptype, None), file_hint, ptype,
                       origins)
        blocking = [mv for mv in cands if not board.is_capture(mv)]
        return tiers(blocking, cands) if len(blocking) == 1 else tiers(cands)

    # A capture: "takes the pawn", "retakes the bishop". "Gives check, and
    # afterwards takes the queen" describes two moves; only the check is this
    # one, so the capture is left for the ply that follows.
    later = re.search(r"\bafterwards?\b", rest) and "check" in rest
    if re.search(r"\b(takes|retakes)\b", rest) and not later:
        target = None
        m = re.search(r"\b(takes|retakes)\b\s*(.*)$", rest)
        tail = m.group(2) if m else ""
        # The piece captured is the last noun of the phrase: in "takes the
        # adverse king's pawn" it is the pawn, not the king.
        nouns = re.findall(r"\b(king|queen|rook|bishop|knight|pawn)('s)?", tail)
        plain = [n for n, poss in nouns if not poss]
        if plain:
            target = PIECES[plain[0]]
        cands = [mv for mv in find_move(board, ptype, None, capture=True)
                 if target is None
                 or (board.piece_at(mv.to_square) or
                     chess.Piece(chess.PAWN, not board.turn)).piece_type == target]
        keep, drop = narrow_tiered(cands, file_hint, ptype, origins)

        # The phrase also says which piece was taken and whether the move gave
        # check: "the knight takes the rook's pawn, and gives check" rules out
        # taking a bishop's pawn, and rules out a capture that checks nothing.
        try:
            _, _, tfile, _ = piece_and_wing(re.sub(r"^the\s+", "", tail))
        except Unparsed:
            tfile = None
        if tfile is not None:
            named = [mv for mv in keep
                     if home_file(mv.to_square, origins) == tfile]
            if named:
                drop = [mv for mv in keep if mv not in named] + list(drop)
                keep = named
        if "check" in rest:
            checks = [mv for mv in keep if board.gives_check(mv)]
            if checks:
                drop = [mv for mv in keep if mv not in checks] + list(drop)
                keep = checks
        return tiers(keep, drop)

    # A pawn push by distance.
    m = re.search(r"\b(one|two)\b\s*(move|moves|step|steps)", rest)
    if m and ptype == chess.PAWN:
        dist = 1 if m.group(1) == "one" else 2
        file_idx = file_hint
        pushes = [mv for mv in find_move(board, chess.PAWN, None, capture=False)
                  if abs(chess.square_rank(mv.to_square)
                         - chess.square_rank(mv.from_square)) == dist]
        if file_idx is None:
            return tiers(pushes)
        standing, came, rest = by_name(pushes, file_idx, origins)
        # The pawn on that file first, then one that began there and has since
        # captured across. Any other pawn contradicts the text, so it is a
        # fallback the search pays for.
        return tiers(standing + came, rest)

    # "The queen's rook attacks the bishop": named by what it does, not where
    # it goes. Offer the moves that would attack such a piece.
    hit = re.search(r"\battacks?\s+(?:the\s+)?(.*)$", rest)
    if hit and "square" not in rest:
        target = None
        for noun, kind in PIECES.items():
            if re.search(r"\b%s\b" % noun, hit.group(1)):
                target = kind
                break
        moves = find_move(board, ptype, None)
        attacking = []
        for mv in moves:
            after = board.copy(stack=False)
            after.push(mv)
            for sq in after.attacks(mv.to_square):
                pc = after.piece_at(sq)
                if pc and pc.color != board.turn and (
                        target is None or pc.piece_type == target):
                    attacking.append(mv)
                    break
        keep, drop = narrow_tiered(attacking or moves, file_hint, ptype, origins)
        return tiers(keep, drop)

    # "The king's pawn makes a queen, and wins the game."
    if re.search(r"\bmakes? a (queen|new queen)\b", rest):
        promos = [mv for mv in find_move(board, chess.PAWN, None)
                  if mv.promotion == chess.QUEEN]
        keep, drop = narrow_tiered(promos, file_hint, chess.PAWN, origins)
        return tiers(keep, drop)

    # "The bishop retires", "the king retires where he pleases": a retreat
    # with no square named. Backward moves are offered first, and the search
    # settles which one the game needs.
    # "Retires", "removes where he can", "where he pleases": a move with no
    # square named at all.
    unspecified = re.search(r"\bwhere he (can|pleases|will|likes)\b", rest)
    if unspecified or (re.search(r"\b(retires?|removes?)\b", rest)
                       and "square" not in rest):
        cands = narrow(find_move(board, ptype, None), file_hint, ptype,
                       origins)
        back = [mv for mv in cands
                if (chess.square_rank(mv.to_square)
                    - chess.square_rank(mv.from_square))
                * (1 if white else -1) <= 0]
        return tiers(back, cands)

    # "gives check" may name no square at all.
    # "Gives check" is Philidor's form for a move that checks. "To give
    # check", "will give check at the next move" and "to avoid a check" all
    # speak of some other move, and must not be read as a claim about this one.
    checking = bool(re.search(r"\bgiv(?:es|ing)\s+check\b|\bchecks\s+the\b",
                              rest))
    dest, rank = None, None
    try:
        dest, rank = parse_square(rest, wing, white, ptype, file_hint)
    except Unparsed:
        if not checking:
            raise

    if dest is None and rank is not None:
        # A rank without a file: any square on it will do.
        on_rank = [mv for mv in find_move(board, ptype, None)
                   if chess.square_rank(mv.to_square) == rank]
        if on_rank:
            keep, drop = narrow_tiered(on_rank, file_hint, ptype, origins)
            return tiers(keep, drop)

    cands = find_move(board, ptype, dest)
    demoted = []
    if checking:
        giving = [mv for mv in cands if board.gives_check(mv)]
        if giving:
            cands = giving
        else:
            # The text says the move checks and nothing here does. Reading it
            # anyway is going against what is written, so it costs the search
            # something -- and it usually means the position is wrong.
            demoted, cands = cands, []
    keep, drop = narrow_tiered(cands, file_hint, ptype, origins)
    drop = list(drop) + demoted

    # Sometimes the piece named cannot reach the square named -- the Fourth
    # Party sends the queen's knight to the king's second square, which no
    # knight of his could do. Rather than trust the square and hand the search
    # a single wrong move, both readings are offered: the square first, then
    # the piece that was named, wherever it can go. The rest of the game
    # decides between them.
    if file_hint is not None and dest is not None:
        if not any(home_file(mv.from_square, origins) == file_hint
                   for mv in keep):
            standing, came, _ = by_name(find_move(board, ptype, None),
                                        file_hint, origins)
            drop = list(drop) + [mv for mv in standing + came
                                 if mv not in keep and mv not in drop]
    return tiers(keep, drop)
