# -*- coding: utf-8 -*-
"""Verifies the single-file deployable artifact (dist/metchurial.py)
actually is self-contained: builds it fresh, then runs it in a throwaway
virtualenv with *zero* third-party packages installed (not even
antlr4-python3-runtime) against tests/fixtures, and diffs its output
against a normal package-mode run. This is the actual proof the bundling
step didn't silently break anything -- running the bundle in the same dev
venv that has antlr4-python3-runtime pip-installed wouldn't prove
anything, since a broken bundle could still work by accident there.

This test is slow (fresh venv creation + a full bundle rebuild) and needs
the dev-only build tooling (stickytape, see pyproject.toml's
[dependency-groups] dev group) on PATH -- it is not meant to run in the
restricted target environment, only during development, before shipping a
new dist/ build.

Run:
    uv run python -m unittest tests.test_bundle
"""

import os
import subprocess
import sys
import tempfile
import unittest
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def _run(args, cwd, env=None):
    return subprocess.run(args, cwd=str(cwd), env=env, capture_output=True, text=True)


@unittest.skipIf(os.environ.get("SKIP_BUNDLE_TEST") == "1",
                 "bundle self-containment runs in its own CI job (see .github/workflows/ci.yml)")
class TestBundleIsSelfContained(unittest.TestCase):
    def test_bundle_runs_with_zero_third_party_packages(self):
        build = _run([sys.executable, "build/bundle.py"], cwd=ROOT)
        self.assertEqual(build.returncode, 0, msg=build.stderr)

        bundle_path = ROOT / "dist" / "metchurial.py"
        self.assertTrue(bundle_path.is_file())

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            clean_venv = tmp / "clean_venv"
            venv.create(str(clean_venv), with_pip=False)
            clean_python = clean_venv / "bin" / "python"

            # Output filenames are fixed (summary.md/findings.tsv/strings.txt/
            # stopwords.txt/bad_files.txt) rather than flag-configurable, so
            # the bundle-mode and package-mode runs are kept from colliding
            # by giving each its own cwd instead of its own output paths.
            bundle_out = tmp / "bundle_out"
            bundle_out.mkdir()
            bundle_run = _run(
                [str(clean_python), str(bundle_path), str(FIXTURES_DIR)],
                cwd=bundle_out)
            # exit code 1 means findings were detected -- expected for
            # this fixture set, not a failure of the bundle itself
            self.assertIn(bundle_run.returncode, (0, 1), msg=bundle_run.stderr)
            self.assertNotIn("Traceback", bundle_run.stderr)
            # A real scan completed (some findings count was printed);
            # the exact number is deliberately not pinned here -- the
            # findings.tsv diff below compares full content against the
            # package-mode run, which is the stronger check and doesn't
            # go stale every time a fixture is added.
            self.assertRegex(bundle_run.stdout, r"Findings: \d+")

            package_out = tmp / "package_out"
            package_out.mkdir()
            # cwd is package_out (so its output lands there, not in ROOT),
            # so "src" must be reachable via PYTHONPATH instead of cwd.
            package_env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
            package_run = _run(
                [sys.executable, "-m", "metchurial.cli", str(FIXTURES_DIR)],
                cwd=package_out, env=package_env)
            self.assertIn(package_run.returncode, (0, 1), msg=package_run.stderr)

            bundle_tsv = (bundle_out / "findings.tsv").read_text(encoding="utf-8-sig")
            package_tsv = (package_out / "findings.tsv").read_text(encoding="utf-8-sig")
            self.assertEqual(bundle_tsv, package_tsv)


if __name__ == "__main__":
    unittest.main()
