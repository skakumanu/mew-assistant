#!/usr/bin/env python3
import glob
import pathlib
import sys

import yaml


def main():
    files = sorted(
        set(glob.glob("**/*.yml", recursive=True) + glob.glob("**/*.yaml", recursive=True))
    )
    if not files:
        print("No .yml/.yaml files found")
        return 0
    failures = []
    for f in files:
        try:
            data = pathlib.Path(f).read_text(encoding="utf-8")
        except Exception as e:
            print(f"ERROR reading {f}: {e}")
            failures.append((f, f"READ_ERROR: {e}"))
            continue
        try:
            yaml.safe_load(data)
            print(f"OK: {f}")
        except Exception as e:
            print(f"FAIL: {f}: {e}")
            failures.append((f, str(e)))
    if failures:
        print("\n--- YAML PARSE FAILURES SUMMARY ---")
        for f, err in failures:
            print(f"- {f}: {err}")
        return 2
    print("\nAll YAML files parsed OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
