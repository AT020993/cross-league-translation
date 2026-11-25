"""Verify pinned research inputs and preserve stable, hash-addressed snapshots."""

from __future__ import annotations

import errno
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class InputMismatch(ValueError):
    """The run cannot reproduce its pinned input receipt."""


def sha256_file(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def hashes_from_receipt(path: Path) -> dict[str, str]:
    receipt = json.loads(Path(path).read_text())
    inputs = receipt.get("input_receipt", receipt)["inputs"]
    files = inputs.get("files", inputs)
    hashes = {k: v["sha256"] if isinstance(v, dict) else v for k, v in files.items()}
    validate_hashes(hashes)
    return hashes


def validate_hashes(hashes: dict[str, str]) -> None:
    if not hashes:
        raise InputMismatch("Empty input receipt")
    for name, digest in hashes.items():
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or str(path) != name
            or name == ".input-receipt.json"
        ):
            raise InputMismatch(f"Unsafe input name: {name}")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise InputMismatch(f"Invalid SHA-256 for {name}")


def verify_hashes(actual: dict, expected: dict, *, allow_new_inputs=False) -> dict:
    validate_hashes(actual)
    if expected or not allow_new_inputs:
        validate_hashes(expected)
    changes = {
        k: {"expected": expected.get(k), "actual": actual.get(k)}
        for k in sorted(actual.keys() | expected.keys())
        if actual.get(k) != expected.get(k)
    }
    if changes and not allow_new_inputs:
        raise InputMismatch(
            "Inputs differ from the pinned receipt: "
            + ", ".join(changes)
            + ". Restore archived inputs, or use --allow-new-inputs for a new run."
        )
    return {
        "status": "new_inputs" if changes else "matched",
        "changes": changes,
        "allow_new_inputs": bool(allow_new_inputs),
    }


def default_archive_root(repo: Path) -> Path:
    common = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=repo,
            text=True,
        ).strip()
    )
    return common.parent / "_local/research_inputs/snapshots"


def snapshot_id(hashes: dict[str, str]) -> str:
    validate_hashes(hashes)
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def verify_snapshot(root: Path, expected: dict[str, str]) -> None:
    """Glob-based loaders must not discover files absent from the receipt."""
    paths = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise InputMismatch(f"Unexpected symlink in input snapshot: {path}")
        name = str(path.relative_to(root))
        if path.is_file() and name != ".input-receipt.json":
            paths[name] = sha256_file(path)
    verify_hashes(paths, expected)


def snapshot_inputs(
    paths: dict[str, Path],
    expected: dict[str, str],
    archive: Path,
    *,
    allow_new_inputs=False,
) -> tuple[Path, dict]:
    """Verify before copying, verify copies, then return stable input paths.

    Missing files always fail. Existing archives are verified on every use.
    A source changing during copying cannot be accepted.
    """
    actual = {name: sha256_file(path) for name, path in paths.items()}
    verification = verify_hashes(actual, expected, allow_new_inputs=allow_new_inputs)
    archive = Path(archive)
    key = snapshot_id(actual)
    target = archive / key
    if target.exists():
        verify_snapshot(target, actual)
    else:
        archive.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".snapshot-", dir=archive))
        try:
            for name, path in paths.items():
                dest = stage / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
                if sha256_file(dest) != actual[name]:
                    raise InputMismatch(f"Input changed while archiving: {name}")
                dest.chmod(0o444)
            (stage / ".input-receipt.json").write_text(
                json.dumps({"inputs": actual}, indent=2, sort_keys=True) + "\n"
            )
            try:
                stage.rename(target)
            except OSError as exc:
                if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                    raise
                verify_snapshot(target, actual)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return target, {"inputs": actual, "snapshot": key, "verification": verification}


def protect_pinned_output(out: Path, pinned: Path, allow_new_inputs: bool) -> None:
    if allow_new_inputs and out.resolve() == pinned.resolve().parent:
        raise InputMismatch("--allow-new-inputs requires a separate output directory")
