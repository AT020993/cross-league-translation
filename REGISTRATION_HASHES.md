# Registration and frozen-forecast hashes

Paper: *One Number per League: What Translation Factors Add to European Basketball Forecasts* (MIT Sloan Sports Analytics Conference 2027, Paper ID 47).

This file fixes, in public, the content of the pre-registration, its amendments and the frozen 2026-27 forecast file **before the frozen test is scored**. The test is scored on EuroLeague and EuroCup games through 24 November 2026, from files refreshed on or after 25 November 2026.

## What this file proves

Every document listed below existed, with exactly this content, no later than the first public commit of this file. That commit time is recorded by GitHub and does not depend on the author.

The times in the table are the first push times recorded by GitHub for the private development repository. They cannot be checked from outside; they are given so that the order of events is on record. The independent anchor is this file's own commit time.

## How to check

The documents and the forecast file will be published unchanged in this repository with the full-paper materials. Then run `shasum -a 256 <file>` (or `sha256sum <file>`) and compare with the table.

## Hashes

| Item | File name | sha256 | Development commit | First push (UTC) |
|---|---|---|---|---|
| Pre-registration of the full-paper analyses and the 2026-27 frozen test | `sloan-full-paper-preregistration-2026-11-03.md` | `6c6002f9a96f954eeaac4082a02471bcd7017879df07e2a0630de07e345a5194` | `f52e7c831` | 2026-11-03 09:15:02 |
| Frozen 2026-27 forecast file (p1_frozen_forecasts.parquet) | `p1_frozen_forecasts.parquet` | `f3530c1a5ac369c032a996756ced226a93aa2d9f71d2e63aab21694de3d55316` | `9297d5b58` | 2026-11-03 10:55:14 |
| Amendment 1 | `sloan-full-paper-preregistration-amendment-1-2026-11-04.md` | `5e6554dfe2861c0be55a65deef6f9ea3cca95b9bd35fb6c27c4a5dd8d4c42776` | `f1a3453da` | 2026-11-04 22:06:27 |
| Amendment 2 | `sloan-full-paper-preregistration-amendment-2-2026-11-05.md` | `65db21959927cff679a7731d8ba9c48c327024089bcb8a4a1b7305a6b88919fc` | `41efa97c2` | 2026-11-05 06:49:08 |
| Amendment 3 | `sloan-full-paper-preregistration-amendment-3-2026-11-11.md` | `3c56752d05a537fc4843aa89123dfad42351b66bbb0df99f709f2c01f25a0262` | `caf090288` | 2026-11-11 16:06:22 |
| Amendment 4 | `sloan-full-paper-preregistration-amendment-4-2026-11-11.md` | `16c68731112fa64a8890553c0821451ed74b6ae0bf7db7a0dbbd1aedacde2aa9` | `5ab52fac1` | 2026-11-11 19:31:22 |
| Amendment 5 | `sloan-full-paper-preregistration-amendment-5-2026-11-12.md` | `6c478891f8b5e4b3cc40b17485a2640fd8210563db1049be6d0136f4d6c7463f` | `be615140b` | 2026-11-12 14:49:47 |
| Amendment 6 | `sloan-full-paper-preregistration-amendment-6-2026-11-12.md` | `4be2416f22275a19634d097b47bbaa3ee8e8485ab5ef3acf062395d311769e89` | `245bafa4b` | 2026-11-12 18:25:04 |
| Amendment 7 | `sloan-full-paper-preregistration-amendment-7-2026-11-12.md` | `accbe966c12e50264e746ea6fdcb70d8f80ab130e5579d9668333875f840ecfa` | `e884afe8b` | 2026-11-12 22:01:40 |
| Freeze record | `freeze.json` | `07ca3c33278238d3d5d0a1626a8afaf8f2af186e7e74e5656b1476b47d35d67a` | `9297d5b58` | 2026-11-03 10:55:14 |
| Amendment 8 | `sloan-full-paper-preregistration-amendment-8-2026-11-16.md` | `250d3f6181a50e0343076ef74203128016cd4891998683de90a3a452cc11cf34` | `afcfeff58` | 2026-11-16 15:59:44 |
| Amendment 9 | `sloan-full-paper-preregistration-amendment-9-2026-11-16.md` | `6dc8356d56538dcd01d8f619b82c4878143d53c0f674082cfba5a55af567e90d` | `3c915869c` | 2026-11-16 16:01:36 |
| Amendment 10 (wording for one result, written after that result was seen) | `sloan-full-paper-preregistration-amendment-10-2026-11-16.md` | `c92daa919c5cc7e927ae08a896d8d06248a0644b4a0c057df7af0ae108c0c426` | `205207eed` | 2026-11-16 20:18:30 |
| Amendment 11 | `sloan-full-paper-preregistration-amendment-11-2026-11-16.md` | `63d20a7dbf51b5bd8974f088ec0800e1072ecc383d1a179255f33057882adbde` | `40f0d278b` | 2026-11-16 21:22:53 |

## Notes

- The forecast file holds 3,478 forecasts: 1,739 domestic player-seasons of 2025-26, each for the EuroLeague and the EuroCup. It contains no 2026-27 statistic.
- The freeze record names the pre-registration by its sha256 (`6c6002f9…5194`), the first row of the table.
- Later amendments are added to this file in new commits. Earlier rows are never edited. Amendments 8 and 9 were added on 16 November 2026. Amendments 10 and 11 were added on 17 November 2026.
