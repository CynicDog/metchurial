# -*- coding: utf-8 -*-
"""Unit tests for function_visitor.py (Feature 4: function-call usage
extraction, --extract-functions).

Also pins down the known grammar gap documented in function_visitor.py's
module docstring: COUNT/MAX/LOWER are reserved keywords in the vendored
grammar, not the plain `id_` that `function_name` requires, so they can
never be captured by this visitor -- confirmed here rather than just
asserted, so a future grammar update that fixes this gets caught by a
newly-failing test instead of a stale comment nobody notices.

Run:
    python -m unittest tests.test_function_extraction
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from metchurial import engine as scanner  # noqa: E402
from metchurial.models.options import ScanOptions  # noqa: E402


def function_calls_for(text):
    fd, path = tempfile.mkstemp(suffix=".sql")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        result = scanner.scan_file(path, ScanOptions(extract_functions=True))
        return result.function_calls
    finally:
        os.unlink(path)


class TestBasicExtraction(unittest.TestCase):
    def test_single_function_call(self):
        fc = function_calls_for("SELECT SUBSTR(cust_nm, 1, 3) FROM t1;")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "SUBSTR")
        self.assertEqual(fc[0].parameters, "cust_nm, 1, 3")
        self.assertEqual(fc[0].line, 1)

    def test_multiple_calls_in_one_statement(self):
        fc = function_calls_for("SELECT UPPER(col1), COALESCE(a, b) FROM t1;")
        names = sorted(f.function for f in fc)
        self.assertEqual(names, ["COALESCE", "UPPER"])

    def test_nested_function_call_both_captured(self):
        fc = function_calls_for("SELECT SUBSTR(UPPER(col1), 1, 3) FROM t1;")
        names = sorted(f.function for f in fc)
        self.assertEqual(names, ["SUBSTR", "UPPER"])
        substr_row = next(f for f in fc if f.function == "SUBSTR")
        self.assertEqual(substr_row.parameters, "UPPER(col1), 1, 3")

    def test_call_inside_where_clause(self):
        # Both the function call and the "=" predicate wrapping it are
        # captured, as separate rows.
        fc = function_calls_for("SELECT * FROM t1 WHERE UPPER(cust_nm) = 'JOHN';")
        names = sorted(f.function for f in fc)
        self.assertEqual(names, ["=", "UPPER"])
        upper_row = next(f for f in fc if f.function == "UPPER")
        self.assertEqual(upper_row.parameters, "cust_nm")

    def test_disabled_by_default(self):
        fd, path = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("SELECT SUBSTR(cust_nm, 1, 3) FROM t1;")
            result = scanner.scan_file(path)
            self.assertEqual(result.function_calls, [])
        finally:
            os.unlink(path)



class TestReservedKeywordFunctionNames(unittest.TestCase):
    """COUNT/MAX/LOWER (and other common built-ins) are reserved lexer
    tokens, not plain ID -- the vendored grammar's function_name rule
    lists them explicitly so these calls parse like any other. See
    function_visitor.py's module docstring."""

    def test_count_is_captured(self):
        fc = function_calls_for("SELECT COUNT(col1) FROM t1;")
        self.assertIn("COUNT", [f.function for f in fc])

    def test_max_is_captured(self):
        fc = function_calls_for("SELECT MAX(col1) FROM t1;")
        self.assertIn("MAX", [f.function for f in fc])

    def test_reserved_scalar_names_are_captured(self):
        fc = function_calls_for("SELECT LOWER(nm), CHAR(dt), VALUE(x, 0) FROM t1;")
        names = sorted(f.function for f in fc)
        self.assertEqual(names, ["CHAR", "LOWER", "VALUE"])

    def test_sum_and_avg_are_captured(self):
        # SUM/AVG/MIN lex as plain ID and parse normally.
        fc = function_calls_for("SELECT SUM(amt), AVG(amt), MIN(amt) FROM t1;")
        names = sorted(f.function for f in fc)
        self.assertEqual(names, ["AVG", "MIN", "SUM"])


class TestZeroArgumentCall(unittest.TestCase):
    """function_invocation's arg_list is now optional (vendor/grammars-v4
    fix) -- a zero-arg call like NOW() has a valid parse path and is
    captured with an empty parameters string. Previously a known grammar
    gap; see docs/PROVENANCE.md for the fix."""

    def test_zero_argument_call_is_captured(self):
        fc = function_calls_for("SELECT NOW() FROM t1;")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "NOW")
        self.assertEqual(fc[0].parameters, "")


class TestPredicateExtraction(unittest.TestCase):
    def test_comparison_operator(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE ACCT_ID = '123';")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "=")
        self.assertEqual(fc[0].parameters, "ACCT_ID, '123'")

    def test_all_comparison_operators(self):
        fc = function_calls_for(
            "SELECT * FROM t1 WHERE a=1 AND b<>2 AND c<3 AND d>4 AND e<=5 AND f>=6;")
        ops = sorted(f.function for f in fc)
        self.assertEqual(ops, ["<", "<=", "<>", "=", ">", ">="])

    def test_in_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE ACCT_ID IN ('A', 'B', 'C');")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "IN")
        self.assertEqual(fc[0].parameters, "ACCT_ID, ('A', 'B', 'C')")

    def test_not_in_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE ACCT_ID NOT IN ('A', 'B');")
        self.assertEqual(fc[0].function, "NOT IN")

    def test_between_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE amt BETWEEN 1 AND 100;")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "BETWEEN")
        self.assertEqual(fc[0].parameters, "amt, 1, 100")

    def test_not_between_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE amt NOT BETWEEN 1 AND 100;")
        self.assertEqual(fc[0].function, "NOT BETWEEN")

    def test_like_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE cust_nm LIKE 'J%';")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "LIKE")
        self.assertEqual(fc[0].parameters, "cust_nm, 'J%'")

    def test_not_like_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE cust_nm NOT LIKE 'J%';")
        self.assertEqual(fc[0].function, "NOT LIKE")

    def test_is_null_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE cust_nm IS NULL;")
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0].function, "IS NULL")
        self.assertEqual(fc[0].parameters, "cust_nm")

    def test_is_not_null_predicate(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE cust_nm IS NOT NULL;")
        self.assertEqual(fc[0].function, "IS NOT NULL")

    def test_multiple_predicates_in_one_where_clause(self):
        fc = function_calls_for(
            "SELECT * FROM t1 WHERE a.x = 1 AND b.y IN (1, 2, 3) AND c.z IS NULL;")
        ops = sorted(f.function for f in fc)
        self.assertEqual(ops, ["=", "IN", "IS NULL"])

    def test_disabled_by_default(self):
        fd, path = tempfile.mkstemp(suffix=".sql")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("SELECT * FROM t1 WHERE ACCT_ID = '123';")
            result = scanner.scan_file(path)
            self.assertEqual(result.function_calls, [])
        finally:
            os.unlink(path)


class TestUnsupportedPredicatesSkipped(unittest.TestCase):
    """See function_visitor.py's module docstring, Known Limitation 4."""

    def test_exists_is_not_captured(self):
        fc = function_calls_for("SELECT * FROM t1 WHERE EXISTS (SELECT 1 FROM t2);")
        self.assertEqual(fc, [])

    def test_in_distinct_from_is_not_misclassified_as_in(self):
        # `expression IN NOT? DISTINCT FROM expression` shares the IN/NOT
        # tokens with ordinary `IN (...)` -- must not be misclassified.
        fc = function_calls_for("SELECT * FROM t1 WHERE a IN DISTINCT FROM b;")
        self.assertEqual(fc, [])


if __name__ == "__main__":
    unittest.main()
