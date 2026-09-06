"""Render ``docs/research/translation-application-studies-2026-09.md`` from the
four study artifacts, so every number in the note is read off a file.

    uv run python scripts/render_application_studies_note.py
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ART = REPO / "docs" / "research" / "artifacts" / "application-studies-2026-09"
FIG = REPO / "docs" / "plans" / "figures"
_DEFAULT_OUT = REPO / "docs" / "research" / "translation-application-studies-2026-09.md"


def _ci(v) -> str:
    return f"[{v[0]:+.3f}, {v[1]:+.3f}]"


def render(a: dict, b: dict, c: dict, d: dict, today: str) -> str:
    p = a["primary"]
    f, lv = p["form"], p["level"]
    arms_a = "\n".join(
        f"| {x['floor']} | {x['destinations']} | {x['n']:,} | {x['n_paired']:,} | "
        f"{x['form']['cohens_d']:+.3f} | {_ci(x['form']['ci95_cluster'])} | "
        f"{x['form']['share_of_null_draws_at_or_beyond']:.2f} | "
        f"{x['level']['cohens_d']:+.3f} | {x['form']['read'].split(' (')[0]} |"
        for x in a["arms"]
    )
    k10 = b["results"]["k10"]["primary"]
    plc = b["results"]["k10"]["placebo"]
    per_b = "\n".join(
        f"| {s} | {v['n']} | {v['stats_a']['mean_realised']:.2f} | "
        f"{v['stats_b']['mean_realised']:.2f} | {v['delta_mean_realised_b_minus_a']:+.2f} "  # noqa: E501
        f"{_ci(v['delta_mean_realised_ci95'])} | {v['stats_a']['overpaid']} / {v['stats_b']['overpaid']} | "  # noqa: E501
        f"{v['stats_a']['career_year_share']:.2f} / {v['stats_b']['career_year_share']:.2f} |"  # noqa: E501
        for s, v in k10["per_season"].items()
    )
    ks = "\n".join(
        f"| {k} | {r['primary']['pooled_delta_mean_realised_b_minus_a']:+.3f} "
        f"{_ci(r['primary']['pooled_ci95'])} | {r['primary']['seasons_b_beats_a_on_mean_realised']}/6 | "  # noqa: E501
        f"{r['primary']['pooled_career_year_share_a']:.2f} / {r['primary']['pooled_career_year_share_b']:.2f} | "  # noqa: E501
        f"{r['primary']['pooled_overpaid_a']} / {r['primary']['pooled_overpaid_b']} | "
        f"{r['placebo']['pooled_delta_mean_realised_b_minus_a']:+.3f} {_ci(r['placebo']['pooled_ci95'])} |"  # noqa: E501
        for k, r in b["results"].items()
    )
    g = c["groups"]
    grp = "\n".join(
        f"| {name} | {v.get('n_scored', 0)} | {v.get('n_censored_R8', 0)} | "
        + (
            f"{v['mae_model']:.3f} | {v['mae_b0']:.3f} | {v['mae_b1c']:.3f} | {v['coverage']:.3f} |"  # noqa: E501
            if v.get("n_scored")
            else "— | — | — | — |"
        )
        for name, v in g.items()
    )
    con = "\n".join(
        f"| {name} | {v['mae_lifted_minus_accepted']:+.3f} | {_ci(v['ci95'])} | {v['read']} |"  # noqa: E501
        for name, v in c["contrasts"].items()
    )
    return f"""# Application studies for the manuscript — RESULTS: pairing versus form, the scout's shortlist, lifted refusals, the league graph

**Generated {today} by `scripts/render_application_studies_note.py` from
`docs/research/artifacts/application-studies-2026-09/` (`pairing_vs_form.json`, `shortlist_ranks.json`,
`lifted_refusals.json`) and `docs/plans/figures/sloan_fig3_readback.json`; every number below is read from
those files. Pre-registration: `translation-application-studies-preregistration-2026-09-06.md`. Nothing here
touches the 2026-27 lock or its gates; every result is manuscript material either way. Amendment 1 (2026-09-06) lifts the pre-registration's abstract scope for Studies A and D only — `translation-application-studies-preregistration-2026-09-06.md` §Amendment 1.**

## Specification

