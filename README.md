# European League Equivalents: companion repository of the SSAC 2027 full paper

**Paper:** *"European League Equivalents: One Number per League, Tested on League Changes It Was Never Fitted To"* (Amir Tahori; MIT Sloan Sports Analytics Conference 2027,
research paper competition, Paper ID 47).
**This repository:** https://github.com/AT020993/cross-league-translation

Everything needed to check the paper is here: the paper, its pre-registration with all
32 amendments, the result files behind its numbers, the analysis code as it was run, and
the per-season tables from which the main results are recomputed. One command recomputes the main
results and confirms, by file hash, the results it cannot recompute.

## The paper in short

The paper gives one number for each of ten European domestic basketball leagues. The number says
what a player's box-score rate in that league is worth, compared with the same rate in another
league, when he moves up to EuroLeague or EuroCup. The paper tests these numbers on players who
changed domestic league. It also finds that the usual tool for this job, a translation factor
(the average ratio of players' rates in the two competitions), adds nothing detectable once a
forecast has the league numbers. The abstract, word for word:

> European clubs recruit for EuroLeague and EuroCup from domestic leagues whose box scores are not directly comparable. This paper sets the established adjustment, a translation factor, against a plainer benchmark that needs only past arrivals: one number per source league. These are the European League Equivalents, in box-score efficiency per 36 minutes (EFF/36): when career history equals the domestic rate, 16 EFF/36 in Spain's ACB gives the same forecast as about 19 in Germany, Lithuania or VTB. In a test registered and frozen before its outcomes were read, 1,649 players who changed domestic league moved in the direction the table implies, at about three quarters of its size (slope 0.77, 95% interval 0.69 to 0.84). On these league changes and the 2020–2025 arrivals, the paper's league numbers and a league table printed in 2015 are not distinguishable; this paper adds that registered test and an interval for each league number. On those arrivals, examined before registration and so exploratory, a translation factor adds nothing detectable on top of the league numbers: −0.002 EFF/36 (95% interval −0.028 to 0.024). Once the destination is known, knowing the source league improves the forecast slightly for the 2020–2025 arrivals; on 180 older arrivals from two leagues it did not. Forecasts frozen on 3 November 2026, after the season began but before outcome inspection, were scored once on 2026–27 newcomers. That test, separate from the test on league changes, is inconclusive: 7 newcomers without a forecast may be in the frozen file under another spelling, more than the 5% of the 94 joined newcomers that was allowed in advance.

## If you are reviewing the paper

1. **Read the paper.** `ssac27-fullpaper/docs/paper/ssac27/rendered/manuscript.md` is the full text with its tables;
   the figures are in the `figures/` folder beside it (the table "Figure files" below says which
   file is which figure). The PDF submitted to the conference is this text, laid out in the
   conference's Word template; the PDF and the Word file are not in this repository. In the
   Markdown, equation references appear as labels such as `(@eq:model)`; the PDF prints their
   numbers.
2. **Check it in one command.** You need Python 3.13. The first four lines download the
   repository and the packages. The last line is the check: it takes three to ten minutes on a
   recent laptop and makes no network request.

   ```sh
   git clone https://github.com/AT020993/cross-league-translation.git
   cd cross-league-translation
   python -m venv .venv && source .venv/bin/activate
   python -m pip install -r requirements.txt
   python reproduce.py --section fullpaper
   ```

   (`python` must be Python 3.13. On Windows, activate with `.venv\Scripts\activate`.)
   The run ends with a list of its steps, each marked `ok`, `FAILED` or `not run`, then the line
   `FULL-PAPER REPRODUCTION PASSED`, then a short summary whose last line is `fullpaper: passed`.
   If a step fails, its message is printed above that list. The full message is in
   `ssac27-fullpaper/recomputed/report.json`, a file the run writes; every later run, also the one
   of step 3, replaces it.
3. **Check the registrations.** `REGISTRATION_HASHES.md` has 38 rows: the
   pre-registration, the 32 amendments and the frozen files. Each row gives a file name
   and its sha256, a fingerprint that changes if one byte of the file changes. This command
   compares each row with the file it names; it takes about a second and ends with
   `CHECK OF REGISTRATION PASSED`:

   ```sh
   python ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py --only registration
   ```

   The command shows that the files match the list. It does not show when each row became
   public. For that, read the commit history of the list
   (`git log --format='%h %cI %s' -- REGISTRATION_HASHES.md`, or the History button on the
   file's GitHub page). The heading of the list names the paper by the title it had on 16
   November 2026; rows and notes of the list are only ever added, so the heading stays.
4. **Try the result.** Open `ssac27-fullpaper/converter/index.html` in a browser. It is one file
   and loads nothing from the network. It shows the fitted equation, the ten league numbers, a
   table of how often the player with the higher forecast turned out better, and a small
   calculator. To test a league table of your own on the paper's arrivals, write a CSV with the
   columns `league,score` and follow "Score your own league adjustment" in
   `ssac27-fullpaper/README.md`.

## What a pass shows, and what it does not

A hash check shows that a file is the one the paper was written from. It does not show that the
result in it is right; only the rows marked **recomputed** do that. The rows that are carried
need data this repository does not publish: per-game files, birthdates and player-level rows
(rights of the data providers and personal data; see `DATA_TERMS.md`).

| Analysis | Here | From what, or why not |
|---|---|---|
| G0, E1/E2: the submitted numbers, the forecast ladder, six translation recipes | **recomputed** | the published v10 tables |
| E7-E9: pairwise decisions, error bands, the league table | **recomputed** | the published v10 tables |
| E10-E12, E17 and the Equivalents table (Amendment 1) | **recomputed** | the published v10 tables and the results above |
| E14a-c: who the eight-game rule leaves out | **recomputed** | the 808-row tables of all arrivals |
| E15a-b: which skills travel | **recomputed** | the per-component tables of the 674 targets |
| The three vignettes | **recomputed** | the published v10 cohort table, the E16 forecasts and the Equivalents table |
| E27: the three comparisons of the older-seasons test | **recomputed** | the printed arrival rows |
| E30: the slope of the league-changes test, and the slope without Spain | **recomputed** | counts and mean residuals per league pair |
| E31a and E31c: the 2015 league table as a rival, and the second frozen forecast file | **recomputed** | the keyed forecasts and the pinned frozen file |
| The fitted equation: it gives back the Equivalents and the frozen 2026-27 forecasts (gate G30a) | **recomputed** | the committed coefficients and the committed forecasts |
| E3-E6: robustness (outcomes, destinations, seasons, ages, noise floor) | carried, hash-checked | needs per-game rows and ages, which are not published |
| E13, E25, E26: linkage and identity audits | carried, hash-checked | need birthdates and raw API rosters |
| E16: flexible models | carried, hash-checked | needs age features and game files |
| E18-E24 (Amendments 3 and 4; exploratory) | carried, hash-checked | their generator rebuilds season tables from raw game files, which are not published, so this script cannot re-run them |
| E27: freeze, linking and gates of the older-seasons test | carried, hash-checked | needs league-site box scores |
| E28, E29 (Amendments 9 and 11) | carried, hash-checked | need the older-season rows, which are not published |
| E30: the player-bootstrap intervals; E33 (Amendment 22; exploratory) | carried, hash-checked | need player-level league changes and stayer rows |
| E34 (Amendment 23, rule 5; exploratory): two published league scales on the older arrivals | carried, hash-checked | needs the older-season rows, which are not published |
| The 2026-27 freeze (rebuild from raw files) and its scoring | carried, hash-checked | need raw 2025-26 and 2026-27 game files; the frozen file is checked against the sha256 recorded at the freeze |

The numbers of the paper's text are mapped in
`ssac27-fullpaper/docs/paper/ssac27/paper-numbers.json`: 3,972 number tokens: 2,434 are traced to a result file and key, 1,389 are labels (years, citation numbers, units, the reference list) and 149 are listed as typed (protocol constants such as the 2% margin, and result values that the map could not match to one key without ambiguity). The run composes the manuscript
again from the result files and it must match the rendered manuscript byte for byte.

`ssac27-fullpaper/README.md` has the details: where the main items of the paper come from (Table 1,
the figures of the main text, the slope of the league-changes test), the steps of the run, the
input tables with their row counts, and what is not published and why.

## What is where

| Path | What it is |
|---|---|
| `ssac27-fullpaper/README.md` | The detailed guide to the full-paper folder |
| `ssac27-fullpaper/docs/paper/ssac27/rendered/` | The paper (Markdown) and its figures |
| `ssac27-fullpaper/docs/paper/ssac27/` | The template the paper is rendered from and the map of its numbers |
| `ssac27-fullpaper/docs/research/` | The pre-registration of 3 November 2026, its 32 amendments and the results notes |
| `ssac27-fullpaper/docs/research/artifacts/` | The committed result files of every analysis, the frozen forecast files and the per-season tables added for the full paper |
| `ssac27-v10/data/` | The per-season tables published with the submitted abstract; the full paper's recomputation reads them too |
| `ssac27-fullpaper/scripts/`, `ssac27-fullpaper/src/` | The analysis code as run, the renderer and the reproduction script |
| `ssac27-fullpaper/converter/index.html` | A one-file calculator for the league numbers |
| `ssac27-fullpaper/REDACTIONS.json` | The files changed on the way out of the private repository, with both hashes |
| `REGISTRATION_HASHES.md` | sha256 of the pre-registration, its amendments and the frozen files |
| `MANIFEST.json`, `MANIFEST.md` | sha256 of every other file of this repository |
| `reproduce.py` | Runs the checks |
| `DATA_TERMS.md`, `LICENSING.md`, `LICENSE` | Sources and credit; licences |

### Figure files

The file names are older than the figure numbers and do not follow them.

| Figure of the paper | File in `ssac27-fullpaper/docs/paper/ssac27/rendered/figures/` |
|---|---|
| Figure 1 | `fig1_equivalents.png` |
| Figure 2 | `fig4_bias.png` |
| Figure 3 | `fig_mechanism.png` |
| Figure A1 | `figA1_robustness.png` |
| Figure A2 | `fig3_decisions.png` |
| Figure A3 | `fig_stability.png` |
| Figure A4 | `fig_gap_guide.png` |
| Figure A5 | `fig_bands.png` |
| Figure A6 | `fig2_avoidable.png` |
| Figure A7 | `fig_skills.png` |

## Earlier stages

Two earlier stages of the same research are kept unchanged, as history.

| Folder | What it is | Check it |
|---|---|---|
| `ssac27-v10/` | The submitted abstract (29 September 2026) with its tables | `python reproduce.py --section v10` |
| top level (`scripts/`, `src/`, `data/`, `docs/`, `formal/`, `tests/`) | The September 2026 research companion the abstract grew from | `python reproduce.py --section historical` |

The top-level folders are the 6 September 2026 release, kept byte for byte (its own
`reproduce.py` is now `reproduce_historical.py`). Their notes describe earlier drafts, including a
17.6% holdout figure and an NBA arm that are **not** results of the full paper; read them as
history. `python reproduce.py` without an option runs all three sections. `python -m pytest -q`
runs the tests of the September 2026 companion under `tests/`; it is optional.

## Version and provenance

This is release `ssac27-fullpaper-submission`, the only tag of this repository. It was made from the private
research repository at commit `09ee1dd40fa327511abbf0a9dd473c0d6bd368a3` by that repository's export script (the script is
not part of this repository). The historical and v10 files are those of public commit
`fc89c2049`, checked file by file against their git hashes. Every release is one commit
on top of the public history; earlier commits are never rewritten.

Earlier tags (one release tag of 25 November 2026 and sixteen tags named
`registration-hashes-...`, one for each addition to the hash list) were removed when this release
was made, to leave one version. Every commit they pointed to is in the history of `main`. A note
written before this release may still name one of them; the commit named beside it is the
reference.

## Data terms and licence

See `DATA_TERMS.md` (sources, credit and scope) and `LICENSING.md` (MIT for the code; see `LICENSE`).
