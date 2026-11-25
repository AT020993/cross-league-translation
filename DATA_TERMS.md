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

**Status of the two flagged items.** No further answer has been recorded. The author made this
repository public on 29 September 2026 for the SSAC 2027 submission, relying on the 3 September
authorisation for credited publication of derived aggregates.

**SSAC 2027 tables (`ssac27-v10/data/`).** These are of the same class as the tables above: per-season
player aggregates for the domestic and continental sides, with no game-level rows or game dates. They
cover the four factor pools and the forecasting cohort the submission scores. Proballers and the
EuroLeague API are credited as sources. Any rights holder who objects to a file can ask for its removal.

**SSAC 2027 full paper (`ssac27-fullpaper/`, November 2026).** Sources are the same and are credited
the same way: domestic-league statistics from **proballers.com** (Proballers), EuroLeague and
EuroCup statistics from the **EuroLeague API**. Rights in the underlying data stay with them.
The folder adds tables of the kind already published: per-season player aggregates (all 808
continental arrivals of 2020-2025 with at least one appearance; each target's odd/even-game half
rates and career rates per box-score component; model forecasts per target) and one club-season
aggregate (the source club's domestic win share). It relies on the 3 September 2026 authorisation
for credited publication of derived aggregates.

Not published, by rule:

* no raw or per-game file: no EuroLeague or EuroCup API games, box scores or play-by-play, and no
  Proballers game or box-score file;
* no birthdate and nothing a birthdate can be rebuilt from: no ages, so the age analyses (E5b and
  the age features of E16) are carried as committed summaries; the linkage audit (E13) publishes
  its keys, classes and non-birthdate evidence, with birthdates removed;
* no credentials, and no player-level working file the analyses deliberately left uncommitted.

Two things in the folder are not derived from those sources' player statistics. The twelve values
of a league table printed in November 2015 (Layne Vashro, Nylon Calculus) are copied from the
published article with its title, author, date and address; the article's text is not copied.
After the frozen 2026-27 test is scored, a table of named newcomers prints their frozen forecasts
beside their season aggregates so far: professional players in public competitions, player-season
values only, no birthdate and no per-game row.

One table carries dates: the frozen 2026-27 forecast file records, per player-season, the dates of
the first and last source-season game, and per league the last game on disk. It is published
unchanged because its sha256 was recorded at the freeze; it has no game rows.

**Current scope status.** Any rights holder who objects to a file can ask for its removal.
