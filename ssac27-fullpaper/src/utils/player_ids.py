"""Canonical player-ID normalisation (ATI-2772).

Raw EuroLeague boxscores right-pad ``Player_ID`` to 10 characters
(``'P003269   '``); every processed artifact stores it stripped. A join
between the two matches **nothing**, and because a Polars left join fills
misses with nulls rather than raising, the failure is silent.

ATI-2767 is what that costs. ``_boxscore_frame`` renamed ``Player_ID`` to
``player_id`` without stripping it, the join matched **0 of 64,706 rows**,
every box column landed 100% null, and a downstream ``fill_null(0.0)`` turned
the box-score baseline into a *constant* — which then read as a fair-fight
AUC of exactly 0.500 and became a load-bearing claim in a design document.

The codebase defended against the padding in ~31 places, each inlined
independently, and that is precisely what made it dangerous: the next new
consumer that forgets produces an empty join, not an error. This module is the
one place that knows the rule, and
``tests/test_architecture/test_no_inline_player_id_strip.py`` keeps it that
way.

ATI-3778 added the other half of the identity rule: the box-score
``Player_ID`` is ``"P"`` + the EuroLeague ``/people`` person code
(``013278`` -> ``P013278``, ``JLX`` -> ``PJLX``). Three hand-written copies of
that disagreed -- always prefix, prefix only if missing, and ``lstrip("P")``
(which strips EVERY leading P) -- and a wrong rule is again an empty join, not
an error. :func:`box_player_id` and :func:`person_code` own it now.

Placement: ``src/utils/`` sits below ``analysis/``, ``models/``, ``agent/`` and
``data/`` — all four import this, so it cannot live in any of them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = [
    "PLAYER_ID_COLUMN_NAMES",
    "box_player_id",
    "normalize_player_id",
    "normalize_player_id_value",
    "person_code",
    "player_id_expr",
]

#: The spellings this column carries across the corpus. Raw EuroLeague
#: boxscores use ``Player_ID``; PBP and most processed frames use
#: ``PLAYER_ID``; the action-value work lower-cases it. Kept here so the
#: structural guard and the callers agree on what "a player-ID column" means.
PLAYER_ID_COLUMN_NAMES: frozenset[str] = frozenset(
    {"PLAYER_ID", "Player_ID", "player_id", "PlayerID", "playerID"}
)


def player_id_expr(column: str = "PLAYER_ID", *, alias: str | None = None) -> pl.Expr:
    """Return a normalised player-ID expression for *column*.

    Casts to ``Utf8`` non-strictly before stripping, which is a deliberate
    superset of the inline copies this replaces: several of them called
    ``.str.strip_chars()`` on a column that is only *usually* a string, and
    would raise on a frame where it arrived as an integer.

    ``alias`` defaults to *column*, so the common
    ``with_columns(player_id_expr("PLAYER_ID"))`` rewrites in place. Pass an
    alias when the normalised value lands in a different column — the
    ``Player_ID`` -> ``PLAYER_ID`` rename that ATI-2767 got wrong is exactly
    that shape, and doing the rename and the strip in ONE expression is what
    makes it hard to do half of it.

    Composes as an ordinary expression, so comparisons and membership tests
    read naturally::

        df.filter(player_id_expr("Player_ID") == pid)
        df.filter(player_id_expr(col).is_in(sorted(player_ids)))
    """
    return (
        pl.col(column)
        .cast(pl.Utf8, strict=False)
        .str.strip_chars()
        .alias(alias or column)
    )


def normalize_player_id(
    df: pl.DataFrame,
    columns: "str | Iterable[str]" = "PLAYER_ID",
    *,
    alias: str | None = None,
) -> pl.DataFrame:
    """Return *df* with each player-ID column normalised in place.

    Missing columns are skipped rather than raising: several callers accept
    frames whose ID column spelling varies by source, and a hard failure there
    would be a behaviour change, not a fix.

    ``alias`` is only meaningful for a single column.
    """
    names = [columns] if isinstance(columns, str) else list(columns)
    present = [name for name in names if name in df.columns]
    if not present:
        return df
    if alias is not None:
        if len(present) != 1:
            raise ValueError("alias is only valid when normalising ONE column")
        return df.with_columns(player_id_expr(present[0], alias=alias))
    return df.with_columns([player_id_expr(name) for name in present])


def normalize_player_id_value(value: object) -> str:
    """Normalise a SCALAR player id (a filter operand, a dict key).

    ``None`` becomes ``""`` so callers can compare without a null check — an
    empty id never matches a real one, which is the safe direction.
    """
    if value is None:
        return ""
    return str(value).strip()


def box_player_id(person_code: object) -> str:
    """The box-score ``Player_ID`` of a ``/people`` person code (ATI-3778).

    Always ``"P"`` + the stripped code, prefixed exactly once: ``013278`` ->
    ``P013278``, ``JLX`` -> ``PJLX``. Never "already prefixed": a letter code
    can itself start with P (``PDK`` -> ``PPDK``), so the input is always read
    as a person code. Pass a box id through :func:`person_code` first.

    An empty code (``None``, NaN, blank) raises rather than becoming ``"P"``,
    which would match nothing and hide the gap. Vectorised callers use
    ``series.map(box_player_id, na_action="ignore")`` so a missing code stays
    missing.
    """
    if isinstance(person_code, float) and person_code != person_code:  # NaN
        person_code = None
    code = normalize_player_id_value(person_code)
    if not code:
        raise ValueError(f"empty person code: {person_code!r}")
    return f"P{code}"


def person_code(player_id: object) -> str:
    """The person code of a box-score ``Player_ID``: strip, then remove ONE
    leading ``"P"`` (never ``lstrip("P")``, which removes every leading P).

    A value without the prefix comes back stripped and otherwise unchanged.
    """
    return normalize_player_id_value(player_id).removeprefix("P")
