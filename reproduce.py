"""Check this repository: python reproduce.py [--section historical|v10|fullpaper|all]

* historical -- reproduce_historical.py, the September 2026 companion (factor table and
  walk-forward ladder from data/processed/translation/).
* v10 -- ssac27-v10/verify_abstract_numbers.py, the 16 numbers of the submitted abstract.
* fullpaper -- ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py, the full paper.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECTIONS = {
    "historical": ([sys.executable, "reproduce_historical.py"], ROOT),
    "v10": ([sys.executable, "verify_abstract_numbers.py"], ROOT / "ssac27-v10"),
    "fullpaper": (
        [sys.executable, "ssac27-fullpaper/scripts/reproduce_sloan_fullpaper_public.py"],
        ROOT,
    ),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--section", choices=[*SECTIONS, "all"], default="all")
    args = ap.parse_args(argv)
    names = list(SECTIONS) if args.section == "all" else [args.section]
    results = {}
    for name in names:
        cmd, cwd = SECTIONS[name]
        print(f"\n===== {name}: {' '.join(cmd[1:])} =====", flush=True)
        results[name] = subprocess.run(cmd, cwd=cwd).returncode
    print("\n===== summary =====")
    for name, code in results.items():
        print(f"{name}: {'passed' if code == 0 else f'FAILED (exit {code})'}")
    return 0 if all(code == 0 for code in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