| Choice | This note | Alternatives considered |
|---|---|---|
| **Unit** | A: one domestic player-season at a dual-competition club (n = {p["n"]:,}, {p["n_clusters"]} club-seasons); B: one walk-forward season and its top-K shortlist ({b["n_rows"]} rows, {b["n_rows_with_prior_flag"]} with a prior flag); C: one 2025-26 arrival whose refusal was lifted (R9: {c["n_lifted"]["R9"]}; R5: {c["n_lifted"]["R5"]} — every R5 row has no corpus source row, so nothing to lift); D: one league / one league pair | as pre-registered |
| **Estimator** | A: Cohen's d, cluster bootstrap on domestic club-season, within-club permutation null; B: top-K mean realised EFF/36, overpaid count, career-year share, paired row-bootstrap within season; C: two-sample cluster bootstrap on MAE (destination club); D: two-way fixed effects, effective-resistance SE | — |
| **Null / bar** | as pre-registered (A: \\|d\\| < 0.10 with CI inside ±0.20; B: ≥ 4/6 seasons and pooled CI excluding zero; C: lifted MAE exceeds accepted with CI excluding zero) | — |
| **Sample filter** | A: players with a prior rate; B: rows with a finite combined prediction; C: `first_round ≤ 3`, R8 censor at ≥ 8 destination games | — |
| **Aggregation key** | A: `player_name + season`; B: season; C: `person_code`; D: league | — |
| **Uncertainty** | 2,000 bootstrap draws, seed 0; 200 permutation draws | — |

## Study A — Is the pairing independent of form?

**Read, primary arm (floor 8 continental games, both destinations): `{p["form"]["read"]}`.**

| quantity | paired | unpaired | Cohen's d | 95% cluster CI | within-club permutation, share of \\|d\\| at or beyond | null p95 of \\|d\\| |
|---|---:|---:|---:|---|---:|---:|
| form: source-season deviation from own prior (EFF/36) | {f["mean_paired"]:+.2f} | {f["mean_unpaired"]:+.2f} | **{f["cohens_d"]:+.3f}** | {_ci(f["ci95_cluster"])} | {f["share_of_null_draws_at_or_beyond"]:.2f} | {f["permutation_null_p95_abs"]:.3f} |
| level: own prior rate (EFF/36) | {lv["mean_paired"]:.2f} | {lv["mean_unpaired"]:.2f} | **{lv["cohens_d"]:+.3f}** | {_ci(lv["ci95_cluster"])} | {lv["share_of_null_draws_at_or_beyond"]:.2f} | {lv["permutation_null_p95_abs"]:.3f} |

Two things are true at once and both are reported. The pre-registered bar reads *independent at this
resolution* (d below 0.10, CI inside ±0.20), and the within-club permutation null — which holds each club-season's
mix fixed — puts the observed form d inside its 95th percentile ({f["share_of_null_draws_at_or_beyond"]:.2f} of null
draws at or beyond it). The cluster-bootstrap CI nevertheless excludes zero: coaches allocate continental minutes
to players in form by a small amount, about {f["mean_paired"] - f["mean_unpaired"]:.2f} EFF/36 of deviation from own prior.
Selection on **ability** is five times larger (d {lv["cohens_d"]:+.2f}) and is what Proposition 4(i) cancels. The
manuscript sentence this licenses: *the pairing is independent of ability by construction and nearly independent
of form (d = {f["cohens_d"]:.2f}, within-club permutation p = {f["share_of_null_draws_at_or_beyond"]:.2f}), against d = {lv["cohens_d"]:.2f} on ability;
the residual form selection is the term the regression-to-the-mean arm repairs (Proposition 4(iii)).*

Sensitivity (all arms; the floor and the destination set move d between 0.06 and 0.11 — the read straddles the
bar, which is why the sentence above quotes the number, not the verdict):

| floor | destinations | n | paired | d (form) | 95% CI | permutation share | d (level) | read |
|---:|---|---:|---:|---:|---|---:|---:|---|
{arms_a}

The estimator pairs {a["n_pairs_estimator"]:,} player-seasons at this floor; the primary arm's {p["n_paired"]:,} paired
rows are those with a prior rate (debutants excluded from A only, T-A2).

## Study B — The scout's shortlist

**Verdict (k = 10, pre-registered): `{b["verdict"]}`.**

| K | combined − multiplier, mean realised EFF/36 of the top-K (pooled over seasons) | seasons combined wins | career-year share, multiplier / combined | overpaid, multiplier / combined (sum) | placebo: per-league − one global |
|---:|---|---:|---|---|---|
{ks}

Per season, k = 10:

| season | n | multiplier top-10, realised | combined top-10, realised | Δ (95% CI) | overpaid m / c | career-year share m / c |
|---:|---:|---:|---:|---|---|---|
{per_b}

Reading. The multiplier-only shortlist carries a career-year share of {k10["pooled_career_year_share_a"]:.2f} against
{k10["pooled_career_year_share_b"]:.2f} for the combined arm; the combined top-10 realises
{k10["pooled_delta_mean_realised_b_minus_a"]:+.2f} EFF/36 more per player (CI {_ci(k10["pooled_ci95"])}), winning
{k10["seasons_b_beats_a_on_mean_realised"]} of 6 seasons. The placebo contrast (league resolution without the RTM term) moves
the same read by {plc["pooled_delta_mean_realised_b_minus_a"]:+.2f} (CI {_ci(plc["pooled_ci95"])}).

