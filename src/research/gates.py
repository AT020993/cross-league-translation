"""Analysis gates that complement src/research (the repo's own guard).

The repo guard already covers: declared threats, join growth, split-half controls,
estimator spread / load-bearing choices, null references, calibration, caveat
closure. These helpers add the four gaps that produced real errors on
2026-08-11/12, and each RAISES rather than returning advice.

Load order: run the repo guard for threat bookkeeping; use these for the
quantitative gates it does not implement.
"""

import numpy as np
import pandas as pd

INTERPRETABLE_RELIABILITY = 0.40


def spearman_brown(r1, n):
    """Reliability of a mean of n exchangeable observations, given r1 per one."""
    return n * r1 / (1.0 + (n - 1.0) * r1)


def per_observation_reliability(r_obs, n_obs):
    """Invert Spearman-Brown: the per-observation r implying r_obs at n_obs."""
    if n_obs <= 1:
        raise ValueError("n_obs must exceed 1")
    denom = n_obs - r_obs * (n_obs - 1.0)
    if denom <= 0:
        raise ValueError(f"r_obs={r_obs} at n_obs={n_obs} implies r1>=1; check inputs")
    return r_obs / denom


def required_n_for_reliability(r_obs, n_obs, target=0.40):
    """How many observations per unit are needed to reach `target` reliability?"""
    r1 = per_observation_reliability(r_obs, n_obs)
    if target >= 1.0:
        raise ValueError("target must be < 1")
    return int(np.ceil(target * (1.0 - r1) / (r1 * (1.0 - target))))


def power_table(r_obs, n_obs, unit_counts, targets=(0.3, 0.4, 0.5, 0.6)):
    """Achievable reliability vs available units.

    unit_counts: per-unit observation counts (a Series or array), e.g. assists per pair.
    Returns one row per target: required n, and how many units actually have it.
    """
    counts = np.asarray(pd.Series(unit_counts).dropna().values, dtype=float)
    rows = []
    for t in targets:
        need = required_n_for_reliability(r_obs, n_obs, t)
        rows.append(
            {
                "target_reliability": t,
                "required_n_per_unit": need,
                "units_available": int((counts >= need).sum()),
                "units_total": int(counts.size),
            }
        )
    return pd.DataFrame(rows)


def assert_powered_for_null(r_obs, n_obs, n_used, target=0.40, label="measure"):
    """Refuse a 'no effect' claim that is really a 'no power' claim.

    THE ERROR THIS EXISTS FOR: a synergy null was reported from a split-half run at
    15 observations per arm, where the achievable reliability was 0.211. The claim
    'the interaction does not clear the threshold' was partly a statement about
    power. Call this before writing any null conclusion from a reliability figure.
    """
    r1 = per_observation_reliability(r_obs, n_obs)
    ceiling = spearman_brown(r1, n_used)
    need = required_n_for_reliability(r_obs, n_obs, target)
    if ceiling < target:
        raise AssertionError(
            f"{label}: at n={n_used} per unit the ACHIEVABLE reliability is "
            f"{ceiling:.3f} < {target}. A null here is 'no detectable effect at this "
            f"sample size', never 'no effect'. Reaching {target} needs n>={need}."
        )
    return {"achievable_reliability": ceiling, "required_n": need, "n_used": n_used}


def split_half_reliability(df, unit, value, half, min_per_arm=25, agg="mean"):
    """Spearman-Brown split-half reliability of `value` per `unit` across `half`.

    Both arms are filtered to min_per_arm observations so the two sides are
    comparable in precision -- the floor is the load-bearing choice, so it is
    returned in the result.
    """
    g = df.groupby([unit, half])[value].agg([agg, "size"]).reset_index()
    w = g.pivot(index=unit, columns=half, values=[agg, "size"]).dropna()
    arms = list(w[agg].columns)
    if len(arms) != 2:
        raise ValueError(f"expected 2 halves, got {arms}")
    ok = (w[("size", arms[0])] >= min_per_arm) & (w[("size", arms[1])] >= min_per_arm)
    w = w[ok]
    if len(w) < 8:
        raise AssertionError(
            f"only {len(w)} units clear min_per_arm={min_per_arm}; "
            "reliability is not estimable"
        )
    r = float(np.corrcoef(w[(agg, arms[0])], w[(agg, arms[1])])[0, 1])
    return {
        "split_half_r": r,
        "reliability_sb": 2 * r / (1 + r),
        "n_units": int(len(w)),
        "min_per_arm": min_per_arm,
        "interpretable": bool(2 * r / (1 + r) >= INTERPRETABLE_RELIABILITY),
    }


