"""Assemble the Proballers training corpus from BOTH trees (ATI-2795).

``data/raw/proballers/`` is the active tree; ``data/raw/_inactive_leagues/
proballers/`` holds spain-acb (11 seasons), bcl (10) and aba-league (11) that
were archived to keep them out of the agent's answer scope. For cross-league
*estimation* we want all of it — the ACB factor sits at the top of the published
league hierarchy and currently rests on a single season, because the active tree
has spain-acb at 7,280 rows / 1 season while the archive has 70,747 / 11.

This module only READS. It does not move directories and does not touch
``leagues.py``: ``is_active=False`` is a product-scope decision and stays.

Why the dedupe is partition-level, not row-level
------------------------------------------------
ATI-2795 specifies deduping on ``(league, season, game_id, player_name)``.
**That key is unsafe**, measured 2026-08-13 on the one partition present in both
trees with differing counts, ``spain-acb 2025``:

* the archive's 276 games are a strict SUBSET of the active tree's 306;
* yet the archive holds 130 ``(game_id, player_name)`` pairs the active tree
  does not, while having FEWER players per game;
* because **113 of those 130 are name variants of the same player** --
  ``Francisco Alonso`` / ``Francis Alonso``, ``Jon Gudmundsson`` /
  ``Jon Axel Gudmundsson``, ``Emanuel Cate`` / ``Emi Cate``.

A row-level union on that key therefore yields 7,408 pairs out of a 7,278-row
superset: ~113 phantom player-games, each splitting one real player into two
identities. A name is not an identity, so it cannot carry a dedupe -- the same
lesson the registry's surrogate ``player_id`` taught.

So when a ``(league, season)`` exists in both trees we pick ONE partition
wholesale, preferring the copy with more distinct games, and record the choice.
The row-level dedupe survives only as a within-partition backstop for exact
duplicates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from src.config.paths import DATA_ROOT

logger = logging.getLogger(__name__)

#: League directories that are fixtures, not data.
FIXTURE_LEAGUES = frozenset({"test"})

#: ``validation/schemas.py`` requires these to be Float64 for a corpus-wide
#: ``pl.concat``; per-file dtypes drift (ATI-2826 repaired some of them), so
#: coerce rather than trust. A concat that fails here is the whole reason the
#: PIR repair had to re-type every file it touched.
FLOAT_COLUMNS = ("pir", "plus_minus", "assists")


@dataclass(frozen=True)
class PartitionChoice:
    """Which tree won a ``(league, season)`` present in both, and why."""

    league: str
    season: str
    chosen: str
    rejected: str
    chosen_games: int
    rejected_games: int
    chosen_rows: int
    rejected_rows: int
    #: Whether every game_id in the rejected copy also appears in the chosen one.
    #: Computed by the loader, which reads both. A subset can be dropped without
    #: losing anything; a partial overlap cannot.
    rejected_games_all_in_chosen: bool

    @property
    def relation(self) -> str:
        """How the two copies relate, in game terms.

        Three states, not two. ``tie`` is equal coverage — benign, and calling it
        "not a subset" reads as an anomaly. ``subset`` means the dropped copy
        added nothing. ``disjoint`` is the one that should stop a reader: each
        tree holds games the other lacks, so choosing one wholesale DOES lose
        data and that partition needs a human rather than this heuristic.
        """
        if not self.rejected_games_all_in_chosen:
            return "disjoint"
        return "subset" if self.rejected_games < self.chosen_games else "tie"

    @property
    def loses_data(self) -> bool:
        """True when dropping the rejected copy discards games."""
        return self.relation == "disjoint"


@dataclass
class CorpusReport:
    """What the loader did. Printed rather than implied.

    A loader that silently drops a partition is indistinguishable from one that
    never saw it, so every skip and every contested partition is recorded.
    """

    rows: int = 0
    leagues: tuple[str, ...] = ()
    partitions_read: int = 0
    partitions_skipped_fixture: tuple[str, ...] = ()
    contested: list[PartitionChoice] = field(default_factory=list)
    rows_dropped_exact_duplicates: int = 0
    coerced_columns: tuple[str, ...] = ()

    def format(self) -> str:
        lines = [
            f"Proballers corpus: {self.rows:,} player-games "
            f"across {len(self.leagues)} leagues, "
            f"{self.partitions_read} league-seasons.",
        ]
        if self.contested:
            lines.append(
                f"  {len(self.contested)} league-season(s) present in BOTH trees; "
                "chose the copy with more distinct games:"
            )
            for c in self.contested:
                flag = " <-- LOSES GAMES, needs a human" if c.loses_data else ""
                lines.append(
                    f"    {c.league} {c.season}: kept {c.chosen} "
                    f"({c.chosen_games} games / {c.chosen_rows:,} rows), "
                    f"dropped {c.rejected} "
                    f"({c.rejected_games} games / {c.rejected_rows:,} rows) "
                    f"[{c.relation}]{flag}"
                )
        if self.rows_dropped_exact_duplicates:
            lines.append(
                f"  dropped {self.rows_dropped_exact_duplicates:,} exact "
                "duplicate row(s) within partitions"
            )
        if self.partitions_skipped_fixture:
            lines.append(
                f"  skipped fixture leagues: "
                f"{', '.join(self.partitions_skipped_fixture)}"
            )
        if self.coerced_columns:
            lines.append(f"  coerced to Float64: {', '.join(self.coerced_columns)}")
        return "\n".join(lines)


def _discover(tree: Path) -> dict[tuple[str, str], Path]:
    """Map ``(league, season)`` to its ``player_stats`` parquet in one tree."""
    found: dict[tuple[str, str], Path] = {}
    if not tree.is_dir():
        return found
    for path in sorted(tree.glob("*/*/player_stats_*.parquet")):
        league, season = path.parts[-3], path.parts[-2]
        found[(league, season)] = path
    return found


def _game_ids(path: Path) -> tuple[frozenset[object], int]:
    """Distinct ``game_id`` set and row count for one partition file.

    Games rather than rows drive the choice: a partition can have more ROWS
    purely because a second scrape spelled some players differently, which is
    not more coverage. Measured on ``spain-acb 2025``, the archive copy had
    FEWER players per game yet 130 ``(game_id, player_name)`` pairs absent from
    the active copy — 113 of them name variants of players already present.
    """
    frame = pl.read_parquet(path, columns=["game_id"])
    return frozenset(frame["game_id"].unique().to_list()), frame.height


def _coerce(frame: pl.DataFrame) -> tuple[pl.DataFrame, list[str]]:
    coerced = []
    for column in FLOAT_COLUMNS:
        if column in frame.columns and frame.schema[column] != pl.Float64:
            frame = frame.with_columns(pl.col(column).cast(pl.Float64, strict=False))
            coerced.append(column)
    return frame, coerced


def load_proballers_player_stats(
    *,
    repo_root: Path | None = None,
    leagues: set[str] | None = None,
    seasons: set[str] | None = None,
    include_archive: bool = True,
) -> tuple[pl.DataFrame, CorpusReport]:
    """Load player-game rows from both Proballers trees.

    Args:
        repo_root: checkout root. Defaults to this file's own repository, so the
            loader does not depend on the caller's working directory.
        leagues: restrict to these league directory names.
        seasons: restrict to these season directory names.
        include_archive: when False, read only the active tree — the control
            condition for "did the archive actually change the estimate?".

    Returns:
        ``(frame, report)``. The frame carries ``_league``, ``_season`` and
        ``_tree`` provenance columns; ``_tree`` is what lets a downstream
        estimator check whether a result rests on archived data.
    """
    data_root = DATA_ROOT if repo_root is None else Path(repo_root) / "data"
    active = _discover(data_root / "raw/proballers")
    archive = (
        _discover(data_root / "raw/_inactive_leagues/proballers")
        if include_archive
        else {}
    )

    report = CorpusReport()
    skipped_fixture = set()

    keys = sorted(frozenset(active) | frozenset(archive))
    chosen: dict[tuple[str, str], tuple[str, Path]] = {}

    for key in keys:
        league, season = key
        if league in FIXTURE_LEAGUES:
            skipped_fixture.add(league)
            continue
        if leagues is not None and league not in leagues:
            continue
        if seasons is not None and season not in seasons:
            continue

        in_active, in_archive = active.get(key), archive.get(key)
        if in_active is not None and in_archive is not None:
            ids_a, rows_a = _game_ids(in_active)
            ids_r, rows_r = _game_ids(in_archive)
            # Prefer more distinct games; on a tie prefer the active tree, the
            # one the daily pipeline keeps current.
            if len(ids_r) > len(ids_a):
                win, lose = (
                    ("archive", in_archive, ids_r, rows_r),
                    (
                        "active",
                        in_active,
                        ids_a,
                        rows_a,
                    ),
                )
            else:
                win, lose = (
                    ("active", in_active, ids_a, rows_a),
                    (
                        "archive",
                        in_archive,
                        ids_r,
                        rows_r,
                    ),
                )
            win_name, win_path, win_ids, win_rows = win
            lose_name, _lose_path, lose_ids, lose_rows = lose
            report.contested.append(
                PartitionChoice(
                    league=league,
                    season=season,
                    chosen=win_name,
                    rejected=lose_name,
                    chosen_games=len(win_ids),
                    rejected_games=len(lose_ids),
                    chosen_rows=win_rows,
                    rejected_rows=lose_rows,
                    rejected_games_all_in_chosen=lose_ids <= win_ids,
                )
            )
            chosen[key] = (win_name, win_path)
        elif in_active is not None:
            chosen[key] = ("active", in_active)
        elif in_archive is not None:
            chosen[key] = ("archive", in_archive)

    frames: list[pl.DataFrame] = []
    all_coerced: set[str] = set()
    dropped_dupes = 0

    for (league, season), (tree, path) in sorted(chosen.items()):
        frame = pl.read_parquet(path)
        before = frame.height
        # Backstop only: exact whole-row duplicates inside one file. This is NOT
        # the cross-tree mechanism -- see the module docstring.
        frame = frame.unique(keep="first")
        dropped_dupes += before - frame.height
        frame, coerced = _coerce(frame)
        all_coerced.update(coerced)
        frames.append(
            frame.with_columns(
                pl.lit(league).alias("_league"),
                pl.lit(season).alias("_season"),
                pl.lit(tree).alias("_tree"),
            )
        )

    if frames:
        corpus = pl.concat(frames, how="vertical_relaxed")
    else:
        corpus = pl.DataFrame()

    report.rows = corpus.height
    report.leagues = tuple(sorted({lg for lg, _ in chosen}))
    report.partitions_read = len(chosen)
    report.partitions_skipped_fixture = tuple(sorted(skipped_fixture))
    report.rows_dropped_exact_duplicates = dropped_dupes
    report.coerced_columns = tuple(sorted(all_coerced))

    logger.info("%s", report.format())
    return corpus, report
