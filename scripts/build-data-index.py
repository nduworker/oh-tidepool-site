#!/usr/bin/env python3
"""Generate data/media.json and data/index.json from the tracked media files.

This is a local authoring tool. Run it after adding or replacing a rendition and
commit the regenerated JSON with the image. CI never runs this; CI only validates
the committed JSON, so generation must not depend on CI to make an image
available.

    python3 scripts/build-data-index.py

Exits non-zero without touching tracked output on any validation error, and is
idempotent: regenerating unchanged bytes preserves the previous `generated_at`
so a second run produces no diff.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "schemas"))

import public_contract as contract  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def fail(message: str) -> None:
    raise SystemExit(f"build-data-index: {message}")


def collect_assets() -> dict:
    """Describe every versioned WebP rendition by hashing its exact tracked bytes."""
    assets: dict = {}
    seen_filenames: set = set()
    for path in sorted((ROOT / "media").iterdir()):
        if not path.is_file() or path.suffix != ".webp":
            continue
        match = contract.MEDIA_NAME.fullmatch(path.name)
        if match is None:
            fail(f"media/{path.name}: expected <asset-id>-v<revision>.webp")
        asset_id = match.group("asset_id")
        if asset_id in assets:
            fail(f"media/{path.name}: duplicate logical asset id {asset_id!r}")
        if path.name in seen_filenames:
            fail(f"media/{path.name}: duplicate filename")
        seen_filenames.add(path.name)

        payload = path.read_bytes()
        if not payload:
            fail(f"media/{path.name}: empty file")
        assets[asset_id] = {
            "revision": int(match.group("revision")),
            "path": f"media/{path.name}",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "content_type": "image/webp",
            "bytes": len(payload),
        }

    if not assets:
        fail("no versioned WebP renditions found under media/")
    return assets


def preserved_generated_at(path: Path, revision_value: str) -> str | None:
    """Keep the previous timestamp when the semantic revision is unchanged, so a
    no-op regeneration is byte-identical and reviewable in a diff."""
    if not path.exists():
        return None
    try:
        existing = contract.read_json(path)
    except contract.ContractError:
        return None
    if existing.get("revision") == revision_value and isinstance(existing.get("generated_at"), str):
        return existing["generated_at"]
    return None


def write_json(path: Path, value: dict) -> None:
    """Write via fsync + atomic rename so an interrupted run cannot truncate a
    published manifest."""
    payload = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    handle = tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False)
    try:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(handle.name, path)


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    assets = collect_assets()
    media_revision = contract.revision(assets)
    media_document = {
        "schema_version": 1,
        "generated_at": preserved_generated_at(DATA / "media.json", media_revision) or now,
        "revision": media_revision,
        "assets": assets,
    }
    # Validate in memory first: a validation error must not alter tracked output.
    try:
        contract.validate_media(media_document)
    except contract.ContractError as error:
        fail(str(error))

    conditions_path = DATA / "daily-conditions.json"
    if conditions_path.exists():
        try:
            conditions = contract.read_json(conditions_path)
            contract.validate_daily(conditions)
        except contract.ContractError as error:
            fail(str(error))
        conditions_revision = conditions["revision"]
    else:
        # No committed report: the app must not request the missing file.
        conditions_revision = None

    component_revisions = {
        "media_revision": media_revision,
        "conditions_revision": conditions_revision,
    }
    index_revision = contract.revision(component_revisions)
    index_document = {
        "schema_version": 1,
        "generated_at": preserved_generated_at(DATA / "index.json", index_revision) or now,
        "revision": index_revision,
        **component_revisions,
    }
    try:
        contract.validate_index(index_document)
    except contract.ContractError as error:
        fail(str(error))

    write_json(DATA / "media.json", media_document)
    write_json(DATA / "index.json", index_document)

    # Re-read from disk so the published pair is validated exactly as CI will.
    try:
        contract.validate_documents(ROOT)
    except contract.ContractError as error:
        fail(f"generated files failed validation: {error}")

    print(f"build-data-index: {len(assets)} rendition(s), media_revision {media_revision}")
    print(f"build-data-index: conditions_revision {conditions_revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