#: The shots table's three points-derived flags, named so a consumer can refuse
#: them in one call instead of rediscovering the trap (ATI-2907).
#:
#: MEASURED 2026-08-26 over 461,979 EuroLeague shot rows, seasons 2016-2025:
#:
#:     overall make rate across the table   0.5683
#:     FASTBREAK             flagged 21,592  make% 0.9997  (unflagged 0.5471)
#:     SECOND_CHANCE         flagged 35,804  make% 0.9996  (unflagged 0.5320)
#:     POINTS_OFF_TURNOVER   flagged 46,577  make% 0.9997  (unflagged 0.5199)
#:
#: The table holds makes AND misses, so this is not a makes-only extract -- the
#: flags really are set almost exclusively on made shots.
#:
#: NOT A SCRAPER BUG. The feed's semantics are POINTS SCORED, not possession
#: context: `POINTS_OFF_TURNOVER` says so in its own name, and `FASTBREAK` /
#: `SECOND_CHANCE` inherit the same meaning without saying so. `FASTBREAK == 1`
#: means "this shot produced fastbreak points", not "this shot was taken on a
#: fastbreak". Correct data behind a misleading name.
#:
#: The consequence is that they cannot be shot-STYLE covariates. A role model
#: built on `fastbreak_share` would separate players by how often their shots go
#: in while appearing to describe how they play. PR #1998 dropped all three from
#: the role basis for this reason and used the six coordinate-derived features,
#: whose max |corr| with the player's own FG% is 0.53.
OUTCOME_CONDITIONED_SHOT_FLAGS = (
    "FASTBREAK",
    "SECOND_CHANCE",
    "POINTS_OFF_TURNOVER",
)


def assert_not_outcome_conditioned(df, flag_cols, outcome, max_rate=0.99, min_n=100):
    """Refuse a covariate that is a near-deterministic function of the outcome.

    THE ERRORS THIS EXISTS FOR: (1) the shots table's FASTBREAK / SECOND_CHANCE /
    POINTS_OFF_TURNOVER flags are set on made shots at FG% 0.9996 -- they are
    points-derived, so conditioning on them conditions on the outcome; (2) points
    per ASSISTED shot is exactly 2 or 3, because an assist only exists on a make,
    so any 'assist quality' metric built on realised points is degenerate.
    """
    out = []
    for c in flag_cols:
        f = df[c].astype(str).str.strip().isin(["1", "1.0", "True", "true"])
        n = int(f.sum())
        if n < min_n:
            out.append(
                {"col": c, "n_flagged": n, "outcome_rate": np.nan, "verdict": "too few"}
            )
            continue
        rate = float(df.loc[f, outcome].mean())
        bad = rate > max_rate
        out.append(
            {
                "col": c,
                "n_flagged": n,
                "outcome_rate": rate,
                "verdict": "OUTCOME-CONDITIONED" if bad else "usable",
            }
        )
        if bad:
            raise AssertionError(
                f"{c}: outcome rate {rate:.4f} among flagged rows exceeds {max_rate}. "
                "This flag is derived from the outcome; using it as a covariate "
                "conditions on the result."
            )
    return pd.DataFrame(out)


def assert_degenerate_value_absent(df, value, by, min_unique=2):
    """Refuse a 'value' column that is constant within every level of `by`.

    Points-per-assisted-shot by area is exactly 2 or 3 -- one unique value per
    area -- so a metric weighting it measures only the 2/3 split.
    """
    u = df.groupby(by)[value].nunique()
    if (u < min_unique).all():
        raise AssertionError(
            f"'{value}' takes a single value within every level of '{by}' "
            f"(max unique = {int(u.max())}). It is degenerate by construction: "
            "derive value from ALL attempts, not from realised outcomes."
        )
    return {
        "levels": int(len(u)),
        "min_unique": int(u.min()),
        "max_unique": int(u.max()),
    }


