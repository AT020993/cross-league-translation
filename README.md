# Cross-league translation for European basketball — companion repository

**SSAC 2027 submission:** *"What Does League Translation Add? A Benchmark for European Basketball Forecasts"*.
Its data, saved results, paper, protocols and a one-command check of every abstract number are in
[`ssac27-v10/`](ssac27-v10/README.md). Start there.

The rest of this repository is the earlier companion, cut on 6 September 2026 from the private research
repository at commit `e8f80c52512ff5ae825d2afad9823eafb23057b5` (see `MANIFEST.md`). It accompanied an
earlier draft titled *"Double-counting the career year: cross-league translation from a scheduled natural
experiment in European basketball"* and is kept unchanged as the historical record the submission builds on.
This repository: https://github.com/AT020993/cross-league-translation.

## Provenance a reviewer should know before reading a number

* The abstract's pre-registered holdout figures (17.6% of MAE, Δ 0.71, CI 0.47–0.99) are the
  2026-08-17 record on the first corpus; it lives at
  `docs/research/artifacts/holdout-proballers-2026-08-21/`. `data/processed/translation/validation_summary.json`
  is the second record on the re-fit corpus (19.2%), reported beside it, never as a re-score
  (Amendment 4).
* The earliest independent timestamp of both pre-registrations is 2026-08-17 22:56–22:57 UTC on the
  project's issue tracker; the documents were committed 2026-08-25. The holdout gates have no
  external timestamp that precedes their result — see the Provenance block at the top of
  `docs/research/translation-holdout-preregistration-2026-08-17.md`.
* `scripts/build_nba_arm.py` cannot run here. It needs three inputs and this repository carries
  none of them: NBA per-season rows (public at NBA.com but not redistributable under its terms;
  `scripts/fetch_nba_player_seasons.py`, shipped, documents the endpoints and the layout), the
  EuroLeague game-level corpus, and `data/processed/player_bio.parquet` (first-party birthdates for
  the name-and-birth-year identity step). The arm's record is the committed summary
  `docs/research/artifacts/nba-arm-2026-09-03/nba_arm_summary.json`: the numbers the abstract's
  opening quotes are read from it (171 identified moves; the two directional contrasts on the 141
  walk-forward-scored moves, n = 37 up and 104 down; the mechanism on the 82 with two prior
  seasons), and the script shows the computation, not a rerun.
* Scripts that load the game-level corpus (`build_league_factors.py`, the holdout and walk-forward
  validators, the propositions, hierarchical and dynamic arms) cannot run here either; `reproduce.py`
  recomputes what the two aggregate tables allow and the committed summaries carry the rest.

## What is here

* `scripts/`, `src/` — the estimator (`build_league_factors.py`), the pre-registered holdout
  (`validate_translation_holdout.py`), the walk-forward and regression-to-the-mean comparator
  (`validate_translation_walkforward.py`), the five propositions (`instantiate_translation_propositions.py`),
  the hierarchical and dynamic-ability arms, the conformal interval study, the figure generator, and
  the 2026-27 prediction builder and evaluator. Paths are unchanged, so every script's defaults
  resolve; the pairs table is `pairs.parquet` here and both figure generators resolve that name:
  `python scripts/plot_sloan_abstract_figures.py` regenerates the abstract's two figures beside the
  manuscript's, `python scripts/plot_league_graph.py` the league graph.
* `tests/` — synthetic-data tests for the estimators. They need no data: `pytest tests/`.
* `data/processed/translation/pairs.parquet` — 4,074 same-season dual-tier player-season pairs,
  per-36 aggregates (the identification sample). `switchers.parquet` — consecutive-season transfers
  into EuroLeague / EuroCup, unfiltered, the validation sample. Both are aggregates; no game rows.
* `data/processed/translation/*.json|parquet` — the committed summaries every note quotes.
* `docs/research/` — `METHOD.md`, every research note, every pre-registration and amendment with
  its git history in the private repository (the commit SHAs are cited in the notes).
* `formal/translation-propositions/` — Lean 4 + Mathlib proofs of the five propositions
  (`lake exe cache get && lake build`).

## Reproduce

```
uv sync            # or: pip install numpy pandas scipy matplotlib pyarrow pytest
python reproduce.py
pytest tests/
```

`reproduce.py` recomputes the factor table and the walk-forward ladder from the two derived tables
and asserts them against the committed summaries; it prints which numbers are recomputed and which
are read from JSON (the reliability ceiling and the leave-one-league-out arm need game rows).

## Data terms and licence

See `DATA_TERMS.md` (source credit and scope) and `LICENSING.md` (MIT for the code; see `LICENSE`).
Prediction artifacts: locked sets only; drafts excluded.