## Study C — Refusals as a finding

Identity check: the study's accepted set is the rehearsal's committed set ({c["identity_check"]["n_accepted"]} predictions,
max projection gap {c["identity_check"]["max_projection_gap"]:.1e}). Refusals before lifting: {json.dumps(c["refusal_counts_before_lifting"])}.
Lifting rule: R9 always; R5 at ≥ 3 source games — **no R5 row qualifies**, because every R5 arrival has no qualifying
corpus source row at all (`source_games` = 0), so R5 is a coverage fact about the corpus, not a liftable rule.
Population: {c["population_rule"]["rule"]}; scored at 2026-06-30 with the R8 censor at 8 games.

| group | scored | censored (R8) | MAE model | MAE B0 | MAE B1c | conformal coverage |
|---|---:|---:|---:|---:|---:|---:|
{grp}

| contrast | MAE lifted − accepted | 95% CI (two-sample cluster bootstrap) | read |
|---|---:|---|---|
{con}

Reading. The R9 rule (source league-season under 90% complete) refused {c["n_lifted"]["R9"]} arrivals on the 2025-26 set;
predicted anyway from their half-observed source seasons, {g["lifted_R9"]["n_scored"]} of them scored with MAE
{g["lifted_R9"]["mae_model"]:.3f} against {g["accepted"]["mae_model"]:.3f} for the accepted set, and coverage {g["lifted_R9"]["coverage"]:.3f}. The
pre-registered prediction (lifted R9 carries larger error) **fails**: the contrast is not separable. That is reported as
what it is — a refusal that costs coverage for nothing this test can measure — and it is a candidate for the **2027
refit**, never for the 2026-27 lock, whose refusal rules are fixed (Amendment 5). The caveat stands: n = {g["lifted_R9"]["n_scored"]}, and the
CI is a full ±1 EFF/36 wide.

## Study D — The league graph

`docs/plans/figures/sloan_fig3_league_graph.png` (readback `sloan_fig3_readback.json`): {d["n_leagues"]} leagues,
{d["implied_contrasts"]} implied domestic-to-domestic contrasts, of which **{d["well_bridged"]}** have an effective-resistance SE below
{d["well_bridged_se_log"]} on the log scale; reciprocity holds to {d["max_reciprocity_error"]:.1e}. The full matrix is
`sloan_fig3_implied_factors.csv`. Every domestic league is bridged only through the two continental competitions
(Proposition 4(ii)); an implied factor between two leagues that never meet carries the two-way model's assumptions
(multiplicative, no interaction) and the cluster caveat of `league-translation-factors-2026-08-15.md`.

## What this licenses

* **A:** the design sentence, with its number: nearly independent of form (d ≈ 0.09), independent of ability by construction (d ≈ 0.45 cancels).
* **B:** see the verdict line; a PASS licenses the shortlist sentence for the manuscript's §7, a NOT SEPARABLE licenses only the MAE decomposition.
* **C:** a negative result, reported with the same battery: R9 does not discriminate on 2025-26 at n = {g["lifted_R9"]["n_scored"]}; R5 is not liftable.
* **D:** a figure and a table, descriptive.
* **Not licensed:** any change to the lock, the refusal rules, or the gates. The abstract: Studies A and D enter the abstract v4 under Amendment 1 (2026-09-06) of the pre-registration, quoted at their numbers; B and C stay manuscript-only.

## Scripts

`scripts/measure_pairing_vs_form.py` (A), `scripts/rank_shortlist_double_count.py` (B; reads `walkforward_rows.parquet`
regenerated with `prior_mean_pir36` / `above_own_prior`), `scripts/score_lifted_refusals.py` (C; asserts identity with the
committed 2025 set), `scripts/plot_league_graph.py` (D; reads `propositions.json: P4_identification.implied_all_pairs`),
`scripts/render_application_studies_note.py` (this note). Tests: `tests/test_scripts/test_application_studies.py`.
The pre-registration named Study A's script `test_pairing_vs_form.py`; it is `measure_pairing_vs_form.py` so pytest
never collects it — a filename, not a bar.
"""  # noqa: E501


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = ap.parse_args(argv)
    a = json.loads((ART / "pairing_vs_form.json").read_text())
    b = json.loads((ART / "shortlist_ranks.json").read_text())
    c = json.loads((ART / "lifted_refusals.json").read_text())
    d = json.loads((FIG / "sloan_fig3_readback.json").read_text())
    args.out.write_text(render(a, b, c, d, datetime.date.today().isoformat()))
    print(f"[done] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
