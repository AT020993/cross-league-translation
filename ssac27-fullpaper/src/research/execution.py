"""Fail-closed CLI execution of historical research in retained input capsules.

Scientific functions remain importable for fixture tests. Executable study
commands enter here before imports that may load data or create output paths.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from collections.abc import Callable

from src.research.input_receipts import (
    InputMismatch,
    default_archive_root,
    hashes_from_receipt,
    sha256_file,
    snapshot_inputs,
    validate_hashes,
    verify_snapshot,
    verify_hashes,
)

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "docs/codex/research-generators.json"
TABLE_SUFFIXES = {
    ".parquet",
    ".csv",
    ".json",
    ".jsonl",
    ".pkl",
    ".pickle",
    ".npz",
    ".npy",
    ".gz",
    ".joblib",
}
SOURCE_DIRS = (
    "data/raw",
    "data/processed",
    "data/registries",
    "docs/research",
    "docs/plans",
)
# Timestamped registry backups (migrate_baskonia_dedupe, build_registries) copy
# the live tables; they are never study inputs and carry season-0 alias overrides
# that fail the bound (ATI-3577). Selecting one explicitly still stages it.
REGISTRY_BACKUP_DIRS = frozenset({"_archive", "_snapshots"})
MARKER = ".research-execution.json"


def inventory(
    source: Path,
    years: list[int] | None,
    includes: list[str],
    selections: list[str] | None = None,
) -> dict[str, Path]:
    """Conservative input envelope; never discover secrets, databases or env files."""
    paths = {}
    for directory in [*(selections or SOURCE_DIRS), *includes]:
        rel = Path(directory)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:
            raise InputMismatch(
                f"Input directory must be repository-relative: {directory}"
            )
        root = source / rel
        if not root.exists():
            continue
        files = [root] if root.is_file() else root.rglob("*")
        for path in files:
            if not path.is_file() or path.name.startswith("."):
                continue
            name = path.relative_to(source).as_posix()
            if name.startswith(
                "data/registries/"
            ) and REGISTRY_BACKUP_DIRS.intersection(path.relative_to(root).parts[:-1]):
                continue
            if path.suffix not in TABLE_SUFFIXES | {
                ".md",
                ".html",
                ".tex",
                ".txt",
                ".yaml",
                ".yml",
                ".png",
                ".svg",
                ".pdf",
                ".tsv",
            }:
                continue
            # Raw partitions are selected explicitly, including inactive leagues.
            if name.startswith("data/raw/"):
                partitions = [
                    int(p) for p in Path(name).parts if re.fullmatch(r"20[0-9]{2}", p)
                ]
                if (
                    years is not None
                    and partitions
                    and any(year not in years for year in partitions)
                ):
                    continue
            paths[name] = path
    if not paths:
        raise InputMismatch("No research inputs found in the selected source tree")
    return dict(sorted(paths.items()))


def parse_season(value, name: str, column: str) -> int | None:
    if value is None:
        return None
    match = re.fullmatch(r"(20[0-9]{2})(?:\.0|[-/][0-9]{2,4})?", str(value))
    if not match:
        raise InputMismatch(f"Unrecognized season in {name}:{column}: {value!r}")
    return int(match[1])


def snapshot_seasons(root: Path, names) -> list[int]:
    """Freeze an inventory-defined population before its first numerical run."""
    import pyarrow.parquet as pq

    years = set()
    for name in names:
        if not name.startswith("data/"):
            continue
        if name.startswith("data/raw/"):
            years.update(
                int(p) for p in Path(name).parts if re.fullmatch(r"20[0-9]{2}", p)
            )
        if not name.endswith(".parquet"):
            continue
        schema = pq.read_schema(root / name)
        columns = [
            c
            for c in ("Season", "season", "season_src", "season_dest")
            if c in schema.names
        ]
        if columns:
            table = pq.read_table(root / name, columns=columns)
            for column in columns:
                years.update(
                    year
                    for value in table[column].unique().to_pylist()
                    if (year := parse_season(value, name, column)) is not None
                )
    return sorted(years)


def bound_tables(tree: Path, paths: dict[str, Path], years: list[int]) -> dict:
    """Filter source tables, retaining original byte hashes separately.

    Frozen result artifacts are never rewritten; this filter only applies to
    source data. Registered narrower study filters still execute in the study.
    """
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    changes = {}
    for name in paths:
        if not name.startswith("data/") or not name.endswith(".parquet"):
            continue
        path = tree / name
        schema = pq.read_schema(path)
        columns = [
            c
            for c in ("Season", "season", "season_src", "season_dest")
            if c in schema.names
        ]
        if not columns:
            continue
        table = pq.read_table(path)
        keep = None
        for column in columns:
            values = table[column].to_pylist()
            parsed = []
            for value in values:
                if value is None:
                    parsed.append(True)  # identity/coverage unknowns remain unknown
                    continue
                parsed.append(parse_season(value, name, column) in years)
            mask = pa.array(parsed, type=pa.bool_())
            keep = mask if keep is None else pc.and_(keep, mask)
        if pc.all(keep).as_py():
            continue
        # pyarrow has no take kernel for view types (ATI-3577); filter plain copies.
        table = table.cast(
            pa.schema(
                field.with_type(pa.string())
                if pa.types.is_string_view(field.type)
                else field.with_type(pa.binary())
                if pa.types.is_binary_view(field.type)
                else field
                for field in table.schema
            )
        )
        filtered = table.filter(keep)
        if len(filtered) != len(table):
            pq.write_table(filtered, path)
            changes[name] = {
                "before_rows": len(table),
                "after_rows": len(filtered),
                "columns": columns,
            }
    return changes


def code_files(repo: Path) -> list[Path]:
    if (repo / ".git").exists():
        names = (
            subprocess.check_output(["git", "ls-files", "-z"], cwd=repo)
            .decode()
            .split("\0")
        )
    else:
        manifest = json.loads((repo / "MANIFEST.json").read_text())
        files = manifest["files"]
        hashes = {
            name: value["sha256"] if isinstance(value, dict) else value
            for name, value in files.items()
        }
        validate_hashes(hashes)
        for name, expected in hashes.items():
            if sha256_file(repo / name) != expected:
                raise InputMismatch(f"Bundle file differs from its manifest: {name}")
        names = list(files)
    return [
        repo / name
        for name in names
        if name
        and (
            name.startswith(("src/", "scripts/"))
            or name
            in (
                "pyproject.toml",
                "uv.lock",
                "requirements.txt",
                "pytest.ini",
                "docs/codex/research-generators.json",
            )
        )
        and (repo / name).is_file()
        and not (repo / name).is_symlink()
    ]


def remap_arguments(
    args: list[str], source: Path, repo: Path, workspace: Path, run: Path
) -> list[str]:
    result = []
    for arg in args:
        key, sep, value = arg.partition("=") if arg.startswith("--") else ("", "", arg)
        if not value:
            result.append(arg)
            continue
        path = Path(value)
        if path.is_absolute():
            path = path.resolve()
            value = str(path)
            for root in (source, repo):
                if path.is_relative_to(root):
                    value = str(workspace / path.relative_to(root))
                    break
            else:
                if not path.is_relative_to(run):
                    raise InputMismatch(
                        f"External path {value} is outside the input tree and run. "
                        "Stage inputs beneath --research-source; "
                        "put outputs beneath --research-run."
                    )
        elif ".." in path.parts:
            raise InputMismatch(f"Parent traversal is not a research argument: {value}")
        result.append(key + sep + value)
    return result


def execute(
    entry: str,
    args: list[str],
    options,
    *,
    repo: Path = REPO,
    validate_source: Callable[[], object] | None = None,
) -> int:
    catalog = json.loads((repo / "docs/codex/research-generators.json").read_text())
    policy = catalog["generators"].get(entry)
    if policy is None or policy["mode"] not in ("capsule", "frozen"):
        raise InputMismatch(f"Unregistered research entrypoint: {entry}")
    if policy["mode"] == "frozen" and (
        sha256_file(repo / entry) != policy["source_sha256"]
    ):
        raise InputMismatch(
            f"Frozen generator differs from its source receipt: {entry}"
        )
    registered_years = policy["source_seasons"]
    years = None if registered_years == "snapshot" else registered_years
    expected = {}
    saved = None
    if options.input_receipt:
        saved = json.loads(options.input_receipt.read_text())
        if saved.get("entrypoint") != entry or (
            registered_years != "snapshot" and saved.get("source_seasons") != years
        ):
            raise InputMismatch("Receipt belongs to another study or season envelope")
        years = saved["source_seasons"]
        if not isinstance(years, list) or any(
            type(y) is not int or not 2000 <= y <= 2099 for y in years
        ):
            raise InputMismatch("Invalid saved source-season envelope")
        expected = hashes_from_receipt(options.input_receipt)
    elif not options.allow_new_inputs:
        raise InputMismatch(
            "A pinned --input-receipt is required; "
            "--allow-new-inputs explicitly starts a new input version"
        )
    includes = options.research_include
    selections = getattr(options, "research_select", [])
    if saved is not None:
        if includes and includes != saved["includes"]:
            raise InputMismatch("Input includes differ from the receipt")
        includes = saved["includes"]
        if selections and selections != saved.get("selections", []):
            raise InputMismatch("Input selections differ from the receipt")
        selections = saved.get("selections", [])
    source = options.research_source.resolve()
    run = options.research_run.resolve()
    if run.exists() or run.is_relative_to(source) or source.is_relative_to(run):
        raise InputMismatch(
            "--research-run must be a new directory outside the source tree"
        )
    source_identity = validate_source() if validate_source is not None else None
    paths = inventory(source, years, includes, selections)
    if options.archive_root is None and not (repo / ".git").exists():
        raise InputMismatch("A standalone export requires an explicit --archive-root")
    archive = Path(options.archive_root or default_archive_root(repo)).resolve()
    if any(path.resolve().is_relative_to(archive) for path in paths.values()):
        raise InputMismatch(
            "Input selection contains the archive itself; narrow --research-include"
        )
    snapshot, receipt = snapshot_inputs(
        paths, expected, archive, allow_new_inputs=options.allow_new_inputs
    )
    if years is None:
        years = snapshot_seasons(snapshot, paths)
    # Validate argument routing before creating an output tree.
    workspace = run / "workspace"
    forwarded = remap_arguments(args, source, repo, workspace, run)
    run.mkdir(parents=True)
    workspace.mkdir()
    for name in paths:
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(snapshot / name, target)
    bounded = bound_tables(workspace, paths, years)
    effective = {name: sha256_file(workspace / name) for name in paths}
    effective_root, effective_receipt = snapshot_inputs(
        {name: workspace / name for name in paths},
        saved["effective_inputs"]["inputs"] if saved else {},
        archive,
        allow_new_inputs=options.allow_new_inputs,
    )
    code = {}
    for path in code_files(repo):
        name = path.relative_to(repo).as_posix()
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        code[name] = sha256_file(target)
        if code[name] != sha256_file(path):
            raise InputMismatch(f"Generator changed while copying: {name}")
    code_verification = verify_hashes(
        code,
        saved["code"] if saved else {},
        allow_new_inputs=options.allow_new_inputs,
    )
    receipt.update(
        entrypoint=entry,
        source_seasons=years,
        includes=includes,
        selections=selections,
        source=str(source),
        arguments=forwarded,
        code=code,
        code_verification=code_verification,
        source_provenance=source_identity,
        season_filter=bounded,
        effective_inputs=effective_receipt,
        effective_archive=str(effective_root),
        status="running",
    )
    receipt_path = run / "input-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    (workspace / MARKER).write_text(
        json.dumps(
            {
                "entrypoint": entry,
                "code": code,
                "receipt": str(receipt_path),
                "source_provenance": source_identity,
            }
        )
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    # Existing provenance helpers must report the actual checked-out generator,
    # not manufacture a new commit for the execution copy.
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    if (repo / ".git").exists():
        env["GIT_DIR"] = subprocess.check_output(
            ["git", "rev-parse", "--absolute-git-dir"], cwd=repo, text=True
        ).strip()
        env["GIT_WORK_TREE"] = str(repo)
    env["PYTHONPATH"] = str(workspace)
    for key in ("BA_REPO", "BB_REPO_ROOT", "BB_DATA_ROOT"):
        env[key] = str(workspace)
    env["ISOCOURT_RESEARCH_RECEIPT"] = str(receipt_path)
    try:
        with (
            (run / "stdout.log").open("w") as stdout,
            (run / "stderr.log").open("w") as stderr,
        ):
            result = subprocess.run(
                [sys.executable, str(workspace / entry), *forwarded],
                cwd=workspace,
                env=env,
                stdout=stdout,
                stderr=stderr,
                check=False,
            )
        receipt["returncode"] = result.returncode
        verify_snapshot(snapshot, receipt["inputs"])
        verify_snapshot(effective_root, effective)
        before = {**effective, **code}
        outputs = {}
        for path in run.rglob("*"):
            if (
                not path.is_file()
                or path == receipt_path
                or path.name == MARKER
                or "__pycache__" in path.parts
            ):
                continue
            digest = sha256_file(path)
            relative = (
                path.relative_to(workspace).as_posix()
                if path.is_relative_to(workspace)
                else None
            )
            if relative is None or digest != before.get(relative):
                outputs[path.relative_to(run).as_posix()] = digest
        receipt["outputs"] = outputs
        receipt["status"] = "complete" if result.returncode == 0 else "failed"
        print(f"Research run {receipt['status']}: {run}", flush=True)
        return result.returncode
    finally:
        if receipt["status"] == "running":
            receipt["status"] = "failed"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def enter(script: str, *, validate_source: Callable[[], object] | None = None) -> None:
    """Called before scientific imports, including import-time legacy generators."""
    path = Path(script).resolve()
    repo = REPO
    entry = path.relative_to(repo).as_posix()
    marker = repo / MARKER
    if marker.exists():
        record = json.loads(marker.read_text())
        receipt_path = record["receipt"]
        if (
            os.environ.get("ISOCOURT_RESEARCH_RECEIPT") != receipt_path
            or json.loads(Path(receipt_path).read_text()).get("status") != "running"
        ):
            raise InputMismatch(
                "A retained execution copy cannot start another run directly; "
                "use the original command with a new --research-run and its receipt"
            )
        expected = record["code"].get(entry)
        if expected is None or sha256_file(path) != expected:
            raise InputMismatch("Execution copy does not match its recorded generator")
        if validate_source is not None:
            validate_source()
        return
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--input-receipt", type=Path)
    parser.add_argument("--allow-new-inputs", action="store_true")
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--research-source", type=Path, default=repo)
    parser.add_argument("--research-run", type=Path)
    parser.add_argument("--research-include", action="append", default=[])
    parser.add_argument("--research-select", action="append", default=[])
    options, rest = parser.parse_known_args()
    if "--help" in rest or "-h" in rest:
        parser.print_help()
        tree = ast.parse(path.read_text())
        print("\n" + (ast.get_docstring(tree) or "Research command"))
        flags = sorted(
            {
                arg.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
                for arg in node.args
                if isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and arg.value.startswith("--")
            }
        )
        print("\nStudy options: " + ", ".join(flags))
        print(
            "\nResearch execution requires --research-run NEW_DIRECTORY "
            "plus --input-receipt RECEIPT "
            "(or --allow-new-inputs). Existing study arguments follow these options. "
            "See docs/codex/research-inputs.md."
        )
        raise SystemExit(0)
    if options.research_run is None:
        raise InputMismatch(
            "--research-run NEW_DIRECTORY is required "
            "for a retained, isolated research run"
        )
    raise SystemExit(execute(entry, rest, options, validate_source=validate_source))
