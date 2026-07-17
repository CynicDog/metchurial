# -*- coding: utf-8 -*-
"""Dev-only: bundles the package + generated/ parser + vendored antlr4
runtime into dist/metchurial.py, a single file with zero third-party
imports at runtime -- the artifact carried into the company's restricted
environment.

Uses stickytape (dev dependency, see pyproject.toml's [dependency-groups]
dev group): it statically traces imports from build/entrypoint.py and
inlines each resolved module's source, so at runtime the bundle
reconstructs a temporary directory on disk and imports normally from
there -- no custom import-hook trickery to audit, just plain files. See
docs/PROVENANCE.md for what's being bundled and under what license.

Run:
    uv run python build/bundle.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    dist_dir = ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    output = dist_dir / "metchurial.py"

    stickytape_bin = Path(sys.executable).parent / "stickytape"
    cmd = [
        str(stickytape_bin),
        str(ROOT / "build" / "entrypoint.py"),
        "--add-python-path", str(ROOT),
        "--add-python-path", str(ROOT / "generated"),
        "--add-python-path", str(ROOT / "vendor" / "antlr4-python3-runtime"),
        "--output-file", str(output),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    print("Bundled: {}".format(output))


if __name__ == "__main__":
    main()
