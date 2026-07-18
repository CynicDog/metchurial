# -*- coding: utf-8 -*-
"""Grammar-level smoke tests for the vendored/generated Db2 SQL parser
(antlr/grammars-v4's sql/db2), independent of the extractor visitor.

These pin down the empirically-observed parsing behavior of the specific
DB2-relevant constructs the detector cares about, so a regenerated parser
(e.g. after a grammar patch) can't silently change this behavior without a
test noticing. See docs/PROVENANCE.md and extractor_visitor.py's/
supplementary_checks.py's module docstrings for why each of these matters.

This project previously used Oracle's PL/SQL grammar as a stand-in (no
maintained DB2 grammar existed at the time). Several of the behaviors
pinned here are genuinely *different* from that version -- most notably,
this Db2-specific grammar has *no* parser-level path at all for the bare
'(' or double-quoted-literal quirks (PL/SQL happened to structurally
support both; this grammar hard-fails on them, by design relying entirely
on supplementary_checks.py's Tier 3 token-scan fallback instead).

Run:
    python -m unittest tests/test_grammar_smoke.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from antlr4 import InputStream, CommonTokenStream  # noqa: E402
from antlr4.error.ErrorListener import ErrorListener  # noqa: E402
from metchurial._generated.Db2Lexer import Db2Lexer  # noqa: E402
from metchurial._generated.Db2Parser import Db2Parser  # noqa: E402


class _CollectingErrorListener(ErrorListener):
    def __init__(self):
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append((line, column, msg))


def parse(text, rule):
    """Parse `text` with the given parser rule name. Returns
    (tree, lexer_errors, parser_errors, remaining_token_text)."""
    lexer = Db2Lexer(InputStream(text))
    lexer.removeErrorListeners()
    lex_err = _CollectingErrorListener()
    lexer.addErrorListener(lex_err)

    stream = CommonTokenStream(lexer)
    parser = Db2Parser(stream)
    parser.removeErrorListeners()
    par_err = _CollectingErrorListener()
    parser.addErrorListener(par_err)

    tree = getattr(parser, rule)()
    next_token = stream.LT(1)
    remaining = None if next_token is None or next_token.text == "<EOF>" else next_token.text
    return tree, lex_err.errors, par_err.errors, remaining


def _type_names(ctx):
    """All context/terminal class names in the subtree, as a set."""
    names = set()

    def walk(node):
        names.add(type(node).__name__)
        if hasattr(node, "getChildCount"):
            for i in range(node.getChildCount()):
                walk(node.getChild(i))

    walk(ctx)
    return names


class TestHostVariables(unittest.TestCase):
    def test_hostvar_has_no_usable_parse_path_in_a_comparison(self):
        # Unlike the PL/SQL grammar this project used to use (where
        # :HOSTVAR parsed cleanly as a Bind_variableContext, just never as
        # a literal leaf), this Db2 grammar's `host_variable: ':' id_`
        # rule is never wired into `expression`'s alternatives -- a
        # comparison against a host variable is a hard parse failure here.
        # This is fine for detection purposes (a host variable must never
        # be reported as a hardcoded literal either way) and is exactly
        # the kind of gap the tiered driver's fallback tiers exist for.
        _tree, lex_errs, par_errs, _remaining = parse("ACCT_ID = :HOSTVAR", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertTrue(par_errs)

    def test_hyphenated_hostvar_also_fails(self):
        _tree, lex_errs, par_errs, _remaining = parse("ACCT_ID = :HOST-VAR", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertTrue(par_errs)


class TestBareParenQuirk(unittest.TestCase):
    def test_bare_paren_literal_has_no_usable_parse_path(self):
        # ACCT_ID ('0000001') -- a DB2/embedded-SQL quirk, likely a
        # dropped IN -- has no function-call-shaped fallback in this
        # grammar the way it did in PL/SQL (`expression` requires a real
        # `function_invocation`, not a bare identifier immediately
        # followed by a parenthesized argument). Handled entirely by
        # supplementary_checks.py's Tier 3 token-scan fallback instead.
        _tree, lex_errs, par_errs, _remaining = parse("ACCT_ID ('0000001')", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertTrue(par_errs)


class TestDoubleQuotedLiteral(unittest.TestCase):
    def test_nonblank_dq_literal_has_no_usable_parse_path(self):
        # DOUBLE_QUOTE_ID is a real lexer token (confirmed: `'"' ~'"'+
        # '"'`) but is never referenced anywhere in Db2Parser.g4 -- it can
        # never be consumed by any parser rule at all, unlike PL/SQL where
        # it resolved as a delimited identifier general_element. Handled
        # entirely by supplementary_checks.py's Tier 3, which treats a
        # DOUBLE_QUOTE_ID token as literal-shaped directly.
        _tree, lex_errs, par_errs, _remaining = parse('ACCT_ID = "0000079"', "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertTrue(par_errs)

    def test_empty_dq_literal_is_a_lexer_error(self):
        # A genuinely empty "" doesn't lex as DOUBLE_QUOTE_ID (needs 1+
        # content chars, `~'"'+`). Harmless in practice -- blank literals
        # are filtered downstream regardless -- but confirmed here it's
        # exactly one isolated lexer error, not something that could
        # swallow subsequent live code.
        _tree, lex_errs, _par_errs, _remaining = parse('ACCT_ID = ""', "search_condition")
        self.assertEqual(len(lex_errs), 1)
        self.assertIn('""', lex_errs[0][2])


class TestFetchRowLimiting(unittest.TestCase):
    def test_fetch_first_and_fetch_next_both_parse(self):
        # The vendored grammar originally modeled only `FETCH NEXT ...
        # ROWS ONLY`, not the also-valid, commonly-used `FETCH FIRST ...
        # ROWS ONLY` -- confirmed as a genuine gap, then patched directly
        # in vendor/grammars-v4/Db2Parser.g4 (`FETCH (NEXT | FIRST) ...`,
        # both NEXT and FIRST already existed as lexer tokens, so this
        # was a one-line addition) since it's real DB2 syntax the original
        # regex tool never had trouble with either. See docs/PROVENANCE.md
        # for why this modification is documented as required, not
        # optional, under the grammar's MIT license.
        for keyword in ("FIRST", "NEXT"):
            text = "SELECT * FROM T WHERE ACCT_ID = '1' FETCH {} 10 ROWS ONLY".format(keyword)
            _tree, lex_errs, par_errs, remaining = parse(text, "sql_statement")
            self.assertEqual(lex_errs, [], keyword)
            self.assertEqual(par_errs, [], keyword)
            self.assertIsNone(remaining, keyword)


class TestStrayUnmatchedParen(unittest.TestCase):
    def test_search_condition_stops_cleanly_before_trailing_stray_paren(self):
        # This is the empirical basis for statement_driver.py's tiered
        # design: search_condition() doesn't require EOF, so a stray ')'
        # left behind by a malformed/truncated comment fragment (fixtures
        # 09/13 in the original tool) is simply left unconsumed, not an
        # error.
        tree, lex_errs, par_errs, remaining = parse("ACCT_ID = '0000050' )", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertEqual(par_errs, [])
        self.assertEqual(tree.getText(), "ACCT_ID='0000050'")
        self.assertEqual(remaining, ")")

    def test_search_condition_beats_sql_statement_on_a_bare_identifier(self):
        # sql_statement() alone accepts a bare identifier (e.g. just
        # "ACCT_ID") as a trivially complete statement, which would
        # otherwise prevent the real comparison right after it from ever
        # being parsed -- this is why statement_driver.py races both
        # rules at the same position and takes whichever consumes more,
        # rather than trusting sql_statement() first.
        text = "ACCT_ID = '0000040'  (old test query, kept for reference)"
        stmt_tree, _le1, stmt_errs, _r1 = parse(text, "sql_statement")
        cond_tree, _le2, cond_errs, _r2 = parse(text, "search_condition")
        self.assertEqual(stmt_errs, [])
        self.assertEqual(cond_errs, [])
        self.assertLess(len(stmt_tree.getText()), len(cond_tree.getText()))
        self.assertEqual(cond_tree.getText(), "ACCT_ID='0000040'")


class TestInBetweenLikeRouting(unittest.TestCase):
    """Pins down that =, <>, <, >, <=, >=, IN, BETWEEN, and LIKE are all
    alternatives of a single, unlabeled `predicate` rule -- which alt
    actually fired must be determined by checking non-None accessors
    (extractor_visitor.py's visitPredicate), not by dispatching on
    subclass, since there are no `#label`s on this rule's alternatives."""

    def test_in_resolves_through_predicate_with_expression_list(self):
        tree, lex_errs, par_errs, remaining = parse(
            "ACCT_ID IN ('1000001','1000002')", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertEqual(par_errs, [])
        self.assertIsNone(remaining)
        self.assertIn("Expression_list_in_parenthesesContext", _type_names(tree))

    def test_between_resolves_through_predicate(self):
        tree, lex_errs, par_errs, remaining = parse(
            "ACCT_ID BETWEEN '0000010' AND '0000099'", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertEqual(par_errs, [])
        self.assertIsNone(remaining)
        self.assertIn("PredicateContext", _type_names(tree))

    def test_like_resolves_through_predicate(self):
        tree, lex_errs, par_errs, remaining = parse(
            "ACCT_ID LIKE '%foo%'", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertEqual(par_errs, [])
        self.assertIsNone(remaining)
        self.assertIn("PredicateContext", _type_names(tree))

    def test_equals_resolves_through_predicate_with_comparison_operator(self):
        tree, lex_errs, par_errs, remaining = parse("ACCT_ID = '0000001'", "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertEqual(par_errs, [])
        self.assertIsNone(remaining)
        self.assertIn("Comparison_operatorContext", _type_names(tree))


class TestSubqueryScoping(unittest.TestCase):
    def test_in_subquery_routes_through_fullselect_not_expression_list(self):
        # COL IN (SELECT ...) must route through fullselect_in_parentheses,
        # not expression_list_in_parentheses -- this is what lets
        # extractor_visitor.py avoid attributing the subquery's own inner
        # literals to the outer IN's column (fixture 10_subquery_in_list.sql).
        text = "CTRT_NO IN (SELECT CTRT_NO FROM TBSAMPLE001 WHERE STAT_CD = '02')"
        tree, lex_errs, par_errs, remaining = parse(text, "search_condition")
        self.assertEqual(lex_errs, [])
        self.assertEqual(par_errs, [])
        self.assertIsNone(remaining)
        self.assertIn("Fullselect_in_parenthesesContext", _type_names(tree))
        self.assertNotIn("Expression_list_in_parenthesesContext", _type_names(tree))


class TestCommentNesting(unittest.TestCase):
    def test_block_comments_support_nesting(self):
        # SQL_COMMENT: '/*' (SQL_COMMENT | .)*? '*/' -- unlike the PL/SQL
        # grammar this project used to use (explicitly non-nesting), this
        # one recurses on itself, so a nested /* */ is absorbed into one
        # single outer hidden token rather than ending the comment early.
        lexer = Db2Lexer(InputStream("/* outer /* inner */ still outer */ SELECT 1"))
        stream = CommonTokenStream(lexer)
        stream.fill()
        comment_tok = stream.tokens[0]
        self.assertEqual(comment_tok.type, Db2Lexer.SQL_COMMENT)
        self.assertEqual(comment_tok.text, "/* outer /* inner */ still outer */")


if __name__ == "__main__":
    unittest.main()
