"""Prepare local YOLO phone weights for DriveSense runtime inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESTINATION = (
    PROJECT_ROOT
    / "artifacts"
    / "phone_detection"
    / "weights"
)
DEFAULT_BEST = DESTINATION / "best.pt"
DEFAULT_LAST = DESTINATION / "last.pt"
MODEL_MANIFEST = (
    PROJECT_ROOT
    / "artifacts"
    / "phone_detection"
    / "model_manifest.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_weight(source: Path, destination: Path) -> str:
    if not source.is_file():
        raise FileNotFoundError(f"Weight file not found: {source}")
    if source.resolve() == destination.resolve():
        return sha256(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return sha256(destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help=(
            "A best.pt file, last.pt file, or directory containing both "
            "files."
        ),
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Do not copy; verify that best.pt/last.pt exist locally.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.verify_only:
        expected: dict[str, str] = {}
        if MODEL_MANIFEST.is_file():
            manifest = json.loads(MODEL_MANIFEST.read_text(encoding="utf-8"))
            expected = {
                "best": manifest["weights"]["best"]["sha256"].lower(),
                "last": manifest["weights"]["last"]["sha256"].lower(),
            }
        for destination in (DEFAULT_BEST, DEFAULT_LAST):
            if not destination.is_file():
                raise FileNotFoundError(
                    f"Missing phone weight: {destination}. "
                    "Prepare it using this script or retain a verified artifact."
                )
        best_hash = sha256(DEFAULT_BEST)
        last_hash = sha256(DEFAULT_LAST)
        print(f"best.pt: {best_hash}")
        print(f"last.pt: {last_hash}")
        if expected:
            for name, actual in (
                ("best", best_hash),
                ("last", last_hash),
            ):
                if actual.lower() != expected[name]:
                    raise RuntimeError(
                        f"{name}.pt SHA-256 mismatch. "
                        "Restore the verified checkpoint bundle or update "
                        "model_manifest.json only after a documented retraining."
                    )
        return

    if args.source is None:
        raise SystemExit(
            "Provide a source weight file/directory, or use --verify-only."
        )
    source = args.source.expanduser().resolve()

    if source.is_dir():
        best_source = source / "best.pt"
        last_source = source / "last.pt"
    else:
        if source.name.lower() == "last.pt":
            best_source = DEFAULT_BEST
            last_source = source
        else:
            best_source = source
            last_source = source.with_name("last.pt")

    best_hash = copy_weight(best_source, DEFAULT_BEST)
    last_hash = None
    if last_source.is_file():
        last_hash = copy_weight(last_source, DEFAULT_LAST)

    print(f"Prepared: {DEFAULT_BEST}")
    print(f"SHA256: {best_hash}")
    if last_hash:
        print(f"Prepared: {DEFAULT_LAST}")
        print(f"SHA256: {last_hash}")


if __name__ == "__main__":
    main()
