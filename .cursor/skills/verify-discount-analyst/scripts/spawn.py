"""Spawn a subprocess in a new session so it survives the parent shell exiting."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: spawn.py LOG_PATH [--cwd DIR] -- CMD...", file=sys.stderr)
        raise SystemExit(2)
    log_path = sys.argv[1]
    args = sys.argv[2:]
    cwd: str | None = None
    if args[:1] == ["--cwd"]:
        cwd = args[1]
        args = args[2:]
    if args[:1] != ["--"] or len(args) < 2:
        print("spawn.py: expected -- CMD", file=sys.stderr)
        raise SystemExit(2)
    command = args[1:]
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            cwd=cwd,
        )
    print(proc.pid)


if __name__ == "__main__":
    main()
