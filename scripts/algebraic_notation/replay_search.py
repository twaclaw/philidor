"""Replay a game by search rather than by resolving each ply in isolation.

Descriptive notation is locally ambiguous but globally constrained: "the knight
gives check" may fit either knight, yet usually only one lets the remaining
moves stay legal. So instead of demanding that every ply resolve on its own, we
try each reading and keep whichever carries the game furthest.

The readings of a ply come back in order of fidelity -- the plainest first --
and the search spends as little as it can on the rest. It widens by iterative
deepening over a budget: first it insists on the plainest reading of every ply,
then allows one departure, then two. Without that it would happily "repair" a
misprint in the source by picking whatever alternative keeps the game legal,
which produces a game that is lawful but not Philidor's.
"""

import re

import chess

from to_algebraic import (Unparsed, advance_origins, initial_origins,
                          ply_readings)

# Two overrides is as far as it is worth reaching: beyond that the reading
# owes more to the search than to Philidor, and the cost climbs steeply.
MAX_NODES = 30000
MAX_BUDGET = 2


def _attempt(seq, budget, nodes, pinned, start):
    """Replay under a budget for departing from the plainest reading."""
    board = start.copy()
    best = {"depth": 0, "san": [], "reason": "no moves", "overrides": []}

    def record(i, why):
        if i >= best["depth"]:
            best["reason"] = "ply %d: %s" % (i + 1, why)

    def descend(i, san, spent, origins, overrides):
        if len(san) > best["depth"]:
            best.update(depth=len(san), san=list(san),
                        overrides=list(overrides))
        if i == len(seq):
            return True
        if nodes[0] > MAX_NODES:
            return False
        side, text = seq[i]
        want = chess.WHITE if side == "W" else chess.BLACK
        if board.turn != want:
            record(i, "side out of turn")
            return False
        # "The same", alone or after the piece that does it ("the king's
        # rook's pawn, the same"), mirrors the move just played.
        if re.search(r"\bthe same\b", text.lower()) and san:
            prev = board.peek()
            mirror = chess.Move(chess.square_mirror(prev.from_square),
                                chess.square_mirror(prev.to_square))
            cands = [(mirror, 0)] if mirror in board.legal_moves else []
        elif i + 1 in pinned:
            # Settled by hand in readings.py, on evidence the converter cannot
            # read. It still has to be a legal move.
            try:
                cands = [(board.parse_san(pinned[i + 1]), 0)]
            except ValueError:
                record(i, "pinned reading %s is not legal here" % pinned[i + 1])
                return False
        else:
            try:
                cands = ply_readings(board, text, origins)
            except Unparsed as e:
                # Philidor sometimes ends a line with a verdict rather than a
                # move -- "Loses the game", "lost every where". The game is
                # over, not broken.
                if i == len(seq) - 1 and "no piece" in str(e):
                    return True
                record(i, str(e))
                return False
        if not cands:
            record(i, "no legal reading")
            return False
        for mv, tier in cands:
            # Choosing between equally faithful readings is free; overriding
            # what the text says is what the budget pays for.
            if spent + tier > budget:
                continue
            nodes[0] += 1
            nxt = advance_origins(origins, board, mv)
            san.append(board.san(mv))
            board.push(mv)
            if descend(i + 1, san, spent + tier, nxt,
                       overrides + ([i + 1] if tier else [])):
                return True
            san.pop()
            board.pop()
        return False

    done = descend(0, [], 0, initial_origins(), [])
    return best["san"], best["reason"], done, best["overrides"]


def best_replay(plies, first_side, pinned=None, start=None):
    """Search for the most faithful complete reading of a game.

    Philidor sets four games out beginning with the Black, meaning the player
    he calls Black has the move; those replay with the roles swapped, so the
    result reads as an ordinary game from the first player's side.
    """
    swap = first_side == "B"
    seq = [("W" if swap and s == "B" else "B" if swap and s == "W" else s, t)
           for s, t in plies]

    deepest = ([], "no moves", [])
    for budget in range(MAX_BUDGET + 1):
        san, reason, done, overrides = _attempt(
            seq, budget, [0], pinned or {}, start or chess.Board())
        if done:
            return san, None, True, overrides
        if len(san) > len(deepest[0]):
            deepest = (san, reason, overrides)
    return deepest[0], deepest[1], False, deepest[2]
