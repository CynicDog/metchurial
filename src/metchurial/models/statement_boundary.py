# -*- coding: utf-8 -*-
"""BoundaryGuard: the six rules that stop statement-boundary inference
from cutting a statement in half.

parsing/statement_starts.py decides where one statement ends and the next
begins in a file that never terminates its statements with ';'. Its
positive rule is small -- a statement keyword, at paren depth 0, first on
its source line, not preceded by a token that grammatically demands a
query next. Everything hard about the problem lives in the *negative*
cases: SQL constructs where such a token appears and is nonetheless a
continuation, not a new statement.

Those cases are enumerated here rather than buried in an if-chain,
because they are the load-bearing part of the design and the part most
likely to need extending when a new DB2 construct turns up. A false split
is strictly worse than a missed one -- a missed boundary merely
reproduces the old ';'-only behavior, while a false one shreds a valid
statement into fragments -- so each guard is stated with the exact SQL
shape it protects, and tests/test_statement_starts.py runs every
`example` through the real splitter to prove the guard still fires. That
keeps this file from drifting into stale documentation.

`prev_tokens` names Db2Lexer token *types* as strings rather than
importing them: models/ is stdlib-only by contract (see __init__.py), so
parsing/statement_starts.py resolves each name against the generated
lexer when it builds its lookup table. A typo therefore fails loudly at
import time, not silently at scan time.

Guards that cannot be expressed as "the previous token was one of these"
carry no `prev_tokens` and are implemented procedurally against the
in-progress statement's state (does it lead with SELECT, has its one free
inner SELECT been spent, where does its CTE prologue end).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundaryGuard:
    """`guard_id` is the short stable label used in --verbose output and
    in docs/split-selects-and-metadata.md ("G1".."G6"); `name` is a
    machine-stable slug; `rationale` says what would go wrong without it;
    `example` is SQL that MUST stay a single statement and that actually
    trips this guard -- verified by test, not by assertion in prose.
    `prev_tokens`, when non-empty, are Db2Lexer token type names whose
    presence immediately before a candidate keyword means "continuation";
    an empty tuple means the guard is implemented procedurally."""

    guard_id: str
    name: str
    rationale: str
    example: str
    prev_tokens: tuple[str, ...] = ()


# Evaluation order matters and mirrors parsing/statement_starts.py: G4
# first, because a CTE prologue's own SELECT is already spoken for before
# any other test is meaningful.
GUARDS: tuple[BoundaryGuard, ...] = (
    BoundaryGuard(
        guard_id="G4",
        name="cte-prologue-select",
        rationale=(
            "The SELECT that consumes the current statement's own WITH "
            "prologue belongs to that statement. Without this, every CTE "
            "query would be cut in two at its own body."),
        example="WITH AUX AS (SELECT ACCT_ID FROM TBSTAT)\nSELECT X.ACCT_ID FROM AUX X\n",
    ),
    BoundaryGuard(
        guard_id="G1",
        name="set-operator",
        rationale=(
            "A set operator is the one legal way a depth-0 SELECT "
            "continues a statement rather than starting one. ALL/DISTINCT "
            "cover UNION ALL / UNION DISTINCT written with the second "
            "SELECT on the next line."),
        example="SELECT A.ACCT_ID FROM TBACCT A\nUNION ALL\nSELECT S.ACCT_ID FROM TBSTAT S\n",
        prev_tokens=("UNION", "INTERSECT", "EXCEPT", "MINUS", "ALL", "DISTINCT"),
    ),
    BoundaryGuard(
        guard_id="G2",
        name="query-expected",
        rationale=(
            "These tokens grammatically demand a query next, so whatever "
            "follows is a continuation however it is laid out: CREATE VIEW "
            "v AS, DECLARE c CURSOR FOR, MERGE's WHEN MATCHED THEN, and a "
            "CASE arm."),
        example="CREATE VIEW V_ACTIVE AS\nSELECT A.ACCT_ID FROM TBACCT A\n",
        prev_tokens=("AS", "FOR", "THEN", "ELSE", "WHEN",
                     "COMMA", "DOT", "LEFT_RND_BKT", "INTO", "RETURN"),
    ),
    BoundaryGuard(
        guard_id="G3",
        name="first-inner-select",
        rationale=(
            "A statement that does not lead with SELECT gets exactly one "
            "free depth-0 SELECT, which is its body -- INSERT INTO t / "
            "SELECT, CREATE TABLE t AS / SELECT. The second such SELECT is "
            "a genuine new statement, so INSERT ... SELECT followed by a "
            "bare query still splits."),
        example="INSERT INTO TBSTAT\nSELECT A.ACCT_ID FROM TBACCT A\n",
    ),
    BoundaryGuard(
        guard_id="G5",
        name="with-not-a-cte",
        rationale=(
            "DB2's isolation clause puts a bare depth-0 WITH inside a "
            "SELECT -- WITH UR / RS / RR / CS -- as do WITH HOLD, WITH "
            "RETURN and WITH ORDINALITY. A depth-0 WITH is only a "
            "statement start if it validates as a real CTE list, so the "
            "shape does the work and no isolation-keyword denylist can go "
            "stale."),
        example="SELECT A.ACCT_ID FROM TBACCT A\nWITH UR\n",
    ),
    BoundaryGuard(
        guard_id="G6",
        name="set-outside-select",
        rationale=(
            "SET opens a statement of its own (SET CURRENT SCHEMA) but is "
            "also the second line of UPDATE t / SET col = ... . A SELECT "
            "statement cannot contain a depth-0 SET, so it is trusted as a "
            "boundary only there."),
        example="UPDATE TBACCT\nSET STAT_CD = 'A'\nWHERE ACCT_ID IS NOT NULL\n",
    ),
)

GUARDS_BY_ID: dict[str, BoundaryGuard] = {g.guard_id: g for g in GUARDS}
