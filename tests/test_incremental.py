# -*- coding: utf-8 -*-
"""Tests for --incremental: the per-file result cache in incremental.py,
and its wiring into engine.scan_tree (cached_results/on_file_result).

Run:
    python -m unittest tests.test_incremental
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC_DIR)

from metchurial import engine as scanner  # noqa: E402
from metchurial import incremental  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402
from metchurial.models.references import TableUse  # noqa: E402
from metchurial.models.results import FileScanResult  # noqa: E402


class TestModeSignature(unittest.TestCase):
    def test_differs_across_extract_metadata_and_split_selects(self):
        plain = incremental.mode_signature(ScanOptions())
        metadata = incremental.mode_signature(ScanOptions.metadata())
        split = incremental.mode_signature(ScanOptions(split_selects=True))
        self.assertNotEqual(plain, metadata)
        self.assertNotEqual(plain, split)
        self.assertNotEqual(metadata, split)

    def test_stable_for_equivalent_options(self):
        a = incremental.mode_signature(ScanOptions.metadata(workers=1))
        b = incremental.mode_signature(ScanOptions.metadata(workers=4))
        self.assertEqual(a, b)


class TestRecordAndLookupRoundTrip(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "q.sql")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("SELECT a FROM t1;")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_lookup_hits_after_record_with_unchanged_file(self):
        cache = {}
        mode = incremental.mode_signature(ScanOptions())
        result = FileScanResult(table_uses=[TableUse("S", "T", self.path, 1)])
        incremental.record(cache, self.path, mode, result)

        hit = incremental.lookup(cache, self.path, mode)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.table_uses, [TableUse("S", "T", self.path, 1)])

    def test_lookup_misses_on_mode_change(self):
        cache = {}
        mode_a = incremental.mode_signature(ScanOptions())
        mode_b = incremental.mode_signature(ScanOptions.metadata())
        incremental.record(cache, self.path, mode_a, FileScanResult())
        self.assertIsNone(incremental.lookup(cache, self.path, mode_b))

    def test_lookup_misses_after_content_change(self):
        cache = {}
        mode = incremental.mode_signature(ScanOptions())
        incremental.record(cache, self.path, mode, FileScanResult())

        with open(self.path, "w", encoding="utf-8") as f:
            f.write("SELECT a FROM t1; SELECT b FROM t2;")
        # force an mtime change even if the filesystem's mtime resolution
        # is coarser than the time this test takes to run
        st = os.stat(self.path)
        os.utime(self.path, ns=(st.st_atime_ns, st.st_mtime_ns + 1))

        self.assertIsNone(incremental.lookup(cache, self.path, mode))

    def test_lookup_misses_for_unknown_path(self):
        cache = {}
        mode = incremental.mode_signature(ScanOptions())
        self.assertIsNone(incremental.lookup(cache, self.path, mode))

    def test_record_is_noop_for_deleted_file(self):
        cache = {}
        mode = incremental.mode_signature(ScanOptions())
        os.remove(self.path)
        incremental.record(cache, self.path, mode, FileScanResult())
        self.assertEqual(cache, {})


class TestSaveLoadCacheFile(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.d, "incremental_cache.json")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_missing_file_loads_empty(self):
        self.assertEqual(incremental.load_cache(self.cache_path), {})

    def test_corrupt_file_loads_empty_instead_of_raising(self):
        with open(self.cache_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        self.assertEqual(incremental.load_cache(self.cache_path), {})

    def test_round_trips_through_disk(self):
        entries = {"/tmp/x.sql": {"mode": "1,0,0,0,0,0", "fingerprint": [10, 20],
                                   "result": incremental._serialize_result(FileScanResult())}}
        incremental.save_cache(self.cache_path, entries)
        self.assertEqual(incremental.load_cache(self.cache_path), entries)


class TestScanTreeUsesCachedResults(unittest.TestCase):
    """Proves engine.scan_tree actually takes the cached path (not just
    that the cache module round-trips in isolation) by seeding a cached
    result that couldn't have come from a real scan of the file's actual
    content, then checking that fabricated result -- not a fresh parse --
    is what ends up in the merged tree."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "q.sql")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("SELECT a FROM real_table;")

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_cached_result_wins_over_fresh_scan(self):
        fabricated = FileScanResult(
            table_uses=[TableUse("FAKE", "NOT_IN_FILE", self.path, 99)])
        cached_results = {os.path.abspath(self.path): fabricated}

        tree = scanner.scan_tree(self.d, ScanOptions.metadata(),
                                 cached_results=cached_results)
        self.assertEqual(tree.file_count, 1)
        self.assertEqual(len(tree.table_uses), 1)
        self.assertEqual(tree.table_uses[0].table, "NOT_IN_FILE")

    def test_on_file_result_fires_for_cache_hit_and_miss(self):
        seen = {}

        def record(path, result):
            seen[os.path.abspath(path)] = result

        cached_results = {os.path.abspath(self.path): FileScanResult()}
        d2 = tempfile.mkdtemp()
        try:
            fresh_path = os.path.join(d2, "fresh.sql")
            with open(fresh_path, "w", encoding="utf-8") as f:
                f.write("SELECT b FROM t2;")
            # both files live under separate dirs scanned individually so
            # each root only ever contains one file, keeping the assertion
            # unambiguous about which path is the cache hit/miss.
            scanner.scan_tree(self.d, ScanOptions(), cached_results=cached_results,
                              on_file_result=record)
            scanner.scan_tree(d2, ScanOptions(), on_file_result=record)
        finally:
            shutil.rmtree(d2)

        self.assertIn(os.path.abspath(self.path), seen)
        self.assertIn(os.path.abspath(fresh_path), seen)


