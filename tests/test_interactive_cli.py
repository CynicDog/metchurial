# -*- coding: utf-8 -*-
"""Tests for the interactive wizard (metchurial.interactive.run_wizard and
cli.main()'s zero-argv trigger): entering interactive mode when run with no
arguments, walking every prompt, and handing the assembled argv tokens to
the same argparse parser a normal hand-typed invocation goes through.

Run:
    python -m unittest tests.test_interactive_cli
"""

import builtins
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import cli  # noqa: E402
from metchurial import interactive  # noqa: E402


class _ScriptedInput:
    """Feeds canned answers to input(), one per call, in order -- swapped
    in for builtins.input rather than actually piping stdin, so these
    tests don't depend on subprocess plumbing. Raises EOFError once
    exhausted, matching real input()'s behavior against closed stdin."""

    def __init__(self, answers):
        self._answers = list(answers)

    def __call__(self, prompt=""):
        if not self._answers:
            raise EOFError("no more scripted answers")
        return self._answers.pop(0)


class TestRunWizardTokenAssembly(unittest.TestCase):
    """Exercises interactive.run_wizard() directly -- no cli.py/argparse
    involved -- to pin down exactly which argv tokens each answer produces."""

    def setUp(self):
        self._orig_input = builtins.input
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        builtins.input = self._orig_input
        shutil.rmtree(self.root)

    def _wizard(self, answers):
        builtins.input = _ScriptedInput(answers)
        return interactive.run_wizard()

    def test_all_defaults_produces_bare_root_only(self):
        argv = self._wizard([
            self.root,  # root
            "",  # sensitive columns
            "",  # extensions
            "",  # verbose
            "",  # workers
            "",  # max-chunk-iterations
            "",  # extract-metadata (No)
            "",  # split mode (none)
            "",  # mask-literals
        ])
        self.assertEqual(argv, [self.root])

    def test_extract_metadata_and_non_default_granularity(self):
        argv = self._wizard([
            self.root,
            "",
            "",
            "",
            "",
            "",
            "1",  # extract-metadata -> Yes
            "strict",  # granularity, answered by name rather than number
            "",  # query-similarity -> No
            "",  # split mode -> none
            "",  # mask-literals -> No
        ])
        self.assertEqual(
            argv, [self.root, "--extract-metadata", "--identity-granularity", "strict"])

    def test_query_similarity_requires_extract_metadata_prompt_first(self):
        argv = self._wizard([
            self.root,
            "",
            "",
            "",
            "",
            "",
            "yes",  # extract-metadata -> Yes
            "",  # granularity -> default (structure)
            "1",  # query-similarity -> Yes
            "",  # split mode -> none
            "",  # mask-literals -> No
        ])
        self.assertEqual(argv, [self.root, "--extract-metadata", "--query-similarity"])

    def test_split_mode_un_split(self):
        argv = self._wizard([
            self.root,
            "",
            "",
            "",
            "",
            "",
            "",  # extract-metadata -> No (skips granularity/similarity prompts)
            "3",  # split mode -> un-split (3rd menu option)
            "",  # mask-literals
        ])
        self.assertEqual(argv, [self.root, "--un-split-selects"])

    def test_split_mode_split(self):
        argv = self._wizard([
            self.root, "", "", "", "", "", "", "split", "",
        ])
        self.assertEqual(argv, [self.root, "--split-selects"])

    def test_mask_literals_yes(self):
        argv = self._wizard([
            self.root, "", "", "", "", "", "", "", "yes",
        ])
        self.assertEqual(argv, [self.root, "--mask-literals"])

    def test_non_directory_root_reprompts_until_valid(self):
        argv = self._wizard([
            os.path.join(self.root, "does-not-exist"),  # invalid -> reprompt
            self.root,  # valid on retry
            "", "", "", "", "", "", "", "",
        ])
        self.assertEqual(argv, [self.root])

    def test_non_default_workers_and_extensions(self):
        argv = self._wizard([
            self.root,
            "",  # sensitive columns
            "sql",  # extensions -> just .sql
            "",  # verbose
            "4",  # workers
            "",  # max-chunk-iterations
            "",  # extract-metadata
            "",  # split mode
            "",  # mask-literals
        ])
        self.assertEqual(
            argv, [self.root, "--extensions", "sql", "--workers", "4"])


class TestCliMainEntersWizardOnEmptyArgv(unittest.TestCase):
    """End-to-end: cli.main([]) (equivalent to a bare `metchurial` shell
    invocation, see cli.py's raw_args handling) must run the wizard and
    then the real scan, same tmpdir/chdir pattern test_cli_similarity.py
    uses."""

    def setUp(self):
        self._orig_input = builtins.input
        self.workdir = tempfile.mkdtemp()
        self.sql_root = os.path.join(self.workdir, "sqlroot")
        os.mkdir(self.sql_root)
        with open(os.path.join(self.sql_root, "a.sql"), "w", encoding="utf-8") as f:
            f.write("SELECT c1 FROM s1.t1;\n")
        self.prev_cwd = os.getcwd()
        os.chdir(self.workdir)

    def tearDown(self):
        builtins.input = self._orig_input
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.workdir)

    def test_empty_argv_runs_wizard_and_completes_scan(self):
        answers = [self.sql_root, "", "", "", "", "", "", "", ""]
        builtins.input = _ScriptedInput(answers)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.main([])
        self.assertIn(ctx.exception.code, (0, 1))
        self.assertTrue(os.path.isfile("summary.md"))
        with open("summary.md", encoding="utf-8-sig") as f:
            summary = f.read()
        self.assertIn("metchurial {}".format(self.sql_root), summary)

    def test_eof_during_wizard_exits_cleanly_not_with_a_traceback(self):
        builtins.input = _ScriptedInput([])  # exhausted immediately -> EOFError
        stderr = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                cli.main([])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("interactive input is unavailable", stderr.getvalue())
        self.assertFalse(os.path.isfile("summary.md"))


if __name__ == "__main__":
    unittest.main()
