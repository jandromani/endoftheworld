#!/usr/bin/env python3
"""Backward-compatible NANO entrypoint.

The actual acquisition engine is profile-generic; this wrapper keeps old
commands and external references working.
"""
from acquire import BuildError, main
import sys

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted; partial downloads are resumable.", file=sys.stderr)
        raise SystemExit(130)
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