class TestIncrementalCLIEndToEnd(unittest.TestCase):
    """Drives the real CLI across two --incremental invocations in a temp
    tree: an unchanged file's previously-extracted rows must still show up
    in refs_tables.tsv on the second run (merge-with-prior-outputs), while
    a changed file's rows must reflect its new content."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.stable_path = os.path.join(self.d, "stable.sql")
        self.changing_path = os.path.join(self.d, "changing.sql")
        with open(self.stable_path, "w", encoding="utf-8") as f:
            f.write("SELECT a FROM stable_table;")
        with open(self.changing_path, "w", encoding="utf-8") as f:
            f.write("SELECT b FROM old_table;")

    def tearDown(self):
        shutil.rmtree(self.d)

    def _run_cli(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "metchurial.cli", ".", "--extract-metadata", "--incremental"],
            cwd=self.d, env=env, capture_output=True, text=True)

    def _refs_tables_rows(self):
        with open(os.path.join(self.d, "refs_tables.tsv"), "r", encoding="utf-8-sig") as f:
            lines = [line.rstrip("\n") for line in f]
        return lines[1:]  # drop header

    def test_unchanged_file_rows_persist_across_incremental_runs(self):
        r1 = self._run_cli()
        self.assertEqual(r1.returncode, 0, r1.stderr)
        rows1 = self._refs_tables_rows()
        self.assertTrue(any("STABLE_TABLE" in row for row in rows1))
        self.assertTrue(any("OLD_TABLE" in row for row in rows1))

        with open(self.changing_path, "w", encoding="utf-8") as f:
            f.write("SELECT c FROM new_table;")

        r2 = self._run_cli()
        self.assertEqual(r2.returncode, 0, r2.stderr)
        rows2 = self._refs_tables_rows()
        self.assertTrue(any("STABLE_TABLE" in row for row in rows2),
                        "unchanged file's rows should still be present via cache merge")
        self.assertTrue(any("NEW_TABLE" in row for row in rows2))
        self.assertFalse(any("OLD_TABLE" in row for row in rows2),
                         "changed file must be rescanned, not served stale from cache")


if __name__ == "__main__":
    unittest.main()
