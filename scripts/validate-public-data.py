#!/usr/bin/env python3
"""Read-only validation of the committed public data contract.

    python3 scripts/validate-public-data.py

Never rewrites the payload to make it pass. Exits non-zero with a field-specific
error so a pull request can gate on it and a direct push is monitored. The daily
update agent runs this same checker locally before committing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "schemas"))

import public_contract as contract  # noqa: E402


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    try:
        contract.validate_documents(root)
    except contract.ContractError as error:
        print(f"validate-public-data: {error}", file=sys.stderr)
        return 1
    print("validate-public-data: public data contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
