# Published league tables used as rivals (SSAC27 Amendment 15, E31)

## `vashro_2015_competition_scores.csv`

Twelve values copied from a published article. They are not player data.

| Field | Value |
|---|---|
| Article | Layne Vashro, "Deep Dives: Measuring Level of Competition Around the World", Nylon Calculus (FanSided), 6 November 2015 |
| Address | https://fansided.com/2015/11/06/deep-dives-measuring-level-of-competition-around-the-world/ |
| Read | 17 November 2026 |
| What the values are | Standardised competition scores from the article's table: 0 is the average competitive venue in its data, 1 is one standard deviation above it. The article built them to adjust pre-NBA production for the level of competition |
| Columns | `league` (this project's league key), `name_as_printed`, `rank_as_printed`, `first_year_as_printed`, `last_year_as_printed`, `score` |
| Check | The values were extracted by a script from the saved text of the page (sha256 of that text: `73f743d5d4077752cc26b2cbd961d3a3f89b55bf29a8549b54c371ff9ff6feed`) and compared with the list in Amendment 15. The article text is not copied into this repository |

## Specification

| Field | Registered choice |
|---|---|
| Unit | One competition |
| Population | The ten source leagues of the paper and its two destination competitions |
| Estimator | None. Published values, copied |
| Null | Not applicable |
| Filter | The twelve competitions named in Amendment 15 |
| Key | `league` |
| Uncertainty | None is given by the source for single competitions |
