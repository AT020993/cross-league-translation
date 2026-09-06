# The pre-registered holdout record — Proballers destination side, 2026-08-21 reproduction

These are the outputs of `scripts/validate_translation_holdout.py` and `scripts/validate_translation_walkforward.py`
on the corpus of 2026-08-17/21 (both sides Proballers), the record the abstract's holdout figures are read
from: verdict PARTIAL, Arm A n=231, model MAE 3.3325 / R² 0.3156, B0 4.0449 (17.6%), Δ +0.7124
[+0.4731, +0.9859], B1b 3.3275, Arm B 10/10, coverage 0.922, reliability 0.699, residual SD 3.947.
Until 2026-09-06 the directory lived only at the gitignored path
`data/processed/translation_proballers_2026-08-21/` — a cloner found the API-side second record
(`data/processed/translation/validation_summary.json`, 19.2%) and nothing behind the printed 17.6%.
Amendment 4: this record is not re-scored; the API-side run is a second record beside it.
No game-level rows; `league_factor_pairs.parquet` (player-season pairs) is deliberately not copied here.
