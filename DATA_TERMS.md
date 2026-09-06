# Data terms

**Sources.** Domestic-league box scores were collected from **proballers.com** (Proballers,
Benoît Dujardin, Publishing Director); the continental side (EuroLeague, EuroCup) is read from the
**EuroLeague API**. Rights in the underlying data stay with their owners. Proballers is credited in
the paper, in this repository and in any talk or poster, per the authorisation of 2026-09-03.

**What Proballers was asked, and granted.** Publication of aggregated derived statistics (per-league
translation factors, error rates), and sharing of *one* derived table of roughly five thousand rows,
one per player-season observed in two competitions, containing per-36-minute aggregates rather than
game-level data, so that reviewers can reproduce the result. That table is
`data/processed/translation/pairs.parquet`.

**Beyond the letter of that request — flagged, not assumed.**
* `data/processed/translation/switchers.parquet` is a *second* derived table of the same class
  (player-season aggregates, no game rows): the consecutive-season transfers the validation scores.
  The paper cannot be reproduced without it. Its inclusion is to be confirmed with Proballers when
  the draft is sent before 1 October 2026; until then this file should be treated as provisional.
* `scored_switchers.parquet` and `factors_heldout_le2023.parquet` are subsets and fitted tables of
  the above.
* The EuroLeague API side: no statement of redistribution terms has been obtained; the rows here
  are per-36 aggregates and the API is credited. To be confirmed with the same care.

**No game-level data.** The export refuses any parquet carrying a `game_id` or a game date.

**Status of the two flagged items.** Pending Proballers' answer; the repository stays private until both are settled (re-cut with `--data-terms-note` once it arrives).