def assert_units_not_inflated(before, after, event_keys, label="rebuild"):
    """Refuse a 'better' join that adds rows while duplicating events.

    THE ERROR THIS EXISTS FOR: re-keying the assist join on a seconds clock added
    948 rows (+0.7%) but pair counts FELL (166 vs 187 at >=40 assists). A duplicate
    check on the event key found 23.2% of new rows duplicated a single assist event
    versus 0% before. More rows and fewer derived units means duplicates.
    """
    d_before = int(before.duplicated(subset=event_keys, keep=False).sum())
    d_after = int(after.duplicated(subset=event_keys, keep=False).sum())
    rate_b = d_before / max(len(before), 1)
    rate_a = d_after / max(len(after), 1)
    res = {
        "rows_before": len(before),
        "rows_after": len(after),
        "dup_rate_before": rate_b,
        "dup_rate_after": rate_a,
        "unique_events_before": int(before.drop_duplicates(subset=event_keys).shape[0]),
        "unique_events_after": int(after.drop_duplicates(subset=event_keys).shape[0]),
    }
    if rate_a > rate_b + 0.01:
        raise AssertionError(
            f"{label}: duplicate rate on {event_keys} rose "
            f"{rate_b:.4f} -> {rate_a:.4f}. "
            f"Rows went {len(before)} -> {len(after)} but unique events went "
            f"{res['unique_events_before']} -> {res['unique_events_after']}. "
            "The added rows are duplicates, not new information."
        )
    return res


def residual_ownership(df, value, group_cols, n_perm=400, seed=3):
    """Is a residual a genuine interaction, or a leftover MAIN effect?

    A true pair/interaction residual should not cluster on either constituent
    alone. Returns the variance share by each grouping against a permutation null.

    THE ERROR THIS EXISTS FOR: pair 'synergy' clustered by SHOOTER at 0.373 vs a
    null 95th percentile of 0.344, while passer and team-season were within chance
    -- the signature of a main effect the marginals failed to absorb. (Removing
    BOTH constituents' means dropped the reliability from 0.503 to 0.348; that
    adjustment does not isolate the shooter, so this permutation test -- not the
    reliability drop -- is what identifies WHICH constituent leaked.)
    """
    rng = np.random.default_rng(seed)
    v = df[value].values - np.nanmean(df[value].values)
    rows = []
    for g in group_cols:
        keys = df[g].values

        def share(vals):
            s = pd.Series(vals).groupby(keys)
            sizes = s.size()
            keep = set(sizes[sizes >= 2].index)
            m = np.array([k in keep for k in keys])
            if m.sum() < 4:
                return np.nan
            vv = pd.Series(vals[m])
            kk = keys[m]
            gm = vv.groupby(kk).transform("mean")
            return float(((gm - vv.mean()) ** 2).sum() / ((vv - vv.mean()) ** 2).sum())

        obs = share(v)
        null = np.array([share(rng.permutation(v)) for _ in range(n_perm)])
        p95 = float(np.nanpercentile(null, 95))
        rows.append(
            {
                "grouping": g,
                "variance_share": obs,
                "null_mean": float(np.nanmean(null)),
                "null_p95": p95,
                "verdict": "ABOVE chance (leftover main effect)"
                if obs > p95
                else "within chance",
            }
        )
    return pd.DataFrame(rows)


def magnitude_in_context(effect_sd, comparators, unit="points per shot"):
    """Force an effect size to be reported against comparators on the SAME scale.

    THE ERROR THIS EXISTS FOR: a figure panel put log-rate SDs (0.186, 0.690)
    beside points-per-shot values (0.033, 0.037) on one axis, making incomparable
    quantities look comparable. comparators: {label: value} in the SAME unit.
    """
    rows = [
        {
            "quantity": "this effect (1 SD)",
            "value": float(effect_sd),
            "unit": unit,
            "ratio_to_effect": 1.0,
        }
    ]
    for k, v in comparators.items():
        rows.append(
            {
                "quantity": k,
                "value": float(v),
                "unit": unit,
                "ratio_to_effect": float(v) / float(effect_sd) if effect_sd else np.nan,
            }
        )
    out = (
        pd.DataFrame(rows).sort_values("value", ascending=False).reset_index(drop=True)
    )
    return out


def assert_gate_rejects(gate_fn, passing_args, failing_kwargs, label="gate"):
    """Negative control: prove a gate can FAIL, not merely that it passed.

    THE ERROR THIS EXISTS FOR: a convergence gate was reported as verified because
    it passed on real posteriors. A gate that only ever passes is indistinguishable
    from one that never checks. It must be shown to raise on bad input.
    """
    try:
        gate_fn(*passing_args)
    except Exception as e:  # noqa: BLE001 — the gate under test may raise anything;
        # narrowing here would let an unexpected exception type masquerade as a pass.
        raise AssertionError(f"{label}: rejected input that should PASS: {e!r}") from e
    for kw in failing_kwargs:
        try:
            gate_fn(*passing_args, **kw)
        except (AssertionError, ValueError):
            continue
        raise AssertionError(
            f"{label}: accepted input it should REJECT ({kw}). "
            "A gate that never fails is not a gate."
        )
    return {"label": label, "passes_good": True, "rejects_bad": len(failing_kwargs)}
