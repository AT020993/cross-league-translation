# Amendment 2 to the SSAC27 full-paper pre-registration: E14 stint selection

**Approval record.**

| | |
|---|---|
| Amends | `docs/research/sloan-full-paper-preregistration-amendment-1-2026-11-04.md`, analysis E14 only |
| Written | 2026-11-05, after gate G14 failed and **before any E14 outcome contrast or E14a profile was computed** |
| Approved by | Amir, "Accept as written", 2026-11-05 |
| Basis | committed and pushed **alone**, before the E14 re-run (METHOD.md §8) |

## What happened

Gate G14 requires the ≥ 8-game rows of the all-arrivals population to reproduce the 674 anchor keys. It failed by one key, with outcomes matching exactly on the other 673. The negative control (floor 9) failed as required. No E14 contrast, profile or playing-time number was computed.

The cause is structural. v10 first keeps continental stints with ≥ 8 games and then picks the player's largest-minutes stint. When the floor is lowered to ≥ 1, the same "threshold, then largest" rule can pick a *different* stint. One 2025 player has 4 EuroCup games (113.5 minutes) and 11 EuroLeague games (82.6 minutes). v10 picks EuroLeague; the literal Amendment 1 rule picks EuroCup. So the literal rule does not nest the anchor population, which was the gate's purpose.

## The change (E14 population rule only)

* A player with **at least one continental stint of ≥ 8 games** enters exactly as in v10: the largest-minutes stint among his ≥ 8-game stints.
* A player with **no ≥ 8-game stint** enters with his largest-minutes stint among stints with ≥ 1 appearance and positive minutes.

This is the v10 ledger's own rule for the remaining players. It makes the ≥ 8-game rows identical to the anchor by construction.

## Specification

| Field | Registered choice |
|---|---|
| Unit | Unchanged from Amendment 1 E14 |
| Population | All-arrivals 2020–2025 under the two-step stint rule above; everything else unchanged |
| Estimator | Unchanged (E14a, E14b, E14c as in Amendment 1) |
| Null | Unchanged |
| Filter | Unchanged, apart from the stint rule |
| Key | Unchanged |
| Uncertainty | Unchanged |

**Gate G14 is unchanged:** ≥ 8-game rows reproduce the 674 keys and `pir_per36_dest` to 1e-9. Its negative control (floor 9 must fail) is also unchanged. One further control is added: the literal Amendment 1 rule must still fail G14, which shows the gate can detect a stint-selection error. Everything else in Amendment 1 E14 stands, including all licences.
